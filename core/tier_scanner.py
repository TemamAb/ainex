"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON TIER 1: MARKET SCANNER                              ║
║                     Multi-DEX Opportunity Discovery                            ║
║                                                                                ║
║  Purpose: Scan 8+ DEXs, identify arbitrage patterns, pre-qualify opportunities ║
║  Tier: Standalone distributed scanner agents (can run in parallel)             ║
║  Interval: 1 second scans continuously                                         ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import time
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DEXType(Enum):
    UNISWAP_V3 = "uniswap_v3"
    UNISWAP_V2 = "uniswap_v2"
    SUSHISWAP = "sushiswap"
    CURVE = "curve"
    BALANCER = "balancer"
    DODO = "dodo"
    PANCAKESWAP = "pancakeswap"
    QUICKSWAP = "quickswap"


@dataclass
class PriceQuote:
    """DEX price quote"""
    dex: DEXType
    token_in: str
    token_out: str
    price: Decimal
    timestamp: float
    liquidity_usd: float
    fee_tier: float
    reliability_score: float  # 0.0-1.0


@dataclass
class ArbitrageOpportunity:
    """Pre-qualified arbitrage opportunity for orchestrator"""
    opportunity_id: str
    token_in: str
    token_out: str
    pair_name: str
    buy_dex: DEXType
    sell_dex: DEXType
    buy_price: Decimal
    sell_price: Decimal
    spread_pct: float
    estimated_profit_eth: Decimal
    confidence_score: float  # 0.0-1.0
    risk_flags: List[str]  # ["low_liquidity", "high_slippage", etc]
    timestamp: float
    amount_to_trade: Decimal  # Suggested amount
    scan_duration_ms: float


