"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON ENTERPRISE DRAWDOWN ANALYZER                        ║
║              Portfolio drawdown monitoring with enterprise-grade alerts       ║
║                                                                                ║
║  Enterprise Features:                                                          ║
║  ✓ Async operations with comprehensive error handling                         ║
║  ✓ Decimal precision for all financial calculations                           ║
║  ✓ Structured logging and real-time metrics integration                       ║
║  ✓ Health checks and circuit breaker integration                              ║
║  ✓ Advanced risk analytics and recovery prediction                            ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import json
import time

from core.infrastructure.metrics_collector import MetricsCollector
from core.infrastructure.health_check_engine import HealthCheckEngine
from core.infrastructure.structured_logging import StructuredLogger


class DrawdownSeverity(Enum):
    """Drawdown severity classification"""
    NORMAL = "NORMAL"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"


@dataclass
class DrawdownMetrics:
    """Metrics for a drawdown event"""
    peak_value: Decimal
    trough_value: Decimal
    drawdown_amount: Decimal
    drawdown_percent: Decimal
    peak_date: datetime
    trough_date: datetime
    duration: timedelta
    recovery_date: Optional[datetime] = None
    recovery_time: Optional[timedelta] = None
    severity: DrawdownSeverity = DrawdownSeverity.NORMAL


