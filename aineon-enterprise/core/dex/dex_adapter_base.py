"""
AINEON DEX Adapter Base
Abstract base class for DEX integration with unified interface.

Spec: Multi-DEX support (Uniswap V3/V2, Curve, Balancer, SushiSwap, DODO, Pancake, QuickSwap)
Target: Sub-100ms quote retrieval, <300ms calldata generation, 99%+ reliability
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DEXType(Enum):
    """DEX types."""
    UNISWAP_V3 = "uniswap_v3"
    UNISWAP_V2 = "uniswap_v2"
    CURVE = "curve"
    BALANCER = "balancer"
    SUSHISWAP = "sushiswap"
    DODO = "dodo"
    PANCAKESWAP = "pancakeswap"
    QUICKSWAP = "quickswap"


@dataclass
class PriceQuote:
    """Quote for swap on DEX."""
    dex: DEXType
    token_in: str
    token_out: str
    amount_in: int  # Wei
    amount_out: int  # Wei (expected output)
    amount_out_min: int  # Wei (with slippage)
    price_impact: float  # % (0.0 - 100.0)
    gas_estimate: int  # Wei
    fee: int  # Wei (protocol fee if any)
    liquidity_available: int  # Wei (available liquidity)
    confidence: float  # 0.0 - 1.0
    route_hops: int  # 1 for direct, >1 for multi-hop
    timestamp: int  # Unix timestamp


@dataclass
class SwapCalldata:
    """Encoded swap calldata for on-chain execution."""
    dex: DEXType
    target_contract: str  # Contract to call
    call_data: str  # Encoded call data (0x...)
    value: int  # ETH value to send (if any)
    gas_limit: int  # Estimated gas
    deadline: int  # Unix timestamp for deadline


class DEXAdapter(ABC):
    """
    Abstract base class for DEX adapters.
    Each DEX implementation inherits and implements these methods.
    """
    
    def __init__(self, web3, name: str, dex_type: DEXType):
        """
        Initialize DEX adapter.
        
        Args:
            web3: Web3 instance
            name: Human-readable name
            dex_type: DEX type enumeration
        """
        self.web3 = web3
        self.name = name
        self.dex_type = dex_type
        self.last_quote_time = 0
        self.quote_cache: Dict[str, PriceQuote] = {}
        
        logger.info(f"DEX adapter initialized: {name} ({dex_type.value})")
    
    @abstractmethod
    async def get_price_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        slippage_tolerance: float = 0.001,
    ) -> Optional[PriceQuote]:
        """
        Get price quote for swap.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap (in wei)
            slippage_tolerance: Max slippage as decimal (0.001 = 0.1%)
            
        Returns:
            PriceQuote with swap details or None if unavailable
        """
        pass
    
    @abstractmethod
    async def build_swap_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
        recipient: str,
        deadline: int,
    ) -> Optional[SwapCalldata]:
        """
        Build encoded calldata for swap transaction.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap (in wei)
            amount_out_min: Minimum amount out (with slippage)
            recipient: Address to receive tokens
            deadline: Transaction deadline (Unix timestamp)
            
        Returns:
            SwapCalldata with encoded transaction or None
        """
        pass
    
    @abstractmethod
    async def get_liquidity(
        self,
        token_in: str,
        token_out: str,
    ) -> int:
        """
        Get available liquidity for token pair.
        
        Args:
            token_in: Input token
            token_out: Output token
            
        Returns:
            Available liquidity in wei
        """
        pass
    
    @abstractmethod
    async def validate_pair(
        self,
        token_in: str,
        token_out: str,
    ) -> bool:
        """
        Check if token pair is available on this DEX.
        
        Args:
            token_in: Input token
            token_out: Output token
            
        Returns:
            True if pair is tradeable
        """
        pass
    
    def calculate_price_impact(
        self,
        amount_in: int,
        amount_out: int,
        expected_rate: float,
    ) -> float:
        """
        Calculate price impact percentage.
        
        Args:
            amount_in: Amount in (wei)
            amount_out: Amount out (wei)
            expected_rate: Expected exchange rate
            
        Returns:
            Price impact as percentage (0.0 - 100.0)
        """
        if expected_rate == 0:
            return 0.0
        
        expected_out = amount_in * expected_rate
        actual_out = amount_out
        
        impact = ((expected_out - actual_out) / expected_out) * 100
        return max(0.0, min(100.0, impact))
    
    def cache_quote(
        self,
        cache_key: str,
        quote: PriceQuote,
        ttl_seconds: int = 5,
    ):
        """Cache price quote temporarily."""
        self.quote_cache[cache_key] = quote
        # Note: Simple cache - production would use TTL
    
    def get_cached_quote(self, cache_key: str) -> Optional[PriceQuote]:
        """Get cached quote if available."""
        return self.quote_cache.get(cache_key)
    
    def clear_cache(self):
        """Clear quote cache."""
        self.quote_cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "name": self.name,
            "dex_type": self.dex_type.value,
            "cache_size": len(self.quote_cache),
        }


class DEXAdapterFactory:
    """
    Factory for creating DEX adapters.
    Manages instantiation of all available DEX implementations.
    """
    
    def __init__(self, web3):
        """Initialize factory."""
        self.web3 = web3
        self.adapters: Dict[DEXType, DEXAdapter] = {}
        logger.info("DEX adapter factory initialized")
    
    def register_adapter(self, adapter: DEXAdapter):
        """Register a DEX adapter."""
        self.adapters[adapter.dex_type] = adapter
        logger.info(f"Registered adapter: {adapter.name}")
    
    def get_adapter(self, dex_type: DEXType) -> Optional[DEXAdapter]:
        """Get adapter for DEX type."""
        return self.adapters.get(dex_type)
    
    def get_all_adapters(self) -> List[DEXAdapter]:
        """Get all registered adapters."""
        return list(self.adapters.values())
    
    def get_adapter_status(self) -> Dict[str, Dict]:
        """Get status of all adapters."""
        return {
            adapter.name: adapter.get_status()
            for adapter in self.adapters.values()
        }


# Singleton instance
_dex_adapter_factory: Optional[DEXAdapterFactory] = None


def initialize_dex_adapter_factory(web3) -> DEXAdapterFactory:
    """Initialize DEX adapter factory."""
    global _dex_adapter_factory
    _dex_adapter_factory = DEXAdapterFactory(web3)
    return _dex_adapter_factory


def get_dex_adapter_factory() -> DEXAdapterFactory:
    """Get current DEX adapter factory instance."""
    if _dex_adapter_factory is None:
        raise RuntimeError("DEX adapter factory not initialized")
    return _dex_adapter_factory
