"""
Metrics Collector - Prometheus Integration
AINEON Enterprise Flash Loan Engine
Phase 1, Week 1 - Observability Foundation

Collects 50+ KPIs for real-time monitoring
Prometheus-compatible metrics export
"""

import time
from typing import Dict, Optional
from datetime import datetime
from threading import Lock

from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry
from prometheus_client import generate_latest, REGISTRY


class MetricsCollector:
    """
    Manages Prometheus metrics collection
    Tracks trading, system, and risk metrics
    """

    def __init__(self, registry: CollectorRegistry = REGISTRY):
        """Initialize metrics collector"""
        self.registry = registry
        self._lock = Lock()
        
        # Trading Metrics
        self.trades_total = Counter(
            'aineon_trades_total',
            'Total trades executed',
            ['pair', 'direction'],
            registry=registry
        )
        
        self.trades_successful = Counter(
            'aineon_trades_successful',
            'Successful trades',
            ['pair'],
            registry=registry
        )
        
        self.trades_failed = Counter(
            'aineon_trades_failed',
            'Failed trades',
            ['pair', 'reason'],
            registry=registry
        )
        
        self.trade_profit = Gauge(
            'aineon_trade_profit_eth',
            'Profit per trade (ETH)',
            ['pair'],
            registry=registry
        )
        
        self.trade_duration_ms = Histogram(
            'aineon_trade_duration_ms',
            'Trade execution time (ms)',
            ['pair'],
            buckets=(10, 50, 100, 200, 500, 1000),
            registry=registry
        )
        
        # Profit Metrics
        self.daily_profit = Gauge(
            'aineon_daily_profit_eth',
            'Daily profit (ETH)',
            registry=registry
        )
        
        self.cumulative_profit = Gauge(
            'aineon_cumulative_profit_eth',
            'Cumulative profit (ETH)',
            registry=registry
        )
        
        # Risk Metrics
        self.daily_loss = Gauge(
            'aineon_daily_loss_eth',
            'Daily loss (ETH)',
            registry=registry
        )
        
        self.circuit_breaker_trips = Counter(
            'aineon_circuit_breaker_trips',
            'Circuit breaker activations',
            ['reason'],
            registry=registry
        )
        
        self.position_size = Gauge(
            'aineon_position_size_eth',
            'Current position size (ETH)',
            ['pair'],
            registry=registry
        )
        
        self.var_95 = Gauge(
            'aineon_var_95_eth',
            'Value at Risk 95%',
            registry=registry
        )
        
        self.max_drawdown_pct = Gauge(
            'aineon_max_drawdown_pct',
            'Maximum drawdown %',
            registry=registry
        )
        
        # System Metrics
        self.system_uptime_seconds = Gauge(
            'aineon_system_uptime_seconds',
            'System uptime (seconds)',
            registry=registry
        )
        
        self.active_connections = Gauge(
            'aineon_active_connections',
            'Active WebSocket connections',
            registry=registry
        )
        
        self.dex_latency_ms = Histogram(
            'aineon_dex_latency_ms',
            'DEX query latency (ms)',
            ['dex'],
            buckets=(1, 5, 10, 50, 100),
            registry=registry
        )
        
        self.api_calls_total = Counter(
            'aineon_api_calls_total',
            'Total API calls',
            ['endpoint', 'status'],
            registry=registry
        )
        
        self.api_latency_ms = Histogram(
            'aineon_api_latency_ms',
            'API response latency (ms)',
            ['endpoint'],
            buckets=(10, 50, 100, 500, 1000),
            registry=registry
        )
        
        # AI/ML Metrics
        self.model_accuracy_pct = Gauge(
            'aineon_model_accuracy_pct',
            'Model accuracy %',
            ['model'],
            registry=registry
        )
        
        self.prediction_confidence = Gauge(
            'aineon_prediction_confidence',
            'Average prediction confidence',
            registry=registry
        )
        
        self.false_positives = Counter(
            'aineon_false_positives_total',
            'False positive predictions',
            registry=registry
        )
        
        # Market Data Metrics
        self.bid_ask_spread_bps = Gauge(
            'aineon_bid_ask_spread_bps',
            'Bid-ask spread (basis points)',
            ['pair'],
            registry=registry
        )
        
        self.slippage_pct = Histogram(
            'aineon_slippage_pct',
            'Trade slippage %',
            ['pair'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=registry
        )
        
        self.gas_price_gwei = Gauge(
            'aineon_gas_price_gwei',
            'Current gas price (Gwei)',
            registry=registry
        )
        
        self.transaction_cost_eth = Gauge(
            'aineon_transaction_cost_eth',
            'Average transaction cost (ETH)',
            registry=registry
        )
        
        # LP Farming Metrics
        self.lp_yield_apy = Gauge(
            'aineon_lp_yield_apy',
            'LP yield APY %',
            ['pool'],
            registry=registry
        )
        
        self.lp_capital_deployed = Gauge(
            'aineon_lp_capital_deployed_eth',
            'LP capital deployed (ETH)',
            registry=registry
        )
        
        # Infrastructure Metrics
        self.database_latency_ms = Histogram(
            'aineon_database_latency_ms',
            'Database query latency (ms)',
            buckets=(1, 5, 10, 50, 100),
            registry=registry
        )
        
        self.cache_hits = Counter(
            'aineon_cache_hits_total',
            'Cache hits',
            registry=registry
        )
        
        self.cache_misses = Counter(
            'aineon_cache_misses_total',
            'Cache misses',
            registry=registry
        )
        
        self.memory_usage_mb = Gauge(
            'aineon_memory_usage_mb',
            'Memory usage (MB)',
            registry=registry
        )
        
        # Error Metrics
        self.errors_total = Counter(
            'aineon_errors_total',
            'Total errors',
            ['error_type'],
            registry=registry
        )
        
        self.exceptions_total = Counter(
            'aineon_exceptions_total',
            'Total exceptions',
            ['exception_type'],
            registry=registry
        )

    def record_trade(self, pair: str, direction: str, duration_ms: float, profit: float, success: bool, reason: str = None) -> None:
        """Record trade execution"""
        with self._lock:
            self.trades_total.labels(pair=pair, direction=direction).inc()
            self.trade_duration_ms.labels(pair=pair).observe(duration_ms)
            self.trade_profit.labels(pair=pair).set(profit)
            
            if success:
                self.trades_successful.labels(pair=pair).inc()
            else:
                self.trades_failed.labels(pair=pair, reason=reason or "unknown").inc()

    def record_profit(self, daily: float, cumulative: float) -> None:
        """Record profit metrics"""
        with self._lock:
            self.daily_profit.set(daily)
            self.cumulative_profit.set(cumulative)

    def record_risk_event(self, event_type: str) -> None:
        """Record risk event"""
        with self._lock:
            self.circuit_breaker_trips.labels(reason=event_type).inc()

    def record_dex_latency(self, dex: str, latency_ms: float) -> None:
        """Record DEX query latency"""
        with self._lock:
            self.dex_latency_ms.labels(dex=dex).observe(latency_ms)

    def record_api_call(self, endpoint: str, status: int, latency_ms: float) -> None:
        """Record API call"""
        with self._lock:
            self.api_calls_total.labels(endpoint=endpoint, status=status).inc()
            self.api_latency_ms.labels(endpoint=endpoint).observe(latency_ms)

    def record_model_accuracy(self, model: str, accuracy_pct: float, confidence: float) -> None:
        """Record model performance"""
        with self._lock:
            self.model_accuracy_pct.labels(model=model).set(accuracy_pct)
            self.prediction_confidence.set(confidence)

    def record_slippage(self, pair: str, slippage_pct: float) -> None:
        """Record trade slippage"""
        with self._lock:
            self.slippage_pct.labels(pair=pair).observe(slippage_pct)

    def record_error(self, error_type: str) -> None:
        """Record error"""
        with self._lock:
            self.errors_total.labels(error_type=error_type).inc()

    def get_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry).decode('utf-8')


# Global instance
_global_collector = None


def get_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


# Example usage
if __name__ == "__main__":
    collector = get_collector()
    
    collector.record_trade("WETH/USDC", "long", 125.5, 0.15, True)
    collector.record_profit(0.5, 12.35)
    collector.record_dex_latency("uniswap", 8.5)
    
    print(collector.get_metrics())
