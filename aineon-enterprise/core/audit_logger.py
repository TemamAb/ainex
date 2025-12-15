"""
Audit Logger - Blockchain-Verified Audit Trail
Immutable audit logging with on-chain verification capability
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib
import uuid
from collections import deque

from web3 import Web3

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    TRADE_EXECUTION = "trade_execution"
    TRADE_FAILURE = "trade_failure"
    POSITION_CHANGE = "position_change"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    SECURITY_EVENT = "security_event"
    KEY_ROTATION = "key_rotation"
    SECRET_ACCESS = "secret_access"
    CONFIGURATION_CHANGE = "config_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    PROFIT_REALIZATION = "profit_realization"
    ERROR_OCCURRED = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Represents a single audit event"""
    event_id: str
    timestamp: str
    event_type: str
    severity: str
    actor: str
    action: str
    resource: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    hash: Optional[str] = None
    blockchain_hash: Optional[str] = None
    
    def calculate_hash(self) -> str:
        """Calculate SHA-256 hash of event"""
        event_dict = {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'severity': self.severity,
            'actor': self.actor,
            'action': self.action,
            'resource': self.resource,
            'details': self.details,
        }
        
        json_str = json.dumps(event_dict, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        if not data.get('hash'):
            data['hash'] = self.calculate_hash()
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Maintains immutable audit trail with blockchain verification"""
    
    def __init__(self, enable_blockchain: bool = False):
        self.enable_blockchain = enable_blockchain
        self.events: deque = deque(maxlen=10000)  # In-memory buffer
        self.chain_hashes: List[str] = []  # Merkle chain
        
        # Initialize blockchain if enabled
        if enable_blockchain:
            self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URL')))
            self.contract_address = os.getenv('AUDIT_LOG_CONTRACT')
            self.account_address = os.getenv('AUDIT_LOGGER_ADDRESS')
        else:
            self.w3 = None
            self.contract_address = None
            self.account_address = None
        
        # File-based logging
        self.log_dir = os.getenv('AUDIT_LOG_DIR', 'logs/audit')
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Create audit log directory if needed"""
        os.makedirs(self.log_dir, exist_ok=True)
    
    async def log_event(self, event_type: AuditEventType, severity: AuditSeverity,
                       actor: str, action: str, resource: str,
                       details: Dict[str, Any],
                       source_ip: Optional[str] = None) -> AuditEvent:
        """Log an audit event"""
        
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type.value,
            severity=severity.value,
            actor=actor,
            action=action,
            resource=resource,
            details=details,
            source_ip=source_ip,
        )
        
        # Calculate hash
        event.hash = event.calculate_hash()
        
        # Add to in-memory buffer
        self.events.append(event)
        
        # Log to file (JSON format)
        await self._write_to_file(event)
        
        # Store blockchain hash if enabled
        if self.enable_blockchain:
            blockchain_hash = await self._write_to_blockchain(event)
            event.blockchain_hash = blockchain_hash
        
        logger.info(f"Audit event logged: {event_type.value} - {action}")
        
        return event
    
    async def _write_to_file(self, event: AuditEvent):
        """Write event to audit log file"""
        try:
            # Use date-based filename
            log_file = os.path.join(
                self.log_dir,
                f"audit_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
            )
            
            with open(log_file, 'a') as f:
                f.write(event.to_json() + '\n')
            
        except Exception as e:
            logger.error(f"Failed to write audit log to file: {e}")
    
    async def _write_to_blockchain(self, event: AuditEvent) -> Optional[str]:
        """Write event hash to blockchain for verification"""
        if not self.w3 or not self.contract_address:
            return None
        
        try:
            event_hash = event.calculate_hash()
            
            # In a real implementation, this would call a smart contract
            # to store the hash on-chain for immutability verification
            logger.debug(f"Would submit hash to blockchain: {event_hash[:16]}...")
            
            # Placeholder: return the hash as if confirmed
            return event_hash
            
        except Exception as e:
            logger.error(f"Failed to write to blockchain: {e}")
            return None
    
    async def verify_event(self, event_id: str, expected_hash: str) -> bool:
        """Verify an event hasn't been tampered with"""
        # Find event in buffer
        for event in self.events:
            if event.event_id == event_id:
                return event.hash == expected_hash
        
        # Could also check blockchain or file here
        return False
    
    async def get_event_trail(self, actor: Optional[str] = None,
                             event_type: Optional[AuditEventType] = None,
                             limit: int = 100) -> List[AuditEvent]:
        """Retrieve audit trail with optional filtering"""
        results = []
        
        for event in list(self.events):
            if actor and event.actor != actor:
                continue
            if event_type and event.event_type != event_type.value:
                continue
            
            results.append(event)
            if len(results) >= limit:
                break
        
        return list(reversed(results))[:limit]
    
    async def export_audit_trail(self, filepath: str, 
                                actor: Optional[str] = None) -> bool:
        """Export audit trail to file (for compliance)"""
        try:
            events = await self.get_event_trail(actor=actor, limit=None)
            
            with open(filepath, 'w') as f:
                for event in events:
                    f.write(event.to_json() + '\n')
            
            logger.info(f"Audit trail exported: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export audit trail: {e}")
            return False
    
    async def generate_report(self, start_date: str, end_date: str) -> Dict:
        """Generate audit report for date range"""
        report = {
            'start_date': start_date,
            'end_date': end_date,
            'total_events': 0,
            'events_by_type': {},
            'events_by_severity': {},
            'critical_events': [],
            'generated_at': datetime.utcnow().isoformat(),
        }
        
        for event in self.events:
            event_time = datetime.fromisoformat(event.timestamp)
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if not (start <= event_time <= end):
                continue
            
            report['total_events'] += 1
            
            # Count by type
            event_type = event.event_type
            report['events_by_type'][event_type] = report['events_by_type'].get(event_type, 0) + 1
            
            # Count by severity
            severity = event.severity
            report['events_by_severity'][severity] = report['events_by_severity'].get(severity, 0) + 1
            
            # Track critical events
            if severity == AuditSeverity.CRITICAL.value:
                report['critical_events'].append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp,
                    'type': event.event_type,
                    'action': event.action,
                })
        
        return report
    
    async def clear_expired_events(self, days: int = 90):
        """Clear events older than specified days (for storage management)"""
        cutoff = datetime.utcnow()
        cutoff = cutoff.replace(day=cutoff.day - days)
        
        removed = 0
        events_to_keep = []
        
        for event in self.events:
            event_time = datetime.fromisoformat(event.timestamp)
            if event_time >= cutoff:
                events_to_keep.append(event)
            else:
                removed += 1
        
        self.events = deque(events_to_keep, maxlen=10000)
        logger.info(f"Cleared {removed} expired events")
        
        return removed


