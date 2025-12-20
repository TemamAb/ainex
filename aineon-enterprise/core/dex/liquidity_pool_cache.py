"""
AINEON Liquidity Pool Cache
Real-time pool state caching with TTL and update mechanisms.

Spec: Fast pool lookups, stale data detection, cache invalidation
Target: <1ms cache hits, <5 second data freshness
"""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class PoolSnapshot:
    """Snapshot of pool state at a point in time."""
    pool_id: str
    dex: str
    token_a: str
    token_b: str
    reserve_a: int  # Wei
    reserve_b: int  # Wei
    fee: int  # Basis points
    liquidity: int  # Total liquidity
    last_update: datetime
    price_a: float  # Price of token A
    price_b: float  # Price of token B
    volume_24h: int  # 24h volume
    update_count: int = 0  # Times updated


class LiquidityPoolCache:
    """
    High-performance pool cache with TTL and update tracking.
    
    Features:
    - Fast lookups (<1ms)
    - TTL-based expiration
    - Stale data detection
    - Update frequency tracking
    - Cache statistics
    """
    
    def __init__(self, ttl_seconds: int = 5, max_pools: int = 10000):
        """
        Initialize pool cache.
        
        Args:
            ttl_seconds: Time to live for cache entries
            max_pools: Maximum pools to cache
        """
        self.ttl = timedelta(seconds=ttl_seconds)
        self.max_pools = max_pools
        self.pools: Dict[str, PoolSnapshot] = {}
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.stale_count = 0
        self.updates_count = 0
        
        logger.info(f"Liquidity pool cache initialized (TTL: {ttl_seconds}s, max: {max_pools})")
    
    def get_pool(self, pool_id: str) -> Optional[PoolSnapshot]:
        """
        Get pool snapshot from cache.
        
        Args:
            pool_id: Unique pool identifier
            
        Returns:
            PoolSnapshot if fresh, None if missing or stale
        """
        if pool_id not in self.pools:
            self.misses += 1
            return None
        
        pool = self.pools[pool_id]
        
        # Check if stale
        age = datetime.now() - pool.last_update
        if age > self.ttl:
            self.stale_count += 1
            logger.debug(f"Pool {pool_id} is stale (age: {age.total_seconds():.1f}s)")
            return None  # Return None for stale data
        
        self.hits += 1
        return pool
    
    def set_pool(self, pool_snapshot: PoolSnapshot):
        """
        Cache pool snapshot.
        
        Args:
            pool_snapshot: Pool state to cache
        """
        if len(self.pools) >= self.max_pools:
            # Remove oldest pool
            oldest_id = min(
                self.pools.keys(),
                key=lambda k: self.pools[k].last_update
            )
            del self.pools[oldest_id]
            logger.debug(f"Evicted oldest pool: {oldest_id}")
        
        pool_snapshot.last_update = datetime.now()
        pool_snapshot.update_count += 1
        self.pools[pool_snapshot.pool_id] = pool_snapshot
        self.updates_count += 1
    
    def get_pair_pools(self, token_a: str, token_b: str) -> List[PoolSnapshot]:
        """
        Get all pools for token pair.
        
        Args:
            token_a: Token A address
            token_b: Token B address
            
        Returns:
            List of fresh pools for this pair
        """
        pools = []
        
        for pool in self.pools.values():
            # Check freshness
            age = datetime.now() - pool.last_update
            if age > self.ttl:
                continue
            
            # Check pair match
            if ((pool.token_a.lower() == token_a.lower() and 
                 pool.token_b.lower() == token_b.lower()) or
                (pool.token_a.lower() == token_b.lower() and 
                 pool.token_b.lower() == token_a.lower())):
                pools.append(pool)
        
        return pools
    
    def get_best_pool(
        self,
        token_a: str,
        token_b: str,
        strategy: str = "liquidity",
    ) -> Optional[PoolSnapshot]:
        """
        Get best pool for pair using strategy.
        
        Args:
            token_a: Token A
            token_b: Token B
            strategy: 'liquidity', 'fee', or 'volume'
            
        Returns:
            Best pool or None
        """
        pools = self.get_pair_pools(token_a, token_b)
        
        if not pools:
            return None
        
        if strategy == "liquidity":
            return max(pools, key=lambda p: p.liquidity)
        elif strategy == "fee":
            return min(pools, key=lambda p: p.fee)
        elif strategy == "volume":
            return max(pools, key=lambda p: p.volume_24h)
        else:
            return pools[0]
    
    def update_pool_price(
        self,
        pool_id: str,
        price_a: float,
        price_b: float,
    ):
        """Update pool prices."""
        if pool_id in self.pools:
            pool = self.pools[pool_id]
            pool.price_a = price_a
            pool.price_b = price_b
            pool.last_update = datetime.now()
    
    def invalidate_pool(self, pool_id: str):
        """Invalidate specific pool."""
        if pool_id in self.pools:
            del self.pools[pool_id]
            logger.debug(f"Invalidated pool: {pool_id}")
    
    def invalidate_pair(self, token_a: str, token_b: str):
        """Invalidate all pools for token pair."""
        to_remove = []
        for pool_id, pool in self.pools.items():
            if ((pool.token_a.lower() == token_a.lower() and 
                 pool.token_b.lower() == token_b.lower()) or
                (pool.token_a.lower() == token_b.lower() and 
                 pool.token_b.lower() == token_a.lower())):
                to_remove.append(pool_id)
        
        for pool_id in to_remove:
            del self.pools[pool_id]
        
        logger.debug(f"Invalidated {len(to_remove)} pools for pair")
    
    def clear(self):
        """Clear entire cache."""
        self.pools.clear()
        logger.info("Liquidity pool cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cached_pools": len(self.pools),
            "total_hits": self.hits,
            "total_misses": self.misses,
            "hit_rate": hit_rate,
            "stale_hits": self.stale_count,
            "total_updates": self.updates_count,
            "ttl_seconds": self.ttl.total_seconds(),
            "max_pools": self.max_pools,
        }
    
    def log_stats(self):
        """Log cache statistics."""
        stats = self.get_stats()
        logger.info("=" * 70)
        logger.info("LIQUIDITY POOL CACHE STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Cached Pools: {stats['cached_pools']} / {stats['max_pools']}")
        logger.info(f"Cache Hits: {stats['total_hits']}")
        logger.info(f"Cache Misses: {stats['total_misses']}")
        logger.info(f"Hit Rate: {stats['hit_rate']:.1f}%")
        logger.info(f"Stale Hits: {stats['stale_hits']}")
        logger.info(f"Total Updates: {stats['total_updates']}")
        logger.info(f"TTL: {stats['ttl_seconds']:.0f}s")
        logger.info("=" * 70)
    
    def get_pool_by_dex(self, dex: str) -> List[PoolSnapshot]:
        """Get all fresh pools from specific DEX."""
        pools = []
        for pool in self.pools.values():
            age = datetime.now() - pool.last_update
            if age > self.ttl:
                continue
            if pool.dex.lower() == dex.lower():
                pools.append(pool)
        return pools
    
    def get_liquidity_distribution(self) -> Dict[str, float]:
        """Get liquidity distribution across DEXs."""
        distribution = {}
        total_liquidity = 0
        
        for pool in self.pools.values():
            age = datetime.now() - pool.last_update
            if age > self.ttl:
                continue
            
            dex = pool.dex
            if dex not in distribution:
                distribution[dex] = 0
            
            distribution[dex] += pool.liquidity
            total_liquidity += pool.liquidity
        
        # Normalize to percentages
        if total_liquidity > 0:
            for dex in distribution:
                distribution[dex] = (distribution[dex] / total_liquidity) * 100
        
        return distribution


# Singleton instance
_pool_cache: Optional[LiquidityPoolCache] = None


def initialize_pool_cache(ttl_seconds: int = 5) -> LiquidityPoolCache:
    """Initialize global pool cache."""
    global _pool_cache
    _pool_cache = LiquidityPoolCache(ttl_seconds=ttl_seconds)
    return _pool_cache


def get_pool_cache() -> LiquidityPoolCache:
    """Get current pool cache instance."""
    if _pool_cache is None:
        raise RuntimeError("Pool cache not initialized")
    return _pool_cache
