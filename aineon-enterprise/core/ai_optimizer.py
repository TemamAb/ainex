"""
AINEON AI Optimization Engine
Phase 3: Market Regime Detection + Strategy Weight Optimization
Auto-tuning every 15 minutes with Thompson Sampling
"""

import asyncio
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketRegime:
    """Market condition classification"""
    regime_type: str  # high_vol, trending_up, trending_down, ranging, volatile
    confidence: float
    timestamp: datetime
    metrics: Dict[str, float]


@dataclass
class StrategyMetrics:
    """Performance metrics for a single strategy"""
    strategy_id: str
    trades_count: int = 0
    total_profit: float = 0.0
    win_rate: float = 0.0
    avg_execution_time: float = 0.0
    avg_slippage: float = 0.0
    success_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThompsonSamplingState:
    """Thompson Sampling state for multi-armed bandit optimization"""
    strategy_id: str
    alpha: float = 1.0  # Beta dist parameter
    beta: float = 1.0
    trials: int = 0
    successes: int = 0
    cumulative_reward: float = 0.0


class MarketRegimeDetector:
    """Classifies market conditions into 5 regimes"""
    
    def __init__(self, lookback_minutes: int = 60):
        self.lookback_minutes = lookback_minutes
        self.price_history: List[Tuple[datetime, float]] = []
        self.volatility_window = 20
        
    async def detect_regime(self, current_metrics: Dict[str, float]) -> MarketRegime:
        """
        Classify market into 5 regimes based on volatility + trend
        Regimes: high_vol, trending_up, trending_down, ranging, volatile
        """
        volatility = current_metrics.get('volatility', 0.0)
        trend = current_metrics.get('trend', 0.0)
        momentum = current_metrics.get('momentum', 0.0)
        
        # Regime classification logic
        if volatility > 0.08:
            regime_type = 'high_vol'
            confidence = 0.92
        elif abs(trend) > 0.05 and abs(momentum) > 0.03:
            if trend > 0:
                regime_type = 'trending_up'
            else:
                regime_type = 'trending_down'
            confidence = 0.88
        elif volatility < 0.02:
            regime_type = 'ranging'
            confidence = 0.85
        elif volatility > 0.05:
            regime_type = 'volatile'
            confidence = 0.86
        else:
            regime_type = 'neutral'
            confidence = 0.80
        
        logger.info(f"Market regime: {regime_type} (confidence: {confidence})")
        
        return MarketRegime(
            regime_type=regime_type,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            metrics=current_metrics
        )


