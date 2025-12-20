"""
AINEON Circuit Breaker & Error Recovery
Production-grade circuit breaker with <1 second response time and comprehensive error handling.

Spec: Daily loss limit enforcement, revert detection, exponential backoff, atomic rollback
Target: <1 second circuit breaker response, 99.99% error detection, zero cascade failures
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Stop execution
    HALF_OPEN = "half_open"  # Testing recovery


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    daily_loss_limit: float  # ETH
    max_consecutive_failures: int = 5
    failure_threshold_percentage: float = 10.0  # % of trades failing
    recovery_timeout: int = 300  # seconds
    backoff_base: float = 2.0  # Exponential backoff multiplier
    backoff_max: float = 120.0  # Max backoff (seconds)


@dataclass
class ErrorEvent:
    """Error event tracking."""
    timestamp: datetime
    error_type: str
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[float] = None


@dataclass
class CircuitBreakerMetrics:
    """Metrics tracked by circuit breaker."""
    daily_loss: float = 0.0  # ETH
    consecutive_failures: int = 0
    total_errors: int = 0
    last_error_time: Optional[datetime] = None
    total_recovery_time: float = 0.0
    state_changes: int = 0


class ErrorRecoveryEngine:
    """
    Error recovery with exponential backoff and retry logic.
    
    Features:
    - Exponential backoff calculation
    - Jitter to prevent thundering herd
    - Maximum retry limits
    - Circuit breaker integration
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        """Initialize error recovery engine."""
        self.config = config
        self.retry_counts: Dict[str, int] = {}
        self.backoff_times: Dict[str, float] = {}
    
    async def execute_with_retry(
        self,
        operation_id: str,
        operation: Callable,
        max_retries: Optional[int] = None,
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        Execute operation with exponential backoff retry.
        
        Args:
            operation_id: Unique operation identifier
            operation: Async callable to execute
            max_retries: Maximum retry attempts (default: config max_consecutive_failures)
            
        Returns:
            Tuple of (success, result, error_message)
        """
        if max_retries is None:
            max_retries = self.config.max_consecutive_failures
        
        retry_count = self.retry_counts.get(operation_id, 0)
        
        while retry_count < max_retries:
            try:
                result = await operation()
                
                # Clear retry count on success
                self.retry_counts[operation_id] = 0
                self.backoff_times[operation_id] = 0.0
                
                logger.debug(f"Operation succeeded after {retry_count} retries: {operation_id}")
                return True, result, None
                
            except Exception as e:
                retry_count += 1
                self.retry_counts[operation_id] = retry_count
                
                if retry_count >= max_retries:
                    logger.error(f"Operation failed after {max_retries} retries: {operation_id} - {e}")
                    return False, None, str(e)
                
                # Calculate exponential backoff with jitter
                backoff_time = self._calculate_backoff(retry_count)
                self.backoff_times[operation_id] = backoff_time
                
                logger.warning(
                    f"Operation failed (attempt {retry_count}/{max_retries}): {operation_id} - {e}. "
                    f"Retrying in {backoff_time:.2f}s"
                )
                
                await asyncio.sleep(backoff_time)
        
        return False, None, "Max retries exceeded"
    
    def _calculate_backoff(self, retry_count: int) -> float:
        """
        Calculate exponential backoff time with jitter.
        
        Args:
            retry_count: Retry attempt number (1-indexed)
            
        Returns:
            Backoff time in seconds
        """
        import random
        
        # Exponential: 2^retry_count
        backoff = self.config.backoff_base ** retry_count
        
        # Cap at max backoff
        backoff = min(backoff, self.config.backoff_max)
        
        # Add jitter (±20%)
        jitter = random.uniform(0.8, 1.2)
        
        return backoff * jitter
    
    def get_retry_info(self, operation_id: str) -> Dict[str, Any]:
        """Get retry information for operation."""
        return {
            "retry_count": self.retry_counts.get(operation_id, 0),
            "backoff_time": self.backoff_times.get(operation_id, 0.0),
        }


class CircuitBreaker:
    """
    Production-grade circuit breaker with <1 second response time.
    
    Features:
    - Daily loss limit enforcement (100 ETH hard stop)
    - Consecutive failure tracking
    - State machine (CLOSED → OPEN → HALF_OPEN)
    - Error event logging
    - Automatic recovery
    """
    
    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.error_events: List[ErrorEvent] = []
        self.recovery_start_time: Optional[datetime] = None
        self.error_recovery = ErrorRecoveryEngine(config)
        
        logger.info(f"Circuit breaker initialized with config: {config}")
    
    async def check_before_execution(
        self,
        operation_data: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Check circuit breaker state before executing operation.
        
        Args:
            operation_data: Operation details (profit, loss, etc.)
            
        Returns:
            Tuple of (can_execute, reason_if_blocked)
        """
        # Fast path: <1 microsecond state check
        start_time = time.monotonic()
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            elapsed = time.monotonic() - start_time
            if elapsed > 1.0:  # Warn if >1ms
                logger.warning(f"Circuit breaker check took {elapsed*1000:.2f}ms (>1ms target)")
            return False, "Circuit breaker is OPEN - too many errors"
        
        # Check daily loss limit
        daily_loss = operation_data.get("estimated_loss", 0)
        if self.metrics.daily_loss + daily_loss > self.config.daily_loss_limit:
            self._trip_circuit(
                "daily_loss_exceeded",
                ErrorSeverity.CRITICAL,
                f"Daily loss would exceed {self.config.daily_loss_limit} ETH"
            )
            return False, f"Daily loss limit exceeded ({self.config.daily_loss_limit} ETH)"
        
        elapsed = time.monotonic() - start_time
        if elapsed > 0.001:  # 1ms threshold
            logger.warning(f"Circuit breaker check took {elapsed*1000:.2f}ms (>1ms target)")
        
        return True, None
    
    async def record_execution_result(
        self,
        operation_id: str,
        success: bool,
        result_data: Dict[str, Any],
    ):
        """
        Record execution result and update circuit state.
        
        Args:
            operation_id: Operation identifier
            success: Whether execution was successful
            result_data: Result details (profit, loss, gas, error, etc.)
        """
        if success:
            # Record profit/loss
            if "profit" in result_data:
                profit = result_data["profit"]
                if profit < 0:
                    self.metrics.daily_loss += abs(profit)
            
            # Reset consecutive failures
            self.metrics.consecutive_failures = 0
            
            logger.debug(f"Operation succeeded: {operation_id}")
        else:
            # Record failure
            self.metrics.consecutive_failures += 1
            self.metrics.total_errors += 1
            self.metrics.last_error_time = datetime.now()
            
            error_msg = result_data.get("error", "Unknown error")
            severity = self._determine_severity(result_data)
            
            self._record_error(
                operation_id,
                error_msg,
                severity,
                result_data
            )
            
            logger.warning(
                f"Operation failed: {operation_id} ({severity.value}) - {error_msg}. "
                f"Consecutive failures: {self.metrics.consecutive_failures}"
            )
            
            # Check if should trip circuit
            if self.metrics.consecutive_failures >= self.config.max_consecutive_failures:
                self._trip_circuit(
                    "consecutive_failures",
                    ErrorSeverity.CRITICAL,
                    f"Consecutive failures: {self.metrics.consecutive_failures}"
                )
    
    def _trip_circuit(
        self,
        error_type: str,
        severity: ErrorSeverity,
        message: str,
    ):
        """Trip circuit breaker to OPEN state."""
        if self.state == CircuitState.CLOSED:
            self.state = CircuitState.OPEN
            self.recovery_start_time = datetime.now()
            self.metrics.state_changes += 1
            
            self._record_error(
                "circuit_breaker",
                error_type,
                severity,
                {"message": message}
            )
            
            logger.critical(f"CIRCUIT BREAKER TRIPPED: {error_type} - {message}")
    
    def _determine_severity(self, result_data: Dict[str, Any]) -> ErrorSeverity:
        """Determine error severity from result data."""
        error = result_data.get("error", "").lower()
        
        if any(x in error for x in ["revert", "out_of_gas", "execution_failed"]):
            return ErrorSeverity.CRITICAL
        elif any(x in error for x in ["slippage", "timeout", "invalid"]):
            return ErrorSeverity.HIGH
        elif any(x in error for x in ["connection", "network"]):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _record_error(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity,
        context: Dict[str, Any],
    ):
        """Record error event."""
        event = ErrorEvent(
            timestamp=datetime.now(),
            error_type=error_type,
            severity=severity,
            message=message,
            context=context,
        )
        self.error_events.append(event)
        
        # Keep only last 1000 events
        if len(self.error_events) > 1000:
            self.error_events = self.error_events[-1000:]
    
    async def attempt_recovery(self) -> Tuple[bool, Optional[str]]:
        """
        Attempt to recover from OPEN state.
        
        Returns:
            Tuple of (recovered, error_if_not)
        """
        if self.state != CircuitState.OPEN:
            return True, None
        
        if self.recovery_start_time is None:
            return False, "Recovery start time not set"
        
        # Check if recovery timeout elapsed
        elapsed = (datetime.now() - self.recovery_start_time).total_seconds()
        if elapsed < self.config.recovery_timeout:
            remaining = self.config.recovery_timeout - elapsed
            return False, f"Recovery timeout in {remaining:.0f}s"
        
        # Transition to HALF_OPEN for testing
        self.state = CircuitState.HALF_OPEN
        self.metrics.state_changes += 1
        
        logger.info("Circuit breaker transitioned to HALF_OPEN - testing recovery")
        return True, None
    
    async def confirm_recovery(self):
        """Confirm recovery and close circuit."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.metrics.consecutive_failures = 0
            self.metrics.daily_loss = 0.0
            self.recovery_start_time = None
            self.metrics.state_changes += 1
            
            logger.info("Circuit breaker CLOSED - recovery successful")
    
    async def reopen_circuit(self):
        """Reopen circuit if recovery failed."""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.recovery_start_time = datetime.now()
            self.metrics.state_changes += 1
            
            logger.warning("Circuit breaker reopened - recovery failed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "daily_loss_eth": self.metrics.daily_loss,
            "daily_loss_limit_eth": self.config.daily_loss_limit,
            "consecutive_failures": self.metrics.consecutive_failures,
            "max_failures": self.config.max_consecutive_failures,
            "total_errors": self.metrics.total_errors,
            "state_changes": self.metrics.state_changes,
            "recovery_timeout_sec": self.config.recovery_timeout,
            "last_error_time": self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None,
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error events."""
        recent = self.error_events[-limit:]
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "error_type": e.error_type,
                "severity": e.severity.value,
                "message": e.message,
                "context": e.context,
            }
            for e in recent
        ]
    
    def log_status(self):
        """Log circuit breaker status."""
        status = self.get_status()
        logger.info("=" * 70)
        logger.info("CIRCUIT BREAKER STATUS")
        logger.info("=" * 70)
        logger.info(f"State: {status['state'].upper()}")
        logger.info(f"Daily Loss: {status['daily_loss_eth']:.2f} / {status['daily_loss_limit_eth']:.2f} ETH")
        logger.info(f"Consecutive Failures: {status['consecutive_failures']} / {status['max_failures']}")
        logger.info(f"Total Errors: {status['total_errors']}")
        logger.info(f"State Changes: {status['state_changes']}")
        logger.info(f"Last Error: {status['last_error_time']}")
        logger.info("=" * 70)


# Singleton instances
_circuit_breaker: Optional[CircuitBreaker] = None


def initialize_circuit_breaker(
    config: CircuitBreakerConfig,
) -> CircuitBreaker:
    """Initialize circuit breaker."""
    global _circuit_breaker
    _circuit_breaker = CircuitBreaker(config)
    return _circuit_breaker


def get_circuit_breaker() -> CircuitBreaker:
    """Get current circuit breaker instance."""
    if _circuit_breaker is None:
        raise RuntimeError("Circuit breaker not initialized")
    return _circuit_breaker
