"""
Test Execution Engine - Phase 2.2
Tests for Uniswap V3, Curve, and Arbitrage Builder
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from core.execution.uniswap_v3_executor import UniswapV3Executor, initialize_uniswap_v3_executor
from core.execution.curve_executor import CurveExecutor, initialize_curve_executor
from core.execution.arbitrage_builder import (
    ArbitrageBuilder,
    ArbitrageExecutionPlan,
    ArbitrageStep,
    initialize_arbitrage_builder
)


# Fixtures

@pytest.fixture
def uniswap_executor() -> UniswapV3Executor:
    """Create Uniswap V3 executor"""
    return initialize_uniswap_v3_executor()


@pytest.fixture
def curve_executor() -> CurveExecutor:
    """Create Curve executor"""
    return initialize_curve_executor()


@pytest.fixture
def arbitrage_builder() -> ArbitrageBuilder:
    """Create arbitrage builder"""
    return initialize_arbitrage_builder()


@pytest.fixture
def usdc_token() -> str:
    return "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


@pytest.fixture
def usdt_token() -> str:
    return "0xdAC17F958D2ee523a2206206994597C13D831ec7"


@pytest.fixture
def dai_token() -> str:
    return "0x6B175474E89094C44Da98b954EedeAC495271d0F"


# Uniswap V3 Tests

class TestUniswapV3Executor:
    """Test Uniswap V3 swap execution"""
    
    def test_executor_initialization(self, uniswap_executor):
        """Test executor initialization"""
        assert uniswap_executor is not None
        assert uniswap_executor.UNISWAP_V3_ROUTER
        assert len(uniswap_executor.POOL_FEES) == 4
    
    def test_build_swap_calldata_success(self, uniswap_executor, usdc_token, usdt_token):
        """Test building valid swap calldata"""
        success, calldata = uniswap_executor.build_swap_calldata(
            token_in=usdc_token,
            token_out=usdt_token,
            amount_in=1000000,  # 1 USDC
            min_amount_out=990000  # Min 0.99 USDT
        )
        
        assert success is True
        assert calldata.startswith("0x414bf389")
    
    def test_build_swap_calldata_invalid_tokens(self, uniswap_executor):
        """Test with invalid token addresses"""
        success, calldata = uniswap_executor.build_swap_calldata(
            token_in="",
            token_out="",
            amount_in=1000000,
            min_amount_out=990000
        )
        
        assert success is False
        assert calldata == ""
    
    def test_build_swap_calldata_invalid_amount(self, uniswap_executor, usdc_token, usdt_token):
        """Test with invalid amount"""
        success, calldata = uniswap_executor.build_swap_calldata(
            token_in=usdc_token,
            token_out=usdt_token,
            amount_in=0,  # Invalid
            min_amount_out=990000
        )
        
        assert success is False
    
    def test_estimate_swap_output(self, uniswap_executor, usdc_token, usdt_token):
        """Test swap output estimation"""
        estimate = uniswap_executor.estimate_swap_output(
            token_in=usdc_token,
            token_out=usdt_token,
            amount_in=Decimal("1000000")
        )
        
        assert estimate is not None
        assert estimate["amount_in"] == Decimal("1000000")
        assert estimate["amount_out"] > 0
        assert estimate["min_amount_out"] > 0
        assert estimate["expected_slippage"] == 0.1  # 0.1%
    
    def test_calculate_slippage_protection(self, uniswap_executor):
        """Test slippage protection calculation"""
        estimated = Decimal("1000000")
        min_output = uniswap_executor.calculate_slippage_protection(estimated)
        
        assert min_output > 0
        assert min_output < estimated  # Should be less due to slippage
        
        # Verify slippage is within tolerance
        slippage = (estimated - min_output) / estimated
        assert slippage <= Decimal(uniswap_executor.DEFAULT_SLIPPAGE)
    
    def test_estimate_gas_cost(self, uniswap_executor):
        """Test gas cost estimation"""
        gas_cost = uniswap_executor.estimate_gas_cost(
            gas_limit=120000,
            gas_price_gwei=50.0
        )
        
        assert gas_cost > 0
        # 120,000 gas * 50 gwei = 6,000,000 gwei = 0.006 ETH
        assert gas_cost == Decimal("0.006")
    
    def test_validate_swap_profitability_profitable(self, uniswap_executor):
        """Test profitability validation - profitable case"""
        result = uniswap_executor.validate_swap_profitability(
            amount_out_min=Decimal("1000000"),  # 1 token
            amount_in=Decimal("900000"),         # 0.9 token
            gas_cost_eth=Decimal("0.001")
        )
        
        assert result["profitable"] is True
        assert result["net_profit"] > 0
    
    def test_validate_swap_profitability_unprofitable(self, uniswap_executor):
        """Test profitability validation - unprofitable case"""
        result = uniswap_executor.validate_swap_profitability(
            amount_out_min=Decimal("100000"),    # 0.1 token
            amount_in=Decimal("1000000"),        # 1 token
            gas_cost_eth=Decimal("0.01")
        )
        
        assert result["profitable"] is False
        assert result["net_profit"] < 0
    
    def test_get_stats(self, uniswap_executor):
        """Test statistics reporting"""
        uniswap_executor.metrics["total_swaps"] = 100
        uniswap_executor.metrics["successful_swaps"] = 95
        uniswap_executor.metrics["failed_swaps"] = 5
        
        stats = uniswap_executor.get_stats()
        
        assert stats["total_swaps"] == 100
        assert stats["successful_swaps"] == 95
        assert stats["success_rate"] == 95.0


# Curve Tests

class TestCurveExecutor:
    """Test Curve stable swap execution"""
    
    def test_executor_initialization(self, curve_executor):
        """Test executor initialization"""
        assert curve_executor is not None
        assert curve_executor.CURVE_3CRV_POOL
        assert len(curve_executor.STABLECOINS) == 3
    
    def test_build_stable_swap_calldata(self, curve_executor):
        """Test building stable swap calldata"""
        success, calldata = curve_executor.build_stable_swap_calldata(
            pool_address=curve_executor.CURVE_3CRV_POOL,
            i=1,  # USDC
            j=2,  # USDT
            dx=1000000,
            min_dy=995000
        )
        
        assert success is True
        assert calldata.startswith("0x3df02124")
    
    def test_build_stable_swap_invalid_indices(self, curve_executor):
        """Test with invalid indices"""
        success, calldata = curve_executor.build_stable_swap_calldata(
            pool_address=curve_executor.CURVE_3CRV_POOL,
            i=1,  # Same as j
            j=1,
            dx=1000000,
            min_dy=995000
        )
        
        assert success is False
    
    def test_estimate_stable_swap_output(self, curve_executor, usdc_token, usdt_token):
        """Test stable swap output estimation"""
        estimate = curve_executor.estimate_stable_swap_output(
            token_in=usdc_token,
            token_out=usdt_token,
            amount_in=1000000
        )
        
        assert estimate is not None
        assert estimate["amount_in"] == 1000000
        assert estimate["amount_out"] > 0
        assert estimate["expected_slippage"] == 0.05  # 0.05%
    
    def test_calculate_fee_impact(self, curve_executor):
        """Test fee impact calculation"""
        amount = 1000000
        fee_amount, fee_pct = curve_executor.calculate_fee_impact(amount)
        
        assert fee_amount > 0
        assert fee_pct == 0.04  # 0.04%
        # 1000000 * 0.0004 = 400
        assert fee_amount == 400
    
    def test_estimate_multihop_swap(self, curve_executor, usdc_token, usdt_token, dai_token):
        """Test multihop swap estimation"""
        estimate = curve_executor.estimate_multihop_swap(
            token_path=[usdc_token, usdt_token, dai_token],
            amount_in=1000000
        )
        
        assert estimate is not None
        assert estimate["num_hops"] == 2
        assert len(estimate["hops"]) == 2
        assert estimate["amount_in"] == 1000000
        assert estimate["amount_out"] > 0
    
    def test_validate_slippage_bounds(self, curve_executor):
        """Test slippage bounds validation"""
        result = curve_executor.validate_slippage_bounds(
            amount_out=1000000,
            min_amount_out=999500,  # 0.05% slippage
            max_slippage_pct=0.1
        )
        
        assert result["valid"] is True
        assert result["actual_slippage"] <= 0.1
    
    def test_get_stats(self, curve_executor):
        """Test statistics reporting"""
        curve_executor.metrics["total_swaps"] = 50
        curve_executor.metrics["successful_swaps"] = 48
        curve_executor.metrics["failed_swaps"] = 2
        
        stats = curve_executor.get_stats()
        
        assert stats["total_swaps"] == 50
        assert stats["successful_swaps"] == 48
        assert stats["success_rate"] == 96.0


# Arbitrage Builder Tests

class TestArbitrageBuilder:
    """Test arbitrage execution plan building"""
    
    def test_builder_initialization(self, arbitrage_builder):
        """Test builder initialization"""
        assert arbitrage_builder is not None
        assert arbitrage_builder.uniswap_v3 is not None
        assert arbitrage_builder.curve is not None
    
    def test_build_two_hop_arbitrage(self, arbitrage_builder, usdc_token, usdt_token):
        """Test building 2-hop arbitrage plan"""
        plan = arbitrage_builder.build_two_hop_arbitrage(
            token_a=usdc_token,
            token_b=usdt_token,
            amount_in=1000000,
            dex_path=["uniswap_v3", "curve"]
        )
        
        assert plan is not None
        assert plan.plan_id
        assert len(plan.steps) == 2
        assert plan.steps[0].dex == "uniswap_v3"
        assert plan.steps[1].dex == "curve"
        assert plan.total_gas_estimate > 0
    
    def test_build_three_hop_arbitrage(
        self,
        arbitrage_builder,
        usdc_token,
        usdt_token,
        dai_token
    ):
        """Test building 3-hop arbitrage plan"""
        plan = arbitrage_builder.build_three_hop_arbitrage(
            token_a=usdc_token,
            token_b=usdt_token,
            token_c=dai_token,
            amount_in=1000000,
            dex_path=["uniswap_v3", "curve", "uniswap_v3"]
        )
        
        assert plan is not None
        assert len(plan.steps) == 3
        assert plan.total_gas_estimate > 0
    
    def test_validate_execution_plan_valid(self, arbitrage_builder, usdc_token, usdt_token):
        """Test validating a profitable plan"""
        plan = arbitrage_builder.build_two_hop_arbitrage(
            token_a=usdc_token,
            token_b=usdt_token,
            amount_in=1000000
        )
        
        if plan:
            # Mock a profitable scenario
            plan.net_profit_estimate = Decimal("1.0")
            plan.execution_probability = 0.95
            plan.cumulative_slippage = 0.05
            
            validation = arbitrage_builder.validate_execution_plan(plan)
            
            assert validation["valid"] is True
    
    def test_validate_execution_plan_invalid_profit(self, arbitrage_builder):
        """Test validation with low profit"""
        # Create minimal plan
        step = ArbitrageStep(
            step_number=1,
            dex="uniswap_v3",
            token_in="0x",
            token_out="0x",
            amount_in=1000000,
            amount_out_expected=999000,
            amount_out_minimum=998000,
            calldata="0x",
            gas_estimate=120000,
            fee_estimate=0.1
        )
        
        plan = ArbitrageExecutionPlan(
            plan_id="test",
            strategy="test",
            steps=[step],
            total_profit_estimate=Decimal("0.001"),  # Low profit
            total_gas_estimate=120000,
            net_profit_estimate=Decimal("0.0001"),
            cumulative_slippage=0.1,
            roi_percentage=0.01,
            execution_probability=0.95,
            timestamp=0
        )
        
        validation = arbitrage_builder.validate_execution_plan(plan)
        
        assert validation["profit_valid"] is False
    
    def test_validate_execution_plan_invalid_probability(self, arbitrage_builder):
        """Test validation with low probability"""
        step = ArbitrageStep(
            step_number=1,
            dex="uniswap_v3",
            token_in="0x",
            token_out="0x",
            amount_in=1000000,
            amount_out_expected=999000,
            amount_out_minimum=998000,
            calldata="0x",
            gas_estimate=120000,
            fee_estimate=0.1
        )
        
        plan = ArbitrageExecutionPlan(
            plan_id="test",
            strategy="test",
            steps=[step],
            total_profit_estimate=Decimal("1.0"),
            total_gas_estimate=120000,
            net_profit_estimate=Decimal("0.99"),
            cumulative_slippage=0.1,
            roi_percentage=1.0,
            execution_probability=0.5,  # Low probability
            timestamp=0
        )
        
        validation = arbitrage_builder.validate_execution_plan(plan)
        
        assert validation["probability_valid"] is False
    
    def test_get_stats(self, arbitrage_builder):
        """Test builder statistics"""
        arbitrage_builder.metrics["plans_created"] = 100
        arbitrage_builder.metrics["plans_executed"] = 95
        arbitrage_builder.metrics["plans_failed"] = 5
        arbitrage_builder.metrics["total_profit"] = Decimal("50")
        
        stats = arbitrage_builder.get_stats()
        
        assert stats["plans_created"] == 100
        assert stats["plans_executed"] == 95
        assert stats["success_rate"] == 95.0


# Integration Tests

class TestExecutionIntegration:
    """End-to-end execution tests"""
    
    def test_simple_arbitrage_flow(self, arbitrage_builder, usdc_token, usdt_token):
        """Test complete simple arbitrage flow"""
        # Build plan
        plan = arbitrage_builder.build_two_hop_arbitrage(
            token_a=usdc_token,
            token_b=usdt_token,
            amount_in=1000000
        )
        
        assert plan is not None
        
        # Validate plan
        validation = arbitrage_builder.validate_execution_plan(plan)
        
        # Verify structure
        assert plan.plan_id
        assert len(plan.steps) == 2
        assert all(step.calldata for step in plan.steps)
    
    def test_slippage_accumulation(self, arbitrage_builder, usdc_token, usdt_token, dai_token):
        """Test that slippage accumulates correctly across hops"""
        plan = arbitrage_builder.build_three_hop_arbitrage(
            token_a=usdc_token,
            token_b=usdt_token,
            token_c=dai_token,
            amount_in=1000000
        )
        
        if plan:
            # Slippage should be sum of individual hop slippages
            individual_slippage = sum(step.fee_estimate for step in plan.steps)
            assert plan.cumulative_slippage == individual_slippage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
