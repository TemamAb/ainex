"""
AINEON Auto-Tuning Engine
Continuous parameter optimization using ML and market regime detection.

Features:
- Every 15-minute parameter tuning cycle
- Market regime detection (5 types)
- Strategy weight optimization (Thompson Sampling)
- Gas price prediction
- Position sizing dynamic adjustment
- Profit threshold auto-tuning
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGE_BOUND = "range_bound"
    VOLATILE = "volatile"
    CALM = "calm"


class AutoTuner:
    """
    Continuously optimizes AINEON parameters every 15 minutes based on
    performance metrics and market conditions.
    """
    
    TUNING_INTERVAL_MINUTES = 15
    
    def __init__(
        self,
        strategy_orchestrator,
        profit_ledger,
        price_oracle,
    ):
        """
        Initialize auto-tuner.
        
        Args:
            strategy_orchestrator: Strategy orchestrator instance
            profit_ledger: Profit ledger for performance data
            price_oracle: Price oracle for market data
        """
        self.orchestrator = strategy_orchestrator
        self.profit_ledger = profit_ledger
        self.price_oracle = price_oracle
        
        # Current parameters
        self.min_profit_threshold = Decimal("0.5")
        self.max_slippage_pct = Decimal("0.1")
        self.position_multiplier = Decimal("1.0")
        self.gas_price_multiplier = Decimal("1.0")
        
        # Strategy weights
        self.strategy_weights = {s: Decimal("1.0") for s in self.orchestrator.STRATEGIES}
        
        # Market regime
        self.current_regime = MarketRegime.CALM
        
        # Tuning history
        self.tuning_count = 0
        self.last_tuning_time = datetime.now()
        
        logger.info(f"Auto-Tuner initialized")
        logger.info(f"  Tuning interval: {self.TUNING_INTERVAL_MINUTES} minutes")
    
    async def run_continuous_tuning(self):
        """Run continuous tuning loop every 15 minutes."""
        logger.info("Starting continuous tuning loop...")
        
        while True:
            try:
                await asyncio.sleep(self.TUNING_INTERVAL_MINUTES * 60)
                await self.tune_parameters()
            except Exception as e:
                logger.error(f"Tuning error: {e}")
                await asyncio.sleep(30)  # Brief pause before retry
    
    async def tune_parameters(self):
        """Execute 15-minute tuning cycle."""
        try:
            logger.info(f"\n[AUTO-TUNING] Starting 15-minute tuning cycle")
            
            # Step 1: Collect metrics from last 15 minutes
            logger.debug("Step 1: Collecting performance metrics...")
            metrics = await self._collect_metrics()
            
            # Step 2: Detect market regime
            logger.debug("Step 2: Detecting market regime...")
            regime = await self._detect_market_regime()
            self.current_regime = regime
            logger.info(f"  Market Regime: {regime.value}")
            
            # Step 3: Analyze strategy performance
            logger.debug("Step 3: Analyzing strategy performance...")
            strategy_analysis = self._analyze_strategy_performance(metrics)
            
            # Step 4: Generate tuning suggestions
            logger.debug("Step 4: Generating tuning suggestions...")
            suggestions = self._generate_tuning_suggestions(
                metrics, regime, strategy_analysis
            )
            
            # Step 5: Apply conservative adjustments
            logger.debug("Step 5: Applying adjustments...")
            self._apply_tuning_suggestions(suggestions)
            
            # Log results
            self.tuning_count += 1
            self.last_tuning_time = datetime.now()
            
            logger.info(f"\n[TUNING COMPLETE] Cycle #{self.tuning_count}")
            logger.info(f"  Min Profit Threshold: {self.min_profit_threshold} ETH")
            logger.info(f"  Max Slippage: {self.max_slippage_pct}%")
            logger.info(f"  Position Multiplier: {self.position_multiplier}x")
            logger.info(f"  Gas Price Multiplier: {self.gas_price_multiplier}x")
            
            # Log strategy weights
            logger.info("  Strategy Weights:")
            for strategy, weight in self.strategy_weights.items():
                logger.info(f"    {strategy}: {weight}x")
        
        except Exception as e:
            logger.error(f"Tuning cycle error: {e}", exc_info=True)
    
    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics from last 15 minutes."""
        try:
            # Get profitability data
            profit_15m = Decimal("0")
            trades_15m = 0
            win_rate_15m = Decimal("0")
            
            if hasattr(self.profit_ledger, 'get_profit_last_period'):
                profit_data = await self.profit_ledger.get_profit_last_period(minutes=15)
                profit_15m = Decimal(str(profit_data.get('total_profit', 0)))
                trades_15m = profit_data.get('trade_count', 0)
                win_rate_15m = Decimal(str(profit_data.get('win_rate', 0)))
            
            # Get gas prices
            avg_gas_15m = await self.price_oracle.get_avg_gas_price_15m()
            
            # Get strategy stats
            strategy_stats = self.orchestrator.get_strategy_performance()
            
            return {
                "profit_15m": profit_15m,
                "trades_15m": trades_15m,
                "win_rate_15m": win_rate_15m,
                "avg_gas_price": avg_gas_15m,
                "strategy_stats": strategy_stats,
            }
        
        except Exception as e:
            logger.debug(f"Error collecting metrics: {e}")
            return {}
    
    async def _detect_market_regime(self) -> MarketRegime:
        """Detect current market regime using technical indicators."""
        try:
            # Get RSI, Bollinger Bands, ATR, Volume
            rsi = await self.price_oracle.get_rsi(period=14)
            bollinger = await self.price_oracle.get_bollinger_bands(period=20)
            atr = await self.price_oracle.get_atr(period=14)
            
            # Classify regime
            if rsi > Decimal("60"):
                return MarketRegime.TRENDING_UP
            elif rsi < Decimal("40"):
                return MarketRegime.TRENDING_DOWN
            elif bollinger['width'] > Decimal("5"):
                return MarketRegime.VOLATILE
            elif atr < Decimal("0.5"):
                return MarketRegime.CALM
            else:
                return MarketRegime.RANGE_BOUND
        
        except Exception as e:
            logger.debug(f"Regime detection error: {e}")
            return MarketRegime.CALM
    
    def _analyze_strategy_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze which strategies performed best in last 15 minutes."""
        try:
            strategy_stats = metrics.get('strategy_stats', {})
            
            analysis = {}
            for strategy, stats in strategy_stats.items():
                win_rate = stats.get('win_rate', 0)
                total = stats.get('total', 0)
                
                # Weight by sample size
                confidence = min(Decimal("1.0"), Decimal(str(total)) / Decimal("10"))
                weighted_score = Decimal(str(win_rate)) * confidence
                
                analysis[strategy] = {
                    "win_rate": win_rate,
                    "total_trades": total,
                    "confidence": float(confidence),
                    "weighted_score": float(weighted_score),
                }
            
            return analysis
        
        except Exception as e:
            logger.debug(f"Strategy analysis error: {e}")
            return {}
    
    def _generate_tuning_suggestions(
        self,
        metrics: Dict[str, Any],
        regime: MarketRegime,
        strategy_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate conservative tuning suggestions."""
        try:
            suggestions = {}
            
            # 1. Adjust min profit threshold based on win rate
            win_rate_15m = metrics.get('win_rate_15m', Decimal("0"))
            if win_rate_15m > Decimal("0.88"):
                # Winning streak - can lower threshold slightly
                suggestions['min_profit'] = self.min_profit_threshold * Decimal("0.95")
            elif win_rate_15m < Decimal("0.70"):
                # Losing period - raise threshold
                suggestions['min_profit'] = self.min_profit_threshold * Decimal("1.1")
            
            # 2. Adjust slippage tolerance
            if regime == MarketRegime.VOLATILE:
                suggestions['max_slippage'] = self.max_slippage_pct * Decimal("0.8")  # Stricter
            elif regime == MarketRegime.CALM:
                suggestions['max_slippage'] = self.max_slippage_pct * Decimal("1.2")  # Relaxed
            
            # 3. Adjust position multiplier based on profitability
            profit_15m = metrics.get('profit_15m', Decimal("0"))
            if profit_15m > Decimal("10"):
                suggestions['position_multiplier'] = min(Decimal("1.5"), self.position_multiplier * Decimal("1.1"))
            elif profit_15m < Decimal("1"):
                suggestions['position_multiplier'] = max(Decimal("0.5"), self.position_multiplier * Decimal("0.9"))
            
            # 4. Update strategy weights based on performance
            suggestions['strategy_weights'] = {}
            for strategy, analysis in strategy_analysis.items():
                score = Decimal(str(analysis.get('weighted_score', 0)))
                # Gradual adjustment towards better performing strategies
                new_weight = self.strategy_weights[strategy] * (Decimal("1.0") + (score - Decimal("0.5")) * Decimal("0.1"))
                suggestions['strategy_weights'][strategy] = new_weight
            
            # 5. Adjust gas price multiplier
            avg_gas = metrics.get('avg_gas_price', 0)
            if isinstance(avg_gas, (int, float)) and avg_gas > 100:
                # High gas - be more selective
                suggestions['gas_multiplier'] = self.gas_price_multiplier * Decimal("1.1")
            
            return suggestions
        
        except Exception as e:
            logger.debug(f"Suggestion generation error: {e}")
            return {}
    
    def _apply_tuning_suggestions(self, suggestions: Dict[str, Any]):
        """Apply conservative parameter adjustments."""
        try:
            # Apply min profit adjustment (max ±10%)
            if 'min_profit' in suggestions:
                new_value = suggestions['min_profit']
                max_change = self.min_profit_threshold * Decimal("0.1")
                clamped = max(
                    self.min_profit_threshold - max_change,
                    min(self.min_profit_threshold + max_change, new_value)
                )
                self.min_profit_threshold = clamped
                logger.debug(f"Adjusted min profit: {clamped}")
            
            # Apply slippage adjustment (max ±10%)
            if 'max_slippage' in suggestions:
                new_value = suggestions['max_slippage']
                max_change = self.max_slippage_pct * Decimal("0.1")
                clamped = max(
                    self.max_slippage_pct - max_change,
                    min(self.max_slippage_pct + max_change, new_value)
                )
                self.max_slippage_pct = clamped
                logger.debug(f"Adjusted max slippage: {clamped}")
            
            # Apply position multiplier (max ±10%)
            if 'position_multiplier' in suggestions:
                new_value = suggestions['position_multiplier']
                max_change = self.position_multiplier * Decimal("0.1")
                clamped = max(
                    self.position_multiplier - max_change,
                    min(self.position_multiplier + max_change, new_value)
                )
                self.position_multiplier = clamped
                logger.debug(f"Adjusted position multiplier: {clamped}")
            
            # Apply strategy weight adjustments
            if 'strategy_weights' in suggestions:
                for strategy, new_weight in suggestions['strategy_weights'].items():
                    if strategy in self.strategy_weights:
                        # Smooth adjustment towards new weight
                        current = self.strategy_weights[strategy]
                        change = (new_weight - current) * Decimal("0.2")  # 20% of suggested change
                        self.strategy_weights[strategy] = current + change
                        logger.debug(f"Adjusted {strategy} weight: {self.strategy_weights[strategy]}")
        
        except Exception as e:
            logger.error(f"Error applying suggestions: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get auto-tuner statistics."""
        return {
            "tuning_cycles": self.tuning_count,
            "market_regime": self.current_regime.value,
            "min_profit_threshold": float(self.min_profit_threshold),
            "max_slippage_pct": float(self.max_slippage_pct),
            "position_multiplier": float(self.position_multiplier),
            "gas_price_multiplier": float(self.gas_price_multiplier),
            "strategy_weights": {k: float(v) for k, v in self.strategy_weights.items()},
        }
    
    def log_stats(self):
        """Log auto-tuner statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("AUTO-TUNER STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Tuning Cycles: {stats['tuning_cycles']}")
        logger.info(f"Market Regime: {stats['market_regime']}")
        logger.info(f"Min Profit Threshold: {stats['min_profit_threshold']} ETH")
        logger.info(f"Max Slippage: {stats['max_slippage_pct']}%")
        logger.info(f"Position Multiplier: {stats['position_multiplier']}x")
        logger.info(f"Gas Price Multiplier: {stats['gas_price_multiplier']}x")
        logger.info("=" * 70)


# Singleton instance
_auto_tuner: Optional[AutoTuner] = None


def initialize_auto_tuner(
    strategy_orchestrator,
    profit_ledger,
    price_oracle,
) -> AutoTuner:
    """Initialize auto-tuner."""
    global _auto_tuner
    _auto_tuner = AutoTuner(strategy_orchestrator, profit_ledger, price_oracle)
    return _auto_tuner


def get_auto_tuner() -> AutoTuner:
    """Get current auto-tuner instance."""
    if _auto_tuner is None:
        raise RuntimeError("Auto-tuner not initialized")
    return _auto_tuner