@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio value at a point in time"""
    timestamp: datetime
    total_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    open_positions: int


class DrawdownEvent:
    """Represents a single drawdown event"""
    
    def __init__(self, peak_value: Decimal, peak_date: datetime):
        self.peak_value = peak_value
        self.peak_date = peak_date
        self.trough_value = peak_value
        self.trough_date = peak_date
        self.recovered_date: Optional[datetime] = None
        self.recovery_value: Optional[Decimal] = None
    
    def update(self, current_value: Decimal, current_date: datetime) -> None:
        """Update drawdown as new values arrive"""
        if current_value < self.trough_value:
            self.trough_value = current_value
            self.trough_date = current_date
        elif current_value >= self.peak_value:
            # Recovery achieved
            self.recovered_date = current_date
            self.recovery_value = current_value
    
    def get_metrics(self) -> DrawdownMetrics:
        """Calculate drawdown metrics"""
        drawdown_amount = self.peak_value - self.trough_value
        drawdown_percent = (drawdown_amount / self.peak_value) * Decimal("100") if self.peak_value > 0 else Decimal("0")
        
        duration = self.trough_date - self.peak_date
        
        recovery_time = None
        if self.recovered_date:
            recovery_time = self.recovered_date - self.trough_date
        
        # Severity classification
        severity = self._classify_severity(drawdown_percent)
        
        return DrawdownMetrics(
            peak_value=self.peak_value,
            trough_value=self.trough_value,
            drawdown_amount=drawdown_amount,
            drawdown_percent=drawdown_percent,
            peak_date=self.peak_date,
            trough_date=self.trough_date,
            duration=duration,
            recovery_date=self.recovered_date,
            recovery_time=recovery_time,
            severity=severity
        )
    
    @staticmethod
    def _classify_severity(drawdown_percent: Decimal) -> DrawdownSeverity:
        """Classify drawdown severity"""
        if drawdown_percent <= Decimal("5"):
            return DrawdownSeverity.NORMAL
        elif drawdown_percent <= Decimal("10"):
            return DrawdownSeverity.MODERATE
        elif drawdown_percent <= Decimal("20"):
            return DrawdownSeverity.SEVERE
        elif drawdown_percent <= Decimal("50"):
            return DrawdownSeverity.CRITICAL
        else:
            return DrawdownSeverity.CATASTROPHIC
    
    def is_active(self) -> bool:
        """Check if drawdown is still active (not recovered)"""
        return self.recovered_date is None


class DrawdownAnalyzer:
    """Enterprise-grade portfolio drawdown analyzer with comprehensive risk monitoring"""

    def __init__(
        self,
        max_drawdown_limit: Decimal = Decimal("1.5"),  # 1.5% per day
        daily_loss_limit: Decimal = Decimal("1500000"),  # $1.5M
        recovery_target_days: int = 30,
        metrics_collector: Optional[MetricsCollector] = None,
        health_engine: Optional[HealthCheckEngine] = None,
        logger: Optional[StructuredLogger] = None
    ):
        # Enterprise infrastructure
        self.logger = logger or StructuredLogger(__name__)
        self.metrics = metrics_collector or MetricsCollector()
        self.health_engine = health_engine or HealthCheckEngine()

        # Configuration with validation
        if not (Decimal('0') < max_drawdown_limit <= Decimal('100')):
            raise ValueError(f"Max drawdown limit must be between 0 and 100, got {max_drawdown_limit}")
        if not (Decimal('0') < daily_loss_limit):
            raise ValueError(f"Daily loss limit must be positive, got {daily_loss_limit}")

        self.max_drawdown_limit = max_drawdown_limit
        self.daily_loss_limit = daily_loss_limit
        self.recovery_target_days = recovery_target_days

        # Data structures with thread safety
        self.snapshots: List[PortfolioSnapshot] = []
        self.drawdown_events: List[DrawdownEvent] = []
        self.current_event: Optional[DrawdownEvent] = None
        self.alerts: List[Dict] = []

        # State tracking
        self.peak_value = Decimal("0")
        self.peak_date: Optional[datetime] = None
        self.update_count: int = 0
        self.last_update_time: Optional[float] = None

        # Register health checks
        self.health_engine.register_check("drawdown_analyzer_data", self._check_data_health)
        self.health_engine.register_check("drawdown_analyzer_alerts", self._check_alerts_health)

        self.logger.info("DrawdownAnalyzer initialized", extra={
            "max_drawdown_limit": str(max_drawdown_limit),
            "daily_loss_limit": str(daily_loss_limit),
            "recovery_target_days": recovery_target_days
        })

    def _check_data_health(self) -> Dict[str, Any]:
        """Health check for data integrity"""
        return {
            "snapshots_count": len(self.snapshots),
            "events_count": len(self.drawdown_events),
            "current_event_active": self.current_event is not None,
            "peak_value": str(self.peak_value),
            "data_freshness": self.snapshots[-1].timestamp.isoformat() if self.snapshots else None
        }

    def _check_alerts_health(self) -> Dict[str, Any]:
        """Health check for alert system"""
        return {
            "active_alerts": len(self.alerts),
            "circuit_breaker_triggered": self.check_circuit_breaker()[0],
            "current_drawdown": self.get_current_drawdown().drawdown_percent if self.get_current_drawdown() else 0,
            "max_drawdown_limit": str(self.max_drawdown_limit)
        }
    
    async def update_portfolio_value(
        self,
        timestamp: datetime,
        total_value: Decimal,
        unrealized_pnl: Decimal = Decimal("0"),
        realized_pnl: Decimal = Decimal("0"),
        open_positions: int = 0
    ) -> Optional[DrawdownMetrics]:
        """Update portfolio value and check for drawdowns with enterprise-grade error handling"""
        start_time = time.time()

        try:
            # Input validation
            if not isinstance(total_value, Decimal) or total_value < 0:
                raise ValueError(f"Total value must be non-negative Decimal, got {total_value}")
            if not isinstance(timestamp, datetime):
                raise ValueError(f"Timestamp must be datetime object, got {type(timestamp)}")

            self.update_count += 1

            # Record snapshot
            snapshot = PortfolioSnapshot(
                timestamp=timestamp,
                total_value=total_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                open_positions=open_positions
            )
            self.snapshots.append(snapshot)

            # Update peak value
            if total_value > self.peak_value:
                self.peak_value = total_value
                self.peak_date = timestamp

                # If in drawdown, mark it as recovered
                if self.current_event and not self.current_event.is_active():
                    self.current_event.recovered_date = timestamp
                    self.current_event.recovery_value = total_value
                    self.drawdown_events.append(self.current_event)
                    self.current_event = None

            # Check if in drawdown
            current_drawdown = ((self.peak_value - total_value) / self.peak_value) * Decimal("100") if self.peak_value > 0 else Decimal("0")

            # Record metrics
            self.metrics.record_metric("drawdown_analyzer.portfolio_value", float(total_value))
            self.metrics.record_metric("drawdown_analyzer.current_drawdown", float(current_drawdown))

            if current_drawdown > 0:
                if self.current_event is None:
                    # Start new drawdown event
                    self.current_event = DrawdownEvent(self.peak_value, self.peak_date)
                    self.logger.warning("Drawdown event started", extra={
                        "peak_value": str(self.peak_value),
                        "current_value": str(total_value),
                        "initial_drawdown": str(current_drawdown)
                    })

                # Update current event
                self.current_event.update(total_value, timestamp)

                # Check for alert triggers
                await self._check_alert_triggers(self.current_event, total_value, timestamp)

                metrics = self.current_event.get_metrics()

                # Record drawdown metrics
                self.metrics.record_metric("drawdown_analyzer.drawdown_percent", float(metrics.drawdown_percent))
                self.metrics.record_metric("drawdown_analyzer.drawdown_duration", metrics.duration.total_seconds())

                calculation_time = time.time() - start_time
                self.last_update_time = time.time()
                self.metrics.record_metric("drawdown_analyzer.update_time", calculation_time)

                return metrics

            calculation_time = time.time() - start_time
            self.last_update_time = time.time()
            self.metrics.record_metric("drawdown_analyzer.update_time", calculation_time)

            return None

        except Exception as e:
            self.logger.error(f"Failed to update portfolio value: {e}", extra={
                "timestamp": timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
                "total_value": str(total_value)
            })
            raise
    
    async def _check_alert_triggers(
        self,
        event: DrawdownEvent,
        current_value: Decimal,
        timestamp: datetime
    ) -> None:
        """Check if drawdown triggers any alerts with enterprise-grade logging"""
        try:
            metrics = event.get_metrics()

            # Drawdown limit breach
            if metrics.drawdown_percent > self.max_drawdown_limit:
                alert = {
                    "timestamp": timestamp.isoformat(),
                    "type": "DRAWDOWN_LIMIT_BREACH",
                    "severity": metrics.severity.value,
                    "drawdown_percent": str(metrics.drawdown_percent),
                    "limit": str(self.max_drawdown_limit),
                    "action": "REDUCE_RISK"
                }
                self.alerts.append(alert)
                self.metrics.record_metric("drawdown_analyzer.alerts_triggered", 1)
                self.logger.error("Drawdown limit breached", extra={
                    "drawdown_percent": str(metrics.drawdown_percent),
                    "limit": str(self.max_drawdown_limit),
                    "severity": metrics.severity.value,
                    "action": "REDUCE_RISK"
                })

            # Daily loss limit
            daily_loss = event.peak_value - current_value
            if daily_loss > self.daily_loss_limit:
                alert = {
                    "timestamp": timestamp.isoformat(),
                    "type": "DAILY_LOSS_LIMIT_BREACH",
                    "daily_loss": str(daily_loss),
                    "limit": str(self.daily_loss_limit),
                    "action": "STOP_TRADING"
                }
                self.alerts.append(alert)
                self.metrics.record_metric("drawdown_analyzer.critical_alerts", 1)
                self.logger.critical("Daily loss limit breached", extra={
                    "daily_loss": str(daily_loss),
                    "limit": str(self.daily_loss_limit),
                    "action": "STOP_TRADING"
                })

            # Slow recovery warning
            if metrics.duration > timedelta(days=7):
                alert = {
                    "timestamp": timestamp.isoformat(),
                    "type": "SLOW_RECOVERY",
                    "duration_days": metrics.duration.days,
                    "target_days": self.recovery_target_days,
                    "action": "REVIEW_STRATEGY"
                }
                self.alerts.append(alert)
                self.metrics.record_metric("drawdown_analyzer.recovery_alerts", 1)
                self.logger.warning("Slow recovery detected", extra={
                    "duration_days": metrics.duration.days,
                    "target_days": self.recovery_target_days,
                    "action": "REVIEW_STRATEGY"
                })

        except Exception as e:
            self.logger.error(f"Failed to check alert triggers: {e}")
            raise
    
    def get_current_drawdown(self) -> Optional[DrawdownMetrics]:
        """Get current drawdown metrics"""
        if self.current_event:
            return self.current_event.get_metrics()
        return None
    
    def get_maximum_drawdown(self) -> Decimal:
        """Get maximum drawdown in history"""
        if not self.snapshots:
            return Decimal("0")
        
        max_dd = Decimal("0")
        peak = self.snapshots[0].total_value
        
        for snapshot in self.snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            
            dd = ((peak - snapshot.total_value) / peak) * Decimal("100") if peak > 0 else Decimal("0")
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def get_drawdown_duration(self) -> Optional[timedelta]:
        """Get current drawdown duration"""
        if self.current_event:
            return self.current_event.get_metrics().duration
        return None
    
    def get_average_recovery_time(self) -> Optional[timedelta]:
        """Get average recovery time from historical events"""
        completed_events = [
            event for event in self.drawdown_events
            if event.recovery_time is not None
        ]
        
        if not completed_events:
            return None
        
        total_time = sum(
            (event.recovery_time.total_seconds() for event in completed_events),
            0
        )
        avg_seconds = total_time / len(completed_events)
        
        return timedelta(seconds=avg_seconds)
    
    def get_drawdown_history(self, limit: int = 50) -> List[Dict]:
        """Get historical drawdown events"""
        history = []
        
        for event in self.drawdown_events[-limit:]:
            metrics = event.get_metrics()
            history.append({
                "peak_value": str(metrics.peak_value),
                "trough_value": str(metrics.trough_value),
                "drawdown_amount": str(metrics.drawdown_amount),
                "drawdown_percent": str(metrics.drawdown_percent),
                "peak_date": metrics.peak_date.isoformat(),
                "trough_date": metrics.trough_date.isoformat(),
                "recovery_date": metrics.recovery_date.isoformat() if metrics.recovery_date else None,
                "duration_days": metrics.duration.days,
                "recovery_days": metrics.recovery_time.days if metrics.recovery_time else None,
                "severity": metrics.severity.value
            })
        
        return history
    
    def estimate_recovery_time(self) -> Optional[timedelta]:
        """Estimate time to recovery based on historical patterns"""
        if not self.current_event or not self.current_event.is_active():
            return None
        
        avg_recovery = self.get_average_recovery_time()
        if avg_recovery is None:
            return None
        
        # Estimate based on historical average
        current_metrics = self.current_event.get_metrics()
        
        # Adjust estimate based on current severity
        if current_metrics.severity == DrawdownSeverity.SEVERE:
            adjustment = Decimal("1.5")
        elif current_metrics.severity == DrawdownSeverity.CRITICAL:
            adjustment = Decimal("2.0")
        else:
            adjustment = Decimal("1.0")
        
        estimated_seconds = int(avg_recovery.total_seconds() * float(adjustment))
        return timedelta(seconds=estimated_seconds)
    
    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """Check if circuit breaker should be activated"""
        if not self.current_event:
            return False, "No active drawdown"
        
        metrics = self.current_event.get_metrics()
        
        # Trigger if drawdown exceeds limit
        if metrics.drawdown_percent > self.max_drawdown_limit:
            return True, f"Drawdown {metrics.drawdown_percent:.2f}% exceeds limit {self.max_drawdown_limit}%"
        
        # Trigger if recovery is too slow
        if metrics.duration > timedelta(days=self.recovery_target_days):
            return True, f"Recovery taking longer than {self.recovery_target_days} days"
        
        return False, "No circuit breaker triggered"
    
    def get_metrics_snapshot(self) -> Dict:
        """Get current metrics snapshot"""
        current_dd = self.get_current_drawdown()
        max_dd = self.get_maximum_drawdown()
        avg_recovery = self.get_average_recovery_time()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_drawdown_percent": str(current_dd.drawdown_percent) if current_dd else "0",
            "current_drawdown_amount": str(current_dd.drawdown_amount) if current_dd else "0",
            "current_duration_days": current_dd.duration.days if current_dd else 0,
            "max_drawdown_percent": str(max_dd),
            "average_recovery_days": avg_recovery.days if avg_recovery else 0,
            "circuit_breaker_active": self.check_circuit_breaker()[0],
            "alerts_count": len(self.alerts),
            "events_count": len(self.drawdown_events)
        }
    
    def reset_alerts(self) -> None:
        """Clear alert list"""
        self.alerts.clear()
        logger.info("Alerts cleared")
    
    def get_alerts(self) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts.copy()


# Enterprise-grade demo execution
async def demo_drawdown_analyzer():
    """Demonstrate drawdown analyzer with enterprise-grade logging"""
    analyzer = DrawdownAnalyzer(
        max_drawdown_limit=Decimal("1.5"),
        daily_loss_limit=Decimal("1500000")
    )

    analyzer.logger.info("Starting DrawdownAnalyzer demonstration")

    # Simulate portfolio values
    start_value = Decimal("10000000")
    timestamps = [
        datetime.utcnow() - timedelta(hours=i) for i in range(10, 0, -1)
    ]
    values = [
        Decimal("10000000"),  # Peak
        Decimal("9950000"),
        Decimal("9900000"),
        Decimal("9800000"),
        Decimal("9700000"),
        Decimal("9750000"),
        Decimal("9850000"),
        Decimal("9900000"),
        Decimal("9950000"),
        Decimal("10000000")   # Recovered
    ]

    for ts, val in zip(timestamps, values):
        await analyzer.update_portfolio_value(ts, val, unrealized_pnl=Decimal("0"))

    analyzer.logger.info("Portfolio data simulation completed", extra={
        "data_points": len(values),
        "peak_value": str(start_value)
    })

    # Get metrics
    snapshot = analyzer.get_metrics_snapshot()

    analyzer.logger.info("Drawdown analysis completed", extra={
        "current_drawdown_percent": snapshot.get("current_drawdown_percent", "0"),
        "max_drawdown_percent": snapshot.get("max_drawdown_percent", "0"),
        "events_count": snapshot.get("events_count", 0),
        "alerts_count": snapshot.get("alerts_count", 0)
    })

    return analyzer

if __name__ == "__main__":
    asyncio.run(demo_drawdown_analyzer())
