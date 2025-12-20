"""
PHASE 2 FILE 1: Layer 2 Atomic Executor
Multi-chain atomic execution engine with cross-chain bridge support
Executes arbitrage opportunities atomically across Polygon, Optimism, Arbitrum
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import time
from web3 import Web3
import aiohttp

logger = logging.getLogger(__name__)


class ChainId(Enum):
    """Blockchain network identifiers"""
    ETHEREUM = 1
    POLYGON = 137
    OPTIMISM = 10
    ARBITRUM = 42161


class BridgeType(Enum):
    """Supported bridge protocols"""
    CURVE_STABLECOIN = "curve_bridge"
    ACROSS = "across"
    CONNEXT = "connext"
    NATIVE = "native"  # Chain-native bridges


@dataclass
class L2ChainContext:
    """Execution context for a specific L2 chain"""
    chain_id: ChainId
    chain_name: str
    rpc_url: str
    w3: Optional[Web3] = None
    flash_loan_sources: List[str] = field(default_factory=list)
    max_flash_capacity_eth: float = 1000.0
    gas_price_gwei: float = 50.0
    block_time_seconds: float = 2.5
    min_profit_threshold_eth: float = 0.1
    circuit_breaker_active: bool = False


@dataclass
class AtomicSwapOrder:
    """Represents an atomic multi-step swap operation"""
    operation_id: str
    source_chain_id: ChainId
    dest_chain_id: Optional[ChainId]
    steps: List[Dict] = field(default_factory=list)
    total_profit_eth: float = 0.0
    total_gas_eth: float = 0.0
    status: str = "pending"
    executed_at: Optional[float] = None
    tx_hashes: List[str] = field(default_factory=list)


class Layer2AtomicExecutor:
    """
    Executes flash loan arbitrage atomically across multiple chains.
    Handles cross-chain bridges, position sizing, and profit consolidation.
    """

    def __init__(self, wallet_address: str, private_key: str):
        self.wallet_address = wallet_address
        self.private_key = private_key
        
        # Initialize chain contexts
        self.chains: Dict[str, L2ChainContext] = self._initialize_chains()
        
        # Execution state
        self.active_operations: Dict[str, AtomicSwapOrder] = {}
        self.operation_counter = 0
        self.total_profit_eth = 0.0
        self.total_loss_eth = 0.0
        self.execution_history: List[Dict] = []
        
        # Per-chain risk limits
        self.chain_daily_limits = {
            "ethereum": 100.0,  # ETH
            "polygon": 50.0,
            "optimism": 40.0,
            "arbitrum": 60.0,
        }
        self.chain_daily_used = {k: 0.0 for k in self.chain_daily_limits}

    def _initialize_chains(self) -> Dict[str, L2ChainContext]:
        """Initialize Web3 connections for all supported chains"""
        chains = {}
        
        chain_configs = [
            L2ChainContext(
                chain_id=ChainId.ETHEREUM,
                chain_name="ethereum",
                rpc_url="https://eth-mainnet.g.alchemy.com/v2/demo",
                flash_loan_sources=["Aave V3", "dYdX v3", "Balancer"],
                max_flash_capacity_eth=500.0,
                gas_price_gwei=50.0,
                block_time_seconds=12.0,
                min_profit_threshold_eth=0.2,
            ),
            L2ChainContext(
                chain_id=ChainId.POLYGON,
                chain_name="polygon",
                rpc_url="https://polygon-rpc.com/",
                flash_loan_sources=["Aave V2", "dYdX v3"],
                max_flash_capacity_eth=200.0,
                gas_price_gwei=50.0,
                block_time_seconds=2.5,
                min_profit_threshold_eth=0.1,
            ),
            L2ChainContext(
                chain_id=ChainId.OPTIMISM,
                chain_name="optimism",
                rpc_url="https://mainnet.optimism.io",
                flash_loan_sources=["Aave V3"],
                max_flash_capacity_eth=150.0,
                gas_price_gwei=0.5,
                block_time_seconds=2.0,
                min_profit_threshold_eth=0.1,
            ),
            L2ChainContext(
                chain_id=ChainId.ARBITRUM,
                chain_name="arbitrum",
                rpc_url="https://arb1.arbitrum.io/rpc",
                flash_loan_sources=["Aave V3", "dYdX v3"],
                max_flash_capacity_eth=250.0,
                gas_price_gwei=0.1,
                block_time_seconds=0.25,
                min_profit_threshold_eth=0.08,
            ),
        ]
        
        for config in chain_configs:
            try:
                config.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
                if config.w3.is_connected():
                    chains[config.chain_name] = config
                    logger.info(f"✓ Connected to {config.chain_name} (Chain ID: {config.chain_id.value})")
                else:
                    logger.error(f"✗ Failed to connect to {config.chain_name}")
            except Exception as e:
                logger.error(f"✗ Connection error for {config.chain_name}: {str(e)}")
        
        return chains

    async def execute_single_chain_arbitrage(
        self,
        chain_name: str,
        token_pair: str,
        flash_loan_amount_eth: float,
        expected_profit_eth: float,
        swap_route: List[Dict],
    ) -> Dict:
        """
        Execute single-chain flash loan arbitrage.
        
        Args:
            chain_name: Target chain (ethereum, polygon, optimism, arbitrum)
            token_pair: Token pair (e.g., "USDC/ETH")
            flash_loan_amount_eth: Amount to borrow via flash loan
            expected_profit_eth: Expected profit (before gas)
            swap_route: List of swap steps with DEX/pool info
        
        Returns:
            Execution result with tx hashes and actual profit
        """
        if chain_name not in self.chains:
            logger.error(f"Chain {chain_name} not supported")
            return {"success": False, "error": "unsupported_chain"}
        
        chain = self.chains[chain_name]
        
        # Check risk limits
        if self.chain_daily_used[chain_name] >= self.chain_daily_limits[chain_name]:
            logger.warning(f"Daily loss limit reached for {chain_name}")
            return {"success": False, "error": "daily_limit_exceeded"}
        
        if chain.circuit_breaker_active:
            logger.warning(f"Circuit breaker active for {chain_name}")
            return {"success": False, "error": "circuit_breaker_active"}
        
        try:
            # Create operation record
            op_id = self._generate_operation_id()
            operation = AtomicSwapOrder(
                operation_id=op_id,
                source_chain_id=chain.chain_id,
                dest_chain_id=None,
            )
            self.active_operations[op_id] = operation
            
            logger.info(f"[{op_id}] Executing {token_pair} on {chain_name} (Flash: {flash_loan_amount_eth} ETH)")
            
            # Step 1: Initiate flash loan
            flash_tx = await self._initiate_flash_loan(
                chain_name,
                token_pair,
                flash_loan_amount_eth,
            )
            
            if not flash_tx:
                logger.error(f"[{op_id}] Flash loan initiation failed")
                operation.status = "failed"
                return {"success": False, "error": "flash_loan_failed"}
            
            operation.tx_hashes.append(flash_tx["hash"])
            operation.steps.append(flash_tx)
            
            # Step 2: Execute swap route atomically
            swap_results = await self._execute_swap_route(
                chain_name,
                swap_route,
                flash_loan_amount_eth,
            )
            
            if not swap_results["success"]:
                logger.error(f"[{op_id}] Swap execution failed")
                operation.status = "failed"
                return {"success": False, "error": "swap_failed"}
            
            operation.steps.extend(swap_results["steps"])
            operation.tx_hashes.extend(swap_results["tx_hashes"])
            
            # Step 3: Repay flash loan + profit
            repay_tx = await self._repay_flash_loan(
                chain_name,
                token_pair,
                flash_loan_amount_eth,
            )
            
            if not repay_tx:
                logger.error(f"[{op_id}] Flash loan repayment failed")
                operation.status = "failed"
                return {"success": False, "error": "repay_failed"}
            
            operation.tx_hashes.append(repay_tx["hash"])
            operation.steps.append(repay_tx)
            
            # Calculate actual profit
            gas_cost = self._calculate_gas_cost(
                len(operation.tx_hashes),
                chain.gas_price_gwei,
            )
            actual_profit = swap_results["profit_eth"] - gas_cost
            
            operation.total_profit_eth = actual_profit
            operation.total_gas_eth = gas_cost
            operation.status = "success"
            operation.executed_at = time.time()
            
            # Update state
            self.total_profit_eth += actual_profit
            self.execution_history.append({
                "operation_id": op_id,
                "chain": chain_name,
                "profit_eth": actual_profit,
                "gas_eth": gas_cost,
                "timestamp": operation.executed_at,
            })
            
            logger.info(
                f"[{op_id}] ✓ Success: {actual_profit:.4f} ETH profit "
                f"(gas: {gas_cost:.4f} ETH, expected: {expected_profit_eth:.4f} ETH)"
            )
            
            return {
                "success": True,
                "operation_id": op_id,
                "chain": chain_name,
                "profit_eth": actual_profit,
                "gas_eth": gas_cost,
                "tx_hashes": operation.tx_hashes,
            }
            
        except Exception as e:
            logger.error(f"[{op_id}] Execution error: {str(e)}")
            if op_id in self.active_operations:
                self.active_operations[op_id].status = "error"
            return {"success": False, "error": str(e)}

    async def execute_cross_chain_arbitrage(
        self,
        source_chain: str,
        dest_chain: str,
        token: str,
        bridge_type: BridgeType,
        amount_eth: float,
        source_price: float,
        dest_price: float,
        spread_pct: float,
    ) -> Dict:
        """
        Execute cross-chain bridge arbitrage atomically.
        
        Steps:
        1. Buy token on source chain
        2. Bridge to destination chain
        3. Sell on destination chain
        4. Return profit
        """
        if source_chain not in self.chains or dest_chain not in self.chains:
            logger.error("One or both chains not supported")
            return {"success": False, "error": "unsupported_chain"}
        
        try:
            op_id = self._generate_operation_id()
            operation = AtomicSwapOrder(
                operation_id=op_id,
                source_chain_id=self.chains[source_chain].chain_id,
                dest_chain_id=self.chains[dest_chain].chain_id,
            )
            self.active_operations[op_id] = operation
            
            logger.info(
                f"[{op_id}] Cross-chain arb: {source_chain}→{dest_chain} "
                f"({token}, spread: {spread_pct:.3f}%)"
            )
            
            # Step 1: Buy on source chain
            buy_tx = await self._execute_swap_on_chain(
                source_chain,
                token=token,
                amount_eth=amount_eth,
                direction="buy",
                price=source_price,
            )
            
            if not buy_tx:
                logger.error(f"[{op_id}] Buy on {source_chain} failed")
                operation.status = "failed"
                return {"success": False, "error": "buy_failed"}
            
            operation.tx_hashes.append(buy_tx["hash"])
            operation.steps.append({"step": "buy", **buy_tx})
            
            # Step 2: Bridge to destination chain
            bridge_tx = await self._bridge_tokens(
                source_chain,
                dest_chain,
                token=token,
                amount=amount_eth,
                bridge_type=bridge_type,
            )
            
            if not bridge_tx:
                logger.error(f"[{op_id}] Bridge failed")
                operation.status = "failed"
                return {"success": False, "error": "bridge_failed"}
            
            operation.tx_hashes.append(bridge_tx["hash"])
            operation.steps.append({"step": "bridge", **bridge_tx})
            
            # Step 3: Sell on destination chain
            sell_tx = await self._execute_swap_on_chain(
                dest_chain,
                token=token,
                amount_eth=amount_eth,
                direction="sell",
                price=dest_price,
            )
            
            if not sell_tx:
                logger.error(f"[{op_id}] Sell on {dest_chain} failed")
                operation.status = "failed"
                return {"success": False, "error": "sell_failed"}
            
            operation.tx_hashes.append(sell_tx["hash"])
            operation.steps.append({"step": "sell", **sell_tx})
            
            # Calculate profit
            bridge_fee_pct = self._get_bridge_fee(bridge_type)
            net_spread = spread_pct - (2 * bridge_fee_pct)
            gross_profit = (net_spread / 100) * amount_eth
            
            source_gas = self._calculate_gas_cost(
                1, self.chains[source_chain].gas_price_gwei
            )
            dest_gas = self._calculate_gas_cost(
                1, self.chains[dest_chain].gas_price_gwei
            )
            total_gas = source_gas + dest_gas
            
            actual_profit = gross_profit - total_gas
            
            operation.total_profit_eth = actual_profit
            operation.total_gas_eth = total_gas
            operation.status = "success"
            operation.executed_at = time.time()
            
            # Update state
            self.total_profit_eth += actual_profit
            self.execution_history.append({
                "operation_id": op_id,
                "type": "bridge",
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "profit_eth": actual_profit,
                "timestamp": operation.executed_at,
            })
            
            logger.info(
                f"[{op_id}] ✓ Bridge arb success: {actual_profit:.4f} ETH "
                f"(spread: {spread_pct:.3f}%, net after gas: {net_spread:.3f}%)"
            )
            
            return {
                "success": True,
                "operation_id": op_id,
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "profit_eth": actual_profit,
                "tx_hashes": operation.tx_hashes,
            }
            
        except Exception as e:
            logger.error(f"[{op_id}] Cross-chain error: {str(e)}")
            if op_id in self.active_operations:
                self.active_operations[op_id].status = "error"
            return {"success": False, "error": str(e)}

    async def _initiate_flash_loan(
        self,
        chain_name: str,
        token_pair: str,
        amount_eth: float,
    ) -> Optional[Dict]:
        """Initiate flash loan on specified chain"""
        try:
            chain = self.chains[chain_name]
            
            # Select flash loan source (prefer dYdX for lowest fees)
            flash_source = "dYdX v3" if "dYdX v3" in chain.flash_loan_sources else chain.flash_loan_sources[0]
            
            logger.debug(f"Initiating flash loan via {flash_source}: {amount_eth} ETH")
            
            # Simulate flash loan initiation
            return {
                "hash": self._generate_tx_hash(),
                "flash_source": flash_source,
                "amount_eth": amount_eth,
                "fee_bps": 2,  # 0.02% fee
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Flash loan initiation error: {str(e)}")
            return None

    async def _repay_flash_loan(
        self,
        chain_name: str,
        token_pair: str,
        amount_eth: float,
    ) -> Optional[Dict]:
        """Repay flash loan with profit"""
        try:
            logger.debug(f"Repaying flash loan: {amount_eth} ETH")
            
            return {
                "hash": self._generate_tx_hash(),
                "amount_eth": amount_eth,
                "status": "repaid",
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Flash loan repayment error: {str(e)}")
            return None

    async def _execute_swap_route(
        self,
        chain_name: str,
        swap_route: List[Dict],
        amount_eth: float,
    ) -> Dict:
        """Execute a series of atomic swaps"""
        try:
            steps = []
            tx_hashes = []
            current_amount = amount_eth
            
            for i, swap in enumerate(swap_route):
                swap_result = await self._execute_single_swap(
                    chain_name,
                    swap["dex"],
                    swap["token_in"],
                    swap["token_out"],
                    current_amount,
                )
                
                if not swap_result:
                    return {"success": False, "steps": steps, "tx_hashes": tx_hashes}
                
                steps.append(swap_result)
                tx_hashes.append(swap_result["hash"])
                current_amount = swap_result["amount_out"]
            
            # Calculate profit
            profit_eth = current_amount - amount_eth
            
            return {
                "success": True,
                "steps": steps,
                "tx_hashes": tx_hashes,
                "profit_eth": profit_eth,
            }
            
        except Exception as e:
            logger.error(f"Swap route execution error: {str(e)}")
            return {"success": False, "steps": [], "tx_hashes": []}

    async def _execute_single_swap(
        self,
        chain_name: str,
        dex: str,
        token_in: str,
        token_out: str,
        amount: float,
    ) -> Optional[Dict]:
        """Execute single swap on DEX"""
        try:
            logger.debug(f"{dex}: {amount} {token_in} → {token_out}")
            
            return {
                "hash": self._generate_tx_hash(),
                "dex": dex,
                "token_in": token_in,
                "token_out": token_out,
                "amount_in": amount,
                "amount_out": amount * 1.0015,  # Assume 0.15% profit
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Swap execution error: {str(e)}")
            return None

    async def _execute_swap_on_chain(
        self,
        chain_name: str,
        token: str,
        amount_eth: float,
        direction: str,
        price: float,
    ) -> Optional[Dict]:
        """Execute swap on specific chain"""
        try:
            logger.debug(f"{chain_name}: {direction} {token} @ ${price:.4f}")
            
            return {
                "hash": self._generate_tx_hash(),
                "token": token,
                "amount": amount_eth,
                "price": price,
                "direction": direction,
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Swap on {chain_name} error: {str(e)}")
            return None

    async def _bridge_tokens(
        self,
        source_chain: str,
        dest_chain: str,
        token: str,
        amount: float,
        bridge_type: BridgeType,
    ) -> Optional[Dict]:
        """Bridge tokens between chains"""
        try:
            logger.debug(f"Bridging {amount} {token}: {source_chain}→{dest_chain} via {bridge_type.value}")
            
            return {
                "hash": self._generate_tx_hash(),
                "token": token,
                "amount": amount,
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "bridge": bridge_type.value,
                "timestamp": time.time(),
            }
            
        except Exception as e:
            logger.error(f"Bridge error: {str(e)}")
            return None

    def _calculate_gas_cost(self, num_txs: int, gas_price_gwei: float) -> float:
        """Calculate total gas cost in ETH"""
        # Average gas per tx: 150k units
        gas_units = 150_000
        total_gas_units = gas_units * num_txs
        gas_cost_wei = total_gas_units * (gas_price_gwei * 1e9)
        gas_cost_eth = gas_cost_wei / 1e18
        return gas_cost_eth

    def _get_bridge_fee(self, bridge_type: BridgeType) -> float:
        """Get bridge fee as percentage"""
        fees = {
            BridgeType.CURVE_STABLECOIN: 0.0004,  # 0.04%
            BridgeType.ACROSS: 0.0005,            # 0.05%
            BridgeType.CONNEXT: 0.0008,           # 0.08%
            BridgeType.NATIVE: 0.0001,            # 0.01%
        }
        return fees.get(bridge_type, 0.0005)

    def _generate_operation_id(self) -> str:
        """Generate unique operation ID"""
        self.operation_counter += 1
        return f"OP_{self.operation_counter:06d}_{int(time.time() * 1000)}"

    def _generate_tx_hash(self) -> str:
        """Generate mock transaction hash"""
        import random
        import string
        return "0x" + "".join(random.choices(string.hexdigits[:-6], k=64))

    def get_execution_stats(self) -> Dict:
        """Get execution statistics"""
        successful = sum(
            1 for op in self.active_operations.values() if op.status == "success"
        )
        failed = sum(
            1 for op in self.active_operations.values() if op.status == "failed"
        )
        
        avg_profit = (
            self.total_profit_eth / successful if successful > 0 else 0
        )
        
        return {
            "total_operations": len(self.active_operations),
            "successful": successful,
            "failed": failed,
            "total_profit_eth": self.total_profit_eth,
            "avg_profit_eth": avg_profit,
            "execution_history_count": len(self.execution_history),
        }

    def get_chain_status(self) -> Dict:
        """Get status of all chains"""
        return {
            chain_name: {
                "connected": chain.w3.is_connected() if chain.w3 else False,
                "daily_used_eth": self.chain_daily_used[chain_name],
                "daily_limit_eth": self.chain_daily_limits[chain_name],
                "circuit_breaker": chain.circuit_breaker_active,
            }
            for chain_name, chain in self.chains.items()
        }
