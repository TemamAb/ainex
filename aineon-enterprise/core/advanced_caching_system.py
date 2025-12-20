"""
Advanced Caching System - Code Optimizations Only
Target: 10x performance improvement through intelligent caching

Advanced Features:
- Multi-level cache hierarchy (L1: Memory, L2: Disk, L3: Distributed)
- Intelligent cache eviction policies
- Predictive pre-caching
- Cache warming strategies
- Real-time cache optimization
- Memory-efficient data structures
- Concurrent access optimization
"""

import asyncio
import time
import pickle
import hashlib
import weakref
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque, OrderedDict
from enum import Enum
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

# Performance monitoring
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheLevel(Enum):
    """Cache hierarchy levels"""
    L1_MEMORY = "l1_memory"
    L2_DISK = "l2_disk"
    L3_DISTRIBUTED = "l3_distributed"


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on access patterns


@dataclass
class CacheEntry:
    """Optimized cache entry"""
    key: str
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0
    size_bytes: int = 0
    ttl: Optional[float] = None
    priority: float = 1.0  # Higher priority = less likely to evict
    
    def __post_init__(self):
        self.last_access = self.timestamp
    
    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp
    
    @property
    def is_expired(self) -> bool:
        if self.ttl is None:
            return False
        return self.age_seconds > self.ttl
    
    def access(self):
        """Record cache access"""
        self.access_count += 1
        self.last_access = time.time()


