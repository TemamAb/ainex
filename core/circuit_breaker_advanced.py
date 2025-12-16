"""
Circuit Breaker (Advanced) - Multi-Level Failure Handling
Implements circuit breaker pattern with multiple states, manual override, and auto-recovery
"""

import os
import logging
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery
    ISOLATED = "isolated"  # Manual override


@dataclass
class CircuitMetrics:
    """Metrics for a circuit"""
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    failure_rate: float = 0.0
    
    def update_failure(self):
        """Record a failure"""
        self.total_failures += 1
        self.total_requests += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.utcnow()
        self._update_failure_rate()
    
    def update_success(self):
        """Record a success"""
        self.total_successes += 1
        self.total_requests += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.utcnow()
        self._update_failure_rate()
    
    def _update_failure_rate(self):
        """Calculate failure rate"""
        if self.total_requests > 0:
            self.failure_rate = self.total_failures / self.total_requests
        else:
            self.failure_rate = 0.0
    
    def reset(self):
        """Reset metrics"""
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.failure_rate = 0.0


@dataclass
class CircuitThresholds:
    """Thresholds for circuit state transitions"""
    failure_threshold: int = 5  # Failures to open circuit
    success_threshold: int = 3  # Successes to close circuit
    failure_rate_threshold: float = 0.5  # 50% failure rate
    timeout_seconds: int = 60  # Time before attempting recovery
    half_open_max_calls: int = 1  # Requests in half-open state


class CircuitBreaker:
    """Advanced circuit breaker with multiple levels and recovery"""
    
    def __init__(self, name: str, thresholds: Optional[CircuitThresholds] = None):
        self.name = name
        self.thresholds = thresholds or CircuitThresholds()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.state_changed_at = datetime.utcnow()
        self.manual_override = False
        self.override_state: Optional[CircuitState] = None
        self.state_history: deque = deque(maxlen=1000)
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            current_state = self._get_effective_state()
        
        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(f"Circuit '{self.name}' is OPEN")
        
        if current_state == CircuitState.ISOLATED:
            raise CircuitBreakerIsolatedError(f"Circuit '{self.name}' is ISOLATED (manual override)")
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Record success
            async with self._lock:
                self.metrics.update_success()
                await self._check_state_transition()
            
            return result
            
        except Exception as e:
            # Record failure
            async with self._lock:
                self.metrics.update_failure()
                await self._check_state_transition()
            
            raise
    
    async def _check_state_transition(self):
        """Check if state should change"""
        current_state = self.state
        
        if current_state == CircuitState.CLOSED:
            # Check if should open
            if (self.metrics.consecutive_failures >= self.thresholds.failure_threshold or
                self.metrics.failure_rate >= self.thresholds.failure_rate_threshold):
                await self._transition_to(CircuitState.OPEN)
        
        elif current_state == CircuitState.OPEN:
            # Check if should transition to half-open (timeout elapsed)
            time_open = datetime.utcnow() - self.state_changed_at
            if time_open.total_seconds() >= self.thresholds.timeout_seconds:
                await self._transition_to(CircuitState.HALF_OPEN)
        
        elif current_state == CircuitState.HALF_OPEN:
            # Check if should close or reopen
            if self.metrics.consecutive_successes >= self.thresholds.success_threshold:
                await self._transition_to(CircuitState.CLOSED)
                self.metrics.reset()
            elif self.metrics.consecutive_failures >= 1:
                await self._transition_to(CircuitState.OPEN)
    
    async def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        old_state = self.state
        self.state = new_state
        self.state_changed_at = datetime.utcnow()
        
        self.state_history.append({
            'from': old_state.value,
            'to': new_state.value,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': {
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'failure_rate': self.metrics.failure_rate,
            }
        })
        
        logger.warning(f"Circuit '{self.name}' transitioned: {old_state.value} → {new_state.value}")
    
    def _get_effective_state(self) -> CircuitState:
        """Get the effective current state (considering manual overrides)"""
        if self.manual_override and self.override_state:
            return self.override_state
        return self.state
    
    async def set_manual_override(self, state: Optional[CircuitState] = None):
        """Manually set circuit state"""
        async with self._lock:
            if state is None:
                self.manual_override = False
                self.override_state = None
                logger.info(f"Circuit '{self.name}' manual override removed")
            else:
                self.manual_override = True
                self.override_state = state
                logger.warning(f"Circuit '{self.name}' manually set to {state.value}")
    
    async def reset(self):
        """Reset circuit to closed state"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics.reset()
            self.state_changed_at = datetime.utcnow()
            logger.info(f"Circuit '{self.name}' manually reset to CLOSED")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'effective_state': self._get_effective_state().value,
            'manual_override': self.manual_override,
            'metrics': {
                'total_requests': self.metrics.total_requests,
                'total_failures': self.metrics.total_failures,
                'total_successes': self.metrics.total_successes,
                'consecutive_failures': self.metrics.consecutive_failures,
                'consecutive_successes': self.metrics.consecutive_successes,
                'failure_rate': round(self.metrics.failure_rate, 4),
            },
            'state_changed_at': self.state_changed_at.isoformat(),
            'thresholds': {
                'failure_threshold': self.thresholds.failure_threshold,
                'success_threshold': self.thresholds.success_threshold,
                'failure_rate_threshold': self.thresholds.failure_rate_threshold,
                'timeout_seconds': self.thresholds.timeout_seconds,
            }
        }


class CircuitBreakerRegistry:
    """Registry of circuit breakers"""
    
    def __init__(self):
        self.circuits: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, name: str, thresholds: Optional[CircuitThresholds] = None) -> CircuitBreaker:
        """Register a new circuit breaker"""
        async with self._lock:
            if name in self.circuits:
                logger.warning(f"Circuit '{name}' already registered, returning existing")
                return self.circuits[name]
            
            circuit = CircuitBreaker(name, thresholds)
            self.circuits[name] = circuit
            logger.info(f"Circuit registered: {name}")
            return circuit
    
    async def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker by name"""
        return self.circuits.get(name)
    
    async def get_all_status(self) -> Dict[str, Dict]:
        """Get status of all circuits"""
        return {name: circuit.get_status() for name, circuit in self.circuits.items()}
    
    async def reset_all(self):
        """Reset all circuits"""
        for circuit in self.circuits.values():
            await circuit.reset()
        logger.info("All circuits reset")
    
    async def shutdown(self):
        """Shutdown registry"""
        self.circuits.clear()
        logger.info("Circuit breaker registry shutdown")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit is open"""
    pass


class CircuitBreakerIsolatedError(Exception):
    """Raised when circuit is isolated (manual override)"""
    pass


# Global registry
_registry: Optional[CircuitBreakerRegistry] = None


async def init_circuit_breakers() -> CircuitBreakerRegistry:
    """Initialize global circuit breaker registry"""
    global _registry
    _registry = CircuitBreakerRegistry()
    return _registry


async def get_or_create_circuit(name: str, thresholds: Optional[CircuitThresholds] = None) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    global _registry
    if not _registry:
        _registry = await init_circuit_breakers()
    
    return await _registry.register(name, thresholds)


async def execute_with_circuit(circuit_name: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with circuit breaker protection"""
    circuit = await get_or_create_circuit(circuit_name)
    return await circuit.call(func, *args, **kwargs)


async def get_circuit_status(circuit_name: str) -> Optional[Dict]:
    """Get status of a circuit"""
    circuit = await get_or_create_circuit(circuit_name)
    return circuit.get_status() if circuit else None


async def shutdown_circuits():
    """Shutdown circuit breaker system"""
    global _registry
    if _registry:
        await _registry.shutdown()
        _registry = None
