"""
AINEON Error Recovery Engine
Implements robust error handling and recovery strategies.

Features:
- Revert detection and classification
- Multi-strategy recovery (slippage, gas, liquidity)
- Exponential backoff retry logic
- Circuit breaker with cooldown
- Comprehensive error logging
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Transaction error classification."""
    SLIPPAGE = "slippage_exceeded"
    GAS = "gas_insufficient"
    LIQUIDITY = "insufficient_liquidity"
    EXECUTION = "smart_contract_execution"
    VALIDATION = "validation_failed"
    TIMEOUT = "timeout"
    NETWORK = "network_error"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies."""
    RETRY_REDUCED_SLIPPAGE = "retry_reduced_slippage"
    RETRY_HIGHER_GAS = "retry_higher_gas"
    RETRY_ALTERNATIVE_PROVIDER = "retry_alternative_provider"
    RETRY_SMALLER_POSITION = "retry_smaller_position"
    ABORT_GRACEFUL = "abort_graceful"
    MANUAL_REVIEW = "manual_review"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Breaker tripped, not executing
    HALF_OPEN = "half_open"  # Testing if recovered


class ErrorRecoveryEngine:
    """
    Implements error recovery and resilience strategies.
    
    Features:
    - Error classification and analysis
    - Multi-strategy recovery attempts
    - Exponential backoff
    - Circuit breaker with automatic reset
    - Error tracking and alerting
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 250,
        backoff_multiplier: float = 2.0,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_cooldown_min: int = 15,
    ):
        """
        Initialize error recovery engine.
        
        Args:
            max_retries: Maximum retry attempts
            initial_backoff_ms: Initial backoff in milliseconds
            backoff_multiplier: Exponential backoff multiplier
            circuit_breaker_threshold: Failures before circuit breaker trips
            circuit_breaker_cooldown_min: Cooldown duration in minutes
        """
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.backoff_multiplier = backoff_multiplier
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_cooldown = timedelta(minutes=circuit_breaker_cooldown_min)
        
        # Circuit breaker state
        self.breaker_state = CircuitBreakerState.CLOSED
        self.breaker_trip_time: Optional[datetime] = None
        self.consecutive_failures = 0
        
        # Error tracking
        self.errors_by_type: Dict[ErrorType, int] = {e: 0 for e in ErrorType}
        self.total_recovery_attempts = 0
        self.successful_recoveries = 0
        
        logger.info(f"Error recovery engine initialized")
        logger.info(f"  Max retries: {max_retries}")
        logger.info(f"  Initial backoff: {initial_backoff_ms}ms")
        logger.info(f"  Circuit breaker threshold: {circuit_breaker_threshold}")
    
    async def handle_error(
        self,
        error: Exception,
        transaction_data: Dict[str, Any],
        attempt_number: int = 1,
    ) -> Tuple[Optional[RecoveryStrategy], Optional[Dict[str, Any]]]:
        """
        Handle transaction error and determine recovery strategy.
        
        Args:
            error: The exception that occurred
            transaction_data: Original transaction data
            attempt_number: Current attempt number (1-indexed)
            
        Returns:
            Tuple of (recovery_strategy, adjusted_transaction_data)
        """
        try:
            # Check circuit breaker first
            if self.breaker_state == CircuitBreakerState.OPEN:
                if not self._check_circuit_breaker_reset():
                    logger.error(f"🔴 Circuit breaker OPEN - stopping execution")
                    return None, None
            
            # Classify error
            error_type = self._classify_error(error)
            self.errors_by_type[error_type] += 1
            
            logger.warning(f"⚠️  Error detected: {error_type.value}")
            logger.debug(f"  Error message: {str(error)}")
            logger.debug(f"  Attempt: {attempt_number}/{self.max_retries}")
            
            # Check if we have retries left
            if attempt_number >= self.max_retries:
                logger.error(f"❌ Max retries exhausted ({self.max_retries})")
                self._handle_max_retries_exceeded()
                return RecoveryStrategy.ABORT_GRACEFUL, None
            
            # Determine recovery strategy
            strategy = self._get_recovery_strategy(error_type, attempt_number)
            
            # Apply recovery
            adjusted_tx = await self._apply_recovery_strategy(strategy, transaction_data)
            
            logger.info(f"✅ Recovery strategy: {strategy.value}")
            self.total_recovery_attempts += 1
            
            return strategy, adjusted_tx
            
        except Exception as e:
            logger.error(f"Error in error handling: {e}", exc_info=True)
            return None, None
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error type based on error message.
        
        Args:
            error: Exception to classify
            
        Returns:
            Classified ErrorType
        """
        error_str = str(error).lower()
        
        # Slippage errors
        if "slippage" in error_str or "tolerance" in error_str:
            return ErrorType.SLIPPAGE
        
        # Gas errors
        if "gas" in error_str or "insufficient funds" in error_str:
            return ErrorType.GAS
        
        # Liquidity errors
        if "liquidity" in error_str or "pool" in error_str:
            return ErrorType.LIQUIDITY
        
        # Execution errors
        if "execution" in error_str or "revert" in error_str:
            return ErrorType.EXECUTION
        
        # Validation errors
        if "invalid" in error_str or "validation" in error_str:
            return ErrorType.VALIDATION
        
        # Network/timeout errors
        if "timeout" in error_str or "timeout" in error_str:
            return ErrorType.TIMEOUT
        
        if "connection" in error_str or "network" in error_str:
            return ErrorType.NETWORK
        
        return ErrorType.UNKNOWN
    
    def _get_recovery_strategy(
        self,
        error_type: ErrorType,
        attempt_number: int,
    ) -> RecoveryStrategy:
        """
        Determine recovery strategy based on error type.
        
        Args:
            error_type: Type of error
            attempt_number: Current attempt number
            
        Returns:
            Recommended recovery strategy
        """
        if error_type == ErrorType.SLIPPAGE:
            # Reduce slippage tolerance progressively
            return RecoveryStrategy.RETRY_REDUCED_SLIPPAGE
        
        elif error_type == ErrorType.GAS:
            # Increase gas price
            return RecoveryStrategy.RETRY_HIGHER_GAS
        
        elif error_type == ErrorType.LIQUIDITY:
            # Try alternative flash loan provider
            if attempt_number == 1:
                return RecoveryStrategy.RETRY_ALTERNATIVE_PROVIDER
            else:
                # Fallback to smaller position
                return RecoveryStrategy.RETRY_SMALLER_POSITION
        
        elif error_type == ErrorType.EXECUTION:
            # Smart contract error - likely unrecoverable
            return RecoveryStrategy.MANUAL_REVIEW
        
        elif error_type == ErrorType.VALIDATION:
            # Invalid input - don't retry
            return RecoveryStrategy.ABORT_GRACEFUL
        
        elif error_type in (ErrorType.TIMEOUT, ErrorType.NETWORK):
            # Network issue - retry with backoff
            return RecoveryStrategy.RETRY_HIGHER_GAS
        
        else:
            # Unknown - try retry with higher gas
            return RecoveryStrategy.RETRY_HIGHER_GAS
    
    async def _apply_recovery_strategy(
        self,
        strategy: RecoveryStrategy,
        transaction_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply recovery strategy to transaction data.
        
        Args:
            strategy: Recovery strategy to apply
            transaction_data: Original transaction data
            
        Returns:
            Adjusted transaction data
        """
        adjusted = transaction_data.copy()
        
        try:
            if strategy == RecoveryStrategy.RETRY_REDUCED_SLIPPAGE:
                # Increase slippage tolerance by 0.05%
                current_slippage = Decimal(str(adjusted.get("maxSlippage", "0.1")))
                adjusted["maxSlippage"] = str(current_slippage + Decimal("0.05"))
                logger.debug(f"  Slippage adjusted to {adjusted['maxSlippage']}%")
            
            elif strategy == RecoveryStrategy.RETRY_HIGHER_GAS:
                # Increase gas price by 20%
                current_gas = Decimal(str(adjusted.get("maxFeePerGas", "0")))
                adjusted["maxFeePerGas"] = str(int(current_gas * Decimal("1.2")))
                logger.debug(f"  Gas price increased by 20%")
            
            elif strategy == RecoveryStrategy.RETRY_SMALLER_POSITION:
                # Reduce position size by 30%
                current_amount = Decimal(str(adjusted.get("amount", "0")))
                adjusted["amount"] = str(int(current_amount * Decimal("0.7")))
                logger.debug(f"  Position reduced to 70% of original")
            
            elif strategy == RecoveryStrategy.RETRY_ALTERNATIVE_PROVIDER:
                # Mark for alternative flash loan provider
                adjusted["useAlternativeProvider"] = True
                logger.debug(f"  Marked for alternative provider")
            
            elif strategy == RecoveryStrategy.ABORT_GRACEFUL:
                logger.info(f"  Aborting transaction gracefully")
                return None
            
            elif strategy == RecoveryStrategy.MANUAL_REVIEW:
                logger.warning(f"  Requiring manual review")
                return None
            
            return adjusted
            
        except Exception as e:
            logger.error(f"Error applying strategy: {e}")
            return transaction_data
    
    async def apply_backoff(self, attempt_number: int):
        """
        Apply exponential backoff before retry.
        
        Args:
            attempt_number: Current attempt number (1-indexed)
        """
        if attempt_number >= self.max_retries:
            return
        
        # Calculate backoff: 250ms, 500ms, 1000ms
        backoff_ms = self.initial_backoff_ms * (self.backoff_multiplier ** (attempt_number - 1))
        backoff_seconds = backoff_ms / 1000.0
        
        logger.debug(f"Backoff: sleeping {backoff_ms}ms before retry {attempt_number + 1}")
        await asyncio.sleep(backoff_seconds)
    
    def _check_circuit_breaker_reset(self) -> bool:
        """
        Check if circuit breaker should be reset from OPEN to HALF_OPEN.
        
        Returns:
            True if circuit breaker is reset (CLOSED or HALF_OPEN)
        """
        if self.breaker_state != CircuitBreakerState.OPEN:
            return True
        
        # Check if cooldown expired
        if self.breaker_trip_time is None:
            return False
        
        elapsed = datetime.now() - self.breaker_trip_time
        
        if elapsed >= self.circuit_breaker_cooldown:
            logger.info(f"🟢 Circuit breaker cooldown expired - entering HALF_OPEN state")
            self.breaker_state = CircuitBreakerState.HALF_OPEN
            self.consecutive_failures = 0
            return True
        
        return False
    
    def _handle_max_retries_exceeded(self):
        """Handle situation when maximum retries are exhausted."""
        self.consecutive_failures += 1
        
        if self.consecutive_failures >= self.circuit_breaker_threshold:
            logger.error(f"🔴 Circuit breaker TRIPPED after {self.consecutive_failures} failures")
            self.breaker_state = CircuitBreakerState.OPEN
            self.breaker_trip_time = datetime.now()
        
        logger.error(f"⚠️  Consecutive failures: {self.consecutive_failures}/{self.circuit_breaker_threshold}")
    
    def record_success(self):
        """Record successful execution after recovery."""
        self.successful_recoveries += 1
        self.consecutive_failures = 0
        
        if self.breaker_state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"🟢 Circuit breaker CLOSED - operation succeeded in HALF_OPEN state")
            self.breaker_state = CircuitBreakerState.CLOSED
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error recovery statistics."""
        total_errors = sum(self.errors_by_type.values())
        success_rate = (
            (self.successful_recoveries / self.total_recovery_attempts)
            if self.total_recovery_attempts > 0
            else 0
        )
        
        return {
            "total_errors": total_errors,
            "errors_by_type": {e.value: c for e, c in self.errors_by_type.items()},
            "recovery_attempts": self.total_recovery_attempts,
            "successful_recoveries": self.successful_recoveries,
            "recovery_success_rate": success_rate,
            "circuit_breaker_state": self.breaker_state.value,
            "consecutive_failures": self.consecutive_failures,
        }
    
    def log_stats(self):
        """Log error recovery statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("ERROR RECOVERY STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total Errors: {stats['total_errors']}")
        logger.info(f"  Slippage: {stats['errors_by_type']['slippage_exceeded']}")
        logger.info(f"  Gas: {stats['errors_by_type']['gas_insufficient']}")
        logger.info(f"  Liquidity: {stats['errors_by_type']['insufficient_liquidity']}")
        logger.info(f"  Execution: {stats['errors_by_type']['smart_contract_execution']}")
        logger.info(f"Recovery Attempts: {stats['recovery_attempts']}")
        logger.info(f"Successful Recoveries: {stats['successful_recoveries']}")
        logger.info(f"Recovery Success Rate: {stats['recovery_success_rate']:.2%}")
        logger.info(f"Circuit Breaker State: {stats['circuit_breaker_state']}")
        logger.info(f"Consecutive Failures: {stats['consecutive_failures']}")
        logger.info("=" * 70)


# Singleton instance
_error_recovery: Optional[ErrorRecoveryEngine] = None


def initialize_error_recovery(
    max_retries: int = 3,
    initial_backoff_ms: int = 250,
) -> ErrorRecoveryEngine:
    """Initialize error recovery engine."""
    global _error_recovery
    _error_recovery = ErrorRecoveryEngine(max_retries=max_retries, initial_backoff_ms=initial_backoff_ms)
    return _error_recovery


def get_error_recovery() -> ErrorRecoveryEngine:
    """Get current error recovery engine instance."""
    if _error_recovery is None:
        raise RuntimeError("Error recovery engine not initialized")
    return _error_recovery