class MarketScanner:
    """Tier 1: Scans markets for opportunities"""
    
    def __init__(self):
        self.scanner_id = f"scanner_{int(time.time() * 1000)}"
        self.dex_feeds = self._init_dex_feeds()
        self.price_cache: Dict[str, Dict[DEXType, PriceQuote]] = {}
        self.cache_ttl = 5  # seconds
        self.opportunities: List[ArbitrageOpportunity] = []
        self.scan_stats = {
            "total_scans": 0,
            "opportunities_found": 0,
            "last_scan_time": None,
            "avg_scan_time_ms": 0
        }
        self.token_pairs = [
            ("WETH", "USDC", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
            ("WBTC", "WETH", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
            ("DAI", "USDC", "0x6B175474E89094C44Da98b954EedeAC495271d0F", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
        ]
    
    def _init_dex_feeds(self) -> Dict[DEXType, str]:
        """Initialize DEX API endpoints"""
        return {
            DEXType.UNISWAP_V3: "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
            DEXType.UNISWAP_V2: "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2",
            DEXType.SUSHISWAP: "https://api.thegraph.com/subgraphs/name/sushiswap/exchange",
            DEXType.CURVE: "https://api.thegraph.com/subgraphs/name/convex-community/curve-mainnet",
            DEXType.BALANCER: "https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2",
            DEXType.DODO: "https://api.thegraph.com/subgraphs/name/dodoex/dodo",
        }
    
    async def fetch_price_from_dex(self, dex: DEXType, token_in: str, token_out: str) -> Optional[PriceQuote]:
        """Fetch price from specific DEX with timeout"""
        try:
            endpoint = self.dex_feeds.get(dex)
            if not endpoint:
                return None
            
            # GraphQL query for price
            query = self._build_price_query(dex, token_in, token_out)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={'query': query},
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = self._parse_price_response(dex, data)
                        
                        if price:
                            return PriceQuote(
                                dex=dex,
                                token_in=token_in,
                                token_out=token_out,
                                price=Decimal(str(price['price'])),
                                timestamp=time.time(),
                                liquidity_usd=price.get('liquidity', 0),
                                fee_tier=price.get('fee', 0.003),
                                reliability_score=0.9
                            )
        except asyncio.TimeoutError:
            logger.warning(f"[SCANNER] Timeout fetching {dex.value} price for {token_in}/{token_out}")
        except Exception as e:
            logger.warning(f"[SCANNER] Error fetching {dex.value} price: {e}")
        
        return None
    
    def _build_price_query(self, dex: DEXType, token_in: str, token_out: str) -> str:
        """Build GraphQL query based on DEX type"""
        if dex == DEXType.UNISWAP_V3:
            return f"""
            {{
              pools(where: {{
                token0: "{token_in.lower()}",
                token1: "{token_out.lower()}"
              }}, orderBy: volumeUSD, orderDirection: desc, first: 1) {{
                token0Price
                token1Price
                liquidity
                feeTier
              }}
            }}
            """
        elif dex == DEXType.UNISWAP_V2 or dex == DEXType.SUSHISWAP:
            return f"""
            {{
              pairs(where: {{
                token0: "{token_in.lower()}",
                token1: "{token_out.lower()}"
              }}, orderBy: volumeUSD, orderDirection: desc, first: 1) {{
                token0Price
                token1Price
                reserveUSD
              }}
            }}
            """
        else:
            return "{}"
    
    def _parse_price_response(self, dex: DEXType, data: dict) -> Optional[dict]:
        """Parse price from DEX response"""
        try:
            if dex == DEXType.UNISWAP_V3:
                pools = data.get('data', {}).get('pools', [])
                if pools:
                    return {
                        'price': float(pools[0]['token1Price']),
                        'liquidity': float(pools[0].get('liquidity', 0)),
                        'fee': float(pools[0].get('feeTier', 3000)) / 1e6
                    }
            elif dex == DEXType.UNISWAP_V2 or dex == DEXType.SUSHISWAP:
                pairs = data.get('data', {}).get('pairs', [])
                if pairs:
                    return {
                        'price': float(pairs[0]['token1Price']),
                        'liquidity': float(pairs[0].get('reserveUSD', 0)),
                        'fee': 0.003
                    }
        except Exception as e:
            logger.warning(f"[SCANNER] Failed to parse {dex.value} response: {e}")
        
        return None
    
    async def scan_pair(self, token_in: str, token_out: str, pair_name: str) -> List[ArbitrageOpportunity]:
        """Scan a token pair across multiple DEXs"""
        opportunities = []
        start_time = time.time()
        
        # Fetch prices from all DEXs in parallel
        dex_types = [DEXType.UNISWAP_V3, DEXType.UNISWAP_V2, DEXType.SUSHISWAP]
        price_tasks = [
            self.fetch_price_from_dex(dex, token_in, token_out)
            for dex in dex_types
        ]
        
        prices = await asyncio.gather(*price_tasks)
        quotes = [p for p in prices if p is not None]
        
        if len(quotes) < 2:
            return opportunities
        
        # Find arbitrage spreads
        for i, quote_buy in enumerate(quotes):
            for quote_sell in quotes[i+1:]:
                if quote_buy.price > 0 and quote_sell.price > 0:
                    spread = (quote_sell.price - quote_buy.price) / quote_buy.price
                    spread_pct = spread * 100
                    
                    # Filter by minimum spread (0.3% after fees)
                    if spread_pct > 0.5:  # 0.5% minimum
                        # Calculate confidence based on liquidity and reliability
                        confidence = (
                            quote_buy.reliability_score * 0.5 +
                            quote_sell.reliability_score * 0.5 +
                            min(1.0, (quote_buy.liquidity_usd + quote_sell.liquidity_usd) / 1_000_000) * 0.3
                        ) / 1.3
                        
                        risk_flags = []
                        if quote_buy.liquidity_usd < 100_000:
                            risk_flags.append("low_liquidity_buy")
                        if quote_sell.liquidity_usd < 100_000:
                            risk_flags.append("low_liquidity_sell")
                        
                        estimated_profit = Decimal(str(1.0)) * (Decimal(str(quote_sell.price)) - Decimal(str(quote_buy.price)))
                        
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=f"opp_{int(time.time() * 1000)}",
                            token_in=token_in,
                            token_out=token_out,
                            pair_name=pair_name,
                            buy_dex=quote_buy.dex,
                            sell_dex=quote_sell.dex,
                            buy_price=quote_buy.price,
                            sell_price=quote_sell.price,
                            spread_pct=spread_pct,
                            estimated_profit_eth=estimated_profit,
                            confidence_score=min(1.0, confidence),
                            risk_flags=risk_flags,
                            timestamp=time.time(),
                            amount_to_trade=Decimal(str(1.0)),  # 1 ETH equivalent
                            scan_duration_ms=(time.time() - start_time) * 1000
                        )
                        
                        opportunities.append(opportunity)
                        logger.info(f"[SCANNER {self.scanner_id}] Found {pair_name}: {spread_pct:.2f}% spread (confidence: {confidence:.2%})")
        
        return opportunities
    
    async def scan_all_pairs(self) -> List[ArbitrageOpportunity]:
        """Scan all configured token pairs"""
        self.scan_stats["total_scans"] += 1
        start_time = time.time()
        all_opportunities = []
        
        # Scan all pairs in parallel
        scan_tasks = [
            self.scan_pair(token_in, token_out, pair_name)
            for pair_name, _, token_in, token_out in self.token_pairs
        ]
        
        results = await asyncio.gather(*scan_tasks)
        for opp_list in results:
            all_opportunities.extend(opp_list)
        
        # Update stats
        scan_time = time.time() - start_time
        self.scan_stats["last_scan_time"] = scan_time
        self.scan_stats["opportunities_found"] += len(all_opportunities)
        
        # Update average scan time
        if self.scan_stats["total_scans"] > 0:
            self.scan_stats["avg_scan_time_ms"] = (
                (self.scan_stats["avg_scan_time_ms"] * (self.scan_stats["total_scans"] - 1) + scan_time * 1000) /
                self.scan_stats["total_scans"]
            )
        
        self.opportunities = all_opportunities
        return all_opportunities
    
    def get_top_opportunities(self, limit: int = 10) -> List[ArbitrageOpportunity]:
        """Get top opportunities by confidence score"""
        return sorted(
            self.opportunities,
            key=lambda x: x.confidence_score,
            reverse=True
        )[:limit]
    
    def get_stats(self) -> Dict:
        """Get scanner statistics"""
        return {
            "scanner_id": self.scanner_id,
            "total_scans": self.scan_stats["total_scans"],
            "opportunities_found": self.scan_stats["opportunities_found"],
            "last_scan_time_ms": self.scan_stats["last_scan_time"] * 1000 if self.scan_stats["last_scan_time"] else 0,
            "avg_scan_time_ms": self.scan_stats["avg_scan_time_ms"],
            "current_opportunities": len(self.opportunities)
        }


async def run_scanner():
    """Standalone scanner process"""
    scanner = MarketScanner()
    logger.info(f"[SCANNER] Started scanner: {scanner.scanner_id}")
    
    try:
        while True:
            opportunities = await scanner.scan_all_pairs()
            logger.info(f"[SCANNER] Scan complete: {len(opportunities)} opportunities found")
            
            # Sleep before next scan
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("[SCANNER] Shutdown requested")


if __name__ == "__main__":
    asyncio.run(run_scanner())
