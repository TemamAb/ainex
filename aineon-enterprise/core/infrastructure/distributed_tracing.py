"""
Distributed Tracing Module - OpenTelemetry Integration
AINEON Enterprise Flash Loan Engine
Phase 1, Week 1 - Observability Foundation

Enables end-to-end request tracing with <5ms overhead
"""

import time
import logging
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime
import json

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)


class DistributedTracer:
    """
    Manages distributed tracing across AINEON system
    Integrates OpenTelemetry for end-to-end observability
    """

    def __init__(self, service_name: str = "aineon-engine", jaeger_host: str = "localhost", jaeger_port: int = 6831):
        """Initialize distributed tracing"""
        self.service_name = service_name
        self.tracer = None
        self.meter = None
        self._setup_tracer(jaeger_host, jaeger_port)
        self._setup_metrics()
        self._instrument_libraries()

    def _setup_tracer(self, jaeger_host: str, jaeger_port: int) -> None:
        """Setup Jaeger exporter and tracer"""
        try:
            # Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=jaeger_port,
            )

            # Tracer provider
            trace_provider = TracerProvider(
                resource=Resource.create({"service.name": self.service_name})
            )
            trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
            trace.set_tracer_provider(trace_provider)

            self.tracer = trace.get_tracer(__name__)
            logger.info(f"✓ Distributed tracing initialized (Jaeger: {jaeger_host}:{jaeger_port})")
        except Exception as e:
            logger.warning(f"⚠ Jaeger not available, using noop tracer: {e}")
            self.tracer = trace.get_tracer(__name__)

    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics"""
        try:
            prometheus_reader = PrometheusMetricReader()
            meter_provider = MeterProvider(metric_readers=[prometheus_reader])
            metrics.set_meter_provider(meter_provider)
            self.meter = metrics.get_meter(__name__)
            logger.info("✓ Prometheus metrics initialized")
        except Exception as e:
            logger.warning(f"⚠ Prometheus setup failed: {e}")

    def _instrument_libraries(self) -> None:
        """Auto-instrument common libraries"""
        try:
            FlaskInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            RedisInstrumentor().instrument()
            LoggingInstrumentor().instrument()
            logger.info("✓ Libraries instrumented (Flask, Requests, Redis, Logging)")
        except Exception as e:
            logger.debug(f"Some instrumentations not available: {e}")

    def trace_function(self, operation_name: str = None):
        """Decorator for tracing function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                func_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                with self.tracer.start_as_current_span(func_name) as span:
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        
                        span.set_attribute("status", "success")
                        span.set_attribute("duration_ms", duration_ms)
                        
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("status", "error")
                        span.set_attribute("error", str(e))
                        span.set_attribute("duration_ms", duration_ms)
                        raise
            return wrapper
        return decorator

    def trace_trade(self, trade_id: str, pair: str, direction: str):
        """Trace trading operation"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                span_name = f"trade.{pair}.{direction}"
                
                with self.tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("trade_id", trade_id)
                    span.set_attribute("pair", pair)
                    span.set_attribute("direction", direction)
                    span.set_attribute("timestamp", datetime.utcnow().isoformat())
                    
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        duration_ms = (time.time() - start_time) * 1000
                        
                        span.set_attribute("status", "executed")
                        span.set_attribute("execution_time_ms", duration_ms)
                        
                        if isinstance(result, dict):
                            span.set_attribute("profit", result.get("profit", 0))
                            span.set_attribute("gas_cost", result.get("gas", 0))
                        
                        return result
                    except Exception as e:
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("status", "failed")
                        span.set_attribute("error", str(e))
                        span.set_attribute("execution_time_ms", duration_ms)
                        raise
            return wrapper
        return decorator

    def add_event(self, span_name: str, event_name: str, attributes: Dict[str, Any] = None):
        """Add event to current span"""
        try:
            with self.tracer.start_as_current_span(span_name) as span:
                span.add_event(event_name, attributes=attributes or {})
        except Exception as e:
            logger.debug(f"Failed to add event: {e}")

    def get_tracer(self):
        """Get underlying tracer instance"""
        return self.tracer


# Global instance
_global_tracer = None


def get_tracer(service_name: str = "aineon-engine") -> DistributedTracer:
    """Get or create global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = DistributedTracer(service_name)
    return _global_tracer


# Example usage
if __name__ == "__main__":
    tracer_mgr = get_tracer()

    @tracer_mgr.trace_function("example_function")
    def example_function():
        time.sleep(0.1)
        return {"result": "success"}

    result = example_function()
    print(f"Result: {result}")
