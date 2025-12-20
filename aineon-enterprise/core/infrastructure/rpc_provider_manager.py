"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON RPC PROVIDER FAILOVER SYSTEM                        ║
║              Enterprise-Grade Multi-Provider Redundancy                        ║
║                                                                                ║
║  Purpose: Ensure 99.99% uptime with automatic provider failover               ║
║  Providers: Alchemy, Infura, QuickNode, Ankr, Parity                          ║
║  Latency Target: <100ms p99                                                   ║
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
from datetime import datetime, timedelta
from collections import deque
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider health status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    OFFLINE = "OFFLINE"


@dataclass
class ProviderMetrics:
    """Track provider performance"""
    provider_name: str
    success_count: int = 0
    failure_count: int = 0
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    last_health_check: Optional[datetime] = None
    status: ProviderStatus = ProviderStatus.HEALTHY
    uptime_pct: float = 100.0
    avg_latency_ms: float = 0.0
    error_message: str = ""
    consecutive_failures: int = 0


@dataclass
class RPCResponse:
    """Standardized RPC response"""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    provider_used: str = ""
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class RPCProvider:
    """Individual RPC provider with health tracking"""
    
    def __init__(self, name: str, url: str, api_key: str = ""):
        self.name = name
        self.base_url = url
        self.api_key = api_key
        self.metrics = ProviderMetrics(provider_name=name)
        self.is_available = True
        self.priority = 0  # Higher = preferred
    
    async def call(self, method: str, params: List = None) -> Tuple[bool, Any, float]:
        """Make RPC call with latency tracking"""
        start_time = time.time()
        params = params or []
        
        try:
            url = self.base_url
            if self.api_key:
                url = f"{url}?apikey={self.api_key}" if "?" not in url else f"{url}&apikey={self.api_key}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": int(time.time() * 1000)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    latency = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'result' in data:
                            self.metrics.success_count += 1
                            self.metrics.consecutive_failures = 0
                            self.metrics.latency_samples.append(latency)
                            self.metrics.avg_latency_ms = sum(self.metrics.latency_samples) / len(self.metrics.latency_samples)
                            return True, data['result'], latency
                        elif 'error' in data:
                            error_msg = data['error'].get('message', 'Unknown error')
                            self.metrics.failure_count += 1
                            self.metrics.consecutive_failures += 1
                            self.metrics.error_message = error_msg
                            return False, None, latency
        except asyncio.TimeoutError:
            latency = (time.time() - start_time) * 1000
            self.metrics.failure_count += 1
            self.metrics.consecutive_failures += 1
            self.metrics.error_message = "Timeout"
            return False, None, latency
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.metrics.failure_count += 1
            self.metrics.consecutive_failures += 1
            self.metrics.error_message = str(e)
            return False, None, latency
        
        return False, None, (time.time() - start_time) * 1000
    
    def update_status(self):
        """Update provider status based on recent performance"""
        total_calls = self.metrics.success_count + self.metrics.failure_count
        
        if total_calls == 0:
            self.metrics.status = ProviderStatus.HEALTHY
            return
        
        success_rate = self.metrics.success_count / total_calls
        self.metrics.uptime_pct = success_rate * 100
        
        # Status logic
        if self.metrics.consecutive_failures > 10:
            self.metrics.status = ProviderStatus.OFFLINE
            self.is_available = False
        elif success_rate < 0.7:
            self.metrics.status = ProviderStatus.UNHEALTHY
            self.is_available = False
        elif success_rate < 0.9:
            self.metrics.status = ProviderStatus.DEGRADED
            self.is_available = True
        else:
            self.metrics.status = ProviderStatus.HEALTHY
            self.is_available = True
        
        # Auto-recovery: reset failure count after 5 minutes of not being called
        if self.metrics.last_health_check:
            time_since_check = datetime.now() - self.metrics.last_health_check
            if time_since_check.total_seconds() > 300:
                self.metrics.consecutive_failures = max(0, self.metrics.consecutive_failures - 2)
        
        self.metrics.last_health_check = datetime.now()


