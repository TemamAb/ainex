"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON TIER 2: ORCHESTRATOR                                ║
║                     Strategy Selection & Risk Management                       ║
║                                                                                ║
║  Purpose: Filter opportunities, apply AI, route to executors, manage risk     ║
║  Tier: Central coordinator with per-strategy routing                          ║
║  Interval: 100ms decision cycles, 15-min AI optimization                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Six simultaneous profit strategies"""
    LIQUIDATION_CASCADE = "liquidation_cascade"
    MULTI_DEX_ARBITRAGE = "multi_dex_arbitrage"
    MEV_CAPTURE = "mev_capture"
    LP_FARMING = "lp_farming"
    CROSS_CHAIN = "cross_chain"
    FLASH_CRASH = "flash_crash"


@dataclass
class RiskProfile:
    """Risk management parameters"""
    max_position_usd: Decimal
    max_daily_loss_usd: Decimal
    max_slippage_pct: float
    position_limit_per_pair: int
    correlation_threshold: float  # Risk correlation limit


@dataclass
class ExecutionSignal:
    """Signal sent from orchestrator to executor tier"""
    signal_id: str
    strategy: StrategyType
    token_in: str
    token_out: str
    pair_name: str
    amount: Decimal
    buy_dex: str
    sell_dex: str
    buy_price: Decimal
    sell_price: Decimal
    expected_profit_pct: float
    confidence_score: float
    risk_score: float
    routing_priority: int  # 1 (highest) to 5 (lowest)
    ai_recommendation: str
    gasless_mode: bool
    timestamp: float = field(default_factory=time.time)
    execution_deadline_ms: int = 5000  # 5 seconds


@dataclass
class ExecutionResult:
    """Result from executor tier"""
    signal_id: str
    status: str  # PENDING, CONFIRMED, FAILED, REVERTED
    tx_hash: str
    actual_profit: Decimal
    slippage_pct: float
    execution_time_ms: float
    gas_used: Decimal
    fee_paid: Decimal


class AIOptimizer:
    """AI optimization engine - runs every 15 minutes"""
    
    def __init__(self):
        self.model_version = "1.0"
        self.last_optimization = time.time()
        self.optimization_interval = 900  # 15 minutes
        self.metrics_history = deque(maxlen=96)  # 24 hours of 15-min data
        self.strategy_weights = {
            StrategyType.LIQUIDATION_CASCADE: 0.25,
            StrategyType.MULTI_DEX_ARBITRAGE: 0.25,
            StrategyType.MEV_CAPTURE: 0.20,
            StrategyType.LP_FARMING: 0.15,
            StrategyType.CROSS_CHAIN: 0.10,
            StrategyType.FLASH_CRASH: 0.05,
        }
        self.confidence_threshold = 0.75
        self.slippage_sensitivity = 0.001  # Adjust based on market conditions
    
    async def optimize(self, execution_history: List[ExecutionResult]) -> Dict:
        """Run AI optimization cycle every 15 minutes"""
        logger.info("[AI] Starting optimization cycle...")
        start_time = time.time()
        
        if not execution_history:
            logger.warning("[AI] No execution history available")
            return self._get_default_optimization()
        
        # Analyze recent performance
        recent_trades = execution_history[-100:] if len(execution_history) > 100 else execution_history
        
        # Calculate strategy performance
        strategy_performance = self._analyze_strategy_performance(recent_trades)
        
        # Adjust weights based on performance
        self._adjust_strategy_weights(strategy_performance)
        
        # Optimize confidence thresholds
        self._optimize_confidence_thresholds(recent_trades)
        
        # Update slippage sensitivity
        self._update_slippage_sensitivity(recent_trades)
        
        optimization_time = time.time() - start_time
        logger.info(f"[AI] Optimization complete in {optimization_time:.2f}s")
        
        return {
            "timestamp": time.time(),
            "optimization_time_ms": optimization_time * 1000,
            "strategy_weights": {k.value: v for k, v in self.strategy_weights.items()},
            "confidence_threshold": self.confidence_threshold,
            "slippage_sensitivity": self.slippage_sensitivity,
            "recommendations": self._generate_recommendations(strategy_performance)
        }
    
    def _analyze_strategy_performance(self, trades: List[ExecutionResult]) -> Dict:
        """Analyze profitability and success rate by strategy"""
        performance = {}
        
        for strategy in StrategyType:
            strategy_trades = [t for t in trades if hasattr(t, 'strategy') and t.strategy == strategy]
            
            if not strategy_trades:
                performance[strategy] = {
                    "count": 0,
                    "success_rate": 0,
                    "avg_profit": 0,
                    "roi_pct": 0
                }
                continue
            
            successful = [t for t in strategy_trades if t.status == "CONFIRMED"]
            total_profit = sum(t.actual_profit for t in successful)
            
            performance[strategy] = {
                "count": len(strategy_trades),
                "success_rate": len(successful) / len(strategy_trades),
                "avg_profit": total_profit / len(successful) if successful else 0,
                "roi_pct": (total_profit / (len(strategy_trades) * 1.0)) * 100 if strategy_trades else 0
            }
        
        return performance
    
    def _adjust_strategy_weights(self, performance: Dict) -> None:
        """Adjust strategy weights based on performance"""
        total_weight = sum(self.strategy_weights.values())
        
        for strategy, metrics in performance.items():
            if metrics['success_rate'] > 0.8:
                # Increase weight for high-success strategies
                self.strategy_weights[strategy] = min(
                    self.strategy_weights[strategy] * 1.1,
                    0.4
                )
            elif metrics['success_rate'] < 0.3:
                # Decrease weight for low-success strategies
                self.strategy_weights[strategy] = max(
                    self.strategy_weights[strategy] * 0.9,
                    0.02
                )
        
        # Renormalize weights
        total = sum(self.strategy_weights.values())
        for strategy in self.strategy_weights:
            self.strategy_weights[strategy] /= total
    
    def _optimize_confidence_thresholds(self, trades: List[ExecutionResult]) -> None:
        """Adjust confidence thresholds based on accuracy"""
        if not trades:
            return
        
        successful = [t for t in trades if t.status == "CONFIRMED"]
        if not successful:
            return
        
        success_rate = len(successful) / len(trades)
        
        if success_rate > 0.8:
            self.confidence_threshold = max(self.confidence_threshold - 0.05, 0.5)
        elif success_rate < 0.5:
            self.confidence_threshold = min(self.confidence_threshold + 0.05, 0.95)
    
    def _update_slippage_sensitivity(self, trades: List[ExecutionResult]) -> None:
        """Adjust slippage sensitivity based on market conditions"""
        if not trades:
            return
        
        avg_slippage = sum(t.slippage_pct for t in trades) / len(trades)
        
        if avg_slippage < 0.05:
            self.slippage_sensitivity = max(self.slippage_sensitivity - 0.0001, 0.0001)
        elif avg_slippage > 0.2:
            self.slippage_sensitivity = min(self.slippage_sensitivity + 0.0001, 0.01)
    
    def _generate_recommendations(self, performance: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        for strategy, metrics in performance.items():
            if metrics['success_rate'] > 0.9:
                recommendations.append(f"Increase capital allocation to {strategy.value}")
            elif metrics['success_rate'] < 0.3:
                recommendations.append(f"Review or reduce {strategy.value} strategy")
        
        return recommendations
    
    def _get_default_optimization(self) -> Dict:
        """Return default optimization when history is unavailable"""
        return {
            "timestamp": time.time(),
            "optimization_time_ms": 0,
            "strategy_weights": {k.value: v for k, v in self.strategy_weights.items()},
            "confidence_threshold": self.confidence_threshold,
            "slippage_sensitivity": self.slippage_sensitivity,
            "recommendations": []
        }


class EnterpriseRiskManager:
    """Risk management across all positions"""
    
    def __init__(self, risk_profile: RiskProfile):
        self.risk_profile = risk_profile
        self.active_positions: Dict[str, Dict] = {}
        self.daily_profit = Decimal('0')
        self.daily_loss = Decimal('0')
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.position_history = deque(maxlen=1000)
    
    def can_execute_trade(self, signal: ExecutionSignal) -> Tuple[bool, Optional[str]]:
        """Check if trade can be executed within risk limits"""
        
        # Check daily loss limit
        if self.daily_loss >= self.risk_profile.max_daily_loss_usd:
            return False, "Daily loss limit reached"
        
        # Check position size
        if signal.amount > self.risk_profile.max_position_usd:
            return False, f"Position exceeds max ({signal.amount} > {self.risk_profile.max_position_usd})"
        
        # Check existing positions for same pair
        pair_key = f"{signal.token_in}/{signal.token_out}"
        pair_positions = [p for p in self.active_positions.values() if p.get('pair') == pair_key]
        
        if len(pair_positions) >= self.risk_profile.position_limit_per_pair:
            return False, f"Position limit for {pair_key} reached"
        
        # Check correlation with existing positions
        if not self._check_correlation_limit(signal):
            return False, "Position too correlated with existing positions"
        
        # Check slippage
        if signal.expected_profit_pct < (signal.confidence_score * 0.5):  # Simple slippage check
            return False, "Expected profit too low relative to confidence"
        
        return True, None
    
    def _check_correlation_limit(self, signal: ExecutionSignal) -> bool:
        """Check if position is too correlated with existing positions"""
        if not self.active_positions:
            return True
        
        # Simple correlation check - don't do too many similar pairs at once
        pair_key = f"{signal.token_in}/{signal.token_out}"
        similar_positions = sum(1 for p in self.active_positions.values() if p.get('pair') == pair_key)
        
        return similar_positions < self.risk_profile.position_limit_per_pair
    
    def record_position(self, signal: ExecutionSignal) -> None:
        """Record new position"""
        position_id = str(uuid.uuid4())
        self.active_positions[position_id] = {
            'signal_id': signal.signal_id,
            'pair': f"{signal.token_in}/{signal.token_out}",
            'amount': signal.amount,
            'entry_time': time.time(),
            'expected_profit': signal.expected_profit_pct
        }
    
    def record_result(self, result: ExecutionResult) -> None:
        """Record execution result and update risk metrics"""
        if result.status == "CONFIRMED":
            self.daily_profit += result.actual_profit
        else:
            self.daily_loss += result.actual_profit * Decimal('-1')
        
        self.position_history.append({
            'result': result,
            'timestamp': time.time()
        })
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics"""
        return {
            "active_positions": len(self.active_positions),
            "daily_profit": float(self.daily_profit),
            "daily_loss": float(self.daily_loss),
            "daily_net": float(self.daily_profit - self.daily_loss),
            "loss_limit_remaining": float(self.risk_profile.max_daily_loss_usd - self.daily_loss),
            "position_limit_remaining": self.risk_profile.position_limit_per_pair - len(self.active_positions)
        }


