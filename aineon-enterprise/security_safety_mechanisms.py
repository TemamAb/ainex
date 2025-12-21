#!/usr/bin/env python3
"""
AINEON SECURITY & SAFETY MECHANISMS
Comprehensive security framework for live blockchain operations
Implements safety controls, monitoring, and emergency protocols
"""

import asyncio
import json
import logging
import time
import secrets
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, asdict
from decimal import Decimal
import aiohttp

from web3 import Web3
from eth_account import Account
from hexbytes import HexBytes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event tracking"""
    event_type: str
    severity: str  # low, medium, high, critical
    description: str
    timestamp: float
    source: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    overall_risk_score: float  # 0.0 to 1.0
    risk_level: str  # low, medium, high, critical
    detected_risks: List[str]
    mitigation_suggestions: List[str]
    recommended_actions: List[str]
    timestamp: float

@dataclass
class SafetyThreshold:
    """Safety threshold configuration"""
    metric: str
    warning_threshold: float
    critical_threshold: float
    current_value: float
    status: str  # normal, warning, critical

class SecuritySafetyManager:
    """
    SECURITY & SAFETY MANAGER
    Comprehensive security framework for live blockchain operations
    Implements safety controls, monitoring, and emergency protocols
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Security configuration
        self.security_config = config.get('security', {})
        self.safety_config = config.get('safety', {})
        
        # Security monitoring
        self.security_events = []
        self.risk_assessments = []
        self.safety_thresholds = []
        
        # Emergency controls
        self.emergency_stop_active = False
        self.security_breach_detected = False
        self.maintenance_mode = False
        
        # Wallet protection
        self.authorized_wallets = config.get('authorized_wallets', [])
        self.max_transfer_amount = config.get('max_transfer_amount', 100.0)  # ETH
        self.daily_withdrawal_limit = config.get('daily_withdrawal_limit', 1000.0)  # ETH
        
        # Network monitoring
        self.network_anomalies = []
        self.failed_transactions = []
        self.suspicious_activities = []
        
        # Rate limiting
        self.transaction_rate_limits = {
            'per_minute': 60,
            'per_hour': 1000,
            'per_day': 10000
        }
        self.current_rates = {
            'per_minute': 0,
            'per_hour': 0,
            'per_day': 0,
            'window_start': time.time()
        }
        
        # Safety thresholds
        self.setup_safety_thresholds()
        
        # Web3 connections for monitoring
        self.rpc_urls = config.get('rpc_urls', [
            'https://eth-mainnet.g.alchemy.com/v2/',
            'https://eth-mainnet.public.blastapi.io'
        ])
        self.primary_web3 = Web3(Web3.HTTPProvider(self.rpc_urls[0]))
        
        logger.info("SecuritySafetyManager initialized - COMPREHENSIVE SECURITY FRAMEWORK")
    
    def setup_safety_thresholds(self):
        """Initialize safety thresholds for monitoring"""
        self.safety_thresholds = [
            SafetyThreshold(
                metric='gas_price_gwei',
                warning_threshold=50.0,  # 50 gwei
                critical_threshold=100.0,  # 100 gwei
                current_value=0.0,
                status='normal'
            ),
            SafetyThreshold(
                metric='transaction_failure_rate',
                warning_threshold=0.1,  # 10%
                critical_threshold=0.25,  # 25%
                current_value=0.0,
                status='normal'
            ),
            SafetyThreshold(
                metric='balance_depletion_rate',
                warning_threshold=0.05,  # 5% per hour
                critical_threshold=0.15,  # 15% per hour
                current_value=0.0,
                status='normal'
            ),
            SafetyThreshold(
                metric='profit_loss_rate',
                warning_threshold=0.05,  # 5% loss rate
                critical_threshold=0.10,  # 10% loss rate
                current_value=0.0,
                status='normal'
            ),
            SafetyThreshold(
                metric='network_latency_ms',
                warning_threshold=2000.0,  # 2 seconds
                critical_threshold=5000.0,  # 5 seconds
                current_value=0.0,
                status='normal'
            )
        ]
    
    async def validate_transaction_safety(self, tx_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate transaction safety before execution
        Returns (is_safe, warnings)
        """
        warnings = []
        
        try:
            # Validate amount limits
            if tx_data.get('amount_eth', 0) > self.max_transfer_amount:
                warnings.append(f"Transaction amount {tx_data['amount_eth']} ETH exceeds safety limit {self.max_transfer_amount} ETH")
            
            # Validate wallet authorization
            if tx_data.get('from_address') not in self.authorized_wallets:
                warnings.append(f"Unauthorized wallet: {tx_data['from_address']}")
            
            # Validate gas price
            if tx_data.get('gas_price_gwei', 0) > 100:  # 100 gwei limit
                warnings.append(f"Gas price {tx_data['gas_price_gwei']} gwei exceeds safe limit")
            
            # Rate limiting check
            if not await self.check_rate_limits():
                warnings.append("Transaction rate limit exceeded")
            
            # Check emergency stop
            if self.emergency_stop_active:
                warnings.append("Emergency stop is active - transactions blocked")
            
            # Check maintenance mode
            if self.maintenance_mode:
                warnings.append("System is in maintenance mode - transactions blocked")
            
            # Check safety thresholds
            critical_threshold_breached = False
            for threshold in self.safety_thresholds:
                if threshold.status == 'critical':
                    critical_threshold_breached = True
                    warnings.append(f"Critical safety threshold breached: {threshold.metric}")
            
            # Network anomaly check
            network_anomalies = await self.detect_network_anomalies()
            if network_anomalies:
                warnings.extend(network_anomalies)
            
            is_safe = len(warnings) == 0 and not critical_threshold_breached
            
            # Log security event
            await self.log_security_event(
                event_type='transaction_validation',
                severity='high' if warnings else 'low',
                description=f"Transaction validation: {'SAFE' if is_safe else 'UNSAFE'}",
                source='safety_manager',
                details={'warnings': warnings, 'tx_data': tx_data}
            )
            
            return is_safe, warnings
            
        except Exception as e:
            logger.error(f"Transaction safety validation failed: {e}")
            return False, [f"Safety validation error: {str(e)}"]
    
    async def check_rate_limits(self) -> bool:
        """Check if transaction rate limits are respected"""
        try:
            current_time = time.time()
            
            # Reset counters if time window changed
            if current_time - self.current_rates['window_start'] > 3600:  # 1 hour
                self.current_rates = {
                    'per_minute': 0,
                    'per_hour': 0,
                    'per_day': 0,
                    'window_start': current_time
                }
            
            # Check rate limits
            if self.current_rates['per_minute'] >= self.transaction_rate_limits['per_minute']:
                return False
            if self.current_rates['per_hour'] >= self.transaction_rate_limits['per_hour']:
                return False
            if self.current_rates['per_day'] >= self.transaction_rate_limits['per_day']:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False
    
    async def update_rate_counters(self, transaction_count: int = 1):
        """Update transaction rate counters"""
        try:
            self.current_rates['per_minute'] += transaction_count
            self.current_rates['per_hour'] += transaction_count
            self.current_rates['per_day'] += transaction_count
            
            # Log rate limit breach if exceeded
            if not await self.check_rate_limits():
                await self.log_security_event(
                    event_type='rate_limit_breach',
                    severity='high',
                    description='Transaction rate limit exceeded',
                    source='safety_manager',
                    details=self.current_rates
                )
                
        except Exception as e:
            logger.error(f"Rate counter update failed: {e}")
    
    async def perform_risk_assessment(self) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        try:
            logger.info("Performing comprehensive risk assessment")
            
            detected_risks = []
            mitigation_suggestions = []
            recommended_actions = []
            risk_factors = []
            
            # Check network security
            network_risks = await self.assess_network_security()
            risk_factors.extend(network_risks)
            
            # Check transaction patterns
            transaction_risks = await self.assess_transaction_patterns()
            risk_factors.extend(transaction_risks)
            
            # Check wallet security
            wallet_risks = await self.assess_wallet_security()
            risk_factors.extend(wallet_risks)
            
            # Check system health
            system_risks = await self.assess_system_health()
            risk_factors.extend(system_risks)
            
            # Calculate overall risk score
            risk_score = min(1.0, len(risk_factors) * 0.1)  # Each risk factor adds 0.1 to score
            
            # Determine risk level
            if risk_score < 0.2:
                risk_level = 'low'
            elif risk_score < 0.5:
                risk_level = 'medium'
            elif risk_score < 0.8:
                risk_level = 'high'
            else:
                risk_level = 'critical'
            
            # Generate recommendations
            if risk_level in ['high', 'critical']:
                recommended_actions.extend([
                    'Activate emergency stop procedures',
                    'Reduce transaction volumes',
                    'Review and strengthen security controls',
                    'Monitor all activities more closely'
                ])
            
            if 'high_gas_prices' in risk_factors:
                mitigation_suggestions.append('Implement gas price monitoring and alerts')
            
            if 'frequent_failures' in risk_factors:
                mitigation_suggestions.append('Investigate and resolve transaction failures')
            
            if 'unauthorized_wallets' in risk_factors:
                mitigation_suggestions.append('Review wallet authorization list')
            
            # Create risk assessment
            assessment = RiskAssessment(
                overall_risk_score=risk_score,
                risk_level=risk_level,
                detected_risks=risk_factors,
                mitigation_suggestions=mitigation_suggestions,
                recommended_actions=recommended_actions,
                timestamp=time.time()
            )
            
            self.risk_assessments.append(assessment)
            
            # Log security event
            await self.log_security_event(
                event_type='risk_assessment',
                severity=risk_level,
                description=f'Risk assessment completed: {risk_level} risk ({risk_score:.2f})',
                source='safety_manager',
                details={'risk_factors': risk_factors, 'recommendations': recommended_actions}
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return RiskAssessment(
                overall_risk_score=1.0,
                risk_level='critical',
                detected_risks=['assessment_failure'],
                mitigation_suggestions=['Review system status and restart services'],
                recommended_actions=['Investigate risk assessment failure'],
                timestamp=time.time()
            )
    
    async def assess_network_security(self) -> List[str]:
        """Assess network security risks"""
        risks = []
        
        try:
            # Check network connectivity
            if not self.primary_web3.is_connected():
                risks.append('network_disconnect')
            
            # Check for suspicious network patterns
            recent_failures = len([e for e in self.security_events 
                                 if e.event_type == 'transaction_failure' 
                                 and time.time() - e.timestamp < 3600])
            
            if recent_failures > 10:
                risks.append('high_failure_rate')
            
            # Check gas price anomalies
            try:
                gas_price = self.primary_web3.eth.gas_price
                if gas_price > 100_000_000_000:  # 100 gwei
                    risks.append('high_gas_prices')
            except Exception:
                pass
                
        except Exception as e:
            logger.warning(f"Network security assessment failed: {e}")
        
        return risks
    
    async def assess_transaction_patterns(self) -> List[str]:
        """Assess transaction pattern risks"""
        risks = []
        
        try:
            # Check for unusual transaction patterns
            now = time.time()
            recent_transactions = len([e for e in self.security_events 
                                     if e.event_type == 'transaction_execution' 
                                     and now - e.timestamp < 300])  # 5 minutes
            
            if recent_transactions > 100:
                risks.append('high_transaction_volume')
            
            # Check for failed transactions
            recent_failures = len([e for e in self.security_events 
                                 if e.event_type == 'transaction_failure' 
                                 and now - e.timestamp < 300])
            
            failure_rate = recent_failures / max(1, recent_transactions)
            if failure_rate > 0.2:  # 20% failure rate
                risks.append('high_failure_rate')
            
        except Exception as e:
            logger.warning(f"Transaction pattern assessment failed: {e}")
        
        return risks
    
    async def assess_wallet_security(self) -> List[str]:
        """Assess wallet security risks"""
        risks = []
        
        try:
            # Check for unauthorized wallet usage
            for event in self.security_events[-100:]:  # Last 100 events
                if event.event_type == 'unauthorized_wallet_access':
                    risks.append('unauthorized_wallets')
                    break
            
            # Check wallet balance depletion
            # This would need real wallet balance monitoring
            # For now, we'll use proxy indicators
            
        except Exception as e:
            logger.warning(f"Wallet security assessment failed: {e}")
        
        return risks
    
    async def assess_system_health(self) -> List[str]:
        """Assess overall system health risks"""
        risks = []
        
        try:
            # Check safety thresholds
            for threshold in self.safety_thresholds:
                if threshold.status == 'critical':
                    risks.append(f'critical_{threshold.metric}')
            
            # Check for emergency conditions
            if self.emergency_stop_active:
                risks.append('emergency_stop_active')
            
            if self.security_breach_detected:
                risks.append('security_breach_detected')
            
            if self.maintenance_mode:
                risks.append('maintenance_mode')
                
        except Exception as e:
            logger.warning(f"System health assessment failed: {e}")
        
        return risks
    
    async def detect_network_anomalies(self) -> List[str]:
        """Detect network anomalies and potential attacks"""
        anomalies = []
        
        try:
            # Check for rapid transaction failures
            recent_failures = [e for e in self.security_events 
                             if e.event_type == 'transaction_failure' 
                             and time.time() - e.timestamp < 60]  # Last minute
            
            if len(recent_failures) > 5:
                anomalies.append('Rapid transaction failures detected')
            
            # Check for unusual gas price spikes
            try:
                gas_price = self.primary_web3.eth.gas_price
                if gas_price > 200_000_000_000:  # 200 gwei - unusual spike
                    anomalies.append('Unusual gas price spike detected')
            except Exception:
                pass
            
            # Check for RPC endpoint issues
            if not self.primary_web3.is_connected():
                anomalies.append('RPC endpoint connectivity issues')
            
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        
        return anomalies
    
    async def activate_emergency_stop(self, reason: str = "Manual emergency stop") -> Dict[str, Any]:
        """Activate emergency stop protocol"""
        try:
            logger.critical("EMERGENCY STOP ACTIVATED")
            logger.critical(f"Reason: {reason}")
            
            self.emergency_stop_active = True
            
            # Log security event
            await self.log_security_event(
                event_type='emergency_stop',
                severity='critical',
                description=f'Emergency stop activated: {reason}',
                source='safety_manager',
                details={'reason': reason}
            )
            
            return {
                'success': True,
                'message': 'Emergency stop activated successfully',
                'status': 'emergency_stop_active'
            }
            
        except Exception as e:
            logger.error(f"Emergency stop activation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def deactivate_emergency_stop(self) -> Dict[str, Any]:
        """Deactivate emergency stop protocol"""
        try:
            logger.info("EMERGENCY STOP DEACTIVATED")
            
            self.emergency_stop_active = False
            
            # Log security event
            await self.log_security_event(
                event_type='emergency_stop_deactivation',
                severity='medium',
                description='Emergency stop deactivated',
                source='safety_manager'
            )
            
            return {
                'success': True,
                'message': 'Emergency stop deactivated successfully',
                'status': 'normal'
            }
            
        except Exception as e:
            logger.error(f"Emergency stop deactivation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def log_security_event(self, event_type: str, severity: str, description: str, 
                                source: str, details: Optional[Dict[str, Any]] = None):
        """Log security event for monitoring and analysis"""
        try:
            event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                description=description,
                timestamp=time.time(),
                source=source,
                details=details
            )
            
            self.security_events.append(event)
            
            # Keep only recent events (last 1000)
            if len(self.security_events) > 1000:
                self.security_events = self.security_events[-1000:]
            
            # Log to standard logger based on severity
            log_level = {
                'low': logging.INFO,
                'medium': logging.WARNING,
                'high': logging.ERROR,
                'critical': logging.CRITICAL
            }.get(severity, logging.INFO)
            
            logger.log(log_level, f"SECURITY EVENT [{severity.upper()}] {description}")
            
        except Exception as e:
            logger.error(f"Security event logging failed: {e}")
    
    async def monitor_safety_thresholds(self) -> Dict[str, Any]:
        """Monitor and update safety thresholds"""
        try:
            threshold_updates = []
            
            # Update gas price threshold
            try:
                gas_price_gwei = self.primary_web3.eth.gas_price / 1e9
                gas_threshold = next(t for t in self.safety_thresholds if t.metric == 'gas_price_gwei')
                gas_threshold.current_value = gas_price_gwei
                
                if gas_price_gwei > gas_threshold.critical_threshold:
                    gas_threshold.status = 'critical'
                    threshold_updates.append(f'Gas price critical: {gas_price_gwei:.1f} gwei')
                elif gas_price_gwei > gas_threshold.warning_threshold:
                    gas_threshold.status = 'warning'
                else:
                    gas_threshold.status = 'normal'
                    
            except Exception as e:
                logger.warning(f"Gas price threshold update failed: {e}")
            
            # Check for threshold breaches
            critical_thresholds = [t for t in self.safety_thresholds if t.status == 'critical']
            
            if critical_thresholds:
                await self.log_security_event(
                    event_type='threshold_breach',
                    severity='high',
                    description=f'Critical thresholds breached: {len(critical_thresholds)}',
                    source='safety_monitor',
                    details=[{'metric': t.metric, 'value': t.current_value} for t in critical_thresholds]
                )
            
            return {
                'thresholds_monitored': len(self.safety_thresholds),
                'critical_breaches': len(critical_thresholds),
                'updates': threshold_updates
            }
            
        except Exception as e:
            logger.error(f"Safety threshold monitoring failed: {e}")
            return {'error': str(e)}
    
    async def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        try:
            now = time.time()
            recent_events = [e for e in self.security_events if now - e.timestamp < 86400]  # Last 24 hours
            
            # Event statistics
            event_counts = {}
            for event in recent_events:
                event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
            
            # Severity distribution
            severity_counts = {}
            for event in recent_events:
                severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
            
            # Risk assessment
            latest_assessment = self.risk_assessments[-1] if self.risk_assessments else None
            
            return {
                'timestamp': now,
                'system_status': {
                    'emergency_stop_active': self.emergency_stop_active,
                    'security_breach_detected': self.security_breach_detected,
                    'maintenance_mode': self.maintenance_mode
                },
                'recent_24h_activity': {
                    'total_events': len(recent_events),
                    'event_counts': event_counts,
                    'severity_distribution': severity_counts
                },
                'latest_risk_assessment': asdict(latest_assessment) if latest_assessment else None,
                'safety_thresholds': [asdict(t) for t in self.safety_thresholds],
                'rate_limits': {
                    'current_usage': self.current_rates,
                    'limits': self.transaction_rate_limits
                },
                'recommendations': [
                    'Continue monitoring security events',
                    'Review threshold configurations regularly',
                    'Maintain emergency stop procedures',
                    'Regular security assessments'
                ]
            }
            
        except Exception as e:
            logger.error(f"Security report generation failed: {e}")
            return {'error': str(e)}
    
    def get_security_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get security events with optional filtering"""
        try:
            events = self.security_events[-limit:]  # Get recent events
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            return [asdict(event) for event in events]
            
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []

# Configuration for security and safety manager
SECURITY_SAFETY_CONFIG = {
    'authorized_wallets': [
        '0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490'  # Add your authorized wallet
    ],
    'max_transfer_amount': 100.0,  # ETH
    'daily_withdrawal_limit': 1000.0,  # ETH
    'security': {
        'enable_encryption': True,
        'enable_audit_logging': True,
        'enable_rate_limiting': True
    },
    'safety': {
        'enable_emergency_stop': True,
        'enable_threshold_monitoring': True,
        'enable_risk_assessment': True
    },
    'rpc_urls': [
        'https://eth-mainnet.g.alchemy.com/v2/',
        'https://eth-mainnet.public.blastapi.io'
    ]
}

async def main():
    """Test security and safety manager"""
    print("🔐 AINEON SECURITY & SAFETY MANAGER - COMPREHENSIVE PROTECTION")
    print("=" * 80)
    
    # Initialize security manager
    security_manager = SecuritySafetyManager(SECURITY_SAFETY_CONFIG)
    
    # Test risk assessment
    print("\n⚠️  RISK ASSESSMENT")
    risk_assessment = await security_manager.perform_risk_assessment()
    
    print(f"Overall Risk Score: {risk_assessment.overall_risk_score:.2f}")
    print(f"Risk Level: {risk_assessment.risk_level.upper()}")
    print(f"Detected Risks: {len(risk_assessment.detected_risks)}")
    
    if risk_assessment.detected_risks:
        print("Risks Found:")
        for risk in risk_assessment.detected_risks:
            print(f"  - {risk}")
    
    # Test safety threshold monitoring
    print("\n📊 SAFETY THRESHOLDS")
    threshold_status = await security_manager.monitor_safety_thresholds()
    
    print(f"Thresholds Monitored: {threshold_status.get('thresholds_monitored', 0)}")
    print(f"Critical Breaches: {threshold_status.get('critical_breaches', 0)}")
    
    # Test transaction safety validation
    print("\n🛡️  TRANSACTION SAFETY VALIDATION")
    test_tx = {
        'from_address': '0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490',
        'to_address': '0x0000000000000000000000000000000000000000',
        'amount_eth': 1.0,
        'gas_price_gwei': 25.0
    }
    
    is_safe, warnings = await security_manager.validate_transaction_safety(test_tx)
    
    print(f"Transaction Safety: {'SAFE' if is_safe else 'UNSAFE'}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("✅ No safety concerns detected")
    
    # Test security event logging
    await security_manager.log_security_event(
        event_type='test_security_check',
        severity='low',
        description='Security system test completed',
        source='test_script'
    )
    
    # Generate security report
    print("\n📋 SECURITY REPORT")
    security_report = await security_manager.generate_security_report()
    
    print(f"System Status:")
    for status, value in security_report['system_status'].items():
        print(f"  {status}: {value}")
    
    print(f"Recent 24h Activity:")
    print(f"  Total Events: {security_report['recent_24h_activity']['total_events']}")
    
    # Test emergency stop
    print("\n🚨 EMERGENCY STOP TEST")
    emergency_result = await security_manager.activate_emergency_stop("Test emergency stop")
    print(f"Emergency Stop: {emergency_result['status']}")
    
    # Deactivate emergency stop
    deactivation_result = await security_manager.deactivate_emergency_stop()
    print(f"Emergency Stop: {deactivation_result['status']}")
    
    # Show recent security events
    print("\n📝 RECENT SECURITY EVENTS")
    recent_events = security_manager.get_security_events(5)
    
    for event in recent_events:
        print(f"[{event['severity'].upper()}] {event['description']}")
        print(f"  Type: {event['event_type']} | Source: {event['source']}")
        print(f"  Time: {time.ctime(event['timestamp'])}")
        print()
    
    print("\n✅ SECURITY & SAFETY MANAGER TEST COMPLETE")
    print("🔒 Comprehensive security framework operational!")

if __name__ == "__main__":
    asyncio.run(main())