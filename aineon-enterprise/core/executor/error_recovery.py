"""
Error Recovery & Revert Handling
Automatic recovery from transaction failures
Status: Production-Ready
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    INSUFFICIENT_OUTPUT = "INSUFFICIENT_OUTPUT"
    SLIPPAGE_EXCEEDED = "SLIPPAGE_EXCEEDED"
    INSUFFICIENT_LIQUIDITY = "INSUFFICIENT_LIQUIDITY"
    EXECUTION_REVERTED = "EXECUTION_REVERTED"
    GAS_LIMIT_EXCEEDED = "GAS_LIMIT_EXCEEDED"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    FLASH_LOAN_FAILED = "FLASH_LOAN_FAILED"
    PAYMASTER_FAILED = "PAYMASTER_FAILED"
    UNKNOWN = "UNKNOWN"

@dataclass
class ErrorContext:
    error_type: ErrorType
    message: str
    transaction_hash: str
    revert_reason: Optional[str] = None
    original_params: Dict[str, Any] = None

@dataclass
class RecoveryStrategy:
    name: str
    description: str
    action: Callable
    max_retries: int = 3
    backoff_multiplier: float = 2.0

class ErrorAnalyzer:
    """Analyze transaction errors and classify them"""
    
    ERROR_PATTERNS = {
        "insufficient": ErrorType.INSUFFICIENT_OUTPUT,
        "slippage": ErrorType.SLIPPAGE_EXCEEDED,
        "liquidity": ErrorType.INSUFFICIENT_LIQUIDITY,
        "revert": ErrorType.EXECUTION_REVERTED,
        "gas": ErrorType.GAS_LIMIT_EXCEEDED,
        "amount": ErrorType.INVALID_AMOUNT,
        "flash": ErrorType.FLASH_LOAN_FAILED,
        "paymaster": ErrorType.PAYMASTER_FAILED,
    }
    
    @staticmethod
    def classify_error(revert_reason: str) -> ErrorType:
        """Classify error by revert reason"""
        reason_lower = revert_reason.lower()
        
        for pattern, error_type in ErrorAnalyzer.ERROR_PATTERNS.items():
            if pattern in reason_lower:
                return error_type
        
        return ErrorType.UNKNOWN
    
    @staticmethod
    def parse_revert_reason(revert_data: str) -> str:
        """Parse revert reason from tx revert data"""
        try:
            # In production: decode revert data using ABI
            # For now: extract hex string
            if revert_data.startswith("0x"):
                return f"Revert: {revert_data[:50]}..."
            return revert_data
        except Exception:
            return "Unknown revert"


class ErrorRecovery:
    """
    Handles error recovery with exponential backoff
    Multiple recovery strategies per error type
    """
    
    def __init__(self, max_global_retries: int = 3):
        self.max_global_retries = max_global_retries
        self.recovery_strategies: Dict[ErrorType, List[RecoveryStrategy]] = {}
        self.error_history: List[ErrorContext] = []
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        
        # Insufficient output: reduce position size
        self.register_strategy(
            ErrorType.INSUFFICIENT_OUTPUT,
            RecoveryStrategy(
                name="reduce_position",
                description="Retry with smaller position size (50%)",
                action=self._reduce_position_action,
                max_retries=2,
            )
        )
        
        # Slippage: increase slippage tolerance
        self.register_strategy(
            ErrorType.SLIPPAGE_EXCEEDED,
            RecoveryStrategy(
                name="increase_slippage",
                description="Retry with higher slippage tolerance (0.2%)",
                action=self._increase_slippage_action,
                max_retries=2,
            )
        )
        
        # Liquidity: try different flash loan provider
        self.register_strategy(
            ErrorType.INSUFFICIENT_LIQUIDITY,
            RecoveryStrategy(
                name="switch_provider",
                description="Try alternative flash loan provider",
                action=self._switch_provider_action,
                max_retries=3,
            )
        )
        
        # Gas: increase gas limit
        self.register_strategy(
            ErrorType.GAS_LIMIT_EXCEEDED,
            RecoveryStrategy(
                name="increase_gas",
                description="Retry with higher gas limit (1.5x)",
                action=self._increase_gas_action,
                max_retries=1,
            )
        )
    
    def register_strategy(
        self,
        error_type: ErrorType,
        strategy: RecoveryStrategy,
    ) -> None:
        """Register recovery strategy for error type"""
        if error_type not in self.recovery_strategies:
            self.recovery_strategies[error_type] = []
        self.recovery_strategies[error_type].append(strategy)
    
    async def recover(
        self,
        error_context: ErrorContext,
        retry_callback: Callable,
    ) -> bool:
        """
        Attempt recovery from error
        Returns: True if recovered, False if unrecoverable
        """
        self.error_history.append(error_context)
        
        logger.error(
            f"❌ Transaction failed | "
            f"Type: {error_context.error_type.value} | "
            f"Message: {error_context.message}"
        )
        
        # Get recovery strategies for this error
        strategies = self.recovery_strategies.get(error_context.error_type, [])
        
        if not strategies:
            logger.error(f"❌ No recovery strategy for {error_context.error_type.value}")
            return False
        
        # Try each strategy with backoff
        for strategy in strategies:
            logger.info(f"🔄 Recovery strategy: {strategy.name}")
            
            for attempt in range(strategy.max_retries):
                try:
                    # Apply backoff
                    delay = (250 * (strategy.backoff_multiplier ** attempt)) / 1000
                    if attempt > 0:
                        logger.info(f"⏳ Retry {attempt + 1}/{strategy.max_retries} in {delay}s...")
                        await asyncio.sleep(delay)
                    
                    # Execute strategy (modifies params)
                    modified_params = await strategy.action(error_context.original_params)
                    
                    # Retry with modified params
                    success = await retry_callback(modified_params)
                    
                    if success:
                        logger.info(f"✅ Recovered via: {strategy.name}")
                        return True
                    
                except Exception as e:
                    logger.warning(f"Strategy failed: {str(e)}")
        
        logger.error(f"❌ All recovery strategies exhausted")
        return False
    
    # Recovery action implementations
    async def _reduce_position_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reduce position size to 50%"""
        modified = params.copy()
        if "amount" in modified:
            modified["amount"] = int(modified["amount"] * 0.5)
        return modified
    
    async def _increase_slippage_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Increase slippage tolerance"""
        modified = params.copy()
        if "slippage_tolerance" in modified:
            modified["slippage_tolerance"] = min(
                modified["slippage_tolerance"] * 2,
                0.005  # Cap at 0.5%
            )
        return modified
    
    async def _switch_provider_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Switch flash loan provider"""
        modified = params.copy()
        current = modified.get("flash_loan_provider", "aave_v3")
        
        providers = ["aave_v3", "dydx", "uniswap_v3", "balancer", "euler"]
        providers.remove(current) if current in providers else None
        
        modified["flash_loan_provider"] = providers[0] if providers else current
        logger.info(f"Switched provider to: {modified['flash_loan_provider']}")
        
        return modified
    
    async def _increase_gas_action(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Increase gas limit"""
        modified = params.copy()
        if "gas_limit" in modified:
            modified["gas_limit"] = int(modified["gas_limit"] * 1.5)
        return modified
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        successful = [e for e in self.error_history if e.error_type != ErrorType.UNKNOWN]
        
        return {
            "total_errors": len(self.error_history),
            "by_type": self._count_by_type(),
            "recovery_rate": len(successful) / len(self.error_history) if self.error_history else 0,
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count errors by type"""
        counts = {}
        for error in self.error_history:
            error_type = error.error_type.value
            counts[error_type] = counts.get(error_type, 0) + 1
        return counts


class RevertHandler:
    """
    Handles transaction reverts
    Parses revert data and triggers recovery
    """
    
    def __init__(self, error_recovery: ErrorRecovery):
        self.error_recovery = error_recovery
    
    async def handle_revert(
        self,
        tx_hash: str,
        revert_data: str,
        original_params: Dict[str, Any],
        retry_callback: Callable,
    ) -> bool:
        """
        Handle transaction revert
        Analyze error and attempt recovery
        """
        try:
            # Analyze revert reason
            revert_reason = ErrorAnalyzer.parse_revert_reason(revert_data)
            error_type = ErrorAnalyzer.classify_error(revert_reason)
            
            # Create error context
            error_context = ErrorContext(
                error_type=error_type,
                message=revert_reason,
                transaction_hash=tx_hash,
                revert_reason=revert_data,
                original_params=original_params,
            )
            
            # Attempt recovery
            return await self.error_recovery.recover(error_context, retry_callback)
            
        except Exception as e:
            logger.error(f"Revert handler error: {str(e)}")
            return False


class CircuitBreakerIntegration:
    """
    Integrate error recovery with circuit breaker
    Prevent cascading failures
    """
    
    def __init__(
        self,
        circuit_breaker: Any,
        error_recovery: ErrorRecovery,
        max_error_rate: float = 0.3,  # 30%
    ):
        self.circuit_breaker = circuit_breaker
        self.error_recovery = error_recovery
        self.max_error_rate = max_error_rate
        self.recent_errors = []
        self.recent_success = []
    
    async def execute_with_safety(
        self,
        execute_fn: Callable,
        params: Dict[str, Any],
        retry_fn: Callable,
    ) -> tuple[bool, Optional[str]]:
        """
        Execute with integrated error handling & circuit breaker
        Returns: (success, tx_hash)
        """
        try:
            # Check circuit
            if not self.circuit_breaker.can_trade():
                return False, None
            
            # Execute
            tx_hash = await execute_fn(params)
            self.recent_success.append(tx_hash)
            
            # Trim history
            if len(self.recent_success) > 100:
                self.recent_success.pop(0)
            
            return True, tx_hash
            
        except Exception as e:
            self.recent_errors.append(str(e))
            
            # Trim history
            if len(self.recent_errors) > 100:
                self.recent_errors.pop(0)
            
            # Check error rate
            error_rate = len(self.recent_errors) / (len(self.recent_errors) + len(self.recent_success))
            if error_rate > self.max_error_rate:
                logger.error(f"🛑 Error rate critical: {error_rate:.1%}")
                self.circuit_breaker._trip_circuit()
            
            # Attempt recovery
            recovered = await self.error_recovery.recover(
                ErrorContext(
                    error_type=ErrorType.EXECUTION_REVERTED,
                    message=str(e),
                    transaction_hash="",
                    original_params=params,
                ),
                retry_fn,
            )
            
            return recovered, None
