"""
DEX Adapter Factory - Extensible DEX Integration Pattern
Abstract interface for DEX interactions with plugin architecture
"""

import os
import logging
from typing import Dict, Any, Optional, List, Protocol, Type
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class DEXType(Enum):
    """DEX types"""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    UNISWAP_V4 = "uniswap_v4"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"
    AAVE = "aave"
    DYDX = "dydx"


@dataclass
class SwapQuote:
    """Quote for a swap"""
    dex: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    price: float
    slippage_bps: float
    path: List[str]
    gas_estimate: int
    execution_time_ms: float
    liquidity: float


@dataclass
class LiquidityPool:
    """DEX liquidity pool information"""
    pool_id: str
    dex: str
    token0: str
    token1: str
    reserve0: float
    reserve1: float
    fee_tier: Optional[float] = None
    tvl_usd: float = 0.0
    volume_24h: float = 0.0
    apy: float = 0.0


@dataclass
class DEXMetrics:
    """Metrics for a DEX connection"""
    dex: str
    last_update: datetime
    pools_tracked: int
    total_liquidity: float
    request_count: int
    error_count: int
    average_latency_ms: float


class DEXAdapter(ABC):
    """Abstract base class for DEX adapters"""
    
    def __init__(self, dex_type: DEXType):
        self.dex_type = dex_type
        self.connected = False
        self.metrics = DEXMetrics(
            dex=dex_type.value,
            last_update=datetime.utcnow(),
            pools_tracked=0,
            total_liquidity=0.0,
            request_count=0,
            error_count=0,
            average_latency_ms=0.0,
        )
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to DEX"""
        pass
    
    @abstractmethod
    async def get_quote(self, token_in: str, token_out: str, amount_in: float) -> Optional[SwapQuote]:
        """Get swap quote"""
        pass
    
    @abstractmethod
    async def get_liquidity(self, token0: str, token1: str) -> Optional[float]:
        """Get liquidity for pair"""
        pass
    
    @abstractmethod
    async def get_pools(self, token0: str, token1: str) -> List[LiquidityPool]:
        """Get pools for token pair"""
        pass
    
    @abstractmethod
    async def execute_swap(self, token_in: str, token_out: str, amount_in: float,
                          min_amount_out: float) -> Optional[Dict]:
        """Execute a swap (on mainnet)"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from DEX"""
        pass
    
    async def record_metric(self, latency_ms: float, success: bool = True):
        """Record request metric"""
        self.metrics.request_count += 1
        if not success:
            self.metrics.error_count += 1
        
        # Update average latency
        current_avg = self.metrics.average_latency_ms
        new_avg = (current_avg * (self.metrics.request_count - 1) + latency_ms) / self.metrics.request_count
        self.metrics.average_latency_ms = new_avg
        self.metrics.last_update = datetime.utcnow()


class UniswapV2Adapter(DEXAdapter):
    """Uniswap V2 adapter"""
    
    def __init__(self):
        super().__init__(DEXType.UNISWAP_V2)
        self.router_address = os.getenv('UNISWAP_V2_ROUTER', '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')
        self.factory_address = os.getenv('UNISWAP_V2_FACTORY', '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')
    
    async def connect(self) -> bool:
        self.connected = True
        logger.info("Connected to Uniswap V2")
        return True
    
    async def get_quote(self, token_in: str, token_out: str, amount_in: float) -> Optional[SwapQuote]:
        try:
            # Simplified quote calculation
            quote = SwapQuote(
                dex=self.dex_type.value,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out=amount_in * 0.998,  # 0.2% fee
                price=0.998,
                slippage_bps=20,
                path=[token_in, token_out],
                gas_estimate=150000,
                execution_time_ms=5.0,
                liquidity=1000000.0,
            )
            return quote
        except Exception as e:
            logger.error(f"Quote error: {e}")
            return None
    
    async def get_liquidity(self, token0: str, token1: str) -> Optional[float]:
        try:
            return 1000000.0
        except Exception:
            return None
    
    async def get_pools(self, token0: str, token1: str) -> List[LiquidityPool]:
        try:
            return [
                LiquidityPool(
                    pool_id=f"{token0}-{token1}",
                    dex=self.dex_type.value,
                    token0=token0,
                    token1=token1,
                    reserve0=1000000.0,
                    reserve1=1000000.0,
                    tvl_usd=2000000.0,
                )
            ]
        except Exception:
            return []
    
    async def execute_swap(self, token_in: str, token_out: str, amount_in: float,
                          min_amount_out: float) -> Optional[Dict]:
        try:
            return {
                'tx_hash': '0x...',
                'amount_out': amount_in * 0.998,
                'status': 'success',
            }
        except Exception:
            return None
    
    async def disconnect(self):
        self.connected = False
        logger.info("Disconnected from Uniswap V2")


