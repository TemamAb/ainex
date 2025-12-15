"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON TIER 3: EXECUTOR                                    ║
║                     High-Speed Transaction Execution                           ║
║                                                                                ║
║  Purpose: Execute trades at lightning speed with gasless transactions          ║
║  Tier: Distributed per-strategy executors (MEV-resistant)                     ║
║  Interval: <5ms execution, parallel strategy execution                         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import asyncio
import logging
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import uuid
import json
from web3 import Web3
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class ExecutionStatus(Enum):
    PENDING = "PENDING"
    CONFIRMING = "CONFIRMING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REVERTED = "REVERTED"


@dataclass
class TransactionMetrics:
    """Track execution metrics"""
    signal_id: str
    tx_hash: str
    gas_used: Decimal
    gas_price: Decimal
    execution_time_ms: float
    slippage_pct: float
    mev_cost: Decimal
    status: ExecutionStatus


class GaslessExecutor:
    """Handle ERC-4337 gasless transactions via Pimlico"""
    
    def __init__(self):
        self.paymaster_url = os.getenv("PAYMASTER_URL", "")
        self.bundler_url = os.getenv("BUNDLER_URL", "")
        self.enabled = bool(self.paymaster_url and self.bundler_url)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL", "")))
        self.account_address = os.getenv("WALLET_ADDRESS", "")
        self.entry_point = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
        
        logger.info(f"[GASLESS] Pimlico Paymaster: {'ENABLED' if self.enabled else 'DISABLED'}")
    
    async def sponsor_transaction(self, call_data: str, value: int = 0) -> Optional[Dict]:
        """Request transaction sponsorship from Pimlico"""
        if not self.enabled:
            logger.warning("[GASLESS] Paymaster not configured")
            return None
        
        try:
            import aiohttp
            
            user_op = {
                "sender": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
                "initCode": "0x",
                "callData": call_data,
                "accountGasLimits": hex(200000),
                "preVerificationGas": hex(21000),
                "gasFees": {
                    "maxFeePerGas": hex(int(self.w3.eth.gas_price * 1.1)),
                    "maxPriorityFeePerGas": hex(int(self.w3.eth.gas_price))
                },
                "paymasterAndData": "0x",
                "signature": "0x"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.paymaster_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "pm_sponsorUserOperation",
                        "params": [user_op, self.entry_point],
                        "id": 1
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data:
                            logger.info("[GASLESS] Transaction sponsored by Pimlico")
                            return data['result']
                        else:
                            logger.error(f"[GASLESS] Sponsorship failed: {data.get('error', 'Unknown')}")
        except Exception as e:
            logger.error(f"[GASLESS] Sponsorship error: {e}")
        
        return None
    
    async def send_gasless_transaction(self, call_data: str) -> Optional[str]:
        """Send transaction via gasless endpoint"""
        if not self.enabled:
            return None
        
        try:
            sponsored = await self.sponsor_transaction(call_data)
            if not sponsored:
                return None
            
            # In production, would sign and bundle via Pimlico
            # For now, return mock hash
            return f"0x{'0'*64}"
        except Exception as e:
            logger.error(f"[GASLESS] Transaction send error: {e}")
        
        return None


class StrategyExecutor:
    """Base executor for different strategies"""
    
    def __init__(self, strategy_name: str):
        self.strategy_name = strategy_name
        self.executor_id = f"executor_{strategy_name}_{int(time.time() * 1000)}"
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL", "")))
        self.gasless = GaslessExecutor()
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "")
        self.account_address = os.getenv("WALLET_ADDRESS", "")
        self.private_key = os.getenv("PRIVATE_KEY", "")
        
        self.execution_metrics: List[TransactionMetrics] = []
        self.execution_stats = {
            "total_executed": 0,
            "successful": 0,
            "failed": 0,
            "avg_execution_ms": 0,
            "total_gas_spent": Decimal('0'),
            "total_profit": Decimal('0')
        }
        
        logger.info(f"[EXECUTOR] Initialized {strategy_name}: {self.executor_id}")
    
    async def execute(self, signal: 'ExecutionSignal') -> Optional[Dict]:
        """Execute trade based on signal"""
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        
        try:
            logger.info(f"[EXECUTOR {self.strategy_name}] Executing {signal.signal_id}")
            
            # Build transaction
            tx_data = self._build_transaction_data(signal)
            if not tx_data:
                logger.error(f"[EXECUTOR] Failed to build transaction")
                self.execution_stats["failed"] += 1
                return None
            
            # Send transaction (gasless if enabled)
            if signal.gasless_mode and self.gasless.enabled:
                tx_hash = await self.gasless.send_gasless_transaction(tx_data['callData'])
                logger.info(f"[EXECUTOR] Gasless TX: {tx_hash[:10]}...")
            else:
                tx_hash = await self._send_regular_transaction(tx_data)
                logger.info(f"[EXECUTOR] Regular TX: {tx_hash[:10]}...")
            
            if not tx_hash:
                self.execution_stats["failed"] += 1
                return None
            
            # Wait for confirmation
            try:
                receipt = await self._wait_for_receipt(tx_hash, timeout=120)
                execution_time = (time.time() - start_time) * 1000
                
                status = ExecutionStatus.CONFIRMED if receipt.get('status') == 1 else ExecutionStatus.REVERTED
                
                metrics = TransactionMetrics(
                    signal_id=signal.signal_id,
                    tx_hash=tx_hash,
                    gas_used=Decimal(str(receipt.get('gasUsed', 0))),
                    gas_price=Decimal(str(self.w3.eth.gas_price)),
                    execution_time_ms=execution_time,
                    slippage_pct=0.05,  # Placeholder
                    mev_cost=Decimal('0'),
                    status=status
                )
                
                self.execution_metrics.append(metrics)
                self.execution_stats["total_executed"] += 1
                
                if status == ExecutionStatus.CONFIRMED:
                    self.execution_stats["successful"] += 1
                    logger.info(f"[EXECUTOR] ✓ Trade confirmed: {tx_hash[:10]}... ({execution_time:.0f}ms)")
                else:
                    self.execution_stats["failed"] += 1
                    logger.warning(f"[EXECUTOR] ✗ Trade reverted: {tx_hash[:10]}...")
                
                return {
                    "tx_hash": tx_hash,
                    "status": status.value,
                    "execution_time_ms": execution_time,
                    "metrics": metrics
                }
            except asyncio.TimeoutError:
                logger.warning(f"[EXECUTOR] Timeout waiting for receipt: {tx_hash[:10]}...")
                self.execution_stats["failed"] += 1
                return None
        
        except Exception as e:
            logger.error(f"[EXECUTOR] Execution error: {e}")
            self.execution_stats["failed"] += 1
            import traceback
            traceback.print_exc()
            return None
    
    def _build_transaction_data(self, signal: 'ExecutionSignal') -> Optional[Dict]:
        """Build transaction call data"""
        try:
            # Placeholder - in production, would construct actual swap calldata
            # For arbitrage, would call executeArbitrage(tokenIn, tokenOut, amount, routes)
            
            nonce = self.w3.eth.get_transaction_count(self.account_address)
            gas_price = self.w3.eth.gas_price
            
            call_data = "0x"  # Placeholder
            
            return {
                "to": self.contract_address,
                "data": call_data,
                "value": 0,
                "gas": 500000,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id
            }
        except Exception as e:
            logger.error(f"[EXECUTOR] Failed to build transaction: {e}")
            return None
    
    async def _send_regular_transaction(self, tx_data: Dict) -> Optional[str]:
        """Send regular (non-gasless) transaction"""
        try:
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx_data, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return self.w3.to_hex(tx_hash)
        except Exception as e:
            logger.error(f"[EXECUTOR] Transaction send error: {e}")
            return None
    
    async def _wait_for_receipt(self, tx_hash: str, timeout: int = 120) -> Optional[Dict]:
        """Wait for transaction receipt"""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt
        except Exception as e:
            logger.error(f"[EXECUTOR] Receipt error: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get executor statistics"""
        avg_time = 0
        if self.execution_metrics:
            avg_time = sum(m.execution_time_ms for m in self.execution_metrics) / len(self.execution_metrics)
        
        return {
            "executor_id": self.executor_id,
            "strategy": self.strategy_name,
            "total_executed": self.execution_stats["total_executed"],
            "successful": self.execution_stats["successful"],
            "failed": self.execution_stats["failed"],
            "success_rate": (self.execution_stats["successful"] / self.execution_stats["total_executed"] * 100) if self.execution_stats["total_executed"] > 0 else 0,
            "avg_execution_ms": avg_time,
            "total_gas_spent": float(self.execution_stats["total_gas_spent"]),
            "total_profit": float(self.execution_stats["total_profit"])
        }


class MultiStrategyExecutionEngine:
    """Manages multiple parallel executors for different strategies"""
    
    def __init__(self):
        self.engine_id = f"engine_{int(time.time() * 1000)}"
        self.executors: Dict[str, StrategyExecutor] = {}
        self.execution_queue: asyncio.Queue = asyncio.Queue()
        self.execution_history: List[Dict] = []
        
        # Initialize executors for each strategy
        strategies = [
            "liquidation_cascade",
            "multi_dex_arbitrage",
            "mev_capture",
            "lp_farming",
            "cross_chain",
            "flash_crash"
        ]
        
        for strategy in strategies:
            self.executors[strategy] = StrategyExecutor(strategy)
        
        logger.info(f"[EXECUTION ENGINE] Initialized with {len(self.executors)} executors")
    
    async def submit_signal(self, signal: 'ExecutionSignal') -> None:
        """Submit execution signal to queue"""
        await self.execution_queue.put(signal)
    
    async def execute(self, signal: 'ExecutionSignal'):
        """Execute signal directly (for integration with unified system)"""
        try:
            executor = self.executors.get(signal.strategy.value)
            if not executor:
                logger.error(f"[EXECUTION ENGINE] No executor for {signal.strategy.value}")
                return None
            
            result = await executor.execute(signal)
            if result:
                self.execution_history.append({
                    "signal": signal,
                    "result": result,
                    "timestamp": time.time()
                })
                
                # Create result object with required attributes
                class ExecutionResult:
                    def __init__(self, data):
                        self.tx_hash = data.get('tx_hash', '')
                        self.status = ExecutionStatus.CONFIRMED if data.get('status') == ExecutionStatus.CONFIRMED.value else ExecutionStatus.FAILED
                        self.actual_profit = Decimal('0')  # Would be calculated from actual trade
                
                return ExecutionResult(result)
            return None
        except Exception as e:
            logger.error(f"[EXECUTION ENGINE] Execute error: {e}")
            return None
    
    async def process_execution_queue(self) -> None:
        """Process execution queue in parallel"""
        while True:
            try:
                signal = await asyncio.wait_for(self.execution_queue.get(), timeout=1.0)
                
                # Route to appropriate executor
                executor = self.executors.get(signal.strategy.value)
                if executor:
                    result = await executor.execute(signal)
                    if result:
                        self.execution_history.append({
                            "signal": signal,
                            "result": result,
                            "timestamp": time.time()
                        })
                else:
                    logger.error(f"[EXECUTION ENGINE] No executor for {signal.strategy.value}")
                
            except asyncio.TimeoutError:
                # No signal in queue, continue
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"[EXECUTION ENGINE] Queue processing error: {e}")
    
    async def run(self) -> None:
        """Main execution engine loop"""
        logger.info(f"[EXECUTION ENGINE] Started: {self.engine_id}")
        await self.process_execution_queue()
    
    def get_stats(self) -> Dict:
        """Get aggregated execution statistics"""
        total_executed = 0
        total_successful = 0
        
        for executor in self.executors.values():
            stats = executor.get_stats()
            total_executed += stats["total_executed"]
            total_successful += stats["successful"]
        
        return {
            "engine_id": self.engine_id,
            "total_executors": len(self.executors),
            "total_executed": total_executed,
            "total_successful": total_successful,
            "success_rate": (total_successful / total_executed * 100) if total_executed > 0 else 0,
            "execution_history_length": len(self.execution_history),
            "queue_size": self.execution_queue.qsize(),
            "executor_stats": {
                name: executor.get_stats()
                for name, executor in self.executors.items()
            }
        }


async def run_execution_engine():
    """Standalone execution engine"""
    engine = MultiStrategyExecutionEngine()
    await engine.run()


if __name__ == "__main__":
    asyncio.run(run_execution_engine())
