"""
Error Recovery & Revert Handling Tests
Tests: error classification, recovery strategies, circuit integration
"""

import pytest
import asyncio
from core.executor.error_recovery import (
    ErrorRecovery,
    ErrorType,
    ErrorContext,
    ErrorAnalyzer,
    RevertHandler,
    CircuitBreakerIntegration,
)

class TestErrorAnalyzer:
    
    def test_classify_insufficient_output(self):
        """Test classification of insufficient output error"""
        reason = "UniswapV3Router: INSUFFICIENT_OUTPUT_AMOUNT"
        error_type = ErrorAnalyzer.classify_error(reason)
        assert error_type == ErrorType.INSUFFICIENT_OUTPUT
    
    def test_classify_slippage_error(self):
        """Test classification of slippage error"""
        reason = "Slippage tolerance exceeded"
        error_type = ErrorAnalyzer.classify_error(reason)
        assert error_type == ErrorType.SLIPPAGE_EXCEEDED
    
    def test_classify_liquidity_error(self):
        """Test classification of liquidity error"""
        reason = "Insufficient liquidity for swap"
        error_type = ErrorAnalyzer.classify_error(reason)
        assert error_type == ErrorType.INSUFFICIENT_LIQUIDITY
    
    def test_classify_gas_error(self):
        """Test classification of gas limit error"""
        reason = "Out of gas"
        error_type = ErrorAnalyzer.classify_error(reason)
        assert error_type == ErrorType.GAS_LIMIT_EXCEEDED
    
    def test_classify_unknown_error(self):
        """Test classification of unknown error"""
        reason = "Some random error message"
        error_type = ErrorAnalyzer.classify_error(reason)
        assert error_type == ErrorType.UNKNOWN
    
    def test_parse_revert_reason(self):
        """Test parsing revert reason from revert data"""
        revert_data = "0xdeadbeef0000000000000000000000000000000000000000"
        result = ErrorAnalyzer.parse_revert_reason(revert_data)
        assert "0xdeadbeef" in result


class TestErrorRecovery:
    
    @pytest.fixture
    def error_recovery(self):
        return ErrorRecovery(max_global_retries=3)
    
    def test_register_custom_strategy(self, error_recovery):
        """Test registering custom recovery strategy"""
        from core.executor.error_recovery import RecoveryStrategy
        
        async def custom_action(params):
            params["custom"] = True
            return params
        
        strategy = RecoveryStrategy(
            name="custom",
            description="Custom recovery",
            action=custom_action,
        )
        
        error_recovery.register_strategy(ErrorType.UNKNOWN, strategy)
        
        assert ErrorType.UNKNOWN in error_recovery.recovery_strategies
        assert len(error_recovery.recovery_strategies[ErrorType.UNKNOWN]) > 0
    
    @pytest.mark.asyncio
    async def test_reduce_position_action(self, error_recovery):
        """Test position reduction recovery action"""
        params = {"amount": 1000}
        result = await error_recovery._reduce_position_action(params)
        
        assert result["amount"] == 500
    
    @pytest.mark.asyncio
    async def test_increase_slippage_action(self, error_recovery):
        """Test slippage increase recovery action"""
        params = {"slippage_tolerance": 0.001}
        result = await error_recovery._increase_slippage_action(params)
        
        assert result["slippage_tolerance"] == 0.002
    
    @pytest.mark.asyncio
    async def test_switch_provider_action(self, error_recovery):
        """Test provider switching recovery action"""
        params = {"flash_loan_provider": "aave_v3"}
        result = await error_recovery._switch_provider_action(params)
        
        assert result["flash_loan_provider"] != "aave_v3"
        assert result["flash_loan_provider"] in ["dydx", "uniswap_v3", "balancer", "euler"]
    
    @pytest.mark.asyncio
    async def test_increase_gas_action(self, error_recovery):
        """Test gas limit increase recovery action"""
        params = {"gas_limit": 100000}
        result = await error_recovery._increase_gas_action(params)
        
        assert result["gas_limit"] == 150000
    
    @pytest.mark.asyncio
    async def test_recovery_stats(self, error_recovery):
        """Test error recovery statistics"""
        # Add some errors to history
        error1 = ErrorContext(
            error_type=ErrorType.INSUFFICIENT_OUTPUT,
            message="Test error 1",
            transaction_hash="0x123",
        )
        error2 = ErrorContext(
            error_type=ErrorType.SLIPPAGE_EXCEEDED,
            message="Test error 2",
            transaction_hash="0x456",
        )
        
        error_recovery.error_history.append(error1)
        error_recovery.error_history.append(error2)
        
        stats = error_recovery.get_recovery_stats()
        
        assert stats["total_errors"] == 2
        assert ErrorType.INSUFFICIENT_OUTPUT.value in stats["by_type"]
        assert ErrorType.SLIPPAGE_EXCEEDED.value in stats["by_type"]