class RPCProviderManager:
    """Enterprise RPC provider management with automatic failover"""
    
    def __init__(self):
        self.providers: List[RPCProvider] = []
        self.active_provider_index = 0
        self.call_history: deque = deque(maxlen=1000)
        self.health_check_interval = 30  # seconds
        self.last_health_check = time.time()
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "provider_switches": 0,
            "avg_latency_ms": 0.0,
            "uptime_pct": 99.9
        }
        logger.info("[RPC] Provider manager initialized")
    
    def register_provider(self, name: str, url: str, api_key: str = "", priority: int = 0):
        """Register RPC provider"""
        provider = RPCProvider(name, url, api_key)
        provider.priority = priority
        self.providers.append(provider)
        # Sort by priority (higher first)
        self.providers.sort(key=lambda p: p.priority, reverse=True)
        logger.info(f"[RPC] Registered provider: {name} (priority: {priority})")
    
    async def call(self, method: str, params: List = None) -> RPCResponse:
        """Make RPC call with automatic failover"""
        params = params or []
        start_time = time.time()
        
        # Periodic health check
        if time.time() - self.last_health_check > self.health_check_interval:
            await self._health_check_all_providers()
        
        # Find best available provider
        available_providers = [p for p in self.providers if p.is_available]
        
        if not available_providers:
            logger.error("[RPC] No available providers! Attempting with degraded providers...")
            available_providers = self.providers  # Fall back to all providers
        
        # Try providers in order
        last_error = None
        for provider in available_providers:
            success, result, latency = await provider.call(method, params)
            
            if success:
                self.stats["total_calls"] += 1
                self.stats["successful_calls"] += 1
                self.stats["avg_latency_ms"] = (self.stats["avg_latency_ms"] * (self.stats["successful_calls"] - 1) + latency) / self.stats["successful_calls"]
                
                self.call_history.append({
                    "provider": provider.name,
                    "method": method,
                    "success": True,
                    "latency_ms": latency,
                    "timestamp": time.time()
                })
                
                logger.debug(f"[RPC] ✓ {provider.name}: {method} ({latency:.1f}ms)")
                
                return RPCResponse(
                    success=True,
                    result=result,
                    provider_used=provider.name,
                    latency_ms=latency
                )
            else:
                last_error = provider.metrics.error_message
                logger.warning(f"[RPC] ✗ {provider.name}: {method} failed - {last_error}")
                provider.update_status()
        
        # All providers failed
        self.stats["total_calls"] += 1
        self.stats["failed_calls"] += 1
        
        self.call_history.append({
            "provider": "NONE",
            "method": method,
            "success": False,
            "error": last_error,
            "timestamp": time.time()
        })
        
        logger.error(f"[RPC] ✗ All providers failed for {method}: {last_error}")
        
        return RPCResponse(
            success=False,
            error=f"All providers failed: {last_error}",
            provider_used="NONE"
        )
    
    async def _health_check_all_providers(self):
        """Periodic health check of all providers"""
        logger.info("[RPC] Running health checks on all providers...")
        
        health_check_tasks = [
            self._health_check_provider(provider)
            for provider in self.providers
        ]
        
        await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        self.last_health_check = time.time()
        
        # Log health status
        for provider in self.providers:
            logger.info(f"[RPC] {provider.name}: {provider.metrics.status.value} "
                       f"({provider.metrics.uptime_pct:.1f}% uptime, "
                       f"{provider.metrics.avg_latency_ms:.1f}ms latency)")
    
    async def _health_check_provider(self, provider: RPCProvider):
        """Health check single provider"""
        success, _, _ = await provider.call("eth_chainId", [])
        provider.update_status()
    
    def get_stats(self) -> Dict:
        """Get RPC manager statistics"""
        total_calls = self.stats["successful_calls"] + self.stats["failed_calls"]
        uptime = (self.stats["successful_calls"] / total_calls * 100) if total_calls > 0 else 100
        
        return {
            "total_calls": self.stats["total_calls"],
            "successful_calls": self.stats["successful_calls"],
            "failed_calls": self.stats["failed_calls"],
            "success_rate": f"{(self.stats['successful_calls'] / total_calls * 100):.2f}%" if total_calls > 0 else "0%",
            "avg_latency_ms": f"{self.stats['avg_latency_ms']:.2f}",
            "uptime_pct": f"{uptime:.2f}%",
            "providers": [
                {
                    "name": p.name,
                    "status": p.metrics.status.value,
                    "uptime": f"{p.metrics.uptime_pct:.1f}%",
                    "latency_ms": f"{p.metrics.avg_latency_ms:.1f}",
                    "success_count": p.metrics.success_count,
                    "failure_count": p.metrics.failure_count
                }
                for p in self.providers
            ]
        }
    
    async def ensure_provider_health(self):
        """Continuous provider health monitoring (run as background task)"""
        logger.info("[RPC] Starting continuous provider health monitoring...")
        
        while True:
            try:
                await self._health_check_all_providers()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"[RPC] Health check error: {e}")
                await asyncio.sleep(10)


# Singleton instance
_rpc_manager: Optional[RPCProviderManager] = None


def get_rpc_manager() -> RPCProviderManager:
    """Get singleton RPC manager instance"""
    global _rpc_manager
    if _rpc_manager is None:
        _rpc_manager = RPCProviderManager()
        
        # Register default providers
        import os
        
        # High priority providers (fastest/most reliable)
        if os.getenv("ALCHEMY_API_KEY"):
            _rpc_manager.register_provider(
                "Alchemy",
                "https://eth-mainnet.g.alchemy.com/v2",
                os.getenv("ALCHEMY_API_KEY"),
                priority=100
            )
        
        if os.getenv("INFURA_API_KEY"):
            _rpc_manager.register_provider(
                "Infura",
                "https://mainnet.infura.io/v3",
                os.getenv("INFURA_API_KEY"),
                priority=90
            )
        
        # Medium priority providers
        if os.getenv("QUICKNODE_API_KEY"):
            _rpc_manager.register_provider(
                "QuickNode",
                "https://mainnet.quicknode.pro",
                os.getenv("QUICKNODE_API_KEY"),
                priority=80
            )
        
        if os.getenv("ANKR_API_KEY"):
            _rpc_manager.register_provider(
                "Ankr",
                "https://rpc.ankr.com/eth",
                os.getenv("ANKR_API_KEY"),
                priority=70
            )
        
        # Low priority fallback
        _rpc_manager.register_provider(
            "Public RPC",
            "https://eth.public-rpc.com",
            "",
            priority=50
        )
    
    return _rpc_manager


if __name__ == "__main__":
    async def test_rpc():
        manager = get_rpc_manager()
        
        # Test call
        response = await manager.call("eth_chainId", [])
        print(f"Chain ID: {response.result}")
        print(f"Provider used: {response.provider_used}")
        print(f"Latency: {response.latency_ms:.2f}ms")
        
        # Get stats
        print("\nProvider Statistics:")
        print(json.dumps(manager.get_stats(), indent=2))
    
    asyncio.run(test_rpc())
