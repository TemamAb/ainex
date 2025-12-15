"""
AINEON Enterprise Infrastructure Layer
Phase 1: Foundation modules for observability, security, resilience, and state management

This package provides the enterprise-grade infrastructure foundation for the AINEON system:
- Distributed tracing and observability
- Structured logging
- Metrics collection
- Health checks
- Security hardening
- Resilience patterns
- State management and persistence

Author: Chief Architect
Date: December 14, 2025
Status: Phase 1 - Infrastructure Foundation
"""

from .distributed_tracing import TracingManager
from .structured_logging import LogManager
from .metrics_collector import MetricsCollector
from .health_check_engine import HealthCheckEngine

__version__ = "1.0.0"
__all__ = [
    "TracingManager",
    "LogManager",
    "MetricsCollector",
    "HealthCheckEngine",
]