class CurveAdapter(DEXAdapter):
    """Curve Finance adapter"""
    
    def __init__(self):
        super().__init__(DEXType.CURVE)
    
    async def connect(self) -> bool:
        self.connected = True
        logger.info("Connected to Curve")
        return True
    
    async def get_quote(self, token_in: str, token_out: str, amount_in: float) -> Optional[SwapQuote]:
        try:
            quote = SwapQuote(
                dex=self.dex_type.value,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out=amount_in * 0.9995,  # 0.05% fee for stablecoins
                price=0.9995,
                slippage_bps=5,
                path=[token_in, token_out],
                gas_estimate=200000,
                execution_time_ms=8.0,
                liquidity=5000000.0,
            )
            return quote
        except Exception:
            return None
    
    async def get_liquidity(self, token0: str, token1: str) -> Optional[float]:
        return 5000000.0
    
    async def get_pools(self, token0: str, token1: str) -> List[LiquidityPool]:
        return [
            LiquidityPool(
                pool_id=f"curve_{token0}_{token1}",
                dex=self.dex_type.value,
                token0=token0,
                token1=token1,
                reserve0=2500000.0,
                reserve1=2500000.0,
                fee_tier=0.04,
                tvl_usd=5000000.0,
            )
        ]
    
    async def execute_swap(self, token_in: str, token_out: str, amount_in: float,
                          min_amount_out: float) -> Optional[Dict]:
        return {
            'tx_hash': '0x...',
            'amount_out': amount_in * 0.9995,
            'status': 'success',
        }
    
    async def disconnect(self):
        self.connected = False


class BalancerAdapter(DEXAdapter):
    """Balancer adapter"""
    
    def __init__(self):
        super().__init__(DEXType.BALANCER)
    
    async def connect(self) -> bool:
        self.connected = True
        logger.info("Connected to Balancer")
        return True
    
    async def get_quote(self, token_in: str, token_out: str, amount_in: float) -> Optional[SwapQuote]:
        quote = SwapQuote(
            dex=self.dex_type.value,
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            amount_out=amount_in * 0.997,  # 0.3% fee
            price=0.997,
            slippage_bps=30,
            path=[token_in, token_out],
            gas_estimate=250000,
            execution_time_ms=10.0,
            liquidity=3000000.0,
        )
        return quote
    
    async def get_liquidity(self, token0: str, token1: str) -> Optional[float]:
        return 3000000.0
    
    async def get_pools(self, token0: str, token1: str) -> List[LiquidityPool]:
        return [
            LiquidityPool(
                pool_id=f"balancer_{token0}_{token1}",
                dex=self.dex_type.value,
                token0=token0,
                token1=token1,
                reserve0=1500000.0,
                reserve1=1500000.0,
                fee_tier=0.30,
                tvl_usd=3000000.0,
            )
        ]
    
    async def execute_swap(self, token_in: str, token_out: str, amount_in: float,
                          min_amount_out: float) -> Optional[Dict]:
        return {'tx_hash': '0x...', 'amount_out': amount_in * 0.997, 'status': 'success'}
    
    async def disconnect(self):
        self.connected = False