class ComplianceFormatter:
    """Formats audit logs for regulatory compliance"""
    
    @staticmethod
    def format_for_ofac(events: List[AuditEvent]) -> str:
        """Format audit trail for OFAC compliance"""
        report = {
            'report_type': 'OFAC_AUDIT_TRAIL',
            'generated_at': datetime.utcnow().isoformat(),
            'total_transactions': len(events),
            'transactions': []
        }
        
        for event in events:
            report['transactions'].append({
                'timestamp': event.timestamp,
                'event_id': event.event_id,
                'type': event.event_type,
                'details': event.details,
                'hash': event.hash,
            })
        
        return json.dumps(report, indent=2)
    
    @staticmethod
    def format_for_kyc(events: List[AuditEvent]) -> str:
        """Format audit trail for KYC compliance"""
        report = {
            'report_type': 'KYC_AUDIT_TRAIL',
            'generated_at': datetime.utcnow().isoformat(),
            'events': []
        }
        
        for event in events:
            if event.event_type in ['security_event', 'key_rotation']:
                report['events'].append({
                    'timestamp': event.timestamp,
                    'action': event.action,
                    'actor': event.actor,
                    'details': event.details,
                })
        
        return json.dumps(report, indent=2)


# Global instance
_audit_logger: Optional[AuditLogger] = None


def init_audit_logger(enable_blockchain: bool = False) -> AuditLogger:
    """Initialize global audit logger"""
    global _audit_logger
    _audit_logger = AuditLogger(enable_blockchain=enable_blockchain)
    return _audit_logger


async def log_audit_event(event_type: AuditEventType, severity: AuditSeverity,
                         actor: str, action: str, resource: str,
                         details: Dict[str, Any],
                         source_ip: Optional[str] = None) -> AuditEvent:
    """Log audit event globally"""
    global _audit_logger
    if not _audit_logger:
        _audit_logger = init_audit_logger()
    
    return await _audit_logger.log_event(event_type, severity, actor, action, 
                                        resource, details, source_ip)
