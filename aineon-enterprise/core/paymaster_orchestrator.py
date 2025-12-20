import asyncio
import time
import logging
from typing import Dict, List
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)

class PaymasterConfig:
    def __init__(self):
        self.paymasters = [
            {
                "name": "Pimlico",
                "endpoint": "https://api.pimlico.io/v2/ethereum/rpc",
                "fee_bps": 110,  # 1.1% markup
                "rate_limit": 1000,
                "supports": ["userOp", "bundle"],
            },
            {
                "name": "Gelato",
                "endpoint": "https://relay.gelato.digital/rpc",
                "fee_bps": 105,  # 1.05% markup
                "rate_limit": 800,
                "supports": ["userOp", "bundle"],
            },
            {
                "name": "Candide",
                "endpoint": "https://mainnet.bundler.candide.dev",
                "fee_bps": 115,  # 1.15% markup
                "rate_limit": 600,
                "supports": ["userOp"],
            },
        ]

class PaymasterHealth:
    def __init__(self, name: str):
        self.name = name
        self.operational = True
        self.success_rate = 0.95
        self.avg_response_time_ms = 0
        self.last_request = 0
        self.cumulative_fee = 0

class PaymasterOrchestrator:
    def __init__(self):
        self.config = PaymasterConfig()
        self.health = {p["name"]: PaymasterHealth(p["name"]) for p in self.config.paymasters}
        self.request_count = 0
        self.total_fees_saved = 0
    
    async def select_best_paymaster(self, estimated_gas_cost_wei: int) -> Dict:
        """Select paymaster with best rate + health"""
        # Filter operational paymasters
        operational = [
            p for p in self.config.paymasters
            if self.health[p["name"]].operational
        ]
        
        if not operational:
            # Fallback to any paymaster
            operational = self.config.paymasters
        
        # Calculate cost for each
        costs = {}
        for pm in operational:
            fee_amount = (estimated_gas_cost_wei * pm["fee_bps"]) // 10000
            adjusted_cost = fee_amount / self.health[pm["name"]].success_rate
            costs[pm["name"]] = adjusted_cost
        
        # Select cheapest + most reliable
        best = min(costs, key=costs.get)
        return next(p for p in self.config.paymasters if p["name"] == best)
    
    async def submit_user_operation(self, user_op: Dict, estimated_gas: int) -> Dict:
        """Submit UserOperation with automatic paymaster selection"""
        paymaster = await self.select_best_paymaster(estimated_gas)
        
        start_time = time.time()
        try:
            response = await self.call_paymaster(paymaster, user_op)
            
            response_time = (time.time() - start_time) * 1000
            
            # Update health on success
            self.health[paymaster["name"]].success_rate = 0.98
            self.health[paymaster["name"]].avg_response_time_ms = response_time
            self.request_count += 1
            
            # Log fee savings
            baseline_fee = (estimated_gas * 110) // 10000  # Worst case
            actual_fee = (estimated_gas * paymaster["fee_bps"]) // 10000
            savings = baseline_fee - actual_fee
            self.total_fees_saved += savings
            
            return response
            
        except Exception as e:
            # Mark paymaster as degraded
            self.health[paymaster["name"]].operational = False
            self.health[paymaster["name"]].success_rate *= 0.9
            
            # Retry with next best
            return await self.submit_user_operation_retry(user_op, estimated_gas)
    
    async def call_paymaster(self, paymaster: Dict, user_op: Dict) -> Dict:
        """Call paymaster RPC endpoint"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {paymaster.get('api_key', '')}"
            }
            
            payload = {
                "jsonrpc": "2.0",
                "id": self.request_count,
                "method": "pm_sendUserOperation",
                "params": [user_op, "0x..."]  # EntryPoint
            }
            
            async with session.post(
                paymaster["endpoint"],
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                return await resp.json()
    
    async def submit_user_operation_retry(self, user_op: Dict, estimated_gas: int) -> Dict:
        """Retry with next best paymaster"""
        paymaster = await self.select_best_paymaster(estimated_gas)
        try:
            return await self.call_paymaster(paymaster, user_op)
        except Exception as e:
            raise Exception(f"All paymasters failed: {e}")
    
    def get_cost_optimization_report(self) -> Dict:
        """Report on cost savings"""
        avg_savings_per_tx = self.total_fees_saved / max(self.request_count, 1)
        return {
            "total_transactions": self.request_count,
            "total_fees_saved_wei": self.total_fees_saved,
            "avg_savings_per_tx": avg_savings_per_tx,
            "paymaster_health": {
                name: {
                    "operational": health.operational,
                    "success_rate": health.success_rate,
                    "avg_response_time_ms": health.avg_response_time_ms,
                }
                for name, health in self.health.items()
            }
        }
