"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON PAYMASTER ORCHESTRATOR                              ║
║           Enterprise-Grade ERC-4337 Gasless Transaction Management             ║
║                                                                                ║
║  Purpose: Multi-paymaster coordination with automatic failover & fund mgmt    ║
║  Providers: Pimlico, Alchemy, custom paymasters                               ║
║  Target: Zero gas costs + MEV protection                                      ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import aiohttp
from datetime import datetime
from collections import deque
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaymasterStatus(Enum):
    """Paymaster health status"""
    AVAILABLE = "AVAILABLE"
    LOW_BALANCE = "LOW_BALANCE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class PaymasterMetrics:
    """Track paymaster performance"""
    paymaster_name: str
    balance_wei: Decimal = Decimal('0')
    min_balance_wei: Decimal = Decimal('0.1') * Decimal('10') ** Decimal('18')  # 0.1 ETH
    status: PaymasterStatus = PaymasterStatus.AVAILABLE
    operations_sponsored: int = 0
    operations_failed: int = 0
    total_gas_sponsored_wei: Decimal = Decimal('0')
    avg_gas_cost_wei: Decimal = Decimal('0')
    last_update: Optional[datetime] = None
    success_rate: float = 100.0


class Paymaster:
    """Individual Paymaster provider"""
    
    def __init__(self, name: str, url: str, address: str = ""):
        self.name = name
        self.url = url
        self.address = address  # Optional on-chain paymaster address
        self.metrics = PaymasterMetrics(paymaster_name=name)
        self.priority = 0
        self.is_available = True
    
    async def sponsor_operation(self, user_op: Dict, entry_point: str) -> Tuple[bool, Optional[Dict], str]:
        """Request operation sponsorship"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json={
                        "jsonrpc": "2.0",
                        "method": "pm_sponsorUserOperation",
                        "params": [user_op, entry_point],
                        "id": int(time.time() * 1000)
                    },
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'result' in data:
                            self.metrics.operations_sponsored += 1
                            result = data['result']
                            
                            # Extract gas cost if available
                            if 'callGasLimit' in result:
                                gas_cost = int(result.get('callGasLimit', 0))
                                self.metrics.total_gas_sponsored_wei += Decimal(str(gas_cost))
                                if self.metrics.operations_sponsored > 0:
                                    self.metrics.avg_gas_cost_wei = self.metrics.total_gas_sponsored_wei / Decimal(str(self.metrics.operations_sponsored))
                            
                            return True, result, ""
                        elif 'error' in data:
                            self.metrics.operations_failed += 1
                            error_msg = data['error'].get('message', 'Unknown error')
                            return False, None, error_msg
        except asyncio.TimeoutError:
            self.metrics.operations_failed += 1
            return False, None, "Paymaster timeout"
        except Exception as e:
            self.metrics.operations_failed += 1
            return False, None, str(e)
        
        self.metrics.operations_failed += 1
        return False, None, "Unknown error"
    
    def update_status(self, balance: Optional[Decimal] = None):
        """Update paymaster status"""
        if balance is not None:
            self.metrics.balance_wei = balance
        
        total_ops = self.metrics.operations_sponsored + self.metrics.operations_failed
        if total_ops > 0:
            self.metrics.success_rate = (self.metrics.operations_sponsored / total_ops) * 100
        
        # Status logic
        if self.metrics.balance_wei < self.metrics.min_balance_wei:
            self.metrics.status = PaymasterStatus.LOW_BALANCE
            self.is_available = False
        elif self.metrics.success_rate < 70:
            self.metrics.status = PaymasterStatus.UNAVAILABLE
            self.is_available = False
        elif self.metrics.success_rate < 90:
            self.metrics.status = PaymasterStatus.DEGRADED
            self.is_available = True
        else:
            self.metrics.status = PaymasterStatus.AVAILABLE
            self.is_available = True
        
        self.metrics.last_update = datetime.now()


class PaymasterOrchestrator:
    """Enterprise paymaster management with automatic selection"""
    
    def __init__(self):
        self.paymasters: List[Paymaster] = []
        self.operation_history: deque = deque(maxlen=10000)
        self.sponsorship_requests = 0
        self.sponsorship_successes = 0
        self.sponsorship_failures = 0
        self.balance_check_interval = 60  # seconds
        self.last_balance_check = time.time()
        self.stats = {
            "total_requests": 0,
            "successful_sponsorships": 0,
            "failed_sponsorships": 0,
            "avg_gas_cost_wei": Decimal('0'),
            "total_gas_sponsored_wei": Decimal('0')
        }
        logger.info("[PAYMASTER] Orchestrator initialized")
    
    def register_paymaster(self, name: str, url: str, address: str = "", priority: int = 0):
        """Register paymaster provider"""
        paymaster = Paymaster(name, url, address)
        paymaster.priority = priority
        self.paymasters.append(paymaster)
        # Sort by priority
        self.paymasters.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"[PAYMASTER] Registered: {name} (priority: {priority})")
    
    async def sponsor_user_operation(
        self,
        user_op: Dict,
        entry_point: str,
        min_profit_threshold: Decimal = Decimal('0.5') * Decimal('10') ** Decimal('18')
    ) -> Tuple[bool, Optional[Dict], str]:
        """
        Sponsor user operation with automatic paymaster selection
        
        Args:
            user_op: ERC-4337 UserOperation
            entry_point: EntryPoint contract address
            min_profit_threshold: Minimum profit required to sponsor (in wei)
        
        Returns:
            (success, sponsored_op, error_message)
        """
        self.stats["total_requests"] += 1
        
        # Check if sponsorship is profitable
        estimated_gas = int(user_op.get('callGasLimit', 500000))
        estimated_gas_cost = estimated_gas * 50  # ~50 gwei gas price
        
        if estimated_gas_cost > int(min_profit_threshold):
            logger.warning(f"[PAYMASTER] Gas cost ({estimated_gas_cost} wei) exceeds profit threshold")
            self.sponsorship_failures += 1
            return False, None, "Gas cost exceeds profit threshold"
        
        # Try paymasters in priority order
        available = [p for p in self.paymasters if p.is_available]
        if not available:
            available = self.paymasters  # Fallback to all
        
        for paymaster in available:
            success, result, error = await paymaster.sponsor_operation(user_op, entry_point)
            
            if success:
                self.sponsorship_successes += 1
                self.stats["successful_sponsorships"] += 1
                
                if result and 'callGasLimit' in result:
                    gas_cost = Decimal(str(result.get('callGasLimit', 0)))
                    self.stats["total_gas_sponsored_wei"] += gas_cost
                    self.stats["avg_gas_cost_wei"] = self.stats["total_gas_sponsored_wei"] / Decimal(str(self.sponsorship_successes + 1))
                
                self.operation_history.append({
                    "paymaster": paymaster.name,
                    "success": True,
                    "timestamp": time.time(),
                    "gas_cost": result.get('callGasLimit', 0) if result else 0
                })
                
                logger.info(f"[PAYMASTER] ✓ Operation sponsored by {paymaster.name}")
                return True, result, ""
            else:
                logger.warning(f"[PAYMASTER] ✗ {paymaster.name} failed: {error}")
                paymaster.update_status()
        
        # All paymasters failed
        self.sponsorship_failures += 1
        self.stats["failed_sponsorships"] += 1
        
        self.operation_history.append({
            "paymaster": "NONE",
            "success": False,
            "timestamp": time.time(),
            "error": "All paymasters failed"
        })
        
        logger.error("[PAYMASTER] All paymasters failed to sponsor operation")
        return False, None, "All paymasters unavailable"
    
    async def check_paymaster_balances(self, rpc_call_func=None) -> Dict[str, Dict]:
        """Check ETH balances of all paymasters"""
        if time.time() - self.last_balance_check < self.balance_check_interval:
            return {}
        
        logger.info("[PAYMASTER] Checking balances...")
        balances = {}
        
        for paymaster in self.paymasters:
            if not paymaster.address:
                logger.debug(f"[PAYMASTER] {paymaster.name} has no on-chain address")
                continue
            
            try:
                if rpc_call_func:
                    # Use provided RPC function
                    balance = await rpc_call_func("eth_getBalance", [paymaster.address, "latest"])
                    if balance:
                        balance_wei = Decimal(str(int(balance, 16)))
                        paymaster.update_status(balance_wei)
                        balances[paymaster.name] = {
                            "balance_eth": float(balance_wei / Decimal('10') ** Decimal('18')),
                            "status": paymaster.metrics.status.value
                        }
                        logger.info(f"[PAYMASTER] {paymaster.name}: {float(balance_wei / Decimal('10') ** Decimal('18')):.4f} ETH")
            except Exception as e:
                logger.warning(f"[PAYMASTER] Failed to check {paymaster.name} balance: {e}")
        
        self.last_balance_check = time.time()
        return balances
    
    def get_best_paymaster(self) -> Optional[Paymaster]:
        """Get best available paymaster"""
        available = [p for p in self.paymasters if p.is_available]
        if available:
            return available[0]  # Already sorted by priority
        
        # Return least degraded
        if self.paymasters:
            return self.paymasters[0]
        
        return None
    
    def get_stats(self) -> Dict:
        """Get orchestrator statistics"""
        total_ops = self.sponsorship_successes + self.sponsorship_failures
        
        return {
            "total_sponsorship_requests": self.stats["total_requests"],
            "successful_sponsorships": self.stats["successful_sponsorships"],
            "failed_sponsorships": self.stats["failed_sponsorships"],
            "success_rate": f"{(self.stats['successful_sponsorships'] / total_ops * 100):.2f}%" if total_ops > 0 else "0%",
            "avg_gas_cost_eth": float(self.stats["avg_gas_cost_wei"] / Decimal('10') ** Decimal('18')),
            "total_gas_sponsored_eth": float(self.stats["total_gas_sponsored_wei"] / Decimal('10') ** Decimal('18')),
            "paymasters": [
                {
                    "name": p.name,
                    "status": p.metrics.status.value,
                    "balance_eth": float(p.metrics.balance_wei / Decimal('10') ** Decimal('18')),
                    "sponsored": p.metrics.operations_sponsored,
                    "failed": p.metrics.operations_failed,
                    "success_rate": f"{p.metrics.success_rate:.1f}%"
                }
                for p in self.paymasters
            ]
        }
    
    async def continuous_balance_monitoring(self, rpc_call_func=None):
        """Background task for continuous balance monitoring"""
        logger.info("[PAYMASTER] Starting balance monitoring...")
        
        while True:
            try:
                await self.check_paymaster_balances(rpc_call_func)
                await asyncio.sleep(self.balance_check_interval)
            except Exception as e:
                logger.error(f"[PAYMASTER] Balance check error: {e}")
                await asyncio.sleep(10)


# Singleton instance
_paymaster_orchestrator: Optional[PaymasterOrchestrator] = None


def get_paymaster_orchestrator() -> PaymasterOrchestrator:
    """Get singleton paymaster orchestrator"""
    global _paymaster_orchestrator
    if _paymaster_orchestrator is None:
        _paymaster_orchestrator = PaymasterOrchestrator()
        
        import os
        
        # Register Pimlico (highest priority)
        _paymaster_orchestrator.register_paymaster(
            "Pimlico",
            "https://api.pimlico.io/v2/ethereum/rpc",
            os.getenv("PIMLICO_PAYMASTER_ADDRESS", ""),
            priority=100
        )
        
        # Register Alchemy (if available)
        if os.getenv("ALCHEMY_PAYMASTER_URL"):
            _paymaster_orchestrator.register_paymaster(
                "Alchemy",
                os.getenv("ALCHEMY_PAYMASTER_URL"),
                os.getenv("ALCHEMY_PAYMASTER_ADDRESS", ""),
                priority=90
            )
        
        # Register custom paymaster (if available)
        if os.getenv("CUSTOM_PAYMASTER_URL"):
            _paymaster_orchestrator.register_paymaster(
                "Custom",
                os.getenv("CUSTOM_PAYMASTER_URL"),
                os.getenv("CUSTOM_PAYMASTER_ADDRESS", ""),
                priority=80
            )
    
    return _paymaster_orchestrator


if __name__ == "__main__":
    async def test_paymaster():
        orchestrator = get_paymaster_orchestrator()
        
        # Mock user operation
        user_op = {
            "sender": "0x1234567890123456789012345678901234567890",
            "nonce": 0,
            "initCode": "0x",
            "callData": "0x",
            "callGasLimit": 500000,
            "verificationGasLimit": 100000,
            "preVerificationGas": 21000,
            "maxFeePerGas": "0x3b9aca00",
            "maxPriorityFeePerGas": "0x3b9aca00"
        }
        
        entry_point = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
        
        success, result, error = await orchestrator.sponsor_user_operation(user_op, entry_point)
        
        print(f"Sponsorship result: {success}")
        if error:
            print(f"Error: {error}")
        
        # Get stats
        print("\nPaymaster Statistics:")
        print(json.dumps(orchestrator.get_stats(), indent=2, default=str))
    
    asyncio.run(test_paymaster())