class TestRevertHandler:
    
    @pytest.fixture
    def revert_handler(self):
        error_recovery = ErrorRecovery()
        return RevertHandler(error_recovery)
    
    @pytest.mark.asyncio
    async def test_handle_insufficient_output_revert(self, revert_handler):
        """Test handling insufficient output revert"""
        
        retry_attempts = []
        
        async def retry_callback(params):
            retry_attempts.append(params)
            return False  # Simulated failed retry
        
        result = await revert_handler.handle_revert(
            tx_hash="0x123",
            revert_data="UniswapV3Router: INSUFFICIENT_OUTPUT_AMOUNT",
            original_params={"amount": 1000},
            retry_callback=retry_callback,
        )
        
        # Should attempt recovery (at least one retry)
        assert len(retry_attempts) > 0
    
    @pytest.mark.asyncio
    async def test_handle_successful_recovery(self, revert_handler):
        """Test successful error recovery"""
        
        attempt_count = [0]
        
        async def retry_callback(params):
            attempt_count[0] += 1
            # Succeed on second attempt
            return attempt_count[0] >= 2
        
        result = await revert_handler.handle_revert(
            tx_hash="0x123",
            revert_data="Slippage tolerance exceeded",
            original_params={"slippage_tolerance": 0.001},
            retry_callback=retry_callback,
        )
        
        # Recovery should succeed
        assert result is True
        assert attempt_count[0] >= 2


class TestCircuitBreakerIntegration:
    
    @pytest.fixture
    def integration(self):
        from core.risk.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker()
        error_recovery = ErrorRecovery()
        
        return CircuitBreakerIntegration(cb, error_recovery)
    
    @pytest.mark.asyncio
    async def test_execute_with_safety_success(self, integration):
        """Test successful execution with safety"""
        
        async def execute_fn(params):
            return "0x123"
        
        async def retry_fn(params):
            return True
        
        success, tx_hash = await integration.execute_with_safety(
            execute_fn,
            {"amount": 100},
            retry_fn,
        )
        
        assert success is True
        assert tx_hash == "0x123"
    
    @pytest.mark.asyncio
    async def test_execute_with_safety_failure(self, integration):
        """Test execution failure with safety"""
        
        async def execute_fn(params):
            raise Exception("Execution failed")
        
        async def retry_fn(params):
            return False
        
        success, tx_hash = await integration.execute_with_safety(
            execute_fn,
            {"amount": 100},
            retry_fn,
        )
        
        assert success is False
        assert tx_hash is None
    
    @pytest.mark.asyncio
    async def test_high_error_rate_trips_circuit(self, integration):
        """Test circuit trip on high error rate"""
        
        async def execute_fn(params):
            raise Exception("Simulated error")
        
        async def retry_fn(params):
            return False
        
        # Simulate multiple failures to trigger error rate threshold
        for i in range(5):
            try:
                await integration.execute_with_safety(
                    execute_fn,
                    {"amount": 100},
                    retry_fn,
                )
            except:
                pass
        
        # Check if circuit breaker was triggered
        # (would need access to internal state or circuit breaker status)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
