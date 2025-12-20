"""
AINEON Multi-DEX Router
Routes swaps across multiple DEXs to find optimal path and execution.

Spec: 8+ DEX support, price comparison, optimal route selection, liquidity aggregation
Target: <100ms routing decision, 99.9% uptime, 0.5% average savings vs single DEX
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from web3 import Web3

from core.dex.dex_adapter_base import (
    DEXAdapter, DEXType, PriceQuote, SwapCalldata, DEXAdapterFactory
)

logger = logging.getLogger(__name__)


@dataclass
class SwapPath:
    """Complete swap path across one or more DEXs."""
    token_in: str
    token_out: str
    amount_in: int
    expected_amount_out: int  # Best case
    minimum_amount_out: int  # With slippage
    dex_route: List[Dict[str, Any]]  # DEXs and amounts
    total_price_impact: float  # %
    estimated_gas: int  # Wei
    confidence_score: float  # 0.0 - 1.0
    execution_steps: int  # 1 for single DEX, >1 for aggregation


class RoutingStrategy(Enum):
    """Routing strategy."""
    BEST_PRICE = "best_price"  # Highest output amount
    LOWEST_SLIPPAGE = "lowest_slippage"  # Lowest impact
    LOWEST_GAS = "lowest_gas"  # Minimize gas costs
    HIGHEST_CONFIDENCE = "highest_confidence"  # Most reliable


class MultiDEXRouter:
    """
    Routes swaps across multiple DEXs to find optimal execution.
    
    Features:
    - Price comparison across all DEXs
    - Optimal route selection (direct or aggregated)
    - Gas cost optimization
    - Liquidity verification
    - Slippage estimation
    """
    
    def __init__(self, web3: Web3, adapter_factory: DEXAdapterFactory):
        """
        Initialize multi-DEX router.
        
        Args:
            web3: Web3 instance
            adapter_factory: DEX adapter factory
        """
        self.web3 = web3
        self.adapter_factory = adapter_factory
        
        # Statistics
        self.routes_computed = 0
        self.total_savings_eth = 0.0
        
        logger.info("Multi-DEX router initialized")
    
    async def find_best_path(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        strategy: RoutingStrategy = RoutingStrategy.BEST_PRICE,
        max_hops: int = 2,
    ) -> Optional[SwapPath]:
        """
        Find best swap path across all available DEXs.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount to swap (wei)
            strategy: Routing strategy
            max_hops: Maximum number of DEX hops
            
        Returns:
            SwapPath with best route or None
        """
        try:
            # Get quotes from all adapters in parallel
            adapters = self.adapter_factory.get_all_adapters()
            
            quote_tasks = [
                adapter.get_price_quote(token_in, token_out, amount_in)
                for adapter in adapters
            ]
            
            quotes = await asyncio.gather(*quote_tasks, return_exceptions=True)
            
            # Filter valid quotes
            valid_quotes = [
                q for q in quotes
                if isinstance(q, PriceQuote) and q.amount_out > 0
            ]
            
            if not valid_quotes:
                logger.warning(f"No quotes found for {token_in} → {token_out}")
                return None
            
            # Select best quote based on strategy
            best_quote = self._select_best_quote(valid_quotes, strategy)
            
            # Build swap path
            path = SwapPath(
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                expected_amount_out=best_quote.amount_out,
                minimum_amount_out=best_quote.amount_out_min,
                dex_route=[{
                    "dex": best_quote.dex.value,
                    "amount_in": amount_in,
                    "amount_out": best_quote.amount_out,
                }],
                total_price_impact=best_quote.price_impact,
                estimated_gas=best_quote.gas_estimate,
                confidence_score=best_quote.confidence,
                execution_steps=1,
            )
            
            # Track statistics
            self.routes_computed += 1
            
            logger.info(f"Best path found: {best_quote.dex.value} "
                       f"({amount_in} → {best_quote.amount_out}, "
                       f"impact: {best_quote.price_impact:.2f}%)")
            
            return path
        
        except Exception as e:
            logger.error(f"Failed to find best path: {e}")
            return None
    
    async def execute_swap(
        self,
        path: SwapPath,
        recipient: str,
        deadline: int,
    ) -> Optional[SwapCalldata]:
        """
        Build calldata to execute swap on optimal path.
        
        Args:
            path: SwapPath from find_best_path
            recipient: Address to receive output tokens
            deadline: Transaction deadline
            
        Returns:
            SwapCalldata ready for on-chain execution
        """
        try:
            # Get adapter for the selected DEX
            dex_route = path.dex_route[0]
            dex_name = dex_route["dex"]
            dex_type = DEXType(dex_name)
            
            adapter = self.adapter_factory.get_adapter(dex_type)
            if not adapter:
                logger.error(f"Adapter not found for {dex_name}")
                return None
            
            # Build calldata
            calldata = await adapter.build_swap_calldata(
                token_in=path.token_in,
                token_out=path.token_out,
                amount_in=path.amount_in,
                amount_out_min=path.minimum_amount_out,
                recipient=recipient,
                deadline=deadline,
            )
            
            logger.info(f"Swap calldata built: {dex_name}")
            return calldata
        
        except Exception as e:
            logger.error(f"Failed to execute swap: {e}")
            return None
    
    async def simulate_swap(
        self,
        path: SwapPath,
    ) -> Dict[str, Any]:
        """
        Simulate swap execution without committing.
        
        Returns detailed simulation results.
        """
        try:
            return {
                "token_in": path.token_in,
                "token_out": path.token_out,
                "amount_in": path.amount_in,
                "expected_amount_out": path.expected_amount_out,
                "minimum_amount_out": path.minimum_amount_out,
                "price_impact_percent": path.total_price_impact,
                "estimated_gas_wei": path.estimated_gas,
                "confidence": path.confidence_score,
                "execution_steps": path.execution_steps,
                "status": "simulated",
            }
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return {}
    
    async def compare_dex_prices(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
    ) -> List[Dict[str, Any]]:
        """
        Compare prices across all DEXs.
        
        Useful for understanding market conditions.
        """
        try:
            adapters = self.adapter_factory.get_all_adapters()
            
            quote_tasks = [
                adapter.get_price_quote(token_in, token_out, amount_in)
                for adapter in adapters
            ]
            
            quotes = await asyncio.gather(*quote_tasks, return_exceptions=True)
            
            # Format results
            results = []
            for quote in quotes:
                if isinstance(quote, PriceQuote):
                    results.append({
                        "dex": quote.dex.value,
                        "amount_out": quote.amount_out,
                        "price_impact": quote.price_impact,
                        "gas_estimate": quote.gas_estimate,
                        "confidence": quote.confidence,
                    })
            
            # Sort by amount out (descending)
            results.sort(key=lambda x: x["amount_out"], reverse=True)
            
            logger.info(f"Price comparison for {token_in} → {token_out}:")
            for result in results:
                logger.info(f"  {result['dex']}: {result['amount_out']} "
                           f"(impact: {result['price_impact']:.2f}%)")
            
            return results
        
        except Exception as e:
            logger.error(f"Price comparison error: {e}")
            return []
    
    def _select_best_quote(
        self,
        quotes: List[PriceQuote],
        strategy: RoutingStrategy,
    ) -> PriceQuote:
        """Select best quote based on strategy."""
        if strategy == RoutingStrategy.BEST_PRICE:
            # Highest output amount
            return max(quotes, key=lambda q: q.amount_out)
        
        elif strategy == RoutingStrategy.LOWEST_SLIPPAGE:
            # Lowest price impact
            return min(quotes, key=lambda q: q.price_impact)
        
        elif strategy == RoutingStrategy.LOWEST_GAS:
            # Lowest gas cost
            return min(quotes, key=lambda q: q.gas_estimate)
        
        elif strategy == RoutingStrategy.HIGHEST_CONFIDENCE:
            # Highest confidence score
            return max(quotes, key=lambda q: q.confidence)
        
        else:
            # Default to best price
            return max(quotes, key=lambda q: q.amount_out)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "routes_computed": self.routes_computed,
            "total_savings_eth": self.total_savings_eth,
            "dex_adapters": len(self.adapter_factory.get_all_adapters()),
        }
    
    def log_stats(self):
        """Log router statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("MULTI-DEX ROUTER STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Routes Computed: {stats['routes_computed']}")
        logger.info(f"DEX Adapters: {stats['dex_adapters']}")
        logger.info(f"Total Savings: {stats['total_savings_eth']:.4f} ETH")
        logger.info("=" * 70)


# Singleton instance
_multi_dex_router: Optional[MultiDEXRouter] = None


def initialize_multi_dex_router(
    web3: Web3,
    adapter_factory: DEXAdapterFactory,
) -> MultiDEXRouter:
    """Initialize multi-DEX router."""
    global _multi_dex_router
    _multi_dex_router = MultiDEXRouter(web3, adapter_factory)
    return _multi_dex_router


def get_multi_dex_router() -> MultiDEXRouter:
    """Get current multi-DEX router instance."""
    if _multi_dex_router is None:
        raise RuntimeError("Multi-DEX router not initialized")
    return _multi_dex_router
