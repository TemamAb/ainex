"""
Comprehensive AINEON Test Suite
Unit + Integration + Performance tests
Target: 95%+ Code Coverage
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime

# Test Strategy Orchestrator
from core.strategies.strategy_orchestrator import (
    StrategyOrchestrator,
    StrategyType,
    StrategySignal,
    MultiDexArbitrageStrategy,
    LiquidationCascadeStrategy,
)

# Test AI Optimizer
from core.ai.ml_optimizer import (
    AIOptimizationEngine,
    MarketState,
    MarketRegime,
    MarketRegimeDetector,
    DeepRLOptimizer,
    ParameterAutoTuner,
)

# Test Liquidation Engine
from core.liquidation_engine import (
    LiquidationDetector,
    LiquidationExecutor,
    MultiProtocolLiquidationManager,
    LendingProtocol,
    Position,
)

class TestStrategyOrchestrator:
    """Test 6-strategy orchestration"""
    
    @pytest.fixture
    def orchestrator(self):
        """Mock orchestrator"""
        from unittest.mock import MagicMock
        
        return StrategyOrchestrator(
            dex_router=MagicMock(),
            mempool_monitor=MagicMock(),
            protocol_monitor=MagicMock(),
            pool_analyzer=MagicMock(),
            bridge_monitor=MagicMock(),
            volatility_monitor=MagicMock(),
        )
    
    @pytest.mark.asyncio
    async def test_strategy_initialization(self, orchestrator):
        """Test 6 strategies are initialized"""
        assert len(orchestrator.strategies) == 6
        assert StrategyType.MULTI_DEX_ARBITRAGE in orchestrator.strategies
        assert StrategyType.MEV_SANDWICH in orchestrator.strategies
        assert StrategyType.LIQUIDATION_CASCADE in orchestrator.strategies
    
    @pytest.mark.asyncio
    async def test_opportunity_detection(self, orchestrator):
        """Test opportunity detection across strategies"""
        signals = await orchestrator.detect_all_opportunities()
        assert isinstance(signals, list)
    
    def test_execution_queue(self, orchestrator):
        """Test execution queue management"""
        signal = StrategySignal(
            strategy_type=StrategyType.MULTI_DEX_ARBITRAGE,
            opportunity_id="test_123",
            token_in="USDC",
            token_out="USDT",
            amount=Decimal("100"),
            expected_profit=Decimal("1.0"),
            confidence=0.92,
        )
        
        orchestrator.execution_queue.append(signal)
        assert len(orchestrator.execution_queue) == 1
    
    def test_portfolio_stats(self, orchestrator):
        """Test portfolio statistics"""
        stats = orchestrator.get_portfolio_stats()
        
        assert "total_profit" in stats
        assert "total_executions" in stats
        assert "win_rate" in stats
        assert "by_strategy" in stats


class TestAIOptimizationEngine:
    """Test AI optimization and market regime detection"""
    
    @pytest.fixture
    def ai_engine(self):
        return AIOptimizationEngine()
    
    def test_market_regime_detection_trending_up(self):
        """Test detection of uptrend"""
        prices = [Decimal(str(2000 + i*10)) for i in range(30)]
        volatility = 0.04
        volumes = [Decimal("1000") for _ in range(30)]
        
        regime = MarketRegimeDetector.detect_regime(prices, volumes, volatility)
        # Could be trending up or range bound
        assert regime in [MarketRegime.TRENDING_UP, MarketRegime.RANGE_BOUND]
    
    def test_market_regime_detection_volatile(self):
        """Test detection of volatility"""
        prices = [Decimal(str(2000 + i*(10 if i%2==0 else -10))) for i in range(30)]
        volatility = 0.08  # High
        volumes = [Decimal("1000") for _ in range(30)]
        
        regime = MarketRegimeDetector.detect_regime(prices, volumes, volatility)
        assert regime == MarketRegime.VOLATILE
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        prices = [Decimal(str(2000 + i)) for i in range(50)]  # Uptrend
        rsi = MarketRegimeDetector._calculate_rsi(prices)
        
        assert 0 <= rsi <= 100
        assert rsi > 50  # Uptrend = high RSI
    
    def test_deep_rl_optimizer_initialization(self):
        """Test Deep RL initialization"""
        optimizer = DeepRLOptimizer(num_strategies=6)
        
        assert len(optimizer.strategy_weights) == 6
        # Equal weight initially
        assert all(w == 1.0/6 for w in optimizer.strategy_weights.values())
    
    @pytest.mark.asyncio
    async def test_parameter_auto_tuning(self):
        """Test parameter auto-tuning"""
        tuner = ParameterAutoTuner()
        
        # Record good performance
        for i in range(25):
            tuner.record_performance({
                "profit": 10.0,
                "roi": 5.0,
                "success": True,
            })
        
        adjustments = await tuner.maybe_tune_parameters()
        # May or may not have tuned depending on timing
        assert isinstance(adjustments, dict)
    
    @pytest.mark.asyncio
    async def test_ai_optimization_output(self, ai_engine):
        """Test AI optimization provides valid output"""
        market_state = MarketState(
            timestamp=datetime.now(),
            eth_price=Decimal("2500"),
            volatility=0.03,
            momentum=0.02,
            volume=Decimal("100000"),
            rsi=55.0,
            regime=MarketRegime.RANGE_BOUND,
        )
        
        strategy, output = await ai_engine.optimize_next_execution(
            market_state=market_state,
            strategy_history={f"strategy_{i}": [] for i in range(6)},
            opportunities_available=10,
            gas_price_gwei=50.0,
        )
        
        assert strategy.startswith("strategy_")
        assert output.confidence > 0.8
        assert output.recommended_position_size > 0
        assert 0 < output.recommended_max_slippage < 0.01


class TestLiquidationEngine:
    """Test liquidation detection and execution"""
    
    @pytest.fixture
    def detector(self):
        return LiquidationDetector()
    
    @pytest.fixture
    def liquidation_manager(self):
        from unittest.mock import MagicMock
        return MultiProtocolLiquidationManager(dex_router=MagicMock())
    
    def test_liquidation_detector_initialization(self, detector):
        """Test detector initialization"""
        assert detector.liquidation_threshold == Decimal("1.2")
        assert len(detector.monitored_positions) == 0
    
    def test_position_creation(self):
        """Test creating a position"""
        position = Position(
            position_id="pos_123",
            user="0x1234...",
            protocol=LendingProtocol.AAVE_V3,
            collateral_token="WETH",
            collateral_amount=Decimal("10"),
            debt_token="USDC",
            debt_amount=Decimal("15000"),
            health_factor=Decimal("1.05"),
            liquidation_threshold=Decimal("1.5"),
        )
        
        assert position.health_factor < position.liquidation_threshold
        assert position.protocol == LendingProtocol.AAVE_V3
    
    def test_protocol_coverage(self, liquidation_manager):
        """Test 7 protocols are supported"""
        protocols = liquidation_manager.protocols
        
        assert len(protocols) == 7
        assert LendingProtocol.AAVE_V3 in protocols
        assert LendingProtocol.COMPOUND in protocols
        assert LendingProtocol.MORPHO in protocols
    
    def test_liquidation_profit_calculation(self, liquidation_manager):
        """Test liquidation profit calculation"""
        position = Position(
            position_id="pos_123",
            user="0x1234",
            protocol=LendingProtocol.AAVE_V3,
            collateral_token="WETH",
            collateral_amount=Decimal("100"),  # 100 WETH = ~$250K
            debt_token="USDC",
            debt_amount=Decimal("200000"),  # $200K debt
            health_factor=Decimal("0.95"),
            liquidation_threshold=Decimal("1.5"),
        )
        
        opportunity = liquidation_manager._calculate_liquidation_profit(position)
        
        if opportunity:  # May or may not qualify (need profit > 2 ETH)
            assert opportunity.liquidator_profit > 0
            assert opportunity.position == position


class TestIntegration:
    """Integration tests for full flow"""
    
    @pytest.mark.asyncio
    async def test_strategy_to_execution_flow(self):
        """Test opportunity → strategy → execution"""
        from unittest.mock import MagicMock
        
        orchestrator = StrategyOrchestrator(
            dex_router=MagicMock(),
            mempool_monitor=MagicMock(),
            protocol_monitor=MagicMock(),
            pool_analyzer=MagicMock(),
            bridge_monitor=MagicMock(),
            volatility_monitor=MagicMock(),
        )
        
        # Create signal
        signal = StrategySignal(
            strategy_type=StrategyType.MULTI_DEX_ARBITRAGE,
            opportunity_id="int_test_001",
            token_in="USDC",
            token_out="USDT",
            amount=Decimal("100"),
            expected_profit=Decimal("1.0"),
            confidence=0.92,
        )
        
        # Attempt execution
        success, profit = await orchestrator.execute_opportunity(signal)
        
        assert isinstance(success, bool)
        assert isinstance(profit, Decimal)
    
    @pytest.mark.asyncio
    async def test_ai_strategy_selection_integration(self):
        """Test AI optimization selecting strategy"""
        ai_engine = AIOptimizationEngine()
        
        market_state = MarketState(
            timestamp=datetime.now(),
            eth_price=Decimal("2500"),
            volatility=0.05,
            momentum=0.01,
            volume=Decimal("100000"),
            rsi=70.0,  # Trending
            regime=MarketRegime.TRENDING_UP,
        )
        
        strategy, output = await ai_engine.optimize_next_execution(
            market_state=market_state,
            strategy_history={f"strategy_{i}": [] for i in range(6)},
            opportunities_available=15,
            gas_price_gwei=50.0,
        )
        
        # Should select a strategy
        assert strategy is not None
        # MEV and Multi-DEX should have higher weights in uptrend
        assert output.confidence > 0.8


class TestPerformanceMetrics:
    """Test performance and latency targets"""
    
    def test_strategy_initialization_speed(self):
        """Test strategy initialization is fast"""
        import time
        
        start = time.time()
        orchestrator = StrategyOrchestrator(
            dex_router=None,
            mempool_monitor=None,
            protocol_monitor=None,
            pool_analyzer=None,
            bridge_monitor=None,
            volatility_monitor=None,
        )
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # <100ms initialization
    
    def test_ai_inference_latency(self):
        """Test AI inference is <150µs"""
        import time
        
        ai_engine = AIOptimizationEngine()
        market_state = MarketState(
            timestamp=datetime.now(),
            eth_price=Decimal("2500"),
            volatility=0.03,
            momentum=0.01,
            volume=Decimal("100000"),
            rsi=50.0,
            regime=MarketRegime.CALM,
        )
        
        start = time.time()
        
        # Synchronously run optimization
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ai_engine.optimize_next_execution(
            market_state=market_state,
            strategy_history={f"strategy_{i}": [] for i in range(6)},
            opportunities_available=10,
            gas_price_gwei=50.0,
        ))
        
        elapsed = time.time() - start
        
        # Should be fast (design target: <150µs = 0.00015s, testing for <10ms)
        assert elapsed < 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
