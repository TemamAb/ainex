"""
Real DEX Price Fetcher - Fetch actual prices from Uniswap V2/V3 subgraphs
Connects to The Graph API for real market data
"""

import logging
import aiohttp
import asyncio
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DEXType(Enum):
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"


@dataclass
class PriceQuote:
    """Market price quote from a DEX"""
    dex: str
    token_in: str
    token_out: str
    price: Decimal
    liquidity_usd: float
    fee_tier: float
    timestamp: float


class DEXPriceFetcher:
    """Fetch real prices from DEX subgraphs via The Graph API"""
    
    # The Graph API endpoints
    ENDPOINTS = {
        DEXType.UNISWAP_V2: "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
        DEXType.UNISWAP_V3: "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        DEXType.SUSHISWAP: "https://api.thegraph.com/subgraphs/name/sushiswap/exchange",
        DEXType.CURVE: "https://api.thegraph.com/subgraphs/name/messari/curve-finance-ethereum",
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("[DEX_FETCHER] Initialized with real DEX endpoints")
    
    async def start(self):
        """Initialize async session"""
        self.session = aiohttp.ClientSession()
        logger.info("[DEX_FETCHER] Session started")
    
    async def stop(self):
        """Close async session"""
        if self.session:
            await self.session.close()
            logger.info("[DEX_FETCHER] Session closed")
    
    async def get_price(
        self,
        dex: DEXType,
        token_in: str,
        token_out: str
    ) -> Optional[PriceQuote]:
        """
        Fetch real price from DEX
        
        Args:
            dex: DEX type (Uniswap V2, V3, etc)
            token_in: Input token address
            token_out: Output token address
        
        Returns:
            PriceQuote with actual market data, or None if fetch fails
        """
        try:
            if dex == DEXType.UNISWAP_V2:
                return await self._fetch_uniswap_v2_price(token_in, token_out)
            elif dex == DEXType.UNISWAP_V3:
                return await self._fetch_uniswap_v3_price(token_in, token_out)
            elif dex == DEXType.SUSHISWAP:
                return await self._fetch_sushiswap_price(token_in, token_out)
            elif dex == DEXType.CURVE:
                return await self._fetch_curve_price(token_in, token_out)
            else:
                logger.warning(f"[DEX_FETCHER] Unknown DEX type: {dex}")
                return None
                
        except Exception as e:
            logger.error(f"[DEX_FETCHER] Failed to fetch price from {dex.value}: {e}")
            return None
    
    async def _fetch_uniswap_v2_price(
        self,
        token_in: str,
        token_out: str
    ) -> Optional[PriceQuote]:
        """Fetch price from Uniswap V2"""
        
        query = """
        query {
            pairs(where: {
                token0: "%s",
                token1: "%s"
            }, first: 1) {
                id
                token0Price
                token1Price
                reserveUSD
            }
        }
        """ % (token_in.lower(), token_out.lower())
        
        try:
            result = await self._query_subgraph(DEXType.UNISWAP_V2, query)
            
            if result and result.get("pairs"):
                pair = result["pairs"][0]
                
                # Determine which price to use
                token0_price = Decimal(pair.get("token0Price", 0))
                reserve_usd = float(pair.get("reserveUSD", 0))
                
                return PriceQuote(
                    dex=DEXType.UNISWAP_V2.value,
                    token_in=token_in,
                    token_out=token_out,
                    price=token0_price,
                    liquidity_usd=reserve_usd,
                    fee_tier=0.003,  # Uniswap V2 is 0.3%
                    timestamp=self._get_timestamp()
                )
        
        except Exception as e:
            logger.debug(f"[DEX_FETCHER] Uniswap V2 fetch failed: {e}")
        
        return None
    
    async def _fetch_uniswap_v3_price(
        self,
        token_in: str,
        token_out: str
    ) -> Optional[PriceQuote]:
        """Fetch price from Uniswap V3"""
        
        # V3 has multiple fee tiers - query all and use best liquidity
        query = """
        query {
            pools(where: {
                token0: "%s",
                token1: "%s"
            }, orderBy: liquidity, orderDirection: desc, first: 5) {
                id
                token0Price
                token1Price
                liquidity
                totalValueLockedUSD
                feeTier
            }
        }
        """ % (token_in.lower(), token_out.lower())
        
        try:
            result = await self._query_subgraph(DEXType.UNISWAP_V3, query)
            
            if result and result.get("pools"):
                # Use highest liquidity pool
                pool = result["pools"][0]
                
                token0_price = Decimal(pool.get("token0Price", 0))
                liquidity_usd = float(pool.get("totalValueLockedUSD", 0))
                fee_tier = float(pool.get("feeTier", 3000)) / 10000  # Convert to decimal
                
                return PriceQuote(
                    dex=DEXType.UNISWAP_V3.value,
                    token_in=token_in,
                    token_out=token_out,
                    price=token0_price,
                    liquidity_usd=liquidity_usd,
                    fee_tier=fee_tier,
                    timestamp=self._get_timestamp()
                )
        
        except Exception as e:
            logger.debug(f"[DEX_FETCHER] Uniswap V3 fetch failed: {e}")
        
        return None
    
    async def _fetch_sushiswap_price(
        self,
        token_in: str,
        token_out: str
    ) -> Optional[PriceQuote]:
        """Fetch price from SushiSwap"""
        
        query = """
        query {
            pairs(where: {
                token0: "%s",
                token1: "%s"
            }, first: 1) {
                id
                token0Price
                token1Price
                reserveUSD
            }
        }
        """ % (token_in.lower(), token_out.lower())
        
        try:
            result = await self._query_subgraph(DEXType.SUSHISWAP, query)
            
            if result and result.get("pairs"):
                pair = result["pairs"][0]
                
                token0_price = Decimal(pair.get("token0Price", 0))
                reserve_usd = float(pair.get("reserveUSD", 0))
                
                return PriceQuote(
                    dex=DEXType.SUSHISWAP.value,
                    token_in=token_in,
                    token_out=token_out,
                    price=token0_price,
                    liquidity_usd=reserve_usd,
                    fee_tier=0.003,  # SushiSwap is 0.3%
                    timestamp=self._get_timestamp()
                )
        
        except Exception as e:
            logger.debug(f"[DEX_FETCHER] SushiSwap fetch failed: {e}")
        
        return None
    
    async def _fetch_curve_price(
        self,
        token_in: str,
        token_out: str
    ) -> Optional[PriceQuote]:
        """Fetch price from Curve"""
        
        # Simplified Curve price fetch
        query = """
        query {
            exchanges(where: {
                inputTokens_contains: ["%s"],
                outputTokens_contains: ["%s"]
            }, first: 1) {
                id
                rates {
                    rate
                }
            }
        }
        """ % (token_in.lower(), token_out.lower())
        
        try:
            result = await self._query_subgraph(DEXType.CURVE, query)
            
            if result and result.get("exchanges"):
                exchange = result["exchanges"][0]
                rate = exchange.get("rates", [{}])[0].get("rate", 1)
                
                return PriceQuote(
                    dex=DEXType.CURVE.value,
                    token_in=token_in,
                    token_out=token_out,
                    price=Decimal(str(rate)),
                    liquidity_usd=0,  # Curve doesn't expose this easily
                    fee_tier=0.0004,  # Curve typically 0.04%
                    timestamp=self._get_timestamp()
                )
        
        except Exception as e:
            logger.debug(f"[DEX_FETCHER] Curve fetch failed: {e}")
        
        return None
    
    async def _query_subgraph(
        self,
        dex: DEXType,
        query: str
    ) -> Optional[Dict]:
        """Execute GraphQL query against DEX subgraph"""
        
        if not self.session:
            logger.error("[DEX_FETCHER] Session not initialized")
            return None
        
        endpoint = self.ENDPOINTS.get(dex)
        if not endpoint:
            logger.error(f"[DEX_FETCHER] No endpoint for {dex.value}")
            return None
        
        try:
            async with self.session.post(
                endpoint,
                json={"query": query},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("errors"):
                        logger.warning(f"[DEX_FETCHER] GraphQL error: {data.get('errors')}")
                        return None
                    
                    return data.get("data")
                else:
                    logger.warning(f"[DEX_FETCHER] HTTP {response.status}: {endpoint}")
                    return None
        
        except asyncio.TimeoutError:
            logger.warning(f"[DEX_FETCHER] Timeout querying {dex.value}")
            return None
        except Exception as e:
            logger.warning(f"[DEX_FETCHER] Query failed: {e}")
            return None
    
    async def get_multi_dex_prices(
        self,
        token_in: str,
        token_out: str
    ) -> Dict[str, Optional[PriceQuote]]:
        """
        Fetch prices from all DEXs in parallel
        
        Returns:
            {dex_name: price_quote}
        """
        tasks = {
            dex: self.get_price(dex, token_in, token_out)
            for dex in DEXType
        }
        
        results = {}
        for dex, task in tasks.items():
            try:
                quote = await task
                results[dex.value] = quote
            except Exception as e:
                logger.warning(f"[DEX_FETCHER] Failed to fetch {dex.value}: {e}")
                results[dex.value] = None
        
        return results
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
