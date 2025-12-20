import asyncio
import time
import logging
from typing import Dict, List, Optional
from web3 import Web3
from collections import defaultdict

logger = logging.getLogger(__name__)

class RPCProviderConfig:
    def __init__(self):
        self.providers = [
            {
                "name": "Alchemy",
                "url": "${ETH_RPC_URL_ALCHEMY}",
                "priority": 1,
                "rate_limit": 3000,
            },
            {
                "name": "Infura",
                "url": "${ETH_RPC_URL_INFURA}",
                "priority": 2,
                "rate_limit": 100,
            },
            {
                "name": "Ankr",
                "url": "https://rpc.ankr.com/eth",
                "priority": 3,
                "rate_limit": 50,
            },
            {
                "name": "QuickNode",
                "url": "${ETH_RPC_URL_QUICKNODE}",
                "priority": 4,
                "rate_limit": 250,
            },
            {
                "name": "Parity",
                "url": "https://rpc.parity.mainnet.eth",
                "priority": 5,
                "rate_limit": 30,
            },
        ]

class ProviderHealth:
    def __init__(self, name: str):
        self.name = name
        self.healthy = True
        self.latency_ms = 0
        self.error_count = 0
        self.success_count = 0
        self.last_check = 0
        self.consecutive_failures = 0

class RPCProviderManager:
    def __init__(self):
        self.config = RPCProviderConfig()
        self.health = {p["name"]: ProviderHealth(p["name"]) for p in self.config.providers}
        self.current_provider_index = 0
        self.request_counts = defaultdict(int)
        self.health_check_interval = 30  # seconds
        self.failover_timeout = 5  # seconds
    
    async def initialize(self):
        """Start health check loop on initialization"""
        asyncio.create_task(self.health_check_loop())
    
    async def health_check_loop(self):
        """Continuously monitor all RPC providers"""
        while True:
            try:
                await self.check_all_providers()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def check_all_providers(self):
        """Health check all RPC providers in parallel"""
        tasks = [self.health_check_provider(p) for p in self.config.providers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def health_check_provider(self, provider: Dict):
        """Check single provider latency and availability"""
        name = provider["name"]
        try:
            start_ns = time.perf_counter_ns()
            w3 = Web3(Web3.HTTPProvider(provider["url"], request_kwargs={"timeout": 5}))
            
            # Simple RPC call (eth_blockNumber)
            await asyncio.to_thread(w3.eth.block_number)
            
            latency_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            
            # Update health metrics
            self.health[name].healthy = latency_ms < 500
            self.health[name].latency_ms = latency_ms
            self.health[name].success_count += 1
            self.health[name].consecutive_failures = 0
            self.health[name].last_check = time.time()
            
            logger.debug(f"{name}: {latency_ms:.2f}ms - OK")
            
        except Exception as e:
            self.health[name].error_count += 1
            self.health[name].consecutive_failures += 1
            
            # Mark unhealthy after 3 consecutive failures
            if self.health[name].consecutive_failures >= 3:
                self.health[name].healthy = False
            
            logger.warning(f"{name}: FAILED - {str(e)[:50]}")
    
    async def get_best_provider(self) -> Web3:
        """Return Web3 instance for healthiest provider"""
        # Get all healthy providers sorted by latency
        healthy = [
            (p, self.health[p["name"]])
            for p in self.config.providers
            if self.health[p["name"]].healthy
        ]
        
        if not healthy:
            # Fallback to any provider (degraded mode)
            logger.warning("All providers unhealthy, using fallback")
            healthy = [(p, self.health[p["name"]]) for p in self.config.providers]
        
        # Sort by latency
        healthy.sort(key=lambda x: x[1].latency_ms)
        best_provider = healthy[0][0]
        
        return Web3(Web3.HTTPProvider(best_provider["url"]))
    
    async def execute_with_failover(self, method_name: str, *args, **kwargs):
        """Execute RPC method with automatic failover"""
        last_error = None
        
        for attempt in range(5):  # Try up to 5 providers
            try:
                w3 = await self.get_best_provider()
                method = getattr(w3.eth, method_name)
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    asyncio.to_thread(method, *args, **kwargs),
                    timeout=self.failover_timeout
                )
                return result
                
            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(f"RPC timeout (attempt {attempt + 1}/5)")
                if attempt < 4:
                    await asyncio.sleep(0.1 * (2 ** attempt))  # Exponential backoff
                    
            except Exception as e:
                last_error = e
                logger.error(f"RPC error: {str(e)[:100]}")
                if attempt < 4:
                    await asyncio.sleep(0.05)
        
        # All attempts failed
        raise Exception(f"RPC failover exhausted: {last_error}")
    
    def get_health_report(self) -> Dict:
        """Get current health status of all providers"""
        return {
            name: {
                "healthy": health.healthy,
                "latency_ms": health.latency_ms,
                "success_count": health.success_count,
                "error_count": health.error_count,
            }
            for name, health in self.health.items()
        }
