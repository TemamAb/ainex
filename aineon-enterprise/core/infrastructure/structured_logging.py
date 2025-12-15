"""
Structured Logging Module - JSON Format Audit Trail
AINEON Enterprise Flash Loan Engine
Phase 1, Week 1 - Observability Foundation

All logs output as JSON for centralized aggregation
Compliance-ready audit trail with blockchain verification ready
"""

import logging
import json
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from pathlib import Path
import hashlib

try:
    from pythonjsonlogger import jsonlogger
except ImportError:
    jsonlogger = None


class StructuredLogger:
    """
    Manages structured logging with JSON format
    Provides audit trail for compliance and debugging
    """

    def __init__(self, name: str = "aineon", log_dir: str = "logs"):
        """Initialize structured logger"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        self._setup_console_handler()
        self._setup_file_handler()
        self._setup_audit_handler()

    def _setup_console_handler(self) -> None:
        """Setup console output (JSON format)"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if jsonlogger:
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _setup_file_handler(self) -> None:
        """Setup file output (JSON format)"""
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        if jsonlogger:
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s %(extra)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _setup_audit_handler(self) -> None:
        """Setup audit trail handler"""
        audit_file = self.log_dir / f"{self.name}_audit.log"
        audit_handler = logging.FileHandler(audit_file)
        audit_handler.setLevel(logging.WARNING)
        
        if jsonlogger:
            formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s %(event_type)s %(user)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        audit_handler.setFormatter(formatter)
        self.logger.addHandler(audit_handler)

    def log_trade(self, trade_id: str, pair: str, action: str, **kwargs) -> None:
        """Log trading activity"""
        log_entry = {
            "event_type": "TRADE",
            "trade_id": trade_id,
            "pair": pair,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))

    def log_risk_event(self, event_type: str, severity: str, message: str, **kwargs) -> None:
        """Log risk management events"""
        log_entry = {
            "event_type": "RISK",
            "risk_event": event_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if severity in ["CRITICAL", "HIGH"]:
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry))

    def log_security_event(self, event_type: str, action: str, status: str, **kwargs) -> None:
        """Log security-related events"""
        log_entry = {
            "event_type": "SECURITY",
            "security_event": event_type,
            "action": action,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.warning(json.dumps(log_entry))

    def log_system_event(self, component: str, event: str, level: str = "INFO", **kwargs) -> None:
        """Log system events"""
        log_entry = {
            "event_type": "SYSTEM",
            "component": component,
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        
        if level == "ERROR":
            self.logger.error(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        else:
            self.logger.info(json.dumps(log_entry))

    def log_profit(self, amount: float, currency: str, source: str, **kwargs) -> None:
        """Log profit events"""
        log_entry = {
            "event_type": "PROFIT",
            "amount": amount,
            "currency": currency,
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_entry))

    def get_audit_trail(self, hours: int = 24) -> list:
        """Retrieve recent audit trail"""
        audit_file = self.log_dir / f"{self.name}_audit.log"
        if not audit_file.exists():
            return []
        
        entries = []
        try:
            with open(audit_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            self.logger.error(f"Failed to read audit trail: {e}")
        
        return entries

    def get_logger(self) -> logging.Logger:
        """Get underlying logger instance"""
        return self.logger


# Global instance
_global_logger = None


def get_logger(name: str = "aineon") -> StructuredLogger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger


# Example usage
if __name__ == "__main__":
    logger_mgr = get_logger()
    
    logger_mgr.log_trade("TRADE-001", "WETH/USDC", "execute", profit=0.15, gas=45)
    logger_mgr.log_risk_event("DAILY_LOSS_CAP", "WARNING", "Daily loss limit approaching", loss_pct=1.2)
    logger_mgr.log_security_event("KEY_ROTATION", "rotate_keys", "success")
    logger_mgr.log_profit(0.5, "ETH", "arbitrage", pair="WETH/USDC")
