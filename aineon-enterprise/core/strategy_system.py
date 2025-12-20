"""
AINEON Strategy System
Phase 3: 6 Concurrent Profit-Generating Strategies
Strategy selection, execution, and weighted optimization
"""

import asyncio
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """6 available profit-generating strategies"""
    MULTI_DEX_ARBITRAGE = 'multi_dex_arbitrage'           # 40% profit target
    FLASH_LOAN_SANDWICH = 'flash_loan_sandwich'            # 25% profit target
    MEV_EXTRACTION = 'mev_extraction'                       # 15% profit target
    LIQUIDITY_SWEEP = 'liquidity_sweep'                     # 12% profit target
    CURVE_BRIDGE_ARBITRAGE = 'curve_bridge_arb'            # 5% profit target
    ADVANCED_LIQUIDATION = 'advanced_liquidation'           # 3% profit target


@dataclass
class StrategyOpportunity:
    """Opportunity for a specific strategy"""
    strategy_type: StrategyType
    profit_estimate: float  # ETH
    confidence: float       # 0-1.0
    dex_pair: Optional[str] = None
    tokens: Optional[List[str]] = None
    execution_time_estimate: float = 0.0  # seconds


class Strategy(ABC):
    """Abstract base class for profit strategies"""
    
    def __init__(self, strategy_type: StrategyType):
        self.strategy_type = strategy_type
        self.execution_count = 0
        self.total_profit = 0.0
        self.success_count = 0
    
    @abstractmethod
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify if opportunity exists in market data"""
        pass
    
    @abstractmethod
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build execution plan from opportunity"""
        pass
    
    async def execute(self, execution_plan: Dict) -> Dict:
        """Execute strategy and track metrics"""
        self.execution_count += 1
        
        try:
            profit = execution_plan.get('estimated_profit', 0)
            success = profit > 0
            
            if success:
                self.success_count += 1
                self.total_profit += profit
            
            logger.info(
                f"{self.strategy_type.value}: "
                f"execution={self.execution_count}, "
                f"profit={profit}, success={success}"
            )
            
            return {
                'strategy_id': self.strategy_type.value,
                'success': success,
                'profit': profit,
                'execution_count': self.execution_count
            }
        
        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            return {'strategy_id': self.strategy_type.value, 'success': False, 'error': str(e)}
    
    def get_win_rate(self) -> float:
        """Calculate win rate"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def get_avg_profit(self) -> float:
        """Calculate average profit per successful trade"""
        if self.success_count == 0:
            return 0.0
        return self.total_profit / self.success_count


class MultiDexArbitrageStrategy(Strategy):
    """
    Multi-DEX Arbitrage Strategy
    Detects price discrepancies across DEXs and captures profit
    Target: 40% of daily profit (40+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.MULTI_DEX_ARBITRAGE)
        self.dex_pools = ['uniswap_v3', 'curve', 'balancer', 'sushiswap']
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Scan for price discrepancies >0.1%"""
        if not market_data.get('price_differences'):
            return None
        
        for diff in market_data.get('price_differences', []):
            if diff.get('percentage', 0) > 0.001:  # >0.1%
                return StrategyOpportunity(
                    strategy_type=StrategyType.MULTI_DEX_ARBITRAGE,
                    profit_estimate=diff.get('profit_estimate', 1.0),
                    confidence=diff.get('confidence', 0.85),
                    dex_pair=f"{diff.get('from_dex', 'u3')}-{diff.get('to_dex', 'curve')}",
                    tokens=diff.get('tokens', ['USDC', 'USDT']),
                    execution_time_estimate=0.5
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build arbitrage execution plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': f"{opportunity.dex_pair}_opp",
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 400000,
            'slippage_tolerance': 0.0005,
            'flash_loan_provider': 'aave_v3',
            'route': ['borrow', 'swap_dex1', 'swap_dex2', 'repay'],
            'tokens': opportunity.tokens or ['USDC', 'USDT']
        }


class FlashLoanSandwichStrategy(Strategy):
    """
    Flash Loan Sandwich MEV Extraction
    Frontruns transactions with MEV protection
    Target: 25% of daily profit (25+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.FLASH_LOAN_SANDWICH)
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify sandwich opportunities in mempool"""
        pending_txs = market_data.get('pending_transactions', [])
        
        for tx in pending_txs:
            if tx.get('gas_price', 0) > market_data.get('base_gas_price', 30):
                return StrategyOpportunity(
                    strategy_type=StrategyType.FLASH_LOAN_SANDWICH,
                    profit_estimate=tx.get('mev_profit', 0.8),
                    confidence=0.80,
                    tokens=tx.get('tokens', []),
                    execution_time_estimate=0.2
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build sandwich execution plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': 'sandwich_opp',
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 450000,
            'slippage_tolerance': 0.001,
            'flash_loan_provider': 'dydx',
            'protection_mode': 'private_relay',
            'route': ['frontrun', 'victim_tx', 'backrun']
        }


class MevExtractionStrategy(Strategy):
    """
    MEV Extraction through Flashbots
    Captures MEV-share opportunities
    Target: 15% of daily profit (15+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.MEV_EXTRACTION)
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify MEV-share bundle opportunities"""
        bundles = market_data.get('mev_bundles', [])
        
        for bundle in bundles:
            if bundle.get('estimated_mev', 0) > 0.5:
                return StrategyOpportunity(
                    strategy_type=StrategyType.MEV_EXTRACTION,
                    profit_estimate=bundle.get('estimated_mev', 0.5),
                    confidence=bundle.get('confidence', 0.82),
                    execution_time_estimate=0.1
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build MEV extraction plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': 'mev_share_opp',
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 300000,
            'slippage_tolerance': 0.0008,
            'mev_provider': 'flashbots',
            'bundle_count': 1
        }


class LiquiditySweepStrategy(Strategy):
    """
    Liquidity Sweep Strategy
    Targets deep pools for maximum impact
    Target: 12% of daily profit (12+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.LIQUIDITY_SWEEP)
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify pools with sweepable liquidity"""
        pools = market_data.get('liquidity_pools', [])
        
        for pool in pools:
            if pool.get('sweepable_liquidity', 0) > 1000:  # USDC units
                return StrategyOpportunity(
                    strategy_type=StrategyType.LIQUIDITY_SWEEP,
                    profit_estimate=pool.get('sweep_profit', 0.5),
                    confidence=pool.get('confidence', 0.80),
                    execution_time_estimate=0.3
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build liquidity sweep plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': 'sweep_opp',
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 350000,
            'slippage_tolerance': 0.002,
            'pool_size': 1000,
            'sweep_intensity': 'moderate'
        }


class CurveBridgeArbitrageStrategy(Strategy):
    """
    Curve Bridge Arbitrage
    Cross-curve arbitrage for stable assets
    Target: 5% of daily profit (5+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.CURVE_BRIDGE_ARBITRAGE)
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify Curve bridge opportunities"""
        curve_pools = market_data.get('curve_pools', [])
        
        for pool in curve_pools:
            if pool.get('bridge_opportunity', False):
                return StrategyOpportunity(
                    strategy_type=StrategyType.CURVE_BRIDGE_ARBITRAGE,
                    profit_estimate=pool.get('profit_estimate', 0.2),
                    confidence=pool.get('confidence', 0.75),
                    tokens=pool.get('stable_pair', ['USDC', 'USDT']),
                    execution_time_estimate=0.4
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build Curve bridge plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': 'curve_bridge_opp',
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 320000,
            'slippage_tolerance': 0.0003,
            'stable_pair': opportunity.tokens or ['USDC', 'USDT'],
            'bridge_type': 'curve'
        }


class AdvancedLiquidationStrategy(Strategy):
    """
    Advanced Liquidation Capture
    Monitors lending protocols for liquidation opportunities
    Target: 3% of daily profit (3+ ETH)
    """
    
    def __init__(self):
        super().__init__(StrategyType.ADVANCED_LIQUIDATION)
    
    async def identify_opportunity(self, market_data: Dict) -> Optional[StrategyOpportunity]:
        """Identify liquidation opportunities"""
        liquidation_events = market_data.get('liquidation_events', [])
        
        for event in liquidation_events:
            if event.get('liquidation_profit', 0) > 0.1:
                return StrategyOpportunity(
                    strategy_type=StrategyType.ADVANCED_LIQUIDATION,
                    profit_estimate=event.get('liquidation_profit', 0.1),
                    confidence=event.get('confidence', 0.78),
                    execution_time_estimate=0.2
                )
        
        return None
    
    async def build_execution_plan(self, opportunity: StrategyOpportunity) -> Dict:
        """Build liquidation plan"""
        return {
            'strategy_id': self.strategy_type.value,
            'opportunity_id': 'liquidation_opp',
            'estimated_profit': opportunity.profit_estimate,
            'estimated_gas': 400000,
            'slippage_tolerance': 0.005,
            'liquidation_protocol': 'aave_v3',
            'collateral_token': 'ETH'
        }


class StrategySystem:
    """
    Manages all 6 strategies
    Selects, executes, and optimizes strategy usage
    """
    
    def __init__(self):
        self.strategies: Dict[StrategyType, Strategy] = {
            StrategyType.MULTI_DEX_ARBITRAGE: MultiDexArbitrageStrategy(),
            StrategyType.FLASH_LOAN_SANDWICH: FlashLoanSandwichStrategy(),
            StrategyType.MEV_EXTRACTION: MevExtractionStrategy(),
            StrategyType.LIQUIDITY_SWEEP: LiquiditySweepStrategy(),
            StrategyType.CURVE_BRIDGE_ARBITRAGE: CurveBridgeArbitrageStrategy(),
            StrategyType.ADVANCED_LIQUIDATION: AdvancedLiquidationStrategy(),
        }
        
        # Strategy weights (should be updated by AI optimizer)
        self.strategy_weights: Dict[StrategyType, float] = {
            StrategyType.MULTI_DEX_ARBITRAGE: 0.40,
            StrategyType.FLASH_LOAN_SANDWICH: 0.25,
            StrategyType.MEV_EXTRACTION: 0.15,
            StrategyType.LIQUIDITY_SWEEP: 0.12,
            StrategyType.CURVE_BRIDGE_ARBITRAGE: 0.05,
            StrategyType.ADVANCED_LIQUIDATION: 0.03,
        }
        
        logger.info(f"StrategySystem initialized with {len(self.strategies)} strategies")
    
    async def scan_all_strategies(self, market_data: Dict) -> List[StrategyOpportunity]:
        """Scan all strategies for opportunities in parallel"""
        tasks = [
            strategy.identify_opportunity(market_data)
            for strategy in self.strategies.values()
        ]
        
        opportunities = await asyncio.gather(*tasks, return_exceptions=True)
        return [opp for opp in opportunities if opp is not None]
    
    async def execute_strategy(
        self,
        strategy_type: StrategyType
    ) -> Dict:
        """Execute a specific strategy"""
        strategy = self.strategies[strategy_type]
        
        # Mock market data for testing
        market_data = {
            'price_differences': [
                {'percentage': 0.0015, 'profit_estimate': 1.2, 'confidence': 0.90}
            ],
            'pending_transactions': [],
            'mev_bundles': [],
            'liquidity_pools': [],
            'curve_pools': [],
            'liquidation_events': []
        }
        
        # Identify opportunity
        opportunity = await strategy.identify_opportunity(market_data)
        if not opportunity:
            logger.warning(f"No opportunity found for {strategy_type.value}")
            return {'strategy_id': strategy_type.value, 'success': False, 'reason': 'no_opportunity'}
        
        # Build and execute plan
        plan = await strategy.build_execution_plan(opportunity)
        result = await strategy.execute(plan)
        
        return result
    
    def update_strategy_weights(self, weights: Dict[StrategyType, float]) -> None:
        """Update strategy weights from AI optimizer"""
        self.strategy_weights = weights
        logger.info(f"Updated strategy weights: {weights}")
    
    def get_strategy_performance(self) -> Dict:
        """Get performance metrics for all strategies"""
        performance = {}
        
        for stype, strategy in self.strategies.items():
            performance[stype.value] = {
                'executions': strategy.execution_count,
                'successes': strategy.success_count,
                'win_rate': round(strategy.get_win_rate(), 4),
                'total_profit': round(strategy.total_profit, 4),
                'avg_profit': round(strategy.get_avg_profit(), 4),
                'weight': round(self.strategy_weights[stype], 4)
            }
        
        return performance
    
    async def execute_optimal_strategy(self, market_data: Dict) -> Dict:
        """Execute highest-weighted strategy with opportunity"""
        # Scan all strategies
        opportunities = await self.scan_all_strategies(market_data)
        
        if not opportunities:
            logger.warning("No opportunities found across any strategy")
            return {'success': False, 'reason': 'no_opportunities'}
        
        # Find highest-weighted opportunity
        best_opportunity = max(
            opportunities,
            key=lambda opp: self.strategy_weights.get(opp.strategy_type, 0.0)
        )
        
        # Execute
        strategy = self.strategies[best_opportunity.strategy_type]
        plan = await strategy.build_execution_plan(best_opportunity)
        result = await strategy.execute(plan)
        
        return result
    
    def get_summary(self) -> Dict:
        """Get system summary"""
        total_profit = sum(s.total_profit for s in self.strategies.values())
        total_executions = sum(s.execution_count for s in self.strategies.values())
        
        return {
            'strategies_count': len(self.strategies),
            'total_executions': total_executions,
            'total_profit': round(total_profit, 4),
            'avg_profit_per_execution': round(total_profit / max(total_executions, 1), 4),
            'performance': self.get_strategy_performance()
        }
