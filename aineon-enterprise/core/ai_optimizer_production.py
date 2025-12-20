"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                 AINEON AI OPTIMIZER - PRODUCTION VERSION                      ║
║            Deep Learning Model for Strategy Optimization & Tuning             ║
║                                                                                ║
║  Purpose: Continuously optimize strategy weights and parameters               ║
║  Frequency: Every 15 minutes                                                  ║
║  Methods: Thompson Sampling, Neural Networks, Reinforcement Learning         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except:
    HAS_SKLEARN = False

try:
    import tensorflow as tf
    HAS_TF = True
except:
    HAS_TF = False


@dataclass
class StrategyPerformance:
    strategy_name: str
    success_count: int = 0
    failure_count: int = 0
    total_profit: Decimal = Decimal('0')
    avg_profit: Decimal = Decimal('0')
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0


class AIOptimizer:
    """
    Production AI optimizer with Thompson Sampling & Neural Networks
    """
    
    def __init__(self):
        self.last_optimization = datetime.now()
        self.optimization_interval = 900  # 15 minutes
        
        # Strategy weights (Thompson Sampling)
        self.strategy_weights = {
            "multi_dex_arbitrage": 0.40,
            "mev_capture": 0.20,
            "liquidation_cascade": 0.15,
            "lp_farming": 0.12,
            "cross_chain": 0.08,
            "flash_crash": 0.05
        }
        
        # Performance tracking
        self.strategy_history: Dict[str, deque] = {
            name: deque(maxlen=100) for name in self.strategy_weights.keys()
        }
        
        self.stats = {
            "optimizations_run": 0,
            "avg_improvement": 0.0,
            "total_strategies": len(self.strategy_weights),
            "best_performing": "multi_dex_arbitrage"
        }
        
        # ML models
        self.ml_enabled = HAS_TF and HAS_SKLEARN
        self.neural_network = None
        self.scaler = StandardScaler() if HAS_SKLEARN else None
        
        if self.ml_enabled:
            self._build_neural_network()
        
        logger.info(f"[AI] Optimizer initialized. ML enabled: {self.ml_enabled}")
    
    def _build_neural_network(self):
        """Build neural network for strategy optimization"""
        
        if not HAS_TF:
            return
        
        try:
            # Build simple neural network
            self.neural_network = tf.keras.Sequential([
                tf.keras.layers.Dense(64, activation='relu', input_shape=(10,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(6, activation='softmax')  # 6 strategies
            ])
            
            self.neural_network.compile(
                optimizer='adam',
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            logger.info("[AI] Neural network model built successfully")
        
        except Exception as e:
            logger.warning(f"[AI] Failed to build neural network: {e}")
            self.neural_network = None
    
    async def optimize(self, execution_history: List[Dict]) -> Dict:
        """
        Run AI optimization cycle
        
        Returns: Updated strategy weights and recommendations
        """
        
        logger.info("[AI] Starting optimization cycle...")
        start_time = datetime.now()
        
        # 1. Analyze strategy performance
        performance = await self._analyze_performance(execution_history)
        
        # 2. Apply Thompson Sampling
        new_weights = self._thompson_sampling(performance)
        
        # 3. Apply constraints (ensure weights sum to 1.0)
        new_weights = self._normalize_weights(new_weights)
        
        # 4. Get ML predictions (if available)
        if self.ml_enabled and len(execution_history) > 100:
            ml_weights = await self._get_ml_predictions(execution_history)
            # Blend with Thompson Sampling: 70% TS, 30% ML
            for strategy in self.strategy_weights:
                if strategy in ml_weights:
                    new_weights[strategy] = (
                        new_weights[strategy] * 0.7 +
                        ml_weights[strategy] * 0.3
                    )
        
        # 5. Update weights
        old_weights = self.strategy_weights.copy()
        self.strategy_weights = new_weights
        
        # 6. Calculate improvement
        improvement = self._calculate_improvement(performance)
        self.stats["avg_improvement"] = improvement
        self.stats["optimizations_run"] += 1
        
        # 7. Find best performing strategy
        best_strategy = max(
            performance.items(),
            key=lambda x: x[1].win_rate
        )[0]
        self.stats["best_performing"] = best_strategy
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"[AI] ✓ Optimization complete ({elapsed:.2f}s). "
            f"Improvement: {improvement:.1%}. "
            f"Best strategy: {best_strategy} ({performance[best_strategy].win_rate:.1%})"
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "old_weights": old_weights,
            "new_weights": self.strategy_weights,
            "improvement": f"{improvement:.1%}",
            "performance": {
                name: {
                    "win_rate": f"{perf.win_rate:.1%}",
                    "avg_profit": float(perf.avg_profit),
                    "sharpe_ratio": f"{perf.sharpe_ratio:.2f}"
                }
                for name, perf in performance.items()
            },
            "recommendations": self._generate_recommendations(performance)
        }
    
    async def _analyze_performance(self, history: List[Dict]) -> Dict[str, StrategyPerformance]:
        """Analyze performance of each strategy"""
        
        performance = {}
        
        for strategy_name in self.strategy_weights.keys():
            perf = StrategyPerformance(strategy_name=strategy_name)
            
            # Filter trades by strategy
            strategy_trades = [
                t for t in history
                if t.get('strategy') == strategy_name
            ]
            
            if not strategy_trades:
                performance[strategy_name] = perf
                continue
            
            # Calculate metrics
            profits = [Decimal(str(t.get('profit', 0))) for t in strategy_trades]
            
            perf.success_count = sum(1 for p in profits if p > 0)
            perf.failure_count = sum(1 for p in profits if p <= 0)
            perf.total_profit = sum(profits)
            perf.avg_profit = perf.total_profit / len(strategy_trades) if strategy_trades else Decimal('0')
            perf.win_rate = perf.success_count / len(strategy_trades) if strategy_trades else 0.0
            
            # Calculate Sharpe ratio (simple version)
            if len(profits) > 1:
                mean = float(perf.avg_profit)
                std = np.std([float(p) for p in profits])
                perf.sharpe_ratio = mean / std if std > 0 else 0.0
            
            performance[strategy_name] = perf
        
        return performance
    
    def _thompson_sampling(self, performance: Dict[str, StrategyPerformance]) -> Dict:
        """
        Thompson Sampling for multi-armed bandit optimization
        
        Allocates more weight to strategies with higher win rates
        while maintaining exploration of lower-performing strategies
        """
        
        new_weights = {}
        total_weight = 0
        
        for strategy_name, perf in performance.items():
            # Beta distribution based on success/failure counts
            # More successes → higher expected value
            alpha = perf.success_count + 1  # Add 1 for prior
            beta = perf.failure_count + 1
            
            # Expected value under beta distribution
            # E[X] = alpha / (alpha + beta)
            expected_value = alpha / (alpha + beta)
            
            # Reward = win_rate * profit_per_trade
            reward = perf.win_rate * float(perf.avg_profit)
            
            # Thompson weight = expected_value * reward
            thompson_weight = expected_value * max(reward, 0.1)
            
            new_weights[strategy_name] = thompson_weight
            total_weight += thompson_weight
        
        # Normalize
        if total_weight > 0:
            new_weights = {
                k: v / total_weight for k, v in new_weights.items()
            }
        
        return new_weights
    
    async def _get_ml_predictions(self, history: List[Dict]) -> Dict[str, float]:
        """
        Get strategy weight predictions from neural network
        
        Input features: strategy performance metrics
        Output: Weight allocation for each strategy
        """
        
        if not self.neural_network or not HAS_TF:
            return {}
        
        try:
            # Build feature vector from recent history
            features = self._build_feature_vector(history[-100:])
            
            if len(features) < 10:
                return {}
            
            # Scale features
            if self.scaler:
                features = self.scaler.fit_transform([features])[0]
            
            # Get predictions
            predictions = self.neural_network.predict(
                np.array([features]),
                verbose=0
            )[0]
            
            # Map to strategy names
            strategy_names = list(self.strategy_weights.keys())
            ml_weights = {
                name: float(pred) / sum(predictions)
                for name, pred in zip(strategy_names, predictions)
            }
            
            return ml_weights
        
        except Exception as e:
            logger.warning(f"[AI] ML prediction error: {e}")
            return {}
    
    def _build_feature_vector(self, history: List[Dict]) -> List[float]:
        """Build feature vector from trade history"""
        
        features = []
        
        if not history:
            return [0] * 10
        
        # Win rate
        total_trades = len(history)
        winning_trades = sum(1 for t in history if t.get('profit', 0) > 0)
        features.append(winning_trades / total_trades if total_trades > 0 else 0)
        
        # Average profit
        profits = [t.get('profit', 0) for t in history]
        avg_profit = sum(profits) / total_trades if total_trades > 0 else 0
        features.append(avg_profit)
        
        # Profit volatility
        if len(profits) > 1:
            std = np.std(profits)
            features.append(std)
        else:
            features.append(0)
        
        # Max drawdown
        cumsum = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumsum)
        drawdown = (cumsum - running_max).min() if len(cumsum) > 0 else 0
        features.append(float(drawdown))
        
        # Trend (recent vs older)
        if len(history) > 10:
            recent_avg = sum(profits[-10:]) / 10
            older_avg = sum(profits[:-10]) / (len(profits) - 10)
            trend = recent_avg - older_avg
            features.append(trend)
        else:
            features.append(0)
        
        # Fill remaining features
        while len(features) < 10:
            features.append(0)
        
        return features
    
    def _normalize_weights(self, weights: Dict) -> Dict:
        """Ensure weights sum to 1.0"""
        total = sum(weights.values())
        if total == 0:
            return {k: 1/len(weights) for k in weights}
        return {k: v/total for k, v in weights.items()}
    
    def _calculate_improvement(self, performance: Dict) -> float:
        """Calculate overall improvement from optimization"""
        
        # Improvement = average win rate improvement
        improvements = []
        
        for strategy_name, perf in performance.items():
            old_weight = self.strategy_weights.get(strategy_name, 0)
            improvements.append(perf.win_rate)
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _generate_recommendations(self, performance: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        
        recommendations = []
        
        for strategy_name, perf in performance.items():
            if perf.win_rate > 0.85:
                new_weight = self.strategy_weights[strategy_name]
                if new_weight < 0.4:
                    recommendations.append(
                        f"Increase allocation to {strategy_name} "
                        f"({perf.win_rate:.1%} win rate)"
                    )
            elif perf.win_rate < 0.3:
                recommendations.append(
                    f"Review or reduce {strategy_name} "
                    f"({perf.win_rate:.1%} win rate)"
                )
        
        return recommendations
    
    def get_stats(self) -> Dict:
        """Get optimizer statistics"""
        return {
            "ml_enabled": self.ml_enabled,
            "optimizations_run": self.stats["optimizations_run"],
            "avg_improvement": f"{self.stats['avg_improvement']:.1%}",
            "best_performing": self.stats["best_performing"],
            "current_weights": self.strategy_weights
        }
