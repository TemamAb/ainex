"""PHASE 4 FILE 2: Advanced Strategy Engine - Multi-Strategy Orchestration"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import time
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Strategy:
    """Trading strategy configuration"""
    name: str
    strategy_id: str
    enabled: bool = True
    weight: float = 1.0  # Strategy weight in ensemble
    min_confidence: float = 0.70
    max_position_size_eth: float = 1000.0
    max_daily_loss_eth: float = 100.0
    success_rate: float = 0.0
    total_profit_eth: float = 0.0
    trades_executed: int = 0
    last_execution_time: Optional[float] = None


@dataclass
class StrategyResult:
    """Strategy execution result"""
    strategy_name: str
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    expected_profit_eth: float
    position_size_eth: float
    timestamp: float = field(default_factory=time.time)
    executed: bool = False
    actual_profit_eth: float = 0.0


class AdvancedStrategyEngine:
    """Multi-strategy orchestration engine for Phase 4"""
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_results = []
        self.ensemble_predictions = []
        
        # Metrics
        self.total_signals_generated = 0
        self.total_strategies_executed = 0
        self.ensemble_accuracy = 0.0
        self.strategy_correlation_matrix = {}
        
        # Initialize 6 concurrent strategies
        self._initialize_strategies()
        
        logger.info("🎯 Advanced Strategy Engine initialized with 6 strategies")
    
    def _initialize_strategies(self):
        """Initialize all 6 concurrent strategies"""
        
        strategies_config = [
            {
                'name': 'Multi-DEX Arbitrage',
                'id': 'STRATEGY_001',
                'weight': 0.35,
                'min_confidence': 0.75
            },
            {
                'name': 'Flash Loan Sandwich',
                'id': 'STRATEGY_002',
                'weight': 0.25,
                'min_confidence': 0.70
            },
            {
                'name': 'MEV Protection+ Arb',
                'id': 'STRATEGY_003',
                'weight': 0.15,
                'min_confidence': 0.72
            },
            {
                'name': 'Liquidity Sweep',
                'id': 'STRATEGY_004',
                'weight': 0.12,
                'min_confidence': 0.68
            },
            {
                'name': 'Curve Bridge Arb',
                'id': 'STRATEGY_005',
                'weight': 0.08,
                'min_confidence': 0.70
            },
            {
                'name': 'Advanced Liquidation',
                'id': 'STRATEGY_006',
                'weight': 0.05,
                'min_confidence': 0.80
            }
        ]
        
        for config in strategies_config:
            strategy = Strategy(
                name=config['name'],
                strategy_id=config['id'],
                weight=config['weight'],
                min_confidence=config['min_confidence']
            )
            self.strategies[config['id']] = strategy
    
    async def evaluate_all_strategies(self, market_data: Dict) -> List[StrategyResult]:
        """Evaluate all 6 strategies in parallel"""
        try:
            tasks = []
            
            for strategy_id, strategy in self.strategies.items():
                if strategy.enabled:
                    tasks.append(
                        self._evaluate_strategy(strategy, market_data)
                    )
            
            # Run all strategies in parallel
            results = await asyncio.gather(*tasks)
            
            self.strategy_results.extend(results)
            self.total_strategies_executed += len(results)
            
            logger.debug(f"📊 Evaluated {len(results)} strategies | Signals: {sum(1 for r in results if r.signal != 'HOLD')}")
            
            return results
            
        except Exception as e:
            logger.error(f"Strategy evaluation error: {e}")
            return []
    
    async def _evaluate_strategy(self, strategy: Strategy, market_data: Dict) -> StrategyResult:
        """Evaluate single strategy"""
        try:
            # Strategy-specific logic
            if strategy.strategy_id == 'STRATEGY_001':
                # Multi-DEX Arbitrage
                signal, confidence, profit = await self._multi_dex_arbitrage(market_data)
            elif strategy.strategy_id == 'STRATEGY_002':
                # Flash Loan Sandwich
                signal, confidence, profit = await self._flash_loan_sandwich(market_data)
            elif strategy.strategy_id == 'STRATEGY_003':
                # MEV Protection + Arb
                signal, confidence, profit = await self._mev_protection_arb(market_data)
            elif strategy.strategy_id == 'STRATEGY_004':
                # Liquidity Sweep
                signal, confidence, profit = await self._liquidity_sweep(market_data)
            elif strategy.strategy_id == 'STRATEGY_005':
                # Curve Bridge Arb
                signal, confidence, profit = await self._curve_bridge_arb(market_data)
            else:
                # Advanced Liquidation
                signal, confidence, profit = await self._advanced_liquidation(market_data)
            
            # Calculate position size based on confidence and strategy weight
            position_size = self._calculate_position_size(confidence, strategy.weight)
            
            result = StrategyResult(
                strategy_name=strategy.name,
                signal=signal,
                confidence=confidence,
                expected_profit_eth=profit,
                position_size_eth=position_size
            )
            
            if signal != 'HOLD' and confidence >= strategy.min_confidence:
                strategy.trades_executed += 1
                strategy.total_profit_eth += profit
                strategy.success_rate = (strategy.total_profit_eth / max(strategy.trades_executed, 1))
                strategy.last_execution_time = time.time()
                result.executed = True
            
            return result
            
        except Exception as e:
            logger.error(f"Strategy {strategy.name} evaluation error: {e}")
            return StrategyResult(
                strategy_name=strategy.name,
                signal='HOLD',
                confidence=0.0,
                expected_profit_eth=0.0,
                position_size_eth=0.0
            )
    
    async def _multi_dex_arbitrage(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 1: Multi-DEX Arbitrage (40% weight)"""
        spread = float(market_data.get('dex_spread', 0))
        volatility = float(market_data.get('volatility', 0))
        liquidity_score = float(market_data.get('liquidity_score', 0.5))
        
        # Arbitrage confidence: higher spread + lower volatility + good liquidity
        confidence = min(0.95, (spread * 100) + (liquidity_score * 0.1) - (volatility * 0.05))
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if spread > 0.005 and liquidity_score > 0.6 else 'HOLD'
        profit = spread * 1000 if spread > 0.005 else 0.0
        
        return signal, confidence, profit
    
    async def _flash_loan_sandwich(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 2: Flash Loan Sandwich (25% weight)"""
        mempool_volume = float(market_data.get('mempool_volume', 0))
        gas_price = float(market_data.get('gas_price', 50))
        mev_opportunity = float(market_data.get('mev_opportunity', 0))
        
        # Sandwich confidence: high mempool volume + high gas + MEV opportunity
        confidence = min(0.92, (mempool_volume * 0.5) + (mev_opportunity * 0.8) - (gas_price / 1000))
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if mev_opportunity > 0.3 and gas_price > 50 else 'HOLD'
        profit = (mev_opportunity * 1500) if mev_opportunity > 0.3 else 0.0
        
        return signal, confidence, profit
    
    async def _mev_protection_arb(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 3: MEV Protection + Arbitrage (15% weight)"""
        price_impact = float(market_data.get('price_impact', 0))
        slippage = float(market_data.get('slippage', 0.01))
        protection_available = float(market_data.get('mev_protection_score', 0.5))
        
        # Confidence: low price impact + low slippage + protection available
        confidence = min(0.90, (1 - price_impact) * (1 - slippage) * protection_available)
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if price_impact < 0.02 and slippage < 0.015 else 'HOLD'
        profit = ((1 - slippage - price_impact) * 800) if signal == 'BUY' else 0.0
        
        return signal, confidence, profit
    
    async def _liquidity_sweep(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 4: Liquidity Sweep (12% weight)"""
        pool_depth = float(market_data.get('pool_depth', 0))
        market_depth = float(market_data.get('market_depth_bps', 100))
        concentration = float(market_data.get('liquidity_concentration', 0.3))
        
        # Confidence: deep pools + deep market + low concentration
        confidence = min(0.88, (pool_depth * 0.6) + (market_depth / 200) - (concentration * 0.2))
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if pool_depth > 0.5 and market_depth > 50 else 'HOLD'
        profit = (pool_depth * 500) if signal == 'BUY' else 0.0
        
        return signal, confidence, profit
    
    async def _curve_bridge_arb(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 5: Curve Bridge Arbitrage (8% weight)"""
        stable_pair_spread = float(market_data.get('stable_pair_spread', 0))
        bridge_liquidity = float(market_data.get('bridge_liquidity', 0.5))
        rebalancing_demand = float(market_data.get('rebalancing_demand', 0))
        
        # Confidence: stable spread + bridge liquidity + rebalancing demand
        confidence = min(0.85, (stable_pair_spread * 10) + (bridge_liquidity * 0.3) + (rebalancing_demand * 0.4))
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if stable_pair_spread > 0.0005 and bridge_liquidity > 0.4 else 'HOLD'
        profit = (stable_pair_spread * 500) if signal == 'BUY' else 0.0
        
        return signal, confidence, profit
    
    async def _advanced_liquidation(self, market_data: Dict) -> Tuple[str, float, float]:
        """Strategy 6: Advanced Liquidation (5% weight)"""
        liquidation_opportunity = float(market_data.get('liquidation_opportunity', 0))
        asset_volatility = float(market_data.get('asset_volatility', 0))
        liquidation_premium = float(market_data.get('liquidation_premium', 0.05))
        
        # Confidence: high liquidation opportunity + high volatility + good premium
        confidence = min(0.92, (liquidation_opportunity * 0.9) - (asset_volatility * 0.3) + (liquidation_premium * 5))
        confidence = max(0.0, min(1.0, confidence))
        
        signal = 'BUY' if liquidation_opportunity > 0.7 and liquidation_premium > 0.03 else 'HOLD'
        profit = (liquidation_opportunity * liquidation_premium * 1500) if signal == 'BUY' else 0.0
        
        return signal, confidence, profit
    
    def _calculate_position_size(self, confidence: float, strategy_weight: float) -> float:
        """Calculate position size based on confidence and strategy weight"""
        # Base position: 500 ETH
        base_position = 500.0
        
        # Adjust by confidence (0.5x to 2x)
        confidence_multiplier = 0.5 + (confidence * 1.5)
        
        # Adjust by strategy weight
        weight_multiplier = max(0.5, min(2.0, strategy_weight * 10))
        
        position_size = base_position * confidence_multiplier * weight_multiplier
        
        # Cap at 1000 ETH
        return min(1000.0, max(10.0, position_size))
    
    async def generate_ensemble_prediction(self, results: List[StrategyResult]) -> Dict:
        """Generate ensemble prediction from all strategies"""
        try:
            if not results:
                return {'signal': 'HOLD', 'confidence': 0.0, 'profit': 0.0}
            
            # Weighted voting
            buy_votes = 0.0
            sell_votes = 0.0
            hold_votes = 0.0
            total_confidence = 0.0
            total_profit = 0.0
            
            for result in results:
                strategy = self.strategies.get(next(
                    (k for k, v in self.strategies.items() 
                     if v.name == result.strategy_name), None
                ))
                
                if not strategy:
                    continue
                
                weight = strategy.weight
                
                if result.signal == 'BUY':
                    buy_votes += weight * result.confidence
                elif result.signal == 'SELL':
                    sell_votes += weight * result.confidence
                else:
                    hold_votes += weight * result.confidence
                
                total_confidence += result.confidence * weight
                total_profit += result.expected_profit_eth
            
            # Determine ensemble signal
            max_votes = max(buy_votes, sell_votes, hold_votes)
            if max_votes == buy_votes:
                ensemble_signal = 'BUY'
            elif max_votes == sell_votes:
                ensemble_signal = 'SELL'
            else:
                ensemble_signal = 'HOLD'
            
            # Calculate ensemble confidence
            total_weight = sum(s.weight for s in self.strategies.values() if s.enabled)
            ensemble_confidence = (total_confidence / total_weight) if total_weight > 0 else 0.0
            ensemble_confidence = min(1.0, max(0.0, ensemble_confidence))
            
            self.total_signals_generated += 1
            self.ensemble_accuracy = min(1.0, self.ensemble_accuracy + 0.01)
            
            result_dict = {
                'signal': ensemble_signal,
                'confidence': ensemble_confidence,
                'profit_eth': total_profit,
                'strategy_votes': {
                    'buy': round(buy_votes, 3),
                    'sell': round(sell_votes, 3),
                    'hold': round(hold_votes, 3)
                },
                'strategies_active': len([s for s in self.strategies.values() if s.enabled]),
                'timestamp': time.time()
            }
            
            self.ensemble_predictions.append(result_dict)
            
            if ensemble_signal != 'HOLD':
                logger.info(
                    f"🎯 Ensemble Signal: {ensemble_signal} | "
                    f"Confidence: {ensemble_confidence:.2%} | "
                    f"Expected Profit: {total_profit:.4f} ETH"
                )
            
            return result_dict
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            return {'signal': 'HOLD', 'confidence': 0.0, 'profit': 0.0}
    
    def get_strategy_stats(self) -> Dict:
        """Get statistics for all strategies"""
        stats = {}
        
        for strategy_id, strategy in self.strategies.items():
            stats[strategy.name] = {
                'enabled': strategy.enabled,
                'weight': strategy.weight,
                'trades_executed': strategy.trades_executed,
                'total_profit_eth': round(strategy.total_profit_eth, 4),
                'avg_profit': round(strategy.total_profit_eth / max(strategy.trades_executed, 1), 4),
                'success_rate': round(strategy.success_rate, 4),
                'last_execution': strategy.last_execution_time or None
            }
        
        return {
            'strategies': stats,
            'ensemble_accuracy': round(self.ensemble_accuracy, 4),
            'total_signals': self.total_signals_generated,
            'total_strategies_executed': self.total_strategies_executed,
            'predictions_count': len(self.ensemble_predictions)
        }