class Orchestrator:
    """Tier 2: Central orchestration and routing"""
    
    def __init__(self):
        self.orchestrator_id = f"orchestrator_{int(time.time() * 1000)}"
        self.ai_optimizer = AIOptimizer()
        
        # Default risk profile
        risk_profile = RiskProfile(
            max_position_usd=Decimal('10000000'),  # $10M max position
            max_daily_loss_usd=Decimal('1500000'),  # $1.5M daily loss cap
            max_slippage_pct=0.001,  # 0.1% max slippage
            position_limit_per_pair=5,
            correlation_threshold=0.7
        )
        self.risk_manager = EnterpriseRiskManager(risk_profile)
        
        self.execution_signals: List[ExecutionSignal] = []
        self.execution_results: List[ExecutionResult] = []
        self.executor_callbacks: Dict[StrategyType, Callable] = {}
        
        self.stats = {
            "signals_generated": 0,
            "signals_approved": 0,
            "signals_rejected": 0,
            "last_decision_time": 0,
            "ai_optimizations": 0
        }
    
    def register_executor_callback(self, strategy: StrategyType, callback: Callable) -> None:
        """Register callback for specific strategy executor"""
        self.executor_callbacks[strategy] = callback
        logger.info(f"[ORCHESTRATOR] Registered executor for {strategy.value}")
    
    async def process_opportunities(self, opportunities: List) -> List[ExecutionSignal]:
        """Process scanner opportunities and generate execution signals"""
        start_time = time.time()
        signals = []
        
        for opp in opportunities:
            # Apply AI confidence scoring
            ai_score = self.ai_optimizer.confidence_threshold
            adjusted_confidence = opp.confidence_score * ai_score
            
            # Risk check
            signal = ExecutionSignal(
                signal_id=f"sig_{int(time.time() * 1000)}_{opp.opportunity_id[-4:]}",
                strategy=StrategyType.MULTI_DEX_ARBITRAGE,  # Default strategy
                token_in=opp.token_in,
                token_out=opp.token_out,
                pair_name=opp.pair_name,
                amount=opp.amount_to_trade,
                buy_dex=opp.buy_dex.value,
                sell_dex=opp.sell_dex.value,
                buy_price=opp.buy_price,
                sell_price=opp.sell_price,
                expected_profit_pct=opp.spread_pct,
                confidence_score=adjusted_confidence,
                risk_score=1.0 - adjusted_confidence,  # Risk = inverse of confidence
                routing_priority=1 if adjusted_confidence > 0.85 else 2,
                ai_recommendation=f"Execute {opp.pair_name} with {adjusted_confidence:.1%} confidence",
                gasless_mode=True,
                timestamp=time.time()
            )
            
            # Risk manager approval
            can_execute, reason = self.risk_manager.can_execute_trade(signal)
            
            self.stats["signals_generated"] += 1
            
            if can_execute:
                signals.append(signal)
                self.stats["signals_approved"] += 1
                self.risk_manager.record_position(signal)
                logger.info(f"[ORCHESTRATOR] Signal approved: {signal.signal_id}")
            else:
                self.stats["signals_rejected"] += 1
                logger.warning(f"[ORCHESTRATOR] Signal rejected: {reason}")
        
        self.stats["last_decision_time"] = time.time() - start_time
        self.execution_signals.extend(signals)
        
        return signals
    
    async def route_to_executors(self, signals: List[ExecutionSignal]) -> None:
        """Route signals to appropriate executor tiers"""
        for signal in signals:
            executor = self.executor_callbacks.get(signal.strategy)
            if executor:
                try:
                    await executor(signal)
                except Exception as e:
                    logger.error(f"[ORCHESTRATOR] Executor error: {e}")
    
    async def run_ai_optimization(self) -> Dict:
        """Run AI optimization cycle (every 15 minutes)"""
        logger.info("[ORCHESTRATOR] Running AI optimization cycle...")
        
        result = await self.ai_optimizer.optimize(self.execution_results)
        self.stats["ai_optimizations"] += 1
        
        return result
    
    async def run(self, scanner_callback: Callable) -> None:
        """Main orchestrator loop"""
        logger.info(f"[ORCHESTRATOR] Started: {self.orchestrator_id}")
        
        last_ai_update = time.time()
        
        try:
            while True:
                # AI optimization every 15 minutes
                current_time = time.time()
                if current_time - last_ai_update >= 900:  # 900 seconds = 15 minutes
                    ai_result = await self.run_ai_optimization()
                    logger.info(f"[ORCHESTRATOR] AI optimization complete: {ai_result['recommendations']}")
                    last_ai_update = current_time
                
                # Get opportunities from scanner
                opportunities = await scanner_callback()
                
                # Process and route to executors
                signals = await self.process_opportunities(opportunities)
                await self.route_to_executors(signals)
                
                # Decision cycle (100ms)
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("[ORCHESTRATOR] Shutdown requested")
    
    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        return {
            "orchestrator_id": self.orchestrator_id,
            "signals_generated": self.stats["signals_generated"],
            "signals_approved": self.stats["signals_approved"],
            "signals_rejected": self.stats["signals_rejected"],
            "last_decision_time_ms": self.stats["last_decision_time"] * 1000,
            "ai_optimizations": self.stats["ai_optimizations"],
            "risk_metrics": self.risk_manager.get_risk_metrics()
        }


async def run_orchestrator():
    """Standalone orchestrator process"""
    orchestrator = Orchestrator()
    logger.info(f"[ORCHESTRATOR] Started: {orchestrator.orchestrator_id}")
    
    # Mock scanner callback
    async def mock_scanner():
        return []
    
    # Register mock executor
    async def mock_executor(signal: ExecutionSignal):
        logger.info(f"[ORCHESTRATOR] Would execute: {signal.signal_id}")
    
    orchestrator.register_executor_callback(StrategyType.MULTI_DEX_ARBITRAGE, mock_executor)
    
    await orchestrator.run(mock_scanner)


if __name__ == "__main__":
    asyncio.run(run_orchestrator())
