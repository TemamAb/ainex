import time
from contextlib import asynccontextmanager
from collections import defaultdict
from typing import Dict, List
import logging
import statistics

logger = logging.getLogger(__name__)

class LatencyTracer:
    def __init__(self):
        self.timings = defaultdict(list)  # {component: [timing1, timing2, ...]}
        self.trace_enabled = True
        self.max_samples_per_component = 10000  # Rolling window
    
    @asynccontextmanager
    async def trace(self, component_name: str):
        """Microsecond-precision async timing for any component"""
        start_ns = time.perf_counter_ns()
        try:
            yield
        finally:
            if self.trace_enabled:
                elapsed_ns = time.perf_counter_ns() - start_ns
                elapsed_us = elapsed_ns / 1000  # Convert to microseconds
                
                # Keep rolling window
                timings_list = self.timings[component_name]
                if len(timings_list) >= self.max_samples_per_component:
                    timings_list = timings_list[-9999:]  # Keep last 9999
                
                timings_list.append(elapsed_us)
    
    def get_stats(self, component_name: str) -> Dict:
        """Get latency statistics for component"""
        times = self.timings[component_name]
        if not times:
            return None
        
        return {
            "min_us": min(times),
            "max_us": max(times),
            "avg_us": statistics.mean(times),
            "median_us": statistics.median(times),
            "p99_us": statistics.quantiles(times, n=100)[98] if len(times) > 100 else max(times),
            "p95_us": statistics.quantiles(times, n=20)[18] if len(times) > 20 else max(times),
            "samples": len(times),
        }
    
    def get_all_stats(self) -> Dict:
        """Get stats for all components"""
        return {
            component: self.get_stats(component)
            for component in self.timings.keys()
        }
    
    def print_summary(self):
        """Print latency summary for optimization"""
        print("\n" + "="*60)
        print("LATENCY METRICS (Microseconds)")
        print("="*60)
        
        all_stats = self.get_all_stats()
        total_end_to_end = 0
        
        components_by_contribution = sorted(
            all_stats.items(),
            key=lambda x: x[1]["avg_us"] if x[1] else 0,
            reverse=True
        )
        
        for component, stats in components_by_contribution:
            if stats:
                print(f"\n{component}:")
                print(f"  Avg: {stats['avg_us']:>7.1f} µs")
                print(f"  Min: {stats['min_us']:>7.1f} µs")
                print(f"  Max: {stats['max_us']:>7.1f} µs")
                print(f"  P99: {stats['p99_us']:>7.1f} µs")
                print(f"  P95: {stats['p95_us']:>7.1f} µs")
                total_end_to_end += stats['avg_us']
        
        print(f"\n{'='*60}")
        print(f"TOTAL END-TO-END: {total_end_to_end:.1f} µs")
        print(f"TARGET: <150 µs (Phase 1: <300 µs)")
        print(f"STATUS: {'✅ PASS' if total_end_to_end < 300 else '⚠️ NEEDS OPTIMIZATION'}")
        print("="*60 + "\n")

# Global tracer instance
tracer = LatencyTracer()

async def scan_opportunities():
    """Example usage of tracer"""
    # Component 1: Price feed ingestion
    async with tracer.trace("price_feed_ingestion"):
        # prices = await fetch_prices()  # Target: <80µs
        await asyncio.sleep(0.00008)  # Simulate 80µs
    
    # Component 2: Opportunity detection  
    async with tracer.trace("opportunity_detection"):
        # opps = await detect_arbitrage(prices)  # Target: <100µs
        await asyncio.sleep(0.0001)  # Simulate 100µs
    
    # Component 3: AI evaluation
    async with tracer.trace("ai_evaluation"):
        # scores = await evaluate_opportunities(opps)  # Target: <50µs
        await asyncio.sleep(0.00005)  # Simulate 50µs
    
    # Component 4: TX building
    async with tracer.trace("transaction_building"):
        # txs = await build_transactions(scores)  # Target: <10µs
        await asyncio.sleep(0.00001)  # Simulate 10µs
    
    # Component 5: Gas estimation
    async with tracer.trace("gas_estimation"):
        # gas = await estimate_gas(txs)  # Target: <20µs
        await asyncio.sleep(0.00002)  # Simulate 20µs
    
    # Total should be ~260µs (Phase 1 target)

async def latency_reporting_loop():
    """Periodic latency reporting"""
    while True:
        await asyncio.sleep(300)  # Report every 5 minutes
        tracer.print_summary()

import asyncio

# Example run
if __name__ == "__main__":
    async def main():
        # Run some operations to collect data
        for _ in range(10):
            await scan_opportunities()
        
        # Print summary
        tracer.print_summary()
    
    asyncio.run(main())
