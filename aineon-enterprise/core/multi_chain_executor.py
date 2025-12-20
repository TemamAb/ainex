"""
AINEON Multi-Chain Executor
Phase 3: Multi-chain execution across Ethereum, Polygon, Optimism, Arbitrum
Network-agnostic transaction execution with fallover
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChainId(Enum):
    """Supported blockchain networks"""
    ETHEREUM = 1
    POLYGON = 137
    OPTIMISM = 10
    ARBITRUM = 42161


@dataclass
class ChainConfig:
    """Configuration for each blockchain"""
    chain_id: int
    name: str
    rpc_urls: List[str]  # Primary + fallover URLs
    bundler_url: str
    paymaster_url: str
    flash_loan_providers: List[str]
    avg_block_time: int  # seconds
    gas_cost_multiplier: float  # relative to Ethereum
    profit_threshold: float  # minimum profit in ETH equivalent


class ChainRegistry:
    """Registry of supported chains with configurations"""
    
    CONFIGS = {
        ChainId.ETHEREUM: ChainConfig(
            chain_id=1,
            name='Ethereum',
            rpc_urls=[
                'https://eth-mainnet.g.alchemy.com/v2/demo',
                'https://eth.llamarpc.com',
                'https://ethereum.publicnode.com'
            ],
            bundler_url='https://api.pimlico.io/v2/ethereum/rpc',
            paymaster_url='https://api.pimlico.io/v2/ethereum/rpc',
            flash_loan_providers=['aave_v3', 'dydx', 'uniswap_v3', 'balancer'],
            avg_block_time=12,
            gas_cost_multiplier=1.0,
            profit_threshold=0.5
        ),
        ChainId.POLYGON: ChainConfig(
            chain_id=137,
            name='Polygon',
            rpc_urls=[
                'https://polygon-mainnet.g.alchemy.com/v2/demo',
                'https://polygon.llamarpc.com',
                'https://polygon-rpc.com'
            ],
            bundler_url='https://api.pimlico.io/v2/polygon/rpc',
            paymaster_url='https://api.pimlico.io/v2/polygon/rpc',
            flash_loan_providers=['aave_v3', 'balancer'],
            avg_block_time=2,
            gas_cost_multiplier=0.01,  # ~100x cheaper
            profit_threshold=0.05
        ),
        ChainId.OPTIMISM: ChainConfig(
            chain_id=10,
            name='Optimism',
            rpc_urls=[
                'https://optimism-mainnet.g.alchemy.com/v2/demo',
                'https://op-rpc.allthatnode.com',
                'https://mainnet.optimism.io'
            ],
            bundler_url='https://api.pimlico.io/v2/optimism/rpc',
            paymaster_url='https://api.pimlico.io/v2/optimism/rpc',
            flash_loan_providers=['aave_v3', 'balancer'],
            avg_block_time=2,
            gas_cost_multiplier=0.05,
            profit_threshold=0.1
        ),
        ChainId.ARBITRUM: ChainConfig(
            chain_id=42161,
            name='Arbitrum',
            rpc_urls=[
                'https://arbitrum-mainnet.g.alchemy.com/v2/demo',
                'https://arb-rpc.allthatnode.com',
                'https://arb1.arbitrum.io/rpc'
            ],
            bundler_url='https://api.pimlico.io/v2/arbitrum/rpc',
            paymaster_url='https://api.pimlico.io/v2/arbitrum/rpc',
            flash_loan_providers=['aave_v3', 'balancer', 'uniswap_v3'],
            avg_block_time=0.25,
            gas_cost_multiplier=0.1,
            profit_threshold=0.15
        )
    }
    
    @classmethod
    def get_config(cls, chain_id: ChainId) -> ChainConfig:
        """Get configuration for chain"""
        return cls.CONFIGS.get(chain_id)
    
    @classmethod
    def get_all_chains(cls) -> List[ChainId]:
        """Get all supported chains"""
        return list(cls.CONFIGS.keys())


@dataclass
class RpcEndpoint:
    """Represents a single RPC endpoint with health status"""
    url: str
    is_healthy: bool = True
    last_checked: float = 0.0
    response_time_ms: float = 0.0
    consecutive_failures: int = 0


class ChainRpcFailover:
    """
    Manages RPC failover for a single chain
    Health checks + automatic switching to fallback
    """
    
    def __init__(self, chain_id: ChainId, rpc_urls: List[str]):
        self.chain_id = chain_id
        self.chain_name = ChainRegistry.get_config(chain_id).name
        self.endpoints = [RpcEndpoint(url=url) for url in rpc_urls]
        self.current_index = 0
        self.health_check_interval = 30  # seconds
        
        logger.info(f"RpcFailover initialized for {self.chain_name}: {len(self.endpoints)} endpoints")
    
    def get_active_endpoint(self) -> str:
        """Get currently active RPC endpoint"""
        return self.endpoints[self.current_index].url
    
    async def health_check(self) -> bool:
        """Check if current endpoint is healthy"""
        endpoint = self.endpoints[self.current_index]
        
        try:
            # Attempt simple JSON-RPC call
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint.url,
                    json={'jsonrpc': '2.0', 'method': 'eth_blockNumber', 'params': [], 'id': 1},
                    timeout=5
                ) as resp:
                    if resp.status == 200:
                        endpoint.is_healthy = True
                        endpoint.consecutive_failures = 0
                        logger.debug(f"{self.chain_name}: endpoint {self.current_index} healthy")
                        return True
                    else:
                        raise Exception(f"RPC returned {resp.status}")
        
        except Exception as e:
            logger.warning(f"{self.chain_name}: health check failed - {e}")
            endpoint.consecutive_failures += 1
            
            if endpoint.consecutive_failures >= 3:
                await self.failover()
            
            return False
    
    async def failover(self) -> None:
        """Switch to next healthy endpoint"""
        original_index = self.current_index
        
        for i in range(len(self.endpoints)):
            candidate_index = (self.current_index + 1) % len(self.endpoints)
            self.current_index = candidate_index
            candidate = self.endpoints[candidate_index]
            
            if await self.health_check():
                logger.info(
                    f"{self.chain_name}: Failover from endpoint {original_index} "
                    f"to {candidate_index}"
                )
                return
        
        logger.error(f"{self.chain_name}: All endpoints failed, using primary")
        self.current_index = 0


class MultiChainExecutor:
    """
    Manages execution across multiple chains
    Coordinates transaction submission, monitoring, and profit capture
    """
    
    def __init__(self):
        self.rpc_failovers: Dict[ChainId, ChainRpcFailover] = {}
        self.execution_history: Dict[ChainId, List[Dict]] = {}
        
        # Initialize failover for each chain
        for chain_id in ChainRegistry.get_all_chains():
            config = ChainRegistry.get_config(chain_id)
            self.rpc_failovers[chain_id] = ChainRpcFailover(chain_id, config.rpc_urls)
            self.execution_history[chain_id] = []
        
        logger.info(f"MultiChainExecutor initialized with {len(self.rpc_failovers)} chains")
    
    async def get_active_rpc(self, chain_id: ChainId) -> str:
        """Get active RPC endpoint for chain with health check"""
        failover = self.rpc_failovers[chain_id]
        
        # Check health periodically
        if not failover.endpoints[failover.current_index].is_healthy:
            await failover.health_check()
        
        return failover.get_active_endpoint()
    
    async def execute_on_chain(
        self,
        chain_id: ChainId,
        execution_plan: Dict
    ) -> Dict:
        """
        Execute arbitrage on specified chain
        Returns execution result with profit data
        """
        config = ChainRegistry.get_config(chain_id)
        rpc_url = await self.get_active_rpc(chain_id)
        
        logger.info(f"Executing on {config.name} (chain_id={chain_id.value})")
        
        try:
            # Verify profitability on this chain
            profit = execution_plan.get('estimated_profit', 0)
            gas_cost = execution_plan.get('estimated_gas', 0) * config.gas_cost_multiplier / 1e9
            
            if profit < config.profit_threshold:
                logger.warning(
                    f"Profit {profit} below threshold {config.profit_threshold} on {config.name}"
                )
                return {
                    'chain_id': chain_id.value,
                    'success': False,
                    'reason': 'profit_below_threshold'
                }
            
            # Adapt execution plan for this chain
            adapted_plan = self._adapt_execution_plan(execution_plan, chain_id)
            
            # Submit to bundler
            result = await self._submit_to_bundler(
                rpc_url,
                config,
                adapted_plan
            )
            
            # Record execution
            self.execution_history[chain_id].append(result)
            
            # Keep only last 1000 executions per chain
            if len(self.execution_history[chain_id]) > 1000:
                self.execution_history[chain_id] = self.execution_history[chain_id][-1000:]
            
            return result
        
        except Exception as e:
            logger.error(f"Execution failed on {config.name}: {e}")
            await self.rpc_failovers[chain_id].failover()
            return {
                'chain_id': chain_id.value,
                'success': False,
                'error': str(e)
            }
    
    async def execute_parallel(
        self,
        execution_plans: Dict[ChainId, Dict]
    ) -> Dict[ChainId, Dict]:
        """Execute on multiple chains in parallel"""
        tasks = [
            self.execute_on_chain(chain_id, plan)
            for chain_id, plan in execution_plans.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            chain_id: result
            for chain_id, result in zip(execution_plans.keys(), results)
        }
    
    def _adapt_execution_plan(self, plan: Dict, chain_id: ChainId) -> Dict:
        """Adapt execution plan for specific chain"""
        config = ChainRegistry.get_config(chain_id)
        adapted = plan.copy()
        
        # Adjust gas estimates
        adapted['estimated_gas'] = int(
            plan.get('estimated_gas', 400000) * 1.1  # L2s may need slightly different gas
        )
        
        # Use chain-specific flash loan providers
        adapted['flash_loan_provider'] = self._select_provider(chain_id)
        
        # Adjust slippage for L2 latency
        if chain_id != ChainId.ETHEREUM:
            adapted['slippage_tolerance'] = plan.get('slippage_tolerance', 0.001) * 1.5
        
        return adapted
    
    def _select_provider(self, chain_id: ChainId) -> str:
        """Select best flash loan provider for chain"""
        config = ChainRegistry.get_config(chain_id)
        providers = config.flash_loan_providers
        return providers[0] if providers else 'aave_v3'
    
    async def _submit_to_bundler(
        self,
        rpc_url: str,
        config: ChainConfig,
        execution_plan: Dict
    ) -> Dict:
        """Submit transaction to chain bundler"""
        # Mock submission for now
        import hashlib
        
        tx_hash = '0x' + hashlib.sha256(
            json.dumps(execution_plan).encode()
        ).hexdigest()[:40]
        
        logger.info(f"Submitted to bundler: {tx_hash}")
        
        return {
            'chain_id': config.chain_id,
            'tx_hash': tx_hash,
            'success': True,
            'profit': execution_plan.get('estimated_profit', 0),
            'gas_cost': execution_plan.get('estimated_gas', 0) * config.gas_cost_multiplier,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def get_chain_stats(self, chain_id: ChainId) -> Dict:
        """Get execution statistics for chain"""
        history = self.execution_history.get(chain_id, [])
        
        if not history:
            return {
                'chain_id': chain_id.value,
                'chain_name': ChainRegistry.get_config(chain_id).name,
                'executions': 0,
                'success_rate': 0.0,
                'total_profit': 0.0
            }
        
        successful = [h for h in history if h.get('success', False)]
        total_profit = sum(h.get('profit', 0) for h in successful)
        
        return {
            'chain_id': chain_id.value,
            'chain_name': ChainRegistry.get_config(chain_id).name,
            'executions': len(history),
            'successful': len(successful),
            'success_rate': len(successful) / len(history) if history else 0.0,
            'total_profit': round(total_profit, 4),
            'avg_profit_per_tx': round(total_profit / len(successful), 4) if successful else 0.0
        }
    
    async def get_all_stats(self) -> Dict:
        """Get execution statistics across all chains"""
        stats = {}
        total_profit = 0.0
        total_executions = 0
        
        for chain_id in ChainRegistry.get_all_chains():
            chain_stats = await self.get_chain_stats(chain_id)
            stats[chain_id.name.lower()] = chain_stats
            total_profit += chain_stats.get('total_profit', 0)
            total_executions += chain_stats.get('executions', 0)
        
        return {
            'total_executions': total_executions,
            'total_profit': round(total_profit, 4),
            'chains': stats
        }
