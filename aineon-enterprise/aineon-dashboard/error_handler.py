#!/usr/bin/env python3
"""
AINEON Error Handler and Monitoring System
Provides comprehensive error handling, logging, and monitoring for error-free operation
"""

import logging
import traceback
import sys
import os
import time
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import threading
import psutil
import requests
from pathlib import Path

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemStatus(Enum):
    """System status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"

@dataclass
class ErrorEvent:
    """Error event data structure"""
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    component: str
    traceback: str
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    response_time: float
    uptime: float
    error_rate: float

class ErrorHandler:
    """Centralized error handling and monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._load_config()
        self.setup_logging()
        self.error_history: List[ErrorEvent] = []
        self.monitoring_active = False
        self.metrics_buffer = []
        self.max_buffer_size = 1000
        self.alert_thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'response_time': 5000.0  # 5 seconds
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults"""
        return {
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'alert_email': os.getenv('ALERT_EMAIL', ''),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'health_check_url': os.getenv('HEALTH_CHECK_URL', 'http://localhost:8081/api/status'),
            'dashboard_url': os.getenv('DASHBOARD_URL', 'http://localhost:8501'),
            'max_errors_per_hour': 100,
            'enable_email_alerts': os.getenv('ENABLE_EMAIL_ALERTS', 'false').lower() == 'true',
        }
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config['log_level'].upper()),
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / 'aineon_dashboard.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('AINEON-Dashboard')
        self.logger.info("Error Handler initialized")
    
    def handle_error(self, 
                    error: Exception, 
                    component: str, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict[str, Any] = None) -> bool:
        """Handle and log error with proper categorization"""
        
        error_event = ErrorEvent(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            message=str(error),
            severity=severity,
            component=component,
            traceback=traceback.format_exc(),
            context=context or {}
        )
        
        # Log error based on severity
        log_method = {
            ErrorSeverity.LOW: self.logger.warning,
            ErrorSeverity.MEDIUM: self.logger.error,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical
        }
        
        log_method[severity](
            f"[{component}] {error_event.error_type}: {error_event.message}"
        )
        
        # Store error event
        self.error_history.append(error_event)
        
        # Clean old errors (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.error_history = [
            e for e in self.error_history 
            if e.timestamp > cutoff_time
        ]
        
        # Send alert if needed
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self._send_alert(error_event)
        
        # Auto-recovery for certain errors
        if self._should_auto_recover(error, component):
            self._attempt_auto_recovery(component)
        
        return True
    
    def get_system_status(self) -> SystemStatus:
        """Determine current system status based on metrics and errors"""
        metrics = self.get_system_metrics()
        
        # Check error rate
        recent_errors = self._get_recent_error_count()
        error_rate = (recent_errors / max(metrics.uptime, 1)) * 100
        
        if (metrics.cpu_usage > 90 or 
            metrics.memory_usage > 95 or 
            error_rate > 10):
            return SystemStatus.CRITICAL
        elif (metrics.cpu_usage > 80 or 
              metrics.memory_usage > 85 or 
              error_rate > 5):
            return SystemStatus.WARNING
        else:
            return SystemStatus.HEALTHY
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # System resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Response time
            start_time = time.time()
            try:
                response = requests.get(self.config['health_check_url'], timeout=5)
                response_time = (time.time() - start_time) * 1000  # ms
            except:
                response_time = -1  # Error
                
            # Error rate (errors per hour)
            error_count = self._get_recent_error_count()
            uptime_hours = (time.time() - psutil.boot_time()) / 3600
            error_rate = (error_count / max(uptime_hours, 1))
            
            return SystemMetrics(
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=(disk.used / disk.total) * 100,
                network_io={
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                },
                response_time=response_time,
                uptime=(time.time() - psutil.boot_time()) / 3600,  # hours
                error_rate=error_rate
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(0, 0, 0, {}, -1, 0, 999)
    
    def start_monitoring(self):
        """Start continuous system monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self.logger.info("System monitoring started")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Collect metrics
                    metrics = self.get_system_metrics()
                    self.metrics_buffer.append({
                        'timestamp': datetime.now(),
                        'metrics': metrics
                    })
                    
                    # Clean old metrics
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.metrics_buffer = [
                        m for m in self.metrics_buffer 
                        if m['timestamp'] > cutoff_time
                    ]
                    
                    # Check thresholds and alert if needed
                    self._check_alert_thresholds(metrics)
                    
                    # Auto-cleanup if needed
                    self._perform_maintenance()
                    
                    # Sleep for 30 seconds
                    time.sleep(30)
                    
                except Exception as e:
                    self.logger.error(f"Monitoring loop error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring_active = False
        self.logger.info("System monitoring stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        system_status = self.get_system_status()
        metrics = self.get_system_metrics()
        
        # Recent errors
        recent_errors = [
            {
                'timestamp': e.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'component': e.component,
                'error_type': e.error_type,
                'message': e.message,
                'severity': e.severity.value,
                'resolved': e.resolved
            }
            for e in self.error_history[-10:]  # Last 10 errors
        ]
        
        # Error trends (last 24 hours)
        hourly_errors = self._get_hourly_error_trends()
        
        return {
            'system_status': system_status.value,
            'metrics': {
                'cpu_usage': f"{metrics.cpu_usage:.1f}%",
                'memory_usage': f"{metrics.memory_usage:.1f}%",
                'disk_usage': f"{metrics.disk_usage:.1f}%",
                'response_time': f"{metrics.response_time:.2f}ms" if metrics.response_time > 0 else "N/A",
                'uptime': f"{metrics.uptime:.1f}h",
                'error_rate': f"{metrics.error_rate:.2f}/h"
            },
            'recent_errors': recent_errors,
            'error_trends': hourly_errors,
            'alert_thresholds': self.alert_thresholds,
            'monitoring_active': self.monitoring_active,
            'total_errors_24h': len(self.error_history)
        }
    
    def _send_alert(self, error_event: ErrorEvent):
        """Send email alert for critical errors"""
        if not self.config['enable_email_alerts'] or not self.config['alert_email']:
            return
            
        try:
            subject = f"AINEON Alert: {error_event.severity.value.upper()} Error in {error_event.component}"
            
            body = f"""
            AINEON System Alert
            
            Error Details:
            - Component: {error_event.component}
            - Error Type: {error_event.error_type}
            - Severity: {error_event.severity.value.upper()}
            - Message: {error_event.message}
            - Time: {error_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Traceback:
            {error_event.traceback}
            
            System Status: {self.get_system_status().value}
            
            Please check the dashboard for more details.
            Dashboard URL: {self.config['dashboard_url']}
            """
            
            # In production, you would configure SMTP properly
            self.logger.info(f"Alert would be sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
    
    def _get_recent_error_count(self, hours: int = 1) -> int:
        """Get count of errors in recent time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return len([e for e in self.error_history if e.timestamp > cutoff_time])
    
    def _get_hourly_error_trends(self) -> List[Dict]:
        """Get hourly error trends for the last 24 hours"""
        trends = []
        for i in range(24):
            hour_start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_errors = [
                e for e in self.error_history 
                if hour_start <= e.timestamp < hour_end
            ]
            
            trends.append({
                'hour': hour_start.strftime('%H:00'),
                'error_count': len(hour_errors),
                'critical_count': len([e for e in hour_errors if e.severity == ErrorSeverity.CRITICAL])
            })
        
        return list(reversed(trends))  # Oldest first
    
    def _check_alert_thresholds(self, metrics: SystemMetrics):
        """Check if any metrics exceed alert thresholds"""
        alerts = []
        
        if metrics.cpu_usage > self.alert_thresholds['cpu_usage']:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.alert_thresholds['memory_usage']:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.response_time > self.alert_thresholds['response_time']:
            alerts.append(f"Slow response time: {metrics.response_time:.2f}ms")
        
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts.append(f"High error rate: {metrics.error_rate:.2f}/h")
        
        if alerts:
            self.logger.warning(f"Threshold alerts: {'; '.join(alerts)}")
    
    def _should_auto_recover(self, error: Exception, component: str) -> bool:
        """Determine if error should trigger auto-recovery"""
        # Auto-recover from common transient errors
        transient_errors = [
            'ConnectionError',
            'Timeout',
            'TemporaryFailure',
            'ServiceUnavailable'
        ]
        
        return (isinstance(error, (ConnectionError, TimeoutError)) or 
                any(err_name in str(error) for err_name in transient_errors))
    
    def _attempt_auto_recovery(self, component: str):
        """Attempt automatic recovery for specified component"""
        self.logger.info(f"Attempting auto-recovery for {component}")
        
        # Implementation would depend on the component
        # For now, just log the attempt
        recovery_actions = {
            'api': 'Restart API service',
            'dashboard': 'Restart Streamlit server',
            'database': 'Check database connection',
            'blockchain': 'Refresh RPC connection'
        }
        
        action = recovery_actions.get(component, 'Generic recovery action')
        self.logger.info(f"Auto-recovery action: {action}")
    
    def _perform_maintenance(self):
        """Perform system maintenance tasks"""
        # Clean up old log files
        log_dir = Path('logs')
        if log_dir.exists():
            cutoff_time = datetime.now() - timedelta(days=7)
            for log_file in log_dir.glob('*.log'):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
        
        # Clean up metrics buffer
        if len(self.metrics_buffer) > self.max_buffer_size:
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer_size:]
    
    def export_error_report(self, filepath: str):
        """Export error report to file"""
        try:
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'system_status': self.get_system_status().value,
                'metrics': self.get_system_metrics().__dict__,
                'errors': [
                    {
                        'timestamp': e.timestamp.isoformat(),
                        'component': e.component,
                        'error_type': e.error_type,
                        'message': e.message,
                        'severity': e.severity.value,
                        'resolved': e.resolved
                    }
                    for e in self.error_history
                ],
                'config': self.config
            }
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"Error report exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export error report: {e}")
            return False

# Global error handler instance
error_handler = ErrorHandler()

def safe_execute(func, *args, component: str = "unknown", **kwargs):
    """Decorator function to safely execute code with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, component)
        return None

def setup_error_monitoring():
    """Setup global error monitoring"""
    error_handler.start_monitoring()
    return error_handler

if __name__ == "__main__":
    # Test the error handler
    handler = ErrorHandler()
    handler.start_monitoring()
    
    print("Error Handler Test")
    print(f"System Status: {handler.get_system_status().value}")
    print(f"Metrics: {handler.get_system_metrics()}")
    
    # Test error handling
    try:
        raise ValueError("Test error")
    except Exception as e:
        handler.handle_error(e, "test_component", ErrorSeverity.MEDIUM)
    
    print("Dashboard data:", json.dumps(handler.get_dashboard_data(), indent=2, default=str))
