"""
PHASE 2 FILE 2: Multi-Chain Orchestrator Integration
Coordinates signal routing, execution timing, and profit consolidation across chains
Integrates Layer 2 Scanner, Bridge Monitor, and Atomic Executor
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from decimal import Decimal

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """Types of arbitrage opportunities"""
    SINGLE_CHAIN_DEX = "single_chain_dex"
    SINGLE_CHAIN_FLASH = "single_chain_flash"
    BRIDGE_ARBITRAGE = "bridge_arbitrage"
    CROSS_CHAIN_DEX = "cross_chain_dex"


class ExecutionPriority(Enum):
    """Execution priority levels"""
    CRITICAL = 1      # >1% expected profit
    HIGH = 2          # 0.5-1% profit
    MEDIUM = 3        # 0.1-0.5% profit
    LOW = 4           # <0.1% profit


@dataclass
class SignalOpportunity:
    """Represents a detected arbitrage opportunity"""
    opportunity_id: str
    type: OpportunityType
    source_chain: str
    dest_chain: Optional[str] = None
    
    # Opportunity details
    token_pair: str = ""
    expected_profit_eth: float = 0.0
    profit_pct: float = 0.0
    confidence_score: float = 0.0
    
    # Execution parameters
    position_size_eth: float = 0.0
    flash_loan_amount_eth: float = 0.0
    swap_route: List[Dict] = field(default_factory=list)
    bridge_type: Optional[str] = None
    
    # Metadata
    detected_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    priority: ExecutionPriority = ExecutionPriority.MEDIUM
    status: str = "pending"


@dataclass
class ExecutionPlan:
    """Execution plan for an opportunity"""
    plan_id: str
    opportunity_id: str
    chain: str
    steps: List[Dict] = field(default_factory=list)
    estimated_gas_eth: float = 0.0
    estimated_profit_eth: float = 0.0
    estimated_latency_ms: float = 0.0
    created_at: float = field(default_factory=time.time)
    status: str = "ready"


@dataclass
class ExecutionResult:
    """Result of opportunity execution"""
    execution_id: str
    opportunity_id: str
    success: bool
    chain: str
    actual_profit_eth: float = 0.0
    gas_cost_eth: float = 0.0
    tx_hashes: List[str] = field(default_factory=list)
    executed_at: Optional[float] = None
    error_message: Optional[str] = None


class MultiChainOrchestrator:
    """
    Orchestrates multi-chain arbitrage execution.
    Routes signals to appropriate chains, manages execution timing, and consolidates profits.
    """

    def __init__(
        self,
        layer2_scanner,
        bridge_monitor,
        atomic_executor,
        ai_optimizer=None,
    ):
        """
        Initialize orchestrator with components.
        
        Args:
            layer2_scanner: Layer2Scanner instance for L2 opportunity detection
            bridge_monitor: BridgeMonitor instance for cross-chain bridge monitoring
            atomic_executor: Layer2AtomicExecutor instance for execution
            ai_optimizer: Optional AI optimizer for signal ranking
        """
        self.layer2_scanner = layer2_scanner
        self.bridge_monitor = bridge_monitor
        self.atomic_executor = atomic_executor
        self.ai_optimizer = ai_optimizer
        
        # Opportunity management
        self.pending_opportunities: Dict[str, SignalOpportunity] = {}
        self.execution_queue: List[SignalOpportunity] = []
        self.completed_executions: List[ExecutionResult] = []
        
        # Execution plans
        self.active_plans: Dict[str, ExecutionPlan] = {}
        
        # Chain-specific routing
        self.chain_routing_table = {
            "ethereum": {
                "max_concurrent": 3,
                "priority_factor": 1.5,
                "latency_budget_ms": 50,
            },
            "polygon": {
                "max_concurrent": 5,
                "priority_factor": 1.2,
                "latency_budget_ms": 100,
            },
            "optimism": {
                "max_concurrent": 5,
                "priority_factor": 1.0,
                "latency_budget_ms": 100,
            },
            "arbitrum": {
                "max_concurrent": 5,
                "priority_factor": 1.0,
                "latency_budget_ms": 150,
            },
        }
        
        # Performance metrics
        self.metrics = {
            "total_opportunities_detected": 0,
            "total_opportunities_executed": 0,
            "total_profit_eth": 0.0,
            "execution_success_rate": 0.0,
            "average_latency_ms": 0.0,
            "by_chain": {
                "ethereum": {"executed": 0, "profit": 0.0},
                "polygon": {"executed": 0, "profit": 0.0},
                "optimism": {"executed": 0, "profit": 0.0},
                "arbitrum": {"executed": 0, "profit": 0.0},
            },
        }
        
        self.opportunity_counter = 0
        self.execution_counter = 0
        self.running = False

    async def start_orchestration_loop(self, scan_interval: float = 1.0):
        """
        Start continuous orchestration loop.
        Detects opportunities, prioritizes, and executes.
        
        Args:
            scan_interval: Time between scans in seconds
        """
        self.running = True
        logger.info("🚀 Multi-chain orchestrator started")
        
        try:
            while self.running:
                # Phase 1: Detect opportunities
                await self._scan_for_opportunities()
                
                # Phase 2: Prioritize opportunities
                await self._prioritize_opportunities()
                
                # Phase 3: Execute high-priority opportunities
                await self._execute_opportunities()
                
                # Phase 4: Clean up expired opportunities
                await self._cleanup_expired_opportunities()
                
                # Sleep before next cycle
                await asyncio.sleep(scan_interval)
                
        except Exception as e:
            logger.error(f"Orchestration loop error: {str(e)}")
            self.running = False

    async def _scan_for_opportunities(self):
        """Scan all chains for arbitrage opportunities"""
        try:
            # Scan Layer 2 chains
            l2_opportunities = await self.layer2_scanner.scan_all_chains()
            
            # Scan bridges
            bridge_opportunities = await self.bridge_monitor.detect_all_bridge_opportunities()
            
            # Convert to SignalOpportunity objects
            for opp in l2_opportunities:
                signal_opp = self._convert_l2_opportunity(opp)
                if signal_opp:
                    self.pending_opportunities[signal_opp.opportunity_id] = signal_opp
                    self.metrics["total_opportunities_detected"] += 1
            
            for opp in bridge_opportunities:
                signal_opp = self._convert_bridge_opportunity(opp)
                if signal_opp:
                    self.pending_opportunities[signal_opp.opportunity_id] = signal_opp
                    self.metrics["total_opportunities_detected"] += 1
            
            if self.pending_opportunities:
                logger.debug(
                    f"📊 Detected {len(self.pending_opportunities)} total opportunities "
                    f"({len(l2_opportunities)} L2 + {len(bridge_opportunities)} bridge)"
                )
        
        except Exception as e:
            logger.error(f"Error scanning for opportunities: {str(e)}")

    async def _prioritize_opportunities(self):
        """
        Prioritize pending opportunities by expected profit and risk.
        Use AI optimizer if available.
        """
        try:
            ranked_opps = list(self.pending_opportunities.values())
            
            # Filter out sub-threshold opportunities
            ranked_opps = [
                opp for opp in ranked_opps
                if opp.expected_profit_eth >= 0.05  # Minimum 0.05 ETH
            ]
            
            # If AI optimizer available, use it to rank
            if self.ai_optimizer:
                ranked_opps = await self._rank_with_ai(ranked_opps)
            else:
                # Default ranking: by expected profit (descending)
                ranked_opps.sort(
                    key=lambda x: (x.expected_profit_eth, x.confidence_score),
                    reverse=True
                )
            
            # Assign priority based on rank
            for idx, opp in enumerate(ranked_opps):
                if idx < 5:  # Top 5
                    opp.priority = ExecutionPriority.CRITICAL
                elif idx < 15:  # Next 10
                    opp.priority = ExecutionPriority.HIGH
                elif idx < 30:  # Next 15
                    opp.priority = ExecutionPriority.MEDIUM
                else:
                    opp.priority = ExecutionPriority.LOW
            
            # Create execution queue (by priority)
            self.execution_queue = ranked_opps
            
            logger.debug(
                f"📈 Prioritized {len(self.execution_queue)} opportunities "
                f"(critical: {sum(1 for o in ranked_opps if o.priority == ExecutionPriority.CRITICAL)})"
            )
        
        except Exception as e:
            logger.error(f"Error prioritizing opportunities: {str(e)}")

    async def _execute_opportunities(self):
        """Execute high-priority opportunities"""
        try:
            executed_count = 0
            
            # Execute in priority order (CRITICAL > HIGH > MEDIUM)
            for opportunity in self.execution_queue:
                if opportunity.priority.value > ExecutionPriority.MEDIUM.value:
                    continue  # Skip LOW priority
                
                # Check execution capacity
                chain = opportunity.source_chain
                current_count = sum(
                    1 for plan in self.active_plans.values()
                    if plan.chain == chain
                )
                max_concurrent = self.chain_routing_table[chain]["max_concurrent"]
                
                if current_count >= max_concurrent:
                    logger.debug(f"⏸️  {chain} at max concurrent ({max_concurrent})")
                    continue
                
                # Execute the opportunity
                result = await self._execute_opportunity(opportunity)
                
                if result:
                    executed_count += 1
                
                # Rate limiting: brief delay between executions
                await asyncio.sleep(0.01)
            
            if executed_count > 0:
                logger.info(f"⚡ Executed {executed_count} opportunities")
        
        except Exception as e:
            logger.error(f"Error executing opportunities: {str(e)}")

    async def _execute_opportunity(self, opportunity: SignalOpportunity) -> Optional[ExecutionResult]:
        """Execute single opportunity"""
        try:
            execution_id = self._generate_execution_id()
            
            # Route to appropriate executor based on opportunity type
            if opportunity.type == OpportunityType.SINGLE_CHAIN_DEX:
                result = await self._execute_single_chain_dex(opportunity)
            
            elif opportunity.type == OpportunityType.SINGLE_CHAIN_FLASH:
                result = await self._execute_single_chain_flash(opportunity)
            
            elif opportunity.type == OpportunityType.BRIDGE_ARBITRAGE:
                result = await self._execute_bridge_arbitrage(opportunity)
            
            elif opportunity.type == OpportunityType.CROSS_CHAIN_DEX:
                result = await self._execute_cross_chain(opportunity)
            
            else:
                logger.warning(f"Unknown opportunity type: {opportunity.type}")
                return None
            
            # Record result
            if result and result.get("success"):
                exec_result = ExecutionResult(
                    execution_id=execution_id,
                    opportunity_id=opportunity.opportunity_id,
                    success=True,
                    chain=opportunity.source_chain,
                    actual_profit_eth=result.get("profit_eth", 0.0),
                    gas_cost_eth=result.get("gas_eth", 0.0),
                    tx_hashes=result.get("tx_hashes", []),
                    executed_at=time.time(),
                )
                
                self.completed_executions.append(exec_result)
                self.metrics["total_opportunities_executed"] += 1
                self.metrics["total_profit_eth"] += exec_result.actual_profit_eth
                self.metrics["by_chain"][opportunity.source_chain]["executed"] += 1
                self.metrics["by_chain"][opportunity.source_chain]["profit"] += exec_result.actual_profit_eth
                
                logger.info(
                    f"✅ {execution_id}: {opportunity.source_chain} "
                    f"+{exec_result.actual_profit_eth:.4f} ETH"
                )
                
                return exec_result
            else:
                logger.warning(f"❌ {execution_id}: Execution failed")
                return None
        
        except Exception as e:
            logger.error(f"Error executing opportunity: {str(e)}")
            return None

    async def _execute_single_chain_dex(self, opportunity: SignalOpportunity) -> Optional[Dict]:
        """Execute single-chain DEX arbitrage"""
        try:
            result = await self.atomic_executor.execute_single_chain_arbitrage(
                chain_name=opportunity.source_chain,
                token_pair=opportunity.token_pair,
                flash_loan_amount_eth=0.0,  # No flash loan for simple DEX arb
                expected_profit_eth=opportunity.expected_profit_eth,
                swap_route=opportunity.swap_route,
            )
            return result
        
        except Exception as e:
            logger.error(f"DEX execution error: {str(e)}")
            return None

    async def _execute_single_chain_flash(self, opportunity: SignalOpportunity) -> Optional[Dict]:
        """Execute single-chain flash loan arbitrage"""
        try:
            result = await self.atomic_executor.execute_single_chain_arbitrage(
                chain_name=opportunity.source_chain,
                token_pair=opportunity.token_pair,
                flash_loan_amount_eth=opportunity.flash_loan_amount_eth,
                expected_profit_eth=opportunity.expected_profit_eth,
                swap_route=opportunity.swap_route,
            )
            return result
        
        except Exception as e:
            logger.error(f"Flash loan execution error: {str(e)}")
            return None

    async def _execute_bridge_arbitrage(self, opportunity: SignalOpportunity) -> Optional[Dict]:
        """Execute cross-chain bridge arbitrage"""
        try:
            from core.layer2_atomic_executor import BridgeType
            
            result = await self.atomic_executor.execute_cross_chain_arbitrage(
                source_chain=opportunity.source_chain,
                dest_chain=opportunity.dest_chain,
                token=opportunity.token_pair.split("/")[0],
                bridge_type=BridgeType(opportunity.bridge_type),
                amount_eth=opportunity.position_size_eth,
                source_price=0.0,  # Would be in opportunity
                dest_price=0.0,    # Would be in opportunity
                spread_pct=opportunity.profit_pct,
            )
            return result
        
        except Exception as e:
            logger.error(f"Bridge arbitrage execution error: {str(e)}")
            return None

    async def _execute_cross_chain(self, opportunity: SignalOpportunity) -> Optional[Dict]:
        """Execute cross-chain DEX arbitrage"""
        try:
            result = await self.atomic_executor.execute_cross_chain_arbitrage(
                source_chain=opportunity.source_chain,
                dest_chain=opportunity.dest_chain,
                token=opportunity.token_pair.split("/")[0],
                bridge_type="curve_bridge",  # Default bridge
                amount_eth=opportunity.position_size_eth,
                source_price=0.0,
                dest_price=0.0,
                spread_pct=opportunity.profit_pct,
            )
            return result
        
        except Exception as e:
            logger.error(f"Cross-chain execution error: {str(e)}")
            return None

    async def _cleanup_expired_opportunities(self):
        """Remove expired opportunities from pending queue"""
        try:
            current_time = time.time()
            expired_ids = [
                opp_id for opp_id, opp in self.pending_opportunities.items()
                if opp.expires_at and opp.expires_at < current_time
            ]
            
            for opp_id in expired_ids:
                del self.pending_opportunities[opp_id]
            
            if expired_ids:
                logger.debug(f"🗑️  Cleaned up {len(expired_ids)} expired opportunities")
        
        except Exception as e:
            logger.error(f"Error cleaning up opportunities: {str(e)}")

    async def _rank_with_ai(self, opportunities: List[SignalOpportunity]) -> List[SignalOpportunity]:
        """Rank opportunities using AI optimizer"""
        try:
            if not self.ai_optimizer:
                return opportunities
            
            # Convert to AI-friendly format and rank
            ranked = await self.ai_optimizer.rank_opportunities(opportunities)
            return ranked
        
        except Exception as e:
            logger.error(f"AI ranking error: {str(e)}")
            return opportunities

    def _convert_l2_opportunity(self, l2_opp: Dict) -> Optional[SignalOpportunity]:
        """Convert L2 scanner opportunity to SignalOpportunity"""
        try:
            self.opportunity_counter += 1
            
            opportunity_type = (
                OpportunityType.SINGLE_CHAIN_FLASH
                if l2_opp.get("type") == "flash_loan_arbitrage"
                else OpportunityType.SINGLE_CHAIN_DEX
            )
            
            # Set expiration: 5 seconds
            expires_at = time.time() + 5.0
            
            return SignalOpportunity(
                opportunity_id=f"OPP_L2_{self.opportunity_counter:06d}",
                type=opportunity_type,
                source_chain=l2_opp.get("chain", "ethereum"),
                token_pair=l2_opp.get("token_pair", "USDC/ETH"),
                expected_profit_eth=l2_opp.get("profit_eth", 0.0),
                profit_pct=l2_opp.get("spread_pct", 0.0),
                confidence_score=0.75,  # Default confidence
                position_size_eth=l2_opp.get("profit_eth", 0.0) * 100,
                flash_loan_amount_eth=l2_opp.get("profit_eth", 0.0) * 50,
                expires_at=expires_at,
            )
        
        except Exception as e:
            logger.error(f"Error converting L2 opportunity: {str(e)}")
            return None

    def _convert_bridge_opportunity(self, bridge_opp) -> Optional[SignalOpportunity]:
        """Convert BridgeMonitor opportunity to SignalOpportunity"""
        try:
            self.opportunity_counter += 1
            
            # Set expiration: 10 seconds (bridges are slower)
            expires_at = time.time() + 10.0
            
            return SignalOpportunity(
                opportunity_id=f"OPP_BRIDGE_{self.opportunity_counter:06d}",
                type=OpportunityType.BRIDGE_ARBITRAGE,
                source_chain=bridge_opp.source_chain,
                dest_chain=bridge_opp.dest_chain,
                token_pair=f"{bridge_opp.asset}/USD",
                expected_profit_eth=bridge_opp.estimated_profit_eth,
                profit_pct=bridge_opp.spread_pct,
                confidence_score=0.80,
                position_size_eth=100.0,  # Standard bridge position
                bridge_type="curve_bridge",
                expires_at=expires_at,
            )
        
        except Exception as e:
            logger.error(f"Error converting bridge opportunity: {str(e)}")
            return None

    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        self.execution_counter += 1
        return f"EXEC_{self.execution_counter:06d}_{int(time.time() * 1000)}"

    def get_orchestration_status(self) -> Dict:
        """Get current orchestration status"""
        return {
            "running": self.running,
            "pending_opportunities": len(self.pending_opportunities),
            "execution_queue_size": len(self.execution_queue),
            "active_plans": len(self.active_plans),
            "completed_executions": len(self.completed_executions),
            "metrics": {
                "total_detected": self.metrics["total_opportunities_detected"],
                "total_executed": self.metrics["total_opportunities_executed"],
                "total_profit_eth": self.metrics["total_profit_eth"],
                "by_chain": self.metrics["by_chain"],
            },
        }

    def get_profit_summary(self) -> Dict:
        """Get profit summary by chain"""
        summary = {
            "total_profit_eth": self.metrics["total_profit_eth"],
            "by_chain": {},
            "by_type": {},
        }
        
        for chain, stats in self.metrics["by_chain"].items():
            summary["by_chain"][chain] = stats
        
        # Summarize by opportunity type
        for execution in self.completed_executions:
            opp = self.pending_opportunities.get(execution.opportunity_id)
            if opp:
                opp_type = str(opp.type.value)
                if opp_type not in summary["by_type"]:
                    summary["by_type"][opp_type] = {"count": 0, "profit": 0.0}
                summary["by_type"][opp_type]["count"] += 1
                summary["by_type"][opp_type]["profit"] += execution.actual_profit_eth
        
        return summary

    async def stop_orchestration(self):
        """Stop orchestration loop"""
        self.running = False
        logger.info("🛑 Multi-chain orchestrator stopped")
