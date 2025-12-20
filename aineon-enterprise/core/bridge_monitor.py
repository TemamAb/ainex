"""
PHASE 2 MODULE 2: Cross-Chain Bridge Monitor
Detects and executes cross-chain arbitrage via bridges
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class BridgeOpportunity:
    """Represents a bridge arbitrage opportunity"""
    asset: str
    source_chain: str
    dest_chain: str
    source_price: float
    dest_price: float
    spread_pct: float
    liquidity_source: float
    liquidity_dest: float
    bridge_fee_pct: float
    estimated_profit_eth: float
    execution_time_seconds: int


class BridgeConfig:
    """Configuration for cross-chain bridges"""
    
    CURVE_BRIDGE = {
        "name": "Curve Stablecoin Bridge",
        "type": "stablecoin",
        "supported_assets": ["USDC", "USDT", "DAI", "FRAX"],
        "source_chains": ["ethereum"],
        "dest_chains": ["polygon", "optimism", "arbitrum"],
        "fee_bps": 4,  # 0.04% fee
        "min_amount": 1000,
        "max_amount": 10_000_000,
        "confirmation_blocks": 1,
    }
    
    ACROSS_BRIDGE = {
        "name": "Across Protocol",
        "type": "universal",
        "supported_assets": ["ETH", "USDC", "DAI", "USDT", "WBTC"],
        "source_chains": ["ethereum", "polygon", "optimism", "arbitrum"],
        "dest_chains": ["ethereum", "polygon", "optimism", "arbitrum"],
        "fee_bps": 5,  # 0.05% fee
        "min_amount": 100,
        "max_amount": 50_000_000,
        "confirmation_blocks": 2,
    }
    
    CONNEXT_BRIDGE = {
        "name": "Connext",
        "type": "universal",
        "supported_assets": ["ETH", "USDC", "DAI", "USDT"],
        "source_chains": ["ethereum", "polygon", "optimism", "arbitrum"],
        "dest_chains": ["ethereum", "polygon", "optimism", "arbitrum"],
        "fee_bps": 8,  # 0.08% fee
        "min_amount": 100,
        "max_amount": 50_000_000,
        "confirmation_blocks": 3,
    }


class BridgeMonitor:
    """
    Monitor cross-chain bridges for arbitrage opportunities.
    Tracks price differences across chains via bridges.
    """
    
    def __init__(self):
        self.bridges = {
            "curve": BridgeConfig.CURVE_BRIDGE,
            "across": BridgeConfig.ACROSS_BRIDGE,
            "connext": BridgeConfig.CONNEXT_BRIDGE,
        }
        
        self.opportunities: List[BridgeOpportunity] = []
        self.price_cache: Dict[str, Dict[str, float]] = {}
        self.monitoring_active = False
    
    async def monitor_bridges(self, scan_interval: int = 5) -> None:
        """
        Continuously monitor all bridges for opportunities.
        Scan interval: 5 seconds (fast enough for most opportunities)
        """
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                opportunities = await self.detect_all_bridge_opportunities()
                self.opportunities = self._filter_profitable_opportunities(opportunities)
                
                if self.opportunities:
                    logger.info(f"🌉 Found {len(self.opportunities)} bridge opportunities")
                
                await asyncio.sleep(scan_interval)
                
            except Exception as e:
                logger.error(f"Error in bridge monitoring: {e}")
                await asyncio.sleep(10)
    
    async def detect_all_bridge_opportunities(self) -> List[BridgeOpportunity]:
        """
        Detect bridge arbitrage opportunities across all bridges.
        """
        all_opportunities = []
        
        tasks = [
            self._detect_bridge_opportunities(bridge_name, config)
            for bridge_name, config in self.bridges.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_opportunities.extend(result)
        
        return all_opportunities
    
    async def _detect_bridge_opportunities(
        self, bridge_name: str, config: Dict
    ) -> List[BridgeOpportunity]:
        """
        Detect opportunities for a specific bridge.
        """
        opportunities = []
        
        try:
            # Check each asset on this bridge
            for asset in config["supported_assets"]:
                # Get prices on source chains
                for source_chain in config["source_chains"]:
                    source_price = await self._get_price(asset, source_chain)
                    if not source_price:
                        continue
                    
                    # Check prices on destination chains
                    for dest_chain in config["dest_chains"]:
                        if dest_chain == source_chain:
                            continue
                        
                        dest_price = await self._get_price(asset, dest_chain)
                        if not dest_price:
                            continue
                        
                        # Calculate spread
                        spread_pct = ((dest_price - source_price) / source_price) * 100
                        
                        # Skip if not profitable (need to account for bridge fees)
                        bridge_fee_pct = config["fee_bps"] / 100
                        profit_pct = spread_pct - (2 * bridge_fee_pct)
                        
                        if profit_pct > 0.05:  # >0.05% profitable
                            opportunity = BridgeOpportunity(
                                asset=asset,
                                source_chain=source_chain,
                                dest_chain=dest_chain,
                                source_price=source_price,
                                dest_price=dest_price,
                                spread_pct=spread_pct,
                                liquidity_source=await self._get_liquidity(asset, source_chain),
                                liquidity_dest=await self._get_liquidity(asset, dest_chain),
                                bridge_fee_pct=bridge_fee_pct,
                                estimated_profit_eth=self._calculate_profit(
                                    spread_pct, bridge_fee_pct, 100  # 100 ETH position
                                ),
                                execution_time_seconds=config["confirmation_blocks"] * 12,
                            )
                            opportunities.append(opportunity)
        
        except Exception as e:
            logger.error(f"Error detecting opportunities on {bridge_name}: {e}")
        
        return opportunities
    
    async def execute_bridge_arbitrage(self, opportunity: BridgeOpportunity) -> Dict:
        """
        Execute a bridge arbitrage trade.
        
        Steps:
        1. Buy on source chain (at source_price)
        2. Bridge tokens to destination chain
        3. Sell on destination chain (at dest_price)
        4. Return profit
        """
        try:
            logger.info(f"🚀 Executing bridge arb: {opportunity.asset} {opportunity.source_chain}→{opportunity.dest_chain}")
            
            # Step 1: Buy on source chain
            buy_tx = await self._execute_swap_on_chain(
                opportunity.source_chain,
                asset=opportunity.asset,
                amount=100,  # 100 ETH
                direction="buy"
            )
            
            if not buy_tx:
                logger.error("Failed to buy on source chain")
                return {"success": False}
            
            logger.info(f"✓ Bought on {opportunity.source_chain}: {buy_tx.get('tx_hash')}")
            
            # Step 2: Bridge tokens to destination chain
            bridge_tx = await self._bridge_tokens(
                opportunity.asset,
                opportunity.source_chain,
                opportunity.dest_chain,
                amount=100
            )
            
            if not bridge_tx:
                logger.error("Bridge failed")
                return {"success": False}
            
            logger.info(f"✓ Bridged to {opportunity.dest_chain}: {bridge_tx.get('tx_hash')}")
            
            # Step 3: Sell on destination chain
            sell_tx = await self._execute_swap_on_chain(
                opportunity.dest_chain,
                asset=opportunity.asset,
                amount=100,
                direction="sell"
            )
            
            if not sell_tx:
                logger.error("Failed to sell on destination chain")
                return {"success": False}
            
            logger.info(f"✓ Sold on {opportunity.dest_chain}: {sell_tx.get('tx_hash')}")
            
            # Calculate profit
            profit = opportunity.estimated_profit_eth - 0.02  # Minus tx costs
            
            return {
                "success": True,
                "asset": opportunity.asset,
                "source_chain": opportunity.source_chain,
                "dest_chain": opportunity.dest_chain,
                "buy_tx": buy_tx.get("tx_hash"),
                "bridge_tx": bridge_tx.get("tx_hash"),
                "sell_tx": sell_tx.get("tx_hash"),
                "profit_eth": profit,
            }
            
        except Exception as e:
            logger.error(f"Error executing bridge arbitrage: {e}")
            return {"success": False}
    
    async def _get_price(self, asset: str, chain: str) -> Optional[float]:
        """Get current price of asset on specific chain"""
        try:
            cache_key = f"{asset}_{chain}"
            if cache_key in self.price_cache:
                return self.price_cache[cache_key].get(asset)
            
            # Mock implementation - would call chain-specific price feeds
            prices = {
                "ethereum_USDC": 1.0,
                "polygon_USDC": 0.9995,
                "optimism_USDC": 1.0005,
                "arbitrum_USDC": 1.001,
            }
            
            price = prices.get(f"{chain}_{asset}")
            if price:
                self.price_cache[cache_key] = {asset: price}
            
            return price
            
        except Exception as e:
            logger.error(f"Error getting price for {asset} on {chain}: {e}")
            return None
    
    async def _get_liquidity(self, asset: str, chain: str) -> float:
        """Get available liquidity for asset on chain"""
        try:
            # Mock implementation
            return 10_000_000  # 10M USD liquidity
        except Exception:
            return 0
    
    def _calculate_profit(self, spread_pct: float, fee_pct: float, position_size: float) -> float:
        """Calculate estimated profit from bridge arbitrage"""
        net_spread = spread_pct - (2 * fee_pct)  # Account for bridge fee both ways
        return (net_spread / 100) * position_size
    
    async def _execute_swap_on_chain(
        self, chain: str, asset: str, amount: float, direction: str
    ) -> Optional[Dict]:
        """Execute a swap on specific chain"""
        try:
            # Mock implementation
            return {
                "tx_hash": f"0x{'0' * 64}",
                "amount": amount,
                "asset": asset,
                "chain": chain,
                "direction": direction,
            }
        except Exception as e:
            logger.error(f"Error executing swap on {chain}: {e}")
            return None
    
    async def _bridge_tokens(
        self, asset: str, source_chain: str, dest_chain: str, amount: float
    ) -> Optional[Dict]:
        """Bridge tokens from source to destination chain"""
        try:
            # Mock implementation
            return {
                "tx_hash": f"0x{'1' * 64}",
                "asset": asset,
                "source_chain": source_chain,
                "dest_chain": dest_chain,
                "amount": amount,
            }
        except Exception as e:
            logger.error(f"Error bridging {asset}: {e}")
            return None
    
    def _filter_profitable_opportunities(self, opportunities: List[BridgeOpportunity]) -> List[BridgeOpportunity]:
        """Filter opportunities to only profitable ones after all fees"""
        return [opp for opp in opportunities if opp.estimated_profit_eth > 0.1]
    
    def get_opportunity_stats(self) -> Dict:
        """Get statistics about bridge opportunities"""
        if not self.opportunities:
            return {
                "total": 0,
                "by_asset": {},
                "by_path": {},
                "total_profit_eth": 0,
                "avg_spread_pct": 0,
            }
        
        by_asset = {}
        by_path = {}
        total_profit = 0
        total_spread = 0
        
        for opp in self.opportunities:
            by_asset[opp.asset] = by_asset.get(opp.asset, 0) + 1
            path = f"{opp.source_chain}→{opp.dest_chain}"
            by_path[path] = by_path.get(path, 0) + 1
            total_profit += opp.estimated_profit_eth
            total_spread += opp.spread_pct
        
        avg_spread = total_spread / len(self.opportunities) if self.opportunities else 0
        
        return {
            "total": len(self.opportunities),
            "by_asset": by_asset,
            "by_path": by_path,
            "total_profit_eth": total_profit,
            "avg_spread_pct": avg_spread,
        }
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.monitoring_active = False


# Example usage
async def example_usage():
    monitor = BridgeMonitor()
    
    # Detect opportunities
    opportunities = await monitor.detect_all_bridge_opportunities()
    print(f"Found {len(opportunities)} bridge opportunities")
    
    # Get statistics
    stats = monitor.get_opportunity_stats()
    print("Bridge Stats:", stats)


if __name__ == "__main__":
    asyncio.run(example_usage())
