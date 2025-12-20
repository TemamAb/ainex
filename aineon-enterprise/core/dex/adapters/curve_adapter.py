"""
AINEON Curve Adapter
Stable swap curve AMM integration for efficient stablecoin trading.

Spec: Curve pool discovery, stable swap routing, gas optimization
Target: <100ms quotes, optimal fee tier selection, 99%+ availability
"""

import logging
from typing import Optional, Dict, List, Any
import asyncio

from web3 import Web3

from core.dex.dex_adapter_base import (
    DEXAdapter, DEXType, PriceQuote, SwapCalldata
)

logger = logging.getLogger(__name__)


class CurveAdapter(DEXAdapter):
    """Curve stableswap adapter."""
    
    # Curve Registry to find pools
    REGISTRY_ADDRESS = "0x90E00ACe926c6BE8B3c3E7CCf5f9B8503E685CB5"
    ROUTER_ADDRESS = "0xF0d4c12A5768D806021F80a262B4d39d26C58b8D"
    
    # Common stable coin addresses
    STABLE_COINS = {
        "USDC": "0xA0b86991d4F06c43d94c3379A3655Ba24dbbA4b1",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "TUSD": "0x0000000000085d4780B73119b8B580991DEe8d52",
        "BUSD": "0x4Fabb145d64652a948d72533023f6E7A623C7C53",
    }
    
    def __init__(self, web3: Web3):
        """Initialize Curve adapter."""
        super().__init__(web3, "Curve", DEXType.CURVE)
        self.pool_cache: Dict[str, Dict] = {}
    
    async def get_price_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        slippage_tolerance: float = 0.001,
    ) -> Optional[PriceQuote]:
        """Get Curve quote for stable swap."""
        try:
            token_in = Web3.to_checksum_address(token_in)
            token_out = Web3.to_checksum_address(token_out)
            
            cache_key = f"curve_{token_in}_{token_out}_{amount_in}"
            cached = self.get_cached_quote(cache_key)
            if cached:
                return cached
            
            # Find best pool for this pair
            pool = await self._find_best_pool(token_in, token_out)
            if not pool:
                logger.warning(f"No Curve pool found for {token_in} → {token_out}")
                return None
            
            # Get quote from pool
            amount_out = await self._get_dy(pool, token_in, token_out, amount_in)
            if amount_out == 0:
                return None
            
            # Calculate slippage
            amount_out_min = int(amount_out * (1 - slippage_tolerance))
            
            # Get pool fee
            pool_fee = pool.get("fee", 4000000)  # Default 0.4%
            protocol_fee = int(amount_in * pool_fee / 1000000000000)
            
            quote = PriceQuote(
                dex=self.dex_type,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out=amount_out,
                amount_out_min=amount_out_min,
                price_impact=self._calculate_curve_impact(amount_in, amount_out),
                gas_estimate=150000,  # Curve swaps are gas efficient
                fee=protocol_fee,
                liquidity_available=pool.get("liquidity", 100 * 10**18),
                confidence=0.98,  # Curve is highly reliable for stables
                route_hops=1,
                timestamp=int(self.web3.eth.get_block("latest").timestamp),
            )
            
            self.cache_quote(cache_key, quote)
            logger.debug(f"Curve quote: {amount_in} → {amount_out}")
            return quote
        
        except Exception as e:
            logger.error(f"Curve quote error: {e}")
            return None
    
    async def build_swap_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        amount_out_min: int,
        recipient: str,
        deadline: int,
    ) -> Optional[SwapCalldata]:
        """Build Curve swap calldata."""
        try:
            token_in = Web3.to_checksum_address(token_in)
            token_out = Web3.to_checksum_address(token_out)
            recipient = Web3.to_checksum_address(recipient)
            
            # Find pool
            pool = await self._find_best_pool(token_in, token_out)
            if not pool:
                return None
            
            # Build transaction
            call_data = self._encode_swap(pool, token_in, token_out, amount_in, amount_out_min, recipient)
            
            calldata = SwapCalldata(
                dex=self.dex_type,
                target_contract=self.ROUTER_ADDRESS,
                call_data=call_data,
                value=0,
                gas_limit=200000,
                deadline=deadline,
            )
            
            logger.debug(f"Curve calldata built")
            return calldata
        
        except Exception as e:
            logger.error(f"Curve calldata error: {e}")
            return None
    
    async def get_liquidity(
        self,
        token_in: str,
        token_out: str,
    ) -> int:
        """Get available liquidity."""
        try:
            pool = await self._find_best_pool(token_in, token_out)
            return pool.get("liquidity", 0) if pool else 0
        except Exception as e:
            logger.error(f"Failed to get liquidity: {e}")
            return 0
    
    async def validate_pair(
        self,
        token_in: str,
        token_out: str,
    ) -> bool:
        """Check if pair exists on Curve."""
        try:
            pool = await self._find_best_pool(token_in, token_out)
            return pool is not None
        except Exception as e:
            logger.error(f"Failed to validate pair: {e}")
            return False
    
    async def _find_best_pool(self, token_in: str, token_out: str) -> Optional[Dict]:
        """Find best pool for token pair."""
        try:
            # In production would query registry
            # For now return mock pool
            return {
                "address": "0x" + "0" * 40,
                "coins": [token_in, token_out],
                "fee": 4000000,  # 0.4%
                "liquidity": 100 * 10**18,
            }
        except Exception as e:
            logger.error(f"Pool discovery error: {e}")
            return None
    
    async def _get_dy(self, pool: Dict, token_in: str, token_out: str, amount_in: int) -> int:
        """Get output amount from pool."""
        try:
            # Simplified: assume 1:1 for stables minus fee
            fee_rate = pool.get("fee", 4000000) / 1000000000000
            amount_out = int(amount_in * (1 - fee_rate))
            return amount_out
        except Exception as e:
            logger.error(f"dy calculation error: {e}")
            return 0
    
    def _calculate_curve_impact(self, amount_in: int, amount_out: int) -> float:
        """Calculate price impact for Curve swap."""
        if amount_in == 0:
            return 0.0
        impact = ((amount_in - amount_out) / amount_in) * 100
        return min(impact, 5.0)  # Cap at 5%
    
    def _encode_swap(self, pool: Dict, token_in: str, token_out: str, 
                     amount_in: int, amount_out_min: int, recipient: str) -> str:
        """Encode Curve swap call."""
        # Simplified encoding
        return "0x" + "00" * 32


def create_curve_adapter(web3: Web3) -> CurveAdapter:
    """Create Curve adapter."""
    return CurveAdapter(web3)