class OptimizedMemoryCache:
    """
    L1 Memory Cache with advanced optimizations
    """
    
    def __init__(self, max_size_mb: int = 512, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.strategy = strategy
        self.cache = OrderedDict()
        self.metadata = {}  # Store metadata separately
        self.current_size = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Performance optimization settings
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
        self.access_patterns = defaultdict(list)  # Track access patterns
        
        # Memory monitoring
        self.memory_threshold = 0.8  # 80% of max size
        self.auto_cleanup_enabled = True
        
        # Thread safety
        self.lock = threading.RLock()
    
    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            if isinstance(value, (str, int, float, bool)):
                return len(str(value).encode('utf-8')) + 64  # Base overhead
            elif isinstance(value, (list, tuple)):
                return sum(self._calculate_size(item) for item in value) + 64
            elif isinstance(value, dict):
                return sum(self._calculate_size(k) + self._calculate_size(v) for k, v in value.items()) + 64
            else:
                # For complex objects, use pickle
                return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)) + 64
        except Exception:
            return 1024  # Default size estimate
    
    def _should_evict(self) -> bool:
        """Check if eviction is needed"""
        return self.current_size >= self.max_size_bytes * self.memory_threshold
    
    def _evict_entries(self, target_size: int) -> int:
        """Evict entries to free up space"""
        evicted_count = 0
        target_freed = 0
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            while self.cache and self.current_size - target_freed > target_size:
                key, entry = self.cache.popitem(last=False)
                target_freed += entry.size_bytes
                evicted_count += 1
                del self.metadata[key]
        
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            while self.cache and self.current_size - target_freed > target_size:
                # Find entry with lowest access count
                min_access_key = min(self.metadata.keys(), 
                                   key=lambda k: self.metadata[k].access_count)
                entry = self.metadata[min_access_key]
                self.cache.pop(min_access_key, None)
                target_freed += entry.size_bytes
                evicted_count += 1
                del self.metadata[min_access_key]
        
        elif self.strategy == CacheStrategy.TTL:
            # Evict expired entries first, then LRU
            expired_keys = [k for k, v in self.metadata.items() if v.is_expired]
            for key in expired_keys:
                entry = self.metadata[key]
                if key in self.cache:
                    self.cache.pop(key)
                target_freed += entry.size_bytes
                evicted_count += 1
                del self.metadata[key]
            
            # If still need space, evict LRU
            while self.cache and self.current_size - target_freed > target_size:
                key, entry = self.cache.popitem(last=False)
                target_freed += entry.size_bytes
                evicted_count += 1
                del self.metadata[key]
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Adaptive eviction based on access patterns
            while self.cache and self.current_size - target_freed > target_size:
                # Calculate adaptive score for each entry
                adaptive_scores = {}
                current_time = time.time()
                
                for key, entry in self.cache.items():
                    # Score based on: access frequency, recency, priority, and TTL
                    recency_score = 1.0 / (1.0 + (current_time - entry.last_access))
                    frequency_score = entry.access_count / max(1, entry.age_seconds)
                    priority_score = entry.priority
                    ttl_score = 1.0 if not entry.is_expired else 0.1
                    
                    # Weighted adaptive score
                    adaptive_scores[key] = (
                        frequency_score * 0.4 +
                        recency_score * 0.3 +
                        priority_score * 0.2 +
                        ttl_score * 0.1
                    )
                
                # Evict entry with lowest adaptive score
                if adaptive_scores:
                    worst_key = min(adaptive_scores.keys(), key=lambda k: adaptive_scores[k])
                    entry = self.metadata[worst_key]
                    self.cache.pop(worst_key, None)
                    target_freed += entry.size_bytes
                    evicted_count += 1
                    del self.metadata[worst_key]
        
        self.current_size -= target_freed
        self.evictions += evicted_count
        return evicted_count
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with O(1) lookup"""
        with self.lock:
            # Check if key exists
            if key not in self.metadata:
                self.misses += 1
                return None
            
            entry = self.metadata[key]
            
            # Check if expired
            if entry.is_expired:
                self._remove(key)
                self.misses += 1
                return None
            
            # Update access statistics
            entry.access()
            
            # Move to end for LRU
            if self.strategy == CacheStrategy.LRU:
                value = self.cache.pop(key)
                self.cache[key] = value
            
            self.hits += 1
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None, priority: float = 1.0) -> bool:
        """Put value in cache with intelligent eviction"""
        with self.lock:
            # Calculate size
            size = self._calculate_size(value)
            
            # Check if key already exists
            if key in self.metadata:
                # Update existing entry
                old_entry = self.metadata[key]
                self.current_size -= old_entry.size_bytes
                self.cache.pop(key, None)
            
            # Check if we need to evict
            while self.current_size + size > self.max_size_bytes and self.cache:
                target_size = self.current_size + size - self.max_size_bytes * 0.9  # Leave 10% buffer
                evicted = self._evict_entries(target_size)
                if evicted == 0:  # Can't evict anymore
                    return False
            
            # Add new entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                size_bytes=size,
                ttl=ttl,
                priority=priority
            )
            
            self.metadata[key] = entry
            self.cache[key] = value  # Keep value in OrderedDict for LRU
            self.current_size += size
            
            return True
    
    def _remove(self, key: str):
        """Remove entry from cache"""
        if key in self.metadata:
            entry = self.metadata[key]
            self.current_size -= entry.size_bytes
            del self.metadata[key]
            self.cache.pop(key, None)
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.metadata.items():
                if entry.is_expired:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove(key)
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions,
                'current_size_mb': self.current_size / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'utilization': self.current_size / self.max_size_bytes,
                'entries': len(self.cache),
                'strategy': self.strategy.value
            }


class DiskCache:
    """
    L2 Disk Cache for persistent storage
    """
    
    def __init__(self, cache_dir: str = "./cache", max_size_gb: int = 2):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        self.index_file = os.path.join(cache_dir, ".cache_index")
        self.lock = threading.RLock()
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load index
        self.index = self._load_index()
        
        # Cleanup on initialization
        self._cleanup_oversized()
    
    def _load_index(self) -> Dict:
        """Load cache index from disk"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'rb') as f:
                    return pickle.load(f)
        except Exception:
            pass
        return {}
    
    def _save_index(self):
        """Save cache index to disk"""
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.index, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Warning: Failed to save cache index: {e}")
    
    def _get_file_path(self, key: str) -> str:
        """Get file path for key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache"""
        with self.lock:
            if key not in self.index:
                return None
            
            file_path = self._get_file_path(key)
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                    
                # Check TTL
                if 'ttl' in data and data['ttl']:
                    if time.time() > data['timestamp'] + data['ttl']:
                        self._remove(key)
                        return None
                
                return data['value']
            except Exception:
                # Corrupted cache file
                self._remove(key)
                return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Put value in disk cache"""
        with self.lock:
            try:
                file_path = self._get_file_path(key)
                
                # Check if we need to cleanup
                self._cleanup_oversized()
                
                # Prepare data
                data = {
                    'value': value,
                    'timestamp': time.time(),
                    'ttl': ttl
                }
                
                # Write to disk
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                
                # Update index
                self.index[key] = {
                    'file': file_path,
                    'size': os.path.getsize(file_path),
                    'timestamp': time.time()
                }
                
                self._save_index()
                return True
                
            except Exception:
                return False
    
    def _remove(self, key: str):
        """Remove entry from disk cache"""
        if key in self.index:
            try:
                file_path = self.index[key]['file']
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass
            del self.index[key]
            self._save_index()
    
    def _cleanup_oversized(self):
        """Cleanup if cache exceeds size limit"""
        total_size = sum(entry['size'] for entry in self.index.values())
        
        if total_size <= self.max_size_bytes:
            return
        
        # Sort by timestamp (oldest first)
        sorted_entries = sorted(
            self.index.items(),
            key=lambda x: x[1]['timestamp']
        )
        
        # Remove oldest entries until under limit
        target_size = self.max_size_bytes * 0.9
        for key, _ in sorted_entries:
            if total_size <= target_size:
                break
            self._remove(key)
            total_size = sum(entry['size'] for entry in self.index.values())


class AdvancedCachingSystem:
    """
    Multi-level caching system with intelligent coordination
    """
    
    def __init__(self, 
                 l1_size_mb: int = 512,
                 l2_size_gb: int = 2,
                 enable_l3: bool = False):
        
        # Initialize cache levels
        self.l1_cache = OptimizedMemoryCache(l1_size_mb)
        self.l2_cache = DiskCache(max_size_gb=l2_size_gb)
        self.enable_l3 = enable_l3 and REDIS_AVAILABLE
        
        if self.enable_l3:
            try:
                self.l3_cache = redis.Redis(host='localhost', port=6379, db=0)
            except Exception:
                self.enable_l3 = False
        
        # Performance tracking
        self.request_stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'l3_hits': 0,
            'misses': 0,
            'total_requests': 0
        }
        
        # Predictive pre-caching
        self.access_patterns = defaultdict(list)
        self.predictive_cache = set()
        
        # Background tasks
        self.cleanup_task = None
        self.start_background_tasks()
    
    def start_background_tasks(self):
        """Start background maintenance tasks"""
        def cleanup_loop():
            while True:
                try:
                    # L1 cache cleanup
                    self.l1_cache.cleanup_expired()
                    
                    # Update access patterns
                    self._analyze_access_patterns()
                    
                    time.sleep(30)  # Run every 30 seconds
                except Exception as e:
                    print(f"Cache cleanup error: {e}")
                    time.sleep(60)
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Multi-level cache get with intelligent fallback"""
        start_time = time.time()
        
        # Record access pattern
        self.access_patterns[key].append(time.time())
        
        # Try L1 cache first (fastest)
        value = self.l1_cache.get(key)
        if value is not None:
            self.request_stats['l1_hits'] += 1
            self.request_stats['total_requests'] += 1
            return value
        
        # Try L2 cache (persistent)
        value = self.l2_cache.get(key)
        if value is not None:
            self.request_stats['l2_hits'] += 1
            self.request_stats['total_requests'] += 1
            
            # Promote to L1 cache
            self.l1_cache.put(key, value)
            return value
        
        # Try L3 cache if enabled (distributed)
        if self.enable_l3:
            try:
                l3_value = self.l3_cache.get(key)
                if l3_value is not None:
                    self.request_stats['l3_hits'] += 1
                    self.request_stats['total_requests'] += 1
                    
                    # Promote to upper levels
                    self.l2_cache.put(key, l3_value)
                    self.l1_cache.put(key, l3_value)
                    return pickle.loads(l3_value)
            except Exception:
                pass
        
        # Cache miss
        self.request_stats['misses'] += 1
        self.request_stats['total_requests'] += 1
        return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None, 
            promote_immediately: bool = True) -> bool:
        """Multi-level cache put with intelligent promotion"""
        
        success = True
        
        # Put in L1 cache (always)
        if not self.l1_cache.put(key, value, ttl):
            success = False
        
        # Put in L2 cache (persistent)
        if not self.l2_cache.put(key, value, ttl):
            success = False
        
        # Put in L3 cache if enabled
        if self.enable_l3:
            try:
                serialized_value = pickle.dumps(value)
                self.l3_cache.setex(key, int(ttl) if ttl else 3600, serialized_value)
            except Exception:
                success = False
        
        return success
    
    def _analyze_access_patterns(self):
        """Analyze access patterns for predictive caching"""
        current_time = time.time()
        
        for key, access_times in self.access_patterns.items():
            # Remove old access times (older than 1 hour)
            recent_accesses = [t for t in access_times if current_time - t < 3600]
            self.access_patterns[key] = recent_accesses
            
            # If accessed frequently, add to predictive cache
            if len(recent_accesses) >= 5:  # Accessed 5+ times in last hour
                self.predictive_cache.add(key)
    
    def get_predictive_values(self, limit: int = 10) -> List[str]:
        """Get list of keys that should be pre-cached"""
        # Sort by access frequency
        sorted_keys = sorted(
            self.predictive_cache,
            key=lambda k: len(self.access_patterns.get(k, [])),
            reverse=True
        )
        return sorted_keys[:limit]
    
    def prefetch(self, key: str, fetch_function) -> bool:
        """Prefetch value using provided function"""
        try:
            value = fetch_function(key)
            if value is not None:
                self.put(key, value)
                return True
        except Exception:
            pass
        return False
    
    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        total_requests = self.request_stats['total_requests']
        
        return {
            'l1_cache': l1_stats,
            'l2_cache': {
                'entries': len(self.l2_cache.index),
                'total_size_gb': sum(entry['size'] for entry in self.l2_cache.index.values()) / (1024**3)
            },
            'performance': {
                'l1_hit_rate': self.request_stats['l1_hits'] / total_requests if total_requests > 0 else 0,
                'l2_hit_rate': self.request_stats['l2_hits'] / total_requests if total_requests > 0 else 0,
                'l3_hit_rate': self.request_stats['l3_hits'] / total_requests if total_requests > 0 else 0,
                'overall_hit_rate': (self.request_stats['l1_hits'] + self.request_stats['l2_hits'] + self.request_stats['l3_hits']) / total_requests if total_requests > 0 else 0,
                'total_requests': total_requests
            },
            'predictive_cache': {
                'predictive_keys': len(self.predictive_cache),
                'access_patterns': len(self.access_patterns)
            }
        }
    
    def optimize_cache(self):
        """Optimize cache performance"""
        # Analyze L1 cache hit rate
        l1_stats = self.l1_cache.get_stats()
        
        if l1_stats['hit_rate'] < 0.8:
            # Increase L1 cache size
            new_size = int(l1_stats['max_size_mb'] * 1.5)
            self.l1_cache = OptimizedMemoryCache(new_size, self.l1_cache.strategy)
        
        # Clean up old access patterns
        current_time = time.time()
        old_keys = []
        
        for key, access_times in self.access_patterns.items():
            # Remove keys not accessed in last 24 hours
            if not access_times or current_time - max(access_times) > 86400:
                old_keys.append(key)
        
        for key in old_keys:
            del self.access_patterns[key]
            self.predictive_cache.discard(key)
    
    async def benchmark_cache_performance(self, iterations: int = 10000) -> Dict:
        """Benchmark cache performance"""
        print(f"Starting cache performance benchmark ({iterations} iterations)...")
        
        # Generate test data
        test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
        
        # Warm up cache
        for key, value in test_data.items():
            self.put(key, value)
        
        # Benchmark get operations
        start_time = time.time()
        hits = 0
        
        for i in range(iterations):
            key = f"key_{i % 1000}"
            if self.get(key) is not None:
                hits += 1
        
        get_time = time.time() - start_time
        
        # Benchmark put operations
        start_time = time.time()
        puts = 0
        
        for i in range(iterations):
            key = f"new_key_{i}"
            if self.put(key, f"new_value_{i}" * 50):
                puts += 1
        
        put_time = time.time() - start_time
        
        # Get final statistics
        stats = self.get_cache_stats()
        
        print(f"Benchmark Results:")
        print(f"  Get Operations: {iterations} in {get_time:.3f}s ({iterations/get_time:.0f} ops/sec)")
        print(f"  Put Operations: {puts} in {put_time:.3f}s ({puts/put_time:.0f} ops/sec)")
        print(f"  L1 Hit Rate: {stats['performance']['l1_hit_rate']:.1%}")
        print(f"  Overall Hit Rate: {stats['performance']['overall_hit_rate']:.1%}")
        print(f"  L1 Cache Size: {stats['l1_cache']['current_size_mb']:.1f}MB")
        print(f"  L2 Cache Entries: {stats['l2_cache']['entries']}")
        
        return {
            'get_operations_per_second': iterations / get_time,
            'put_operations_per_second': puts / put_time,
            'hit_rates': stats['performance'],
            'cache_sizes': {
                'l1_mb': stats['l1_cache']['current_size_mb'],
                'l2_entries': stats['l2_cache']['entries']
            }
        }


async def main():
    """Test advanced caching system"""
    print("Testing Advanced Caching System...")
    
    # Create caching system
    cache_system = AdvancedCachingSystem(
        l1_size_mb=128,
        l2_size_gb=1,
        enable_l3=False  # Disable Redis for testing
    )
    
    # Run benchmark
    await cache_system.benchmark_cache_performance(5000)
    
    # Test predictive caching
    print("\nTesting predictive caching...")
    
    # Simulate access patterns
    for i in range(100):
        key = f"frequent_key_{i % 10}"  # Access same 10 keys frequently
        cache_system.get(key)
    
    # Show predictive cache
    predictive_keys = cache_system.get_predictive_values()
    print(f"Predictive cache keys: {predictive_keys[:5]}")
    
    # Final statistics
    print("\nFinal Cache Statistics:")
    stats = cache_system.get_cache_stats()
    print(json.dumps(stats, indent=2, default=str))
    
    print("\nAdvanced Caching System ready for integration!")


if __name__ == "__main__":
    asyncio.run(main())