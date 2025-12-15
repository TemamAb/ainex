"""
Week 5: Enterprise UI Components
Reusable components for displaying verified metrics
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .models import VerifiedMetric, VerificationStatus, DataSource

logger = logging.getLogger(__name__)


class MetricDisplay:
    """Displays verified metrics with status indicators"""
    
    @staticmethod
    def format_metric_value(value: Any, metric_type: str, precision: int = 2) -> str:
        """Format metric value for display"""
        if isinstance(value, Decimal):
            if metric_type == 'eth':
                return f"{value:.6f}"
            elif metric_type == 'usd':
                return f"${value:,.{precision}f}"
            else:
                return f"{value}"
        elif isinstance(value, float):
            if metric_type == 'eth':
                return f"{value:.6f}"
            elif metric_type == 'usd':
                return f"${value:,.{precision}f}"
            else:
                return f"{value:.{precision}f}"
        elif isinstance(value, int):
            return str(value)
        return str(value)
    
    @staticmethod
    def get_verification_icon(status: VerificationStatus) -> str:
        """Get icon for verification status"""
        icons = {
            VerificationStatus.VERIFIED: "✅",
            VerificationStatus.PENDING: "⏳",
            VerificationStatus.FAILED: "❌",
            VerificationStatus.NOT_CHECKED: "❓",
            VerificationStatus.SKIPPED: "⏭️",
        }
        return icons.get(status, "❓")
    
    @staticmethod
    def get_verification_color(status: VerificationStatus) -> str:
        """Get color for verification status (Streamlit color names)"""
        colors = {
            VerificationStatus.VERIFIED: "green",
            VerificationStatus.PENDING: "orange",
            VerificationStatus.FAILED: "red",
            VerificationStatus.NOT_CHECKED: "gray",
            VerificationStatus.SKIPPED: "blue",
        }
        return colors.get(status, "gray")
    
    @staticmethod
    def get_source_description(source: DataSource) -> str:
        """Get human-readable description of data source"""
        descriptions = {
            DataSource.BACKEND: "Backend API",
            DataSource.BLOCKCHAIN: "Blockchain (on-chain)",
            DataSource.CACHE: "Cache (stale)",
            DataSource.ETHERSCAN: "Etherscan",
            DataSource.DEX_API: "DEX API",
            DataSource.UNKNOWN: "Unknown Source",
        }
        return descriptions.get(source, "Unknown")
    
    @staticmethod
    def format_metric_status(metric: VerifiedMetric) -> str:
        """Format metric with status information"""
        icon = MetricDisplay.get_verification_icon(metric.verification_status)
        value = MetricDisplay.format_metric_value(metric.value, "usd")
        source = MetricDisplay.get_source_description(metric.source)
        age_str = f"{metric.age_seconds}s old" if metric.is_stale else f"fresh ({metric.age_seconds}s)"
        confidence = f"{metric.confidence*100:.0f}%"
        
        return f"{icon} {value} | Source: {source} | {age_str} | Confidence: {confidence}"


class DataFreshnessIndicator:
    """Indicates data freshness"""
    
    @staticmethod
    def get_freshness_status(metric: VerifiedMetric, max_age_seconds: int = 300) -> str:
        """Get freshness status"""
        if metric.age_seconds > max_age_seconds * 2:
            return "❌ VERY STALE"
        elif metric.age_seconds > max_age_seconds:
            return "⚠️ STALE"
        elif metric.age_seconds > 60:
            return "🟡 AGING"
        else:
            return "✅ FRESH"
    
    @staticmethod
    def get_freshness_color(metric: VerifiedMetric, max_age_seconds: int = 300) -> str:
        """Get color for freshness indicator"""
        if metric.age_seconds > max_age_seconds * 2:
            return "red"
        elif metric.age_seconds > max_age_seconds:
            return "orange"
        elif metric.age_seconds > 60:
            return "yellow"
        else:
            return "green"
    
    @staticmethod
    def format_timestamp(timestamp: datetime) -> str:
        """Format timestamp"""
        delta = datetime.now() - timestamp
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h ago"
        else:
            return f"{int(seconds/86400)}d ago"


class RiskControlDisplay:
    """Displays risk control enforcement status"""
    
    @staticmethod
    def get_enforcement_icon(is_enforced: bool) -> str:
        """Get icon for enforcement status"""
        return "✅" if is_enforced else "❌"
    
    @staticmethod
    def format_risk_control_status(control_name: str, is_enforced: bool, details: str = "") -> str:
        """Format risk control status for display"""
        icon = RiskControlDisplay.get_enforcement_icon(is_enforced)
        enforcement_text = "ENFORCED" if is_enforced else "NOT ENFORCED"
        
        result = f"{icon} {control_name}: {enforcement_text}"
        if details:
            result += f" ({details})"
        
        return result


class AlertDisplay:
    """Displays alerts and notifications"""
    
    ALERT_TEMPLATES = {
        'data_validation_failed': {
            'icon': '🚨',
            'title': 'DATA VALIDATION FAILED',
            'severity': 'critical',
            'color': 'red',
        },
        'verification_failed': {
            'icon': '❌',
            'title': 'DATA VERIFICATION FAILED',
            'severity': 'high',
            'color': 'red',
        },
        'data_mismatch': {
            'icon': '⚠️',
            'title': 'DATA MISMATCH DETECTED',
            'severity': 'critical',
            'color': 'red',
        },
        'backend_unavailable': {
            'icon': '🔴',
            'title': 'BACKEND API UNAVAILABLE',
            'severity': 'high',
            'color': 'orange',
        },
        'blockchain_unavailable': {
            'icon': '🔴',
            'title': 'BLOCKCHAIN RPC UNAVAILABLE',
            'severity': 'high',
            'color': 'orange',
        },
        'stale_data': {
            'icon': '⏰',
            'title': 'DATA IS STALE',
            'severity': 'medium',
            'color': 'orange',
        },
        'risk_enforcement_failure': {
            'icon': '🚨',
            'title': 'RISK CONTROL NOT ENFORCED',
            'severity': 'critical',
            'color': 'red',
        },
        'circuit_breaker_triggered': {
            'icon': '⛔',
            'title': 'CIRCUIT BREAKER TRIGGERED',
            'severity': 'critical',
            'color': 'red',
        },
    }
    
    @staticmethod
    def get_alert_template(alert_type: str) -> Dict[str, Any]:
        """Get alert template"""
        return AlertDisplay.ALERT_TEMPLATES.get(alert_type, {
            'icon': '⚠️',
            'title': 'UNKNOWN ALERT',
            'severity': 'medium',
            'color': 'yellow',
        })
    
    @staticmethod
    def format_alert(alert_type: str, message: str) -> str:
        """Format alert message"""
        template = AlertDisplay.get_alert_template(alert_type)
        icon = template.get('icon', '⚠️')
        title = template.get('title', 'ALERT')
        
        return f"{icon} {title}\n{message}"


class DashboardLayout:
    """Helper for dashboard layout"""
    
    @staticmethod
    def create_metric_row(metrics: Dict[str, VerifiedMetric]) -> str:
        """Create a row of metrics for display"""
        rows = []
        for name, metric in metrics.items():
            display = MetricDisplay.format_metric_status(metric)
            rows.append(f"{name}: {display}")
        return "\n".join(rows)
    
    @staticmethod
    def create_risk_control_row(controls: Dict[str, bool]) -> str:
        """Create a row of risk controls for display"""
        rows = []
        for control, enforced in controls.items():
            display = RiskControlDisplay.format_risk_control_status(control, enforced)
            rows.append(display)
        return "\n".join(rows)
    
    @staticmethod
    def create_status_summary(
        profit_metric: Optional[VerifiedMetric] = None,
        risk_metric: Optional[VerifiedMetric] = None,
        health_metric: Optional[VerifiedMetric] = None,
        enforcement_status: str = "UNKNOWN"
    ) -> str:
        """Create a summary status display"""
        lines = [
            "=" * 60,
            "DASHBOARD STATUS SUMMARY",
            "=" * 60,
        ]
        
        if profit_metric:
            lines.append(f"Profit: {MetricDisplay.format_metric_status(profit_metric)}")
        
        if risk_metric:
            lines.append(f"Risk: {MetricDisplay.format_metric_status(risk_metric)}")
        
        if health_metric:
            lines.append(f"Health: {MetricDisplay.format_metric_status(health_metric)}")
        
        lines.append(f"Risk Control Enforcement: {enforcement_status}")
        lines.append("=" * 60)
        
        return "\n".join(lines)


class MetricValidator:
    """Validates metrics before display"""
    
    @staticmethod
    def should_display(metric: VerifiedMetric, require_verification: bool = True) -> Tuple[bool, str]:
        """
        Determine if metric should be displayed.
        
        Args:
            metric: Metric to check
            require_verification: If True, metric must be verified
            
        Returns:
            (should_display, reason)
        """
        # Check if metric is stale (>10 minutes old)
        if metric.is_stale:
            return False, "Data is stale (older than max age)"
        
        # Check verification status if required
        if require_verification:
            if metric.verification_status == VerificationStatus.VERIFIED:
                return True, "Data verified"
            elif metric.verification_status == VerificationStatus.PENDING:
                return True, "Data pending verification"
            elif metric.verification_status == VerificationStatus.FAILED:
                return False, "Data verification failed"
            else:
                return False, "Data not verified"
        else:
            # Allow display without verification but warn
            return True, f"Data not verified (confidence: {metric.confidence*100:.0f}%)"
    
    @staticmethod
    def get_display_warning(metric: VerifiedMetric) -> Optional[str]:
        """Get warning message if metric should be displayed with caution"""
        if metric.verification_status != VerificationStatus.VERIFIED:
            return f"⚠️ Data not fully verified ({metric.verification_status.value})"
        
        if metric.is_stale:
            return f"⚠️ Data is stale ({metric.age_seconds}s old)"
        
        if metric.confidence < 0.9:
            return f"⚠️ Low confidence ({metric.confidence*100:.0f}%)"
        
        if metric.source == DataSource.CACHE:
            return "⚠️ Using cached data"
        
        return None


# Type hints
from typing import Tuple

if __name__ == "__main__":
    from .models import VerifiedMetric, DataSource, VerificationStatus
    
    # Test display
    test_metric = VerifiedMetric(
        value=1.5,
        source=DataSource.BLOCKCHAIN,
        verification_status=VerificationStatus.VERIFIED,
        verified_at=datetime.now(),
        verified_by="blockchain_verifier",
        confidence=1.0,
        is_stale=False,
        age_seconds=30,
    )
    
    print(MetricDisplay.format_metric_status(test_metric))
    print(DataFreshnessIndicator.get_freshness_status(test_metric))
    print(AlertDisplay.format_alert('verification_failed', 'Blockchain data does not match backend claims'))
