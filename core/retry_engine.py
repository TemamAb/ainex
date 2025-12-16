"""
Retry Engine - Exponential Backoff with Jitter
Intelligent retry logic with dead-letter queue and configurable policies
"""

import os
import logging
import asyncio
import random
from typing import Callable, Any, Optional, List, Dict, Type, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    FIBONACCI = "fibonacci"


@dataclass
class RetryPolicy:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    initial_delay_ms: float = 100
    max_delay_ms: float = 32000
    exponential_base: float = 2.0
    jitter_enabled: bool = True
    jitter_factor: float = 0.1
    timeout_seconds: float = 300
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    
    def get_delay_ms(self, attempt: int) -> float:
        """Calculate delay for attempt number"""
        if self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.initial_delay_ms * (self.exponential_base ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.initial_delay_ms * attempt
        elif self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.initial_delay_ms
        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self._fibonacci_delay(attempt)
        else:
            delay = self.initial_delay_ms
        
        # Cap at max delay
        delay = min(delay, self.max_delay_ms)
        
        # Add jitter if enabled
        if self.jitter_enabled:
            jitter = delay * self.jitter_factor * random.random()
            delay = delay + jitter
        
        return delay
    
    @staticmethod
    def _fibonacci_delay(attempt: int) -> float:
        """Calculate Fibonacci-based delay"""
        fib = [1, 1]
        for i in range(2, attempt):
            fib.append(fib[-1] + fib[-2])
        return float(fib[min(attempt - 1, len(fib) - 1)] * 100)


@dataclass
class RetryAttempt:
    """Record of a retry attempt"""
    attempt_number: int
    timestamp: datetime
    delay_ms: float
    exception: Optional[Exception] = None
    result: Optional[Any] = None
    success: bool = False


@dataclass
class FailedOperation:
    """Operation that failed after all retries"""
    operation_id: str
    function_name: str
    args: tuple
    kwargs: dict
    attempts: List[RetryAttempt]
    final_exception: Exception
    added_to_dlq_at: datetime = field(default_factory=datetime.utcnow)


class RetryEngine:
    """Executes operations with retry logic and dead-letter queue"""
    
    def __init__(self):
        self.policies: Dict[str, RetryPolicy] = {}
        self.dead_letter_queue: deque = deque(maxlen=10000)
        self.operation_history: Dict[str, List[RetryAttempt]] = {}
    
    def register_policy(self, operation_name: str, policy: RetryPolicy) -> None:
        """Register retry policy for an operation"""
        self.policies[operation_name] = policy
        logger.info(f"Retry policy registered: {operation_name}")
    
    async def execute_with_retry(self, operation_name: str, func: Callable,
                                 *args, policy: Optional[RetryPolicy] = None,
                                 **kwargs) -> Any:
        """Execute function with automatic retry logic"""
        
        # Get policy
        if policy is None:
            if operation_name in self.policies:
                policy = self.policies[operation_name]
            else:
                policy = RetryPolicy()
        
        attempts: List[RetryAttempt] = []
        operation_id = f"{operation_name}_{datetime.utcnow().timestamp()}"
        
        for attempt_num in range(1, policy.max_attempts + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=policy.timeout_seconds
                    )
                else:
                    result = func(*args, **kwargs)
                
                # Success
                attempt = RetryAttempt(
                    attempt_number=attempt_num,
                    timestamp=datetime.utcnow(),
                    delay_ms=0,
                    result=result,
                    success=True
                )
                attempts.append(attempt)
                self.operation_history[operation_id] = attempts
                
                logger.debug(f"Operation '{operation_name}' succeeded on attempt {attempt_num}")
                return result
                
            except Exception as e:
                # Check if exception is retryable
                if not isinstance(e, policy.retryable_exceptions):
                    logger.error(f"Non-retryable exception in '{operation_name}': {type(e).__name__}")
                    raise
                
                # Calculate delay
                if attempt_num < policy.max_attempts:
                    delay_ms = policy.get_delay_ms(attempt_num)
                    
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        timestamp=datetime.utcnow(),
                        delay_ms=delay_ms,
                        exception=e,
                        success=False
                    )
                    attempts.append(attempt)
                    
                    logger.warning(f"Operation '{operation_name}' failed (attempt {attempt_num}/{policy.max_attempts}), "
                                 f"retrying in {delay_ms:.0f}ms: {str(e)[:100]}")
                    
                    # Wait before retry
                    await asyncio.sleep(delay_ms / 1000)
                else:
                    # Final attempt
                    attempt = RetryAttempt(
                        attempt_number=attempt_num,
                        timestamp=datetime.utcnow(),
                        delay_ms=0,
                        exception=e,
                        success=False
                    )
                    attempts.append(attempt)
                    
                    # Add to dead-letter queue
                    failed_op = FailedOperation(
                        operation_id=operation_id,
                        function_name=operation_name,
                        args=args,
                        kwargs=kwargs,
                        attempts=attempts,
                        final_exception=e
                    )
                    self.dead_letter_queue.append(failed_op)
                    
                    logger.error(f"Operation '{operation_name}' exhausted all {policy.max_attempts} attempts. "
                               f"Added to DLQ: {operation_id}")
                    
                    self.operation_history[operation_id] = attempts
                    raise
    
    async def process_dead_letter_queue(self, 
                                       processor: Callable[[FailedOperation], None],
                                       limit: Optional[int] = None) -> int:
        """Process dead-letter queue"""
        processed = 0
        remaining_count = limit if limit else len(self.dead_letter_queue)
        
        while self.dead_letter_queue and processed < remaining_count:
            failed_op = self.dead_letter_queue.popleft()
            
            try:
                if asyncio.iscoroutinefunction(processor):
                    await processor(failed_op)
                else:
                    processor(failed_op)
                
                processed += 1
                logger.info(f"Processed DLQ item: {failed_op.operation_id}")
                
            except Exception as e:
                logger.error(f"Failed to process DLQ item {failed_op.operation_id}: {e}")
                # Put back in queue for later retry
                self.dead_letter_queue.append(failed_op)
        
        return processed
    
    async def retry_dead_letter_item(self, operation_id: str, func: Callable,
                                    policy: Optional[RetryPolicy] = None) -> bool:
        """Retry a specific dead-letter item"""
        # Find the failed operation
        failed_op = None
        for dlq_item in self.dead_letter_queue:
            if dlq_item.operation_id == operation_id:
                failed_op = dlq_item
                break
        
        if not failed_op:
            logger.warning(f"Operation not found in DLQ: {operation_id}")
            return False
        
        try:
            # Remove from DLQ and retry
            self.dead_letter_queue.remove(failed_op)
            
            result = await self.execute_with_retry(
                failed_op.function_name,
                func,
                *failed_op.args,
                policy=policy,
                **failed_op.kwargs
            )
            
            logger.info(f"Successfully retried operation: {operation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Retry failed for operation {operation_id}: {e}")
            # Put back in DLQ
            self.dead_letter_queue.append(failed_op)
            return False
    
    def get_dlq_status(self) -> Dict[str, Any]:
        """Get status of dead-letter queue"""
        return {
            'size': len(self.dead_letter_queue),
            'items': [
                {
                    'operation_id': op.operation_id,
                    'function_name': op.function_name,
                    'added_at': op.added_to_dlq_at.isoformat(),
                    'error': str(op.final_exception)[:200],
                    'attempts': len(op.attempts),
                }
                for op in list(self.dead_letter_queue)[:100]  # Show first 100
            ]
        }
    
    def get_operation_history(self, operation_id: str) -> Optional[List[RetryAttempt]]:
        """Get history of retry attempts for an operation"""
        return self.operation_history.get(operation_id)
    
    def clear_dlq(self) -> int:
        """Clear dead-letter queue"""
        count = len(self.dead_letter_queue)
        self.dead_letter_queue.clear()
        logger.info(f"Cleared {count} items from DLQ")
        return count


# Global instance
_retry_engine: Optional[RetryEngine] = None


def init_retry_engine() -> RetryEngine:
    """Initialize global retry engine"""
    global _retry_engine
    _retry_engine = RetryEngine()
    return _retry_engine


async def execute_with_retry(operation_name: str, func: Callable,
                            *args, policy: Optional[RetryPolicy] = None,
                            **kwargs) -> Any:
    """Execute with retry globally"""
    global _retry_engine
    if not _retry_engine:
        _retry_engine = init_retry_engine()
    
    return await _retry_engine.execute_with_retry(operation_name, func, *args, policy=policy, **kwargs)


def register_retry_policy(operation_name: str, policy: RetryPolicy) -> None:
    """Register retry policy globally"""
    global _retry_engine
    if not _retry_engine:
        _retry_engine = init_retry_engine()
    
    _retry_engine.register_policy(operation_name, policy)


def get_retry_engine() -> RetryEngine:
    """Get global retry engine"""
    global _retry_engine
    if not _retry_engine:
        _retry_engine = init_retry_engine()
    
    return _retry_engine
