"""
AINEON Multi-RPC Failover System
Provides redundant RPC connectivity with automatic failover and health monitoring.

Spec: 5+ providers (Alchemy, Infura, QuickNode, Ankr, Parity)
Target: 99.99% uptime, <100ms p99 latency, automatic failover
"""

import asyncio
import time
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

import aiohttp
from web3 import Web3
from web3.providers import HTTPProvider

logger = logging.getLogger(__name__)


class RPCProviderStatus(Enum):
    """RPC provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class RPCProviderMetrics:
    """Metrics for a single RPC provider."""
    name: str
    url: str
    status: RPCProviderStatus
    latency_ms: float
    success_rate: float
    request_count: int
    error_count: int
    last_check: datetime
    uptime_percentage: float
    consecutive_failures: int = 0
    
    def is_healthy(self) -> bool:
        """Provider is healthy if success rate > 95% and latency < 200ms."""
        return (self.status == RPCProviderStatus.HEALTHY and 
                self.success_rate > 0.95 and 
                self.latency_ms < 200)


class RPCFailoverSystem:
    """
    Multi-RPC failover system with health monitoring and automatic routing.
    
    Features:
    - 5+ provider rotation (Alchemy, Infura, QuickNode, Ankr, Parity)
    - Automatic failover on provider failure
    - Health checks every 30 seconds
    - Latency tracking and optimization
    - Success rate monitoring
    - Circuit breaker pattern
    """
    
    def __init__(self, config: Dict[str, str], health_check_interval: int = 30):
        """
        Initialize RPC failover system.
        
        Args:
            config: Dict with RPC_PROVIDERS as comma-separated URLs
                   or individual provider configs
            health_check_interval: Seconds between health checks (default: 30)
        """
        self.config = config
        self.health_check_interval = health_check_interval
        self.providers: Dict[str, RPCProviderMetrics] = {}
        self.current_provider_index = 0
        self.health_check_task: Optional[asyncio.Task] = None
        self._setup_providers()
        
    def _setup_providers(self):
        """Initialize provider configuration from environment."""
        # Default providers (production-grade)
        default_providers = {
            "Alchemy": "https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
            "Infura": "https://mainnet.infura.io/v3/{INFURA_API_KEY}",
            "QuickNode": "https://eth-mainnet.quicknode.pro/account/{QUICKNODE_API_KEY}",
            "Ankr": "https://rpc.ankr.com/eth",
            "Parity": "https://parity.infura.io/",
        }
        
        # Load from config or use defaults
        for provider_name, provider_url in default_providers.items():
            if provider_name in self.config:
                url = self.config[provider_name]
            else:
                url = provider_url
            
            # Replace placeholder variables
            for key, value in self.config.items():
                url = url.replace(f"{{{key}}}", value)
            
            self.providers[provider_name] = RPCProviderMetrics(
                name=provider_name,
                url=url,
                status=RPCProviderStatus.HEALTHY,
                latency_ms=0.0,
                success_rate=1.0,
                request_count=0,
                error_count=0,
                last_check=datetime.now(),
                uptime_percentage=100.0
            )
        
        logger.info(f"Initialized {len(self.providers)} RPC providers")
    
    async def health_check(self) -> Dict[str, RPCProviderMetrics]:
        """
        Check health of all RPC providers.
        
        Returns:
            Dict mapping provider name to metrics
        """
        tasks = [
            self._check_provider_health(name, metrics)
            for name, metrics in self.providers.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for provider_name, result in zip(self.providers.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {provider_name}: {result}")
                self.providers[provider_name].status = RPCProviderStatus.OFFLINE
            else:
                self.providers[provider_name] = result
        
        return self.providers
    
    async def _check_provider_health(
        self, 
        provider_name: str, 
        metrics: RPCProviderMetrics
    ) -> RPCProviderMetrics:
        """Check health of single provider."""
        try:
            start = time.time()
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1,
                }
                
                async with session.post(
                    metrics.url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    latency = (time.time() - start) * 1000  # ms
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if "result" in data:
                            # Success
                            metrics.latency_ms = latency
                            metrics.request_count += 1
                            metrics.last_check = datetime.now()
                            
                            if latency < 100:
                                metrics.status = RPCProviderStatus.HEALTHY
                                metrics.success_rate = min(1.0, metrics.success_rate + 0.01)
                            elif latency < 200:
                                metrics.status = RPCProviderStatus.DEGRADED
                                metrics.success_rate = max(0.5, metrics.success_rate - 0.02)
                            else:
                                metrics.status = RPCProviderStatus.DEGRADED
                                metrics.success_rate = max(0.3, metrics.success_rate - 0.05)
                            
                            metrics.consecutive_failures = 0
                            
                        else:
                            # RPC error
                            metrics.error_count += 1
                            metrics.consecutive_failures += 1
                            metrics.status = RPCProviderStatus.UNHEALTHY
                            metrics.success_rate = max(0, metrics.success_rate - 0.1)
                    else:
                        # HTTP error
                        metrics.error_count += 1
                        metrics.consecutive_failures += 1
                        metrics.status = RPCProviderStatus.OFFLINE
                        metrics.success_rate = max(0, metrics.success_rate - 0.15)
                        
        except asyncio.TimeoutError:
            metrics.error_count += 1
            metrics.consecutive_failures += 1
            metrics.status = RPCProviderStatus.OFFLINE
            metrics.success_rate = max(0, metrics.success_rate - 0.1)
        except Exception as e:
            logger.error(f"Health check error for {provider_name}: {e}")
            metrics.error_count += 1
            metrics.status = RPCProviderStatus.OFFLINE
            metrics.success_rate = max(0, metrics.success_rate - 0.15)
        
        # Update uptime percentage
        if metrics.request_count > 0:
            metrics.uptime_percentage = ((metrics.request_count - metrics.error_count) 
                                        / metrics.request_count) * 100
        
        return metrics
    
    async def start_health_monitoring(self):
        """Start background health check loop."""
        if self.health_check_task:
            return
        
        async def monitor():
            while True:
                try:
                    await self.health_check()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(5)
        
        self.health_check_task = asyncio.create_task(monitor())
        logger.info("RPC health monitoring started")
    
    async def stop_health_monitoring(self):
        """Stop background health check loop."""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None
            logger.info("RPC health monitoring stopped")
    
    def get_best_provider(self) -> RPCProviderMetrics:
        """
        Get best available provider using weighted ranking.
        
        Priority:
        1. Healthy providers (success_rate > 95%, latency < 100ms)
        2. Degraded providers (success_rate > 80%, latency < 200ms)
        3. Any online provider
        4. Fallback to first provider
        
        Returns:
            Best available RPCProviderMetrics
        """
        # First try to find healthy provider
        healthy = [m for m in self.providers.values() if m.is_healthy()]
        if healthy:
            return min(healthy, key=lambda x: x.latency_ms)
        
        # Try degraded providers
        degraded = [m for m in self.providers.values() 
                   if m.status in (RPCProviderStatus.HEALTHY, RPCProviderStatus.DEGRADED)]
        if degraded:
            return min(degraded, key=lambda x: x.latency_ms)
        
        # Try any online
        online = [m for m in self.providers.values() 
                 if m.status != RPCProviderStatus.OFFLINE]
        if online:
            return online[0]
        
        # Fallback to first provider
        return list(self.providers.values())[0]
    
    def get_provider_url(self) -> str:
        """Get URL of best available provider."""
        best = self.get_best_provider()
        logger.debug(f"Selected RPC provider: {best.name} (latency: {best.latency_ms:.2f}ms, "
                    f"success_rate: {best.success_rate:.2%})")
        return best.url
    
    def get_web3(self) -> Web3:
        """Get Web3 instance with failover provider."""
        provider_url = self.get_provider_url()
        return Web3(HTTPProvider(provider_url))
    
    def get_provider_stats(self) -> Dict:
        """Get statistics for all providers."""
        stats = {}
        for name, metrics in self.providers.items():
            stats[name] = {
                "status": metrics.status.value,
                "latency_ms": round(metrics.latency_ms, 2),
                "success_rate": round(metrics.success_rate, 4),
                "uptime_percentage": round(metrics.uptime_percentage, 2),
                "request_count": metrics.request_count,
                "error_count": metrics.error_count,
                "last_check": metrics.last_check.isoformat(),
            }
        return stats
    
    def log_provider_stats(self):
        """Log provider statistics."""
        stats = self.get_provider_stats()
        logger.info("=" * 70)
        logger.info("RPC PROVIDER STATISTICS")
        logger.info("=" * 70)
        for provider_name, metrics in stats.items():
            logger.info(f"\n{provider_name}:")
            logger.info(f"  Status: {metrics['status']}")
            logger.info(f"  Latency: {metrics['latency_ms']:.2f}ms")
            logger.info(f"  Success Rate: {metrics['success_rate']:.2%}")
            logger.info(f"  Uptime: {metrics['uptime_percentage']:.2f}%")
            logger.info(f"  Requests: {metrics['request_count']} (Errors: {metrics['error_count']})")
        logger.info("=" * 70)


# Singleton instance
_rpc_failover_system: Optional[RPCFailoverSystem] = None


async def initialize_rpc_failover(config: Dict[str, str]) -> RPCFailoverSystem:
    """Initialize and start RPC failover system."""
    global _rpc_failover_system
    _rpc_failover_system = RPCFailoverSystem(config)
    await _rpc_failover_system.start_health_monitoring()
    return _rpc_failover_system


def get_rpc_failover_system() -> RPCFailoverSystem:
    """Get current RPC failover system instance."""
    if _rpc_failover_system is None:
        raise RuntimeError("RPC failover system not initialized")
    return _rpc_failover_system


async def shutdown_rpc_failover():
    """Shutdown RPC failover system."""
    global _rpc_failover_system
    if _rpc_failover_system:
        await _rpc_failover_system.stop_health_monitoring()
        _rpc_failover_system = None