class ThompsonSamplingOptimizer:
    """Multi-armed bandit optimizer for strategy selection"""
    
    def __init__(self, strategy_ids: List[str]):
        self.states: Dict[str, ThompsonSamplingState] = {
            sid: ThompsonSamplingState(strategy_id=sid)
            for sid in strategy_ids
        }
        self.min_trials_for_update = 5
    
    def select_strategy(self) -> str:
        """Thompson Sampling: sample from each arm's posterior, select best"""
        samples = {}
        
        for sid, state in self.states.items():
            # Sample from Beta distribution
            sample = np.random.beta(state.alpha, state.beta)
            samples[sid] = sample
        
        # Select highest sampled strategy
        best_strategy = max(samples, key=samples.get)
        logger.debug(f"Thompson sampling selected: {best_strategy} (samples: {samples})")
        return best_strategy
    
    def update(self, strategy_id: str, reward: float, success: bool):
        """Update posterior after strategy execution"""
        if strategy_id not in self.states:
            return
        
        state = self.states[strategy_id]
        state.trials += 1
        state.cumulative_reward += reward
        
        if success:
            state.successes += 1
            state.alpha += 1.0  # Increase alpha for success
        else:
            state.beta += 1.0   # Increase beta for failure
        
        logger.debug(
            f"Updated {strategy_id}: "
            f"trials={state.trials}, successes={state.successes}, "
            f"alpha={state.alpha}, beta={state.beta}"
        )
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get normalized strategy weights based on success rates"""
        weights = {}
        total_successes = sum(s.successes for s in self.states.values())
        total_trials = sum(s.trials for s in self.states.values())
        
        for sid, state in self.states.items():
            if total_trials == 0:
                weights[sid] = 1.0 / len(self.states)
            else:
                success_rate = state.successes / max(state.trials, 1)
                weights[sid] = (state.successes + 1) / (total_trials + len(self.states))
        
        # Normalize
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights


class AIOptimizationEngine:
    """
    24/7 AI optimization engine that auto-tunes every 15 minutes
    Responsibilities:
    - Market regime detection
    - Strategy weight optimization (Thompson Sampling)
    - Parameter tuning
    - Performance analytics
    """
    
    def __init__(self, strategy_ids: List[str], auto_tune_interval_minutes: int = 15):
        self.strategy_ids = strategy_ids
        self.auto_tune_interval = timedelta(minutes=auto_tune_interval_minutes)
        
        # Components
        self.regime_detector = MarketRegimeDetector()
        self.thompson_optimizer = ThompsonSamplingOptimizer(strategy_ids)
        
        # Metrics tracking
        self.metrics: Dict[str, StrategyMetrics] = {
            sid: StrategyMetrics(strategy_id=sid)
            for sid in strategy_ids
        }
        self.last_optimization = datetime.utcnow()
        self.market_regime_history: List[MarketRegime] = []
        
        # Parameters to optimize
        self.parameters = {
            'gas_price_multiplier': 1.2,
            'slippage_tolerance': 0.001,
            'min_profit_threshold': 0.5,
            'max_position_size': 1000.0,
            'execution_timeout_seconds': 30
        }
        
        logger.info(f"AI Optimizer initialized with {len(strategy_ids)} strategies")
    
    async def collect_metrics(self, execution_results: Dict) -> None:
        """
        Collect performance metrics from recent executions
        Input: {'strategy_id': ..., 'profit': ..., 'execution_time': ..., ...}
        """
        if not execution_results:
            return
        
        strategy_id = execution_results.get('strategy_id')
        if strategy_id not in self.metrics:
            return
        
        metrics = self.metrics[strategy_id]
        metrics.trades_count += 1
        metrics.total_profit += execution_results.get('profit', 0.0)
        metrics.avg_execution_time = (
            (metrics.avg_execution_time * (metrics.trades_count - 1) +
             execution_results.get('execution_time', 0.0)) / metrics.trades_count
        )
        metrics.avg_slippage = (
            (metrics.avg_slippage * (metrics.trades_count - 1) +
             execution_results.get('slippage', 0.0)) / metrics.trades_count
        )
        metrics.last_updated = datetime.utcnow()
        
        # Update Thompson Sampling
        success = execution_results.get('success', False)
        reward = execution_results.get('profit', 0.0)
        self.thompson_optimizer.update(strategy_id, reward, success)
        
        logger.debug(f"Collected metrics for {strategy_id}: profit={reward}, success={success}")
    
    async def detect_market_condition(self, current_data: Dict[str, float]) -> MarketRegime:
        """Detect current market regime"""
        regime = await self.regime_detector.detect_regime(current_data)
        self.market_regime_history.append(regime)
        
        # Keep only last 100 regimes
        if len(self.market_regime_history) > 100:
            self.market_regime_history = self.market_regime_history[-100:]
        
        return regime
    
    async def optimize_parameters(self, current_regime: MarketRegime) -> Dict[str, float]:
        """
        Auto-tune parameters based on market regime and performance
        Returns updated parameters
        """
        regime_type = current_regime.regime_type
        
        # Regime-specific parameter adjustments
        if regime_type == 'high_vol':
            self.parameters['slippage_tolerance'] = 0.002
            self.parameters['gas_price_multiplier'] = 1.3
        elif regime_type == 'trending_up':
            self.parameters['slippage_tolerance'] = 0.0008
            self.parameters['gas_price_multiplier'] = 1.1
        elif regime_type == 'ranging':
            self.parameters['slippage_tolerance'] = 0.0005
            self.parameters['gas_price_multiplier'] = 0.95
        
        # Adjust based on recent performance
        best_strategy = max(
            self.metrics.values(),
            key=lambda m: m.total_profit if m.trades_count > 0 else 0
        )
        
        if best_strategy.trades_count > 10:
            if best_strategy.win_rate < 0.80:
                self.parameters['min_profit_threshold'] *= 1.1
            if best_strategy.avg_slippage > 0.001:
                self.parameters['slippage_tolerance'] *= 0.9
        
        logger.info(f"Optimized parameters for {regime_type}: {self.parameters}")
        return self.parameters
    
    async def run_auto_tuning_cycle(self, execution_results: List[Dict]) -> Dict:
        """
        Run complete 15-minute auto-tuning cycle
        Returns optimization report
        """
        logger.info("Starting AI auto-tuning cycle...")
        
        # Collect metrics from recent executions
        for result in execution_results:
            await self.collect_metrics(result)
        
        # Detect market condition (mock data for now)
        current_data = {
            'volatility': np.random.uniform(0.01, 0.1),
            'trend': np.random.uniform(-0.1, 0.1),
            'momentum': np.random.uniform(-0.1, 0.1)
        }
        market_regime = await self.detect_market_condition(current_data)
        
        # Optimize parameters
        optimized_params = await self.optimize_parameters(market_regime)
        
        # Get strategy weights
        strategy_weights = self.thompson_optimizer.get_strategy_weights()
        
        # Generate report
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'market_regime': market_regime.regime_type,
            'regime_confidence': market_regime.confidence,
            'strategy_weights': strategy_weights,
            'optimized_parameters': optimized_params,
            'metrics_summary': {
                sid: {
                    'trades': m.trades_count,
                    'total_profit': round(m.total_profit, 4),
                    'win_rate': round(m.win_rate, 4),
                    'avg_execution_time': round(m.avg_execution_time, 3)
                }
                for sid, m in self.metrics.items()
            }
        }
        
        logger.info(f"Auto-tuning cycle complete: {report}")
        return report
    
    def get_selected_strategy(self) -> str:
        """Get next strategy to execute using Thompson Sampling"""
        return self.thompson_optimizer.select_strategy()
    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get current strategy weights"""
        return self.thompson_optimizer.get_strategy_weights()
    
    def should_run_optimization(self) -> bool:
        """Check if 15-minute interval has elapsed"""
        return (datetime.utcnow() - self.last_optimization) >= self.auto_tune_interval
    
    async def periodic_optimization_loop(self, execution_queue: asyncio.Queue):
        """
        Run continuously, executing optimization every 15 minutes
        """
        logger.info("AI Optimization loop started")
        
        while True:
            try:
                if self.should_run_optimization():
                    # Collect recent execution results
                    recent_results = []
                    try:
                        while len(recent_results) < 50:
                            result = execution_queue.get_nowait()
                            recent_results.append(result)
                    except asyncio.QueueEmpty:
                        pass
                    
                    # Run optimization
                    await self.run_auto_tuning_cycle(recent_results)
                    self.last_optimization = datetime.utcnow()
                
                await asyncio.sleep(60)  # Check every minute
            
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)
