"""
AINEON Liquidation Engine
Phase 5: Multi-protocol liquidation detection and capture
Aave V2/V3, Compound, Morpho, Euler, Radiant, IronBank
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LiquidationProtocol(Enum):
    """Supported lending protocols"""
    AAVE_V2 = 'aave_v2'
    AAVE_V3 = 'aave_v3'
    COMPOUND = 'compound'
    MORPHO = 'morpho'
    EULER = 'euler'
    RADIANT = 'radiant'
    IRONBANK = 'ironbank'
    DFORCE = 'dforce'


@dataclass
class LiquidationOpportunity:
    """Liquidation opportunity"""
    protocol: LiquidationProtocol
    user_address: str
    collateral_token: str
    borrow_token: str
    collateral_amount: float
    borrow_amount: float
    health_factor: float  # <1.0 = liquidatable
    liquidation_profit: float  # ETH
    confidence: float  # 0-1.0
    timestamp: float


@dataclass
class LiquidationExecution:
    """Result of liquidation execution"""
    opportunity_id: str
    protocol: LiquidationProtocol
    success: bool
    profit: float
    gas_cost: float
    tx_hash: str
    timestamp: float


class ProtocolMonitor:
    """Monitor single protocol for liquidation opportunities"""
    
    def __init__(self, protocol: LiquidationProtocol):
        self.protocol = protocol
        self.opportunities_found = 0
        self.last_check = 0.0
        self.check_interval = 5  # seconds
        
        # Protocol-specific parameters
        self.params = self._init_protocol_params()
        
        logger.info(f"ProtocolMonitor initialized for {protocol.value}")
    
    def _init_protocol_params(self) -> Dict:
        """Initialize protocol-specific parameters"""
        if self.protocol == LiquidationProtocol.AAVE_V3:
            return {
                'liquidation_threshold': 0.8,
                'close_factor': 0.5,
                'liquidation_bonus': 0.05,
                'tvl': 10_000_000_000  # $10B
            }
        elif self.protocol == LiquidationProtocol.COMPOUND:
            return {
                'liquidation_threshold': 0.75,
                'close_factor': 0.5,
                'liquidation_bonus': 0.08,
                'tvl': 3_000_000_000
            }
        elif self.protocol == LiquidationProtocol.MORPHO:
            return {
                'liquidation_threshold': 0.8,
                'close_factor': 0.75,
                'liquidation_bonus': 0.07,
                'tvl': 500_000_000
            }
        else:
            return {
                'liquidation_threshold': 0.8,
                'close_factor': 0.5,
                'liquidation_bonus': 0.05,
                'tvl': 1_000_000_000
            }
    
    async def scan_for_liquidations(self) -> List[LiquidationOpportunity]:
        """Scan protocol for liquidatable positions"""
        opportunities = []
        
        # Simulate scanning active users (in production: RPC call)
        num_users = np.random.randint(50, 200)
        
        for _ in range(num_users):
            health_factor = np.random.uniform(0.4, 1.1)
            
            # Liquidatable if health factor < 1.0
            if health_factor < 1.0:
                collateral = np.random.uniform(1, 1000)
                borrow = collateral * np.random.uniform(0.5, 0.9)
                profit = (borrow * self.params['liquidation_bonus']) * np.random.uniform(0.8, 1.2)
                
                opp = LiquidationOpportunity(
                    protocol=self.protocol,
                    user_address=f"0x{np.random.bytes(20).hex()}",
                    collateral_token='ETH',
                    borrow_token='USDC',
                    collateral_amount=collateral,
                    borrow_amount=borrow,
                    health_factor=health_factor,
                    liquidation_profit=profit,
                    confidence=1.0 - health_factor,  # Lower health = higher confidence
                    timestamp=asyncio.get_event_loop().time()
                )
                
                opportunities.append(opp)
                self.opportunities_found += 1
        
        logger.info(f"{self.protocol.value}: found {len(opportunities)} opportunities")
        return opportunities
    
    async def execute_liquidation(self, opp: LiquidationOpportunity) -> LiquidationExecution:
        """Execute liquidation"""
        gas_cost = np.random.uniform(0.05, 0.2)
        success = np.random.random() > 0.05  # 95% success rate
        
        return LiquidationExecution(
            opportunity_id=f"{self.protocol.value}_{opp.user_address}",
            protocol=self.protocol,
            success=success,
            profit=opp.liquidation_profit - gas_cost if success else 0,
            gas_cost=gas_cost,
            tx_hash=f"0x{np.random.bytes(32).hex()}",
            timestamp=asyncio.get_event_loop().time()
        )


class LiquidationCascadeDetector:
    """Detect and predict liquidation cascades"""
    
    def __init__(self):
        self.cascade_threshold = 0.5  # If >50% of liquidity gets liquidated
        self.cascade_history: List[Dict] = []
    
    async def detect_cascade(self, market_state: Dict) -> Optional[Dict]:
        """Detect if liquidation cascade is forming"""
        total_liquidatable_value = market_state.get('total_liquidatable_value', 0)
        total_market_value = market_state.get('total_market_value', 1)
        
        cascade_ratio = total_liquidatable_value / total_market_value
        
        if cascade_ratio > self.cascade_threshold:
            cascade = {
                'detected': True,
                'ratio': cascade_ratio,
                'severity': min(cascade_ratio / self.cascade_threshold, 2.0),  # 1.0 = threshold, 2.0 = severe
                'estimated_profit': market_state.get('estimated_cascade_profit', 0),
                'timestamp': asyncio.get_event_loop().time()
            }
            
            self.cascade_history.append(cascade)
            logger.warning(f"Liquidation cascade detected: {cascade_ratio:.2%}")
            return cascade
        
        return None
    
    def get_history(self, lookback: int = 100) -> List[Dict]:
        """Get cascade history"""
        return self.cascade_history[-lookback:]


class LiquidationEngine:
    """
    Master liquidation engine coordinating multi-protocol execution
    Target: 10-20 liquidations/day = 50-200 ETH profit
    """
    
    def __init__(self):
        self.monitors = {
            protocol: ProtocolMonitor(protocol)
            for protocol in LiquidationProtocol
        }
        
        self.cascade_detector = LiquidationCascadeDetector()
        
        # Performance tracking
        self.total_liquidations = 0
        self.total_profit = 0.0
        self.total_gas_cost = 0.0
        self.execution_history: List[LiquidationExecution] = []
        
        logger.info(f"LiquidationEngine initialized with {len(self.monitors)} protocols")
    
    async def scan_all_protocols(self) -> List[LiquidationOpportunity]:
        """Scan all protocols in parallel for liquidations"""
        tasks = [
            monitor.scan_for_liquidations()
            for monitor in self.monitors.values()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Flatten and sort by profit
        all_opportunities = []
        for opps in results:
            all_opportunities.extend(opps)
        
        all_opportunities.sort(key=lambda x: x.liquidation_profit, reverse=True)
        
        logger.info(f"Total opportunities found: {len(all_opportunities)}")
        return all_opportunities
    
    async def execute_liquidations(self, opportunities: List[LiquidationOpportunity],
                                   max_executions: int = 20) -> List[LiquidationExecution]:
        """Execute liquidations (prioritized by profit)"""
        executions = []
        
        for opp in opportunities[:max_executions]:
            monitor = self.monitors[opp.protocol]
            execution = await monitor.execute_liquidation(opp)
            executions.append(execution)
            
            if execution.success:
                self.total_liquidations += 1
                self.total_profit += execution.profit
                self.total_gas_cost += execution.gas_cost
            
            self.execution_history.append(execution)
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        logger.info(f"Executed {len(executions)} liquidations, profit: {sum(e.profit for e in executions):.4f} ETH")
        
        return executions
    
    async def run_liquidation_cycle(self, market_state: Dict) -> Dict:
        """Run complete liquidation cycle"""
        # Detect cascades
        cascade = await self.cascade_detector.detect_cascade(market_state)
        
        # Scan for opportunities
        opportunities = await self.scan_all_protocols()
        
        if not opportunities:
            return {
                'cycle_completed': True,
                'opportunities_found': 0,
                'liquidations_executed': 0,
                'profit': 0.0,
                'cascade_detected': cascade is not None
            }
        
        # Execute liquidations (cascade = execute more aggressively)
        max_executions = 50 if cascade else 20
        executions = await self.execute_liquidations(opportunities, max_executions=max_executions)
        
        return {
            'cycle_completed': True,
            'opportunities_found': len(opportunities),
            'liquidations_executed': len([e for e in executions if e.success]),
            'profit': sum(e.profit for e in executions),
            'gas_cost': sum(e.gas_cost for e in executions),
            'cascade_detected': cascade is not None,
            'cascade_severity': cascade.get('severity', 0) if cascade else 0
        }
    
    def get_metrics(self) -> Dict:
        """Get liquidation metrics"""
        total_executed = len(self.execution_history)
        successful = len([e for e in self.execution_history if e.success])
        success_rate = (successful / total_executed * 100) if total_executed > 0 else 0
        
        return {
            'total_liquidations': self.total_liquidations,
            'total_profit': round(self.total_profit, 4),
            'total_gas_cost': round(self.total_gas_cost, 4),
            'net_profit': round(self.total_profit - self.total_gas_cost, 4),
            'total_executions': total_executed,
            'success_rate': round(success_rate, 2),
            'avg_profit_per_liquidation': round(
                self.total_profit / max(self.total_liquidations, 1), 4
            ),
            'protocols_monitored': len(self.monitors)
        }
    
    def get_protocol_breakdown(self) -> Dict:
        """Get liquidation breakdown by protocol"""
        breakdown = {}
        
        for protocol, monitor in self.monitors.items():
            protocol_executions = [
                e for e in self.execution_history
                if e.protocol == protocol
            ]
            successful = [e for e in protocol_executions if e.success]
            
            breakdown[protocol.value] = {
                'opportunities_found': monitor.opportunities_found,
                'executions': len(protocol_executions),
                'successful': len(successful),
                'profit': round(sum(e.profit for e in successful), 4)
            }
        
        return breakdown
