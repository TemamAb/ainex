"""
Bundler Metrics - Performance tracking and monitoring
Tracks submission rates, inclusion times, and provider health
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


@dataclass
class SubmissionMetric:
    """Single submission metric"""
    timestamp: datetime
    provider: str
    user_op_hash: str
    success: bool
    inclusion_time: float = 0.0
    gas_estimate: int = 0
    gas_actual: int = 0
    profit: float = 0.0
    error_message: str = ""


class BundlerMetrics:
    """
    Bundler performance metrics tracker
    
    Monitors:
    - Submission success rates per provider
    - Bundle inclusion times
    - Gas estimation accuracy
    - Error rates and types
    """
    
    def __init__(self, window_size: int = 3600):
        """
        Initialize metrics tracker
        
        Args:
            window_size: Seconds to keep metrics (default 1 hour)
        """
        self.window_size = window_size
        self.metrics: List[SubmissionMetric] = []
        self.provider_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "submissions": 0,
            "successful": 0,
            "failed": 0,
            "inclusion_times": [],
            "gas_overestimates": [],
            "gas_underestimates": [],
            "errors": defaultdict(int)
        })
    
    def record_submission(
        self,
        provider: str,
        user_op_hash: str,
        success: bool,
        inclusion_time: float = 0.0,
        gas_estimate: int = 0,
        gas_actual: int = 0,
        profit: float = 0.0,
        error_message: str = ""
    ):
        """Record a submission metric"""
        metric = SubmissionMetric(
            timestamp=datetime.now(),
            provider=provider,
            user_op_hash=user_op_hash,
            success=success,
            inclusion_time=inclusion_time,
            gas_estimate=gas_estimate,
            gas_actual=gas_actual,
            profit=profit,
            error_message=error_message
        )
        
        self.metrics.append(metric)
        self._update_provider_stats(metric)
        self._cleanup_old_metrics()
        
        logger.info(
            f"Recorded submission: {provider} | "
            f"Success: {success} | Time: {inclusion_time:.2f}s"
        )
    
    def _update_provider_stats(self, metric: SubmissionMetric):
        """Update provider statistics"""
        provider = metric.provider
        stats = self.provider_stats[provider]
        
        stats["submissions"] += 1
        
        if metric.success:
            stats["successful"] += 1
            stats["inclusion_times"].append(metric.inclusion_time)
            
            # Track gas accuracy
            if metric.gas_actual > 0:
                if metric.gas_estimate > metric.gas_actual:
                    over = metric.gas_estimate - metric.gas_actual
                    stats["gas_overestimates"].append(over)
                else:
                    under = metric.gas_actual - metric.gas_estimate
                    stats["gas_underestimates"].append(under)
        else:
            stats["failed"] += 1
            if metric.error_message:
                stats["errors"][metric.error_message] += 1
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than window size"""
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
    
    def get_provider_stats(self, provider: str) -> Dict[str, Any]:
        """Get statistics for a specific provider"""
        stats = self.provider_stats[provider]
        
        total = stats["submissions"]
        if total == 0:
            return {"error": "No submissions yet"}
        
        success_rate = stats["successful"] / total * 100
        
        result = {
            "provider": provider,
            "total_submissions": total,
            "successful": stats["successful"],
            "failed": stats["failed"],
            "success_rate": f"{success_rate:.2f}%",
            "average_inclusion_time": 0.0,
            "min_inclusion_time": 0.0,
            "max_inclusion_time": 0.0,
            "gas_estimation_accuracy": "N/A",
            "error_breakdown": dict(stats["errors"])
        }
        
        if stats["inclusion_times"]:
            result["average_inclusion_time"] = statistics.mean(stats["inclusion_times"])
            result["min_inclusion_time"] = min(stats["inclusion_times"])
            result["max_inclusion_time"] = max(stats["inclusion_times"])
        
        # Gas accuracy
        if stats["gas_overestimates"] or stats["gas_underestimates"]:
            avg_over = statistics.mean(stats["gas_overestimates"]) if stats["gas_overestimates"] else 0
            avg_under = statistics.mean(stats["gas_underestimates"]) if stats["gas_underestimates"] else 0
            result["gas_estimation_accuracy"] = {
                "avg_overestimate": avg_over,
                "avg_underestimate": avg_under,
                "overestimate_count": len(stats["gas_overestimates"]),
                "underestimate_count": len(stats["gas_underestimates"])
            }
        
        return result
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics across all providers"""
        if not self.metrics:
            return {"error": "No metrics yet"}
        
        total_submissions = len(self.metrics)
        successful = sum(1 for m in self.metrics if m.success)
        failed = total_submissions - successful
        success_rate = successful / total_submissions * 100
        
        inclusion_times = [m.inclusion_time for m in self.metrics if m.success]
        avg_inclusion = statistics.mean(inclusion_times) if inclusion_times else 0
        
        total_profit = sum(m.profit for m in self.metrics)
        total_gas = sum(m.gas_actual for m in self.metrics)
        
        return {
            "total_submissions": total_submissions,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{success_rate:.2f}%",
            "average_inclusion_time": f"{avg_inclusion:.2f}s",
            "min_inclusion_time": f"{min(inclusion_times):.2f}s" if inclusion_times else "N/A",
            "max_inclusion_time": f"{max(inclusion_times):.2f}s" if inclusion_times else "N/A",
            "total_profit": f"{total_profit:.2f} ETH",
            "total_gas_cost": f"{total_gas:.4f} ETH",
            "net_profit": f"{total_profit - total_gas:.2f} ETH",
            "provider_breakdown": {
                provider: self.get_provider_stats(provider)
                for provider in self.provider_stats.keys()
            }
        }
    
    def get_recent_submissions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent submission history"""
        recent = sorted(self.metrics, key=lambda m: m.timestamp, reverse=True)[:limit]
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "provider": m.provider,
                "user_op_hash": m.user_op_hash,
                "success": m.success,
                "inclusion_time": f"{m.inclusion_time:.2f}s" if m.inclusion_time else "pending",
                "profit": f"{m.profit:.4f} ETH",
                "error": m.error_message
            }
            for m in recent
        ]
    
    def get_trending_success_rate(self, periods: int = 10) -> List[float]:
        """Get success rate trend over time periods"""
        if not self.metrics:
            return []
        
        # Divide metrics into periods
        period_size = max(1, len(self.metrics) // periods)
        trends = []
        
        for i in range(0, len(self.metrics), period_size):
            period_metrics = self.metrics[i:i+period_size]
            successful = sum(1 for m in period_metrics if m.success)
            rate = successful / len(period_metrics) * 100
            trends.append(rate)
        
        return trends
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check of bundler performance"""
        if not self.metrics:
            return {"status": "no_data"}
        
        recent_100 = self.metrics[-100:]
        recent_rate = sum(1 for m in recent_100 if m.success) / len(recent_100) * 100
        
        status = "healthy"
        if recent_rate < 80:
            status = "degraded"
        if recent_rate < 50:
            status = "unhealthy"
        
        # Check inclusion times
        recent_times = [m.inclusion_time for m in recent_100 if m.success]
        avg_time = statistics.mean(recent_times) if recent_times else 0
        
        return {
            "status": status,
            "recent_success_rate": f"{recent_rate:.2f}%",
            "average_inclusion_time": f"{avg_time:.2f}s",
            "target_inclusion_time": "2.0s",
            "on_target": avg_time < 2.0,
            "total_metrics_tracked": len(self.metrics),
            "providers_active": len(self.provider_stats)
        }


# Global metrics instance
_metrics_instance: BundlerMetrics = None


def initialize_metrics(window_size: int = 3600) -> BundlerMetrics:
    """Initialize global metrics instance"""
    global _metrics_instance
    _metrics_instance = BundlerMetrics(window_size)
    logger.info("Bundler metrics initialized")
    return _metrics_instance


def get_metrics() -> BundlerMetrics:
    """Get global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = BundlerMetrics()
    return _metrics_instance