class DEXAdapterFactory:
    """Factory for creating and managing DEX adapters"""
    
    def __init__(self):
        self.adapters: Dict[DEXType, DEXAdapter] = {}
        self.adapter_classes: Dict[DEXType, Type[DEXAdapter]] = {
            DEXType.UNISWAP_V2: UniswapV2Adapter,
            DEXType.CURVE: CurveAdapter,
            DEXType.BALANCER: BalancerAdapter,
        }
    
    async def create_adapter(self, dex_type: DEXType) -> Optional[DEXAdapter]:
        """Create and connect to a DEX adapter"""
        try:
            if dex_type in self.adapters:
                return self.adapters[dex_type]
            
            if dex_type not in self.adapter_classes:
                logger.error(f"Unsupported DEX type: {dex_type}")
                return None
            
            adapter_class = self.adapter_classes[dex_type]
            adapter = adapter_class()
            
            if await adapter.connect():
                self.adapters[dex_type] = adapter
                logger.info(f"Adapter created: {dex_type.value}")
                return adapter
            else:
                logger.error(f"Failed to connect to {dex_type.value}")
                return None
            
        except Exception as e:
            logger.error(f"Adapter creation error: {e}")
            return None
    
    async def get_best_quote(self, token_in: str, token_out: str, amount_in: float,
                            dex_types: Optional[List[DEXType]] = None) -> Optional[SwapQuote]:
        """Get best quote across multiple DEXes"""
        try:
            if dex_types is None:
                dex_types = list(self.adapter_classes.keys())
            
            best_quote = None
            best_amount_out = 0.0
            
            for dex_type in dex_types:
                adapter = await self.create_adapter(dex_type)
                if not adapter:
                    continue
                
                quote = await adapter.get_quote(token_in, token_out, amount_in)
                if quote and quote.amount_out > best_amount_out:
                    best_amount_out = quote.amount_out
                    best_quote = quote
            
            return best_quote
            
        except Exception as e:
            logger.error(f"Quote aggregation error: {e}")
            return None
    
    async def get_total_liquidity(self, token0: str, token1: str) -> float:
        """Get total liquidity across all DEXes"""
        total = 0.0
        
        for adapter in self.adapters.values():
            liquidity = await adapter.get_liquidity(token0, token1)
            if liquidity:
                total += liquidity
        
        return total
    
    def register_adapter(self, dex_type: DEXType, adapter_class: Type[DEXAdapter]):
        """Register custom adapter"""
        self.adapter_classes[dex_type] = adapter_class
        logger.info(f"Adapter registered: {dex_type.value}")
    
    async def disconnect_all(self):
        """Disconnect all adapters"""
        for adapter in self.adapters.values():
            await adapter.disconnect()
        self.adapters.clear()
    
    def get_factory_status(self) -> Dict[str, Any]:
        """Get factory status"""
        return {
            'connected_dexes': len(self.adapters),
            'available_dexes': len(self.adapter_classes),
            'adapters': {
                name: {
                    'connected': adapter.connected,
                    'metrics': {
                        'request_count': adapter.metrics.request_count,
                        'error_count': adapter.metrics.error_count,
                        'avg_latency_ms': adapter.metrics.average_latency_ms,
                    }
                }
                for name, adapter in self.adapters.items()
            },
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global instance
_factory: Optional[DEXAdapterFactory] = None


async def init_dex_adapter_factory() -> DEXAdapterFactory:
    """Initialize global factory"""
    global _factory
    _factory = DEXAdapterFactory()
    return _factory


async def get_dex_factory() -> DEXAdapterFactory:
    """Get global factory"""
    global _factory
    if not _factory:
        _factory = await init_dex_adapter_factory()
    return _factory
