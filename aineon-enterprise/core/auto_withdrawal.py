"""
AINEON 1.0 AUTO WITHDRAWAL SYSTEM
Automatic ETH withdrawal based on profit thresholds

Elite-grade auto withdrawal system for TOP 0.001% performance
Target: Seamless automatic profit extraction with proper safety controls
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

@dataclass
class AutoWithdrawalRule:
    """Auto withdrawal rule configuration"""
    name: str
    threshold_eth: float
    percentage: float  # 0.0 to 1.0
    destination_address: str
    enabled: bool = True
    min_amount_eth: float = 0.1
    max_amount_eth: float = 100.0
    gas_reserve_eth: float = 0.1
    cooldown_hours: float = 1.0  # Minimum time between withdrawals

@dataclass
class AutoWithdrawalExecution:
    """Record of auto withdrawal execution"""
    rule_name: str
    timestamp: datetime
    trigger_balance: float
    withdrawal_amount: float
    destination_address: str
    tx_hash: Optional[str] = None
    success: bool = False
    error: Optional[str] = None

class AutoWithdrawalSystem:
    """Elite-grade automatic withdrawal system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Auto withdrawal configuration
        self.auto_config = {
            'enabled': config.get('enabled', True),
            'check_interval': config.get('check_interval', 3600),  # 1 hour
            'max_concurrent_withdrawals': config.get('max_concurrent_withdrawals', 3),
            'emergency_stop_loss': config.get('emergency_stop_loss', -1.0),  # ETH
            'daily_withdrawal_limit': config.get('daily_withdrawal_limit', 100.0)  # ETH
        }
        
        # Default withdrawal rules
        self.withdrawal_rules: List[AutoWithdrawalRule] = []
        
        # Initialize default rules
        default_rules = config.get('default_rules', [
            {
                'name': 'Conservative',
                'threshold_eth': 5.0,
                'percentage': 0.5,
                'destination_address': '0x742d35Cc6634C0532925a3b8D4A9F3F4F3F7e7e7',
                'enabled': True
            },
            {
                'name': 'Aggressive',
                'threshold_eth': 10.0,
                'percentage': 0.8,
                'destination_address': '0x742d35Cc6634C0532925a3b8D4A9F3F4F3F7e7e7',
                'enabled': False  # Disabled by default
            }
        ])
        
        for rule_config in default_rules:
            rule = AutoWithdrawalRule(**rule_config)
            self.withdrawal_rules.append(rule)
        
        # State tracking
        self.execution_history: List[AutoWithdrawalExecution] = []
        self.last_withdrawal_per_rule: Dict[str, datetime] = {}
        self.daily_withdrawal_stats = {
            'date': datetime.now().date(),
            'total_amount': 0.0,
            'withdrawal_count': 0
        }
        
        # External dependencies (injected)
        self.profit_tracker = None
        self.manual_withdrawal = None
        
        # Monitoring task
        self.monitoring_task = None
        self.running = False
        
        self.logger.info("🤖 AINEON 1.0 Auto Withdrawal System initialized")
        
    def set_dependencies(self, profit_tracker, manual_withdrawal_system):
        """Set external dependencies"""
        self.profit_tracker = profit_tracker
        self.manual_withdrawal = manual_withdrawal_system
        
        # Connect profit tracker to manual withdrawal system
        if self.manual_withdrawal:
            self.manual_withdrawal.set_profit_tracker(profit_tracker)
            
    async def start_auto_withdrawals(self):
        """Start the automatic withdrawal monitoring system"""
        if not self.auto_config['enabled']:
            self.logger.info("🤖 Auto withdrawals are disabled")
            return
            
        self.logger.info("🤖 Starting AINEON 1.0 Auto Withdrawal System")
        self.running = True
        
        try:
            # Start monitoring loop
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Wait for monitoring to complete (runs indefinitely)
            await self.monitoring_task
            
        except Exception as e:
            self.logger.error(f"❌ Error in auto withdrawal system: {e}")
            self.running = False
            raise
            
    async def stop_auto_withdrawals(self):
        """Stop the automatic withdrawal system"""
        self.logger.info("🛑 Stopping Auto Withdrawal System")
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
    async def _monitoring_loop(self):
        """Main monitoring loop for auto withdrawals"""
        while self.running:
            try:
                # Check all enabled rules
                for rule in self.withdrawal_rules:
                    if rule.enabled:
                        await self._check_withdrawal_rule(rule)
                
                # Wait for next check
                await asyncio.sleep(self.auto_config['check_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.auto_config['check_interval'])
                
    async def _check_withdrawal_rule(self, rule: AutoWithdrawalRule):
        """Check if a withdrawal rule should be triggered"""
        try:
            # Get current balance
            current_balance = await self.get_current_balance()
            
            # Check if balance exceeds threshold
            if current_balance <= rule.threshold_eth:
                return
                
            # Check cooldown period
            if self.is_in_cooldown(rule.name):
                return
                
            # Calculate withdrawal amount
            excess_balance = current_balance - rule.threshold_eth
            withdrawal_amount = excess_balance * rule.percentage
            
            # Apply limits
            if withdrawal_amount < rule.min_amount_eth:
                return
                
            withdrawal_amount = min(withdrawal_amount, rule.max_amount_eth)
            
            # Check emergency stop loss
            if withdrawal_amount > abs(self.auto_config['emergency_stop_loss']):
                self.logger.warning(f"🚨 Emergency stop loss triggered for rule {rule.name}")
                return
            
            # Check daily limits
            if not await self.check_daily_limits(withdrawal_amount):
                return
            
            # Execute automatic withdrawal
            await self._execute_auto_withdrawal(rule, current_balance, withdrawal_amount)
            
        except Exception as e:
            self.logger.error(f"Error checking withdrawal rule {rule.name}: {e}")
            
    async def _execute_auto_withdrawal(self, rule: AutoWithdrawalRule, trigger_balance: float, amount: float):
        """Execute automatic withdrawal for a rule"""
        try:
            self.logger.info(f"🤖 Auto withdrawal triggered: {rule.name}")
            self.logger.info(f"   Current balance: {trigger_balance:.4f} ETH")
            self.logger.info(f"   Withdrawal amount: {amount:.4f} ETH")
            self.logger.info(f"   Destination: {rule.destination_address[:10]}...{rule.destination_address[-8:]}")
            
            # Create withdrawal request through manual system
            if self.manual_withdrawal:
                request_result = await self.manual_withdrawal.create_withdrawal_request(
                    amount_eth=amount,
                    destination_address=rule.destination_address
                )
                
                if not request_result['success']:
                    error_msg = f"Failed to create withdrawal request: {request_result['error']}"
                    await self._record_failed_withdrawal(rule, amount, error_msg)
                    return
                
                request_id = request_result['request_id']
                
                # Auto-confirm the withdrawal (no manual confirmation needed for auto)
                confirm_result = await self.manual_withdrawal.confirm_withdrawal(
                    request_id=request_id,
                    confirmation_token="AUTO_CONFIRM"  # Special token for auto withdrawals
                )
                
                if confirm_result['success']:
                    tx_hash = confirm_result.get('tx_hash')
                    self.logger.info(f"✅ Auto withdrawal successful: {tx_hash}")
                    
                    # Record successful execution
                    execution = AutoWithdrawalExecution(
                        rule_name=rule.name,
                        timestamp=datetime.now(),
                        trigger_balance=trigger_balance,
                        withdrawal_amount=amount,
                        destination_address=rule.destination_address,
                        tx_hash=tx_hash,
                        success=True
                    )
                    
                    self.execution_history.append(execution)
                    self.last_withdrawal_per_rule[rule.name] = datetime.now()
                    await self.update_daily_stats(amount)
                    
                    # Keep only last 1000 executions
                    if len(self.execution_history) > 1000:
                        self.execution_history = self.execution_history[-1000:]
                        
                else:
                    error_msg = confirm_result.get('error', 'Unknown error')
                    await self._record_failed_withdrawal(rule, amount, error_msg)
                    
            else:
                error_msg = "Manual withdrawal system not available"
                await self._record_failed_withdrawal(rule, amount, error_msg)
                
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            await self._record_failed_withdrawal(rule, amount, error_msg)
            
    async def _record_failed_withdrawal(self, rule: AutoWithdrawalRule, amount: float, error: str):
        """Record failed withdrawal attempt"""
        execution = AutoWithdrawalExecution(
            rule_name=rule.name,
            timestamp=datetime.now(),
            trigger_balance=0.0,
            withdrawal_amount=amount,
            destination_address=rule.destination_address,
            success=False,
            error=error
        )
        
        self.execution_history.append(execution)
        self.logger.error(f"❌ Auto withdrawal failed: {rule.name} - {error}")
        
    def is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_name not in self.last_withdrawal_per_rule:
            return False
            
        last_withdrawal = self.last_withdrawal_per_rule[rule_name]
        rule = next((r for r in self.withdrawal_rules if r.name == rule_name), None)
        
        if not rule:
            return False
            
        cooldown_duration = timedelta(hours=rule.cooldown_hours)
        return (datetime.now() - last_withdrawal) < cooldown_duration
        
    async def get_current_balance(self) -> float:
        """Get current balance for withdrawal checks"""
        if self.profit_tracker:
            return await self.profit_tracker.get_available_balance()
        else:
            # Fallback for demo
            return 50.0  # Mock balance
            
    async def check_daily_limits(self, withdrawal_amount: float) -> bool:
        """Check daily withdrawal limits"""
        today = datetime.now().date()
        
        # Reset daily stats if new day
        if self.daily_withdrawal_stats['date'] != today:
            self.daily_withdrawal_stats = {
                'date': today,
                'total_amount': 0.0,
                'withdrawal_count': 0
            }
        
        # Check daily amount limit
        if (self.daily_withdrawal_stats['total_amount'] + withdrawal_amount) > self.auto_config['daily_withdrawal_limit']:
            self.logger.warning(f"Daily withdrawal limit exceeded: {self.daily_withdrawal_stats['total_amount'] + withdrawal_amount} > {self.auto_config['daily_withdrawal_limit']}")
            return False
        
        return True
        
    async def update_daily_stats(self, amount: float):
        """Update daily withdrawal statistics"""
        self.daily_withdrawal_stats['total_amount'] += amount
        self.daily_withdrawal_stats['withdrawal_count'] += 1
        
    def add_withdrawal_rule(self, rule: AutoWithdrawalRule):
        """Add a new withdrawal rule"""
        self.withdrawal_rules.append(rule)
        self.logger.info(f"➕ Added withdrawal rule: {rule.name}")
        
    def remove_withdrawal_rule(self, rule_name: str) -> bool:
        """Remove a withdrawal rule"""
        original_count = len(self.withdrawal_rules)
        self.withdrawal_rules = [r for r in self.withdrawal_rules if r.name != rule_name]
        
        if len(self.withdrawal_rules) < original_count:
            self.logger.info(f"➖ Removed withdrawal rule: {rule_name}")
            return True
        else:
            self.logger.warning(f"⚠️ Rule not found: {rule_name}")
            return False
            
    def update_withdrawal_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing withdrawal rule"""
        for rule in self.withdrawal_rules:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                self.logger.info(f"🔄 Updated withdrawal rule: {rule_name}")
                return True
                
        self.logger.warning(f"⚠️ Rule not found for update: {rule_name}")
        return False
        
    def toggle_withdrawal_rule(self, rule_name: str, enabled: bool) -> bool:
        """Toggle withdrawal rule enabled/disabled"""
        return self.update_withdrawal_rule(rule_name, {'enabled': enabled})
        
    async def get_auto_withdrawal_status(self) -> Dict[str, Any]:
        """Get current auto withdrawal system status"""
        enabled_rules = [r for r in self.withdrawal_rules if r.enabled]
        current_balance = await self.get_current_balance()
        
        # Calculate today's stats
        today = datetime.now().date()
        today_executions = [
            e for e in self.execution_history 
            if e.timestamp.date() == today and e.success
        ]
        
        today_amount = sum(e.withdrawal_amount for e in today_executions)
        
        return {
            'system_status': 'running' if self.running else 'stopped',
            'auto_enabled': self.auto_config['enabled'],
            'total_rules': len(self.withdrawal_rules),
            'enabled_rules': len(enabled_rules),
            'current_balance': current_balance,
            'rules_status': [
                {
                    'name': rule.name,
                    'enabled': rule.enabled,
                    'threshold_eth': rule.threshold_eth,
                    'percentage': f"{rule.percentage * 100:.0f}%",
                    'destination_address': rule.destination_address[:10] + '...' + rule.destination_address[-8:],
                    'in_cooldown': self.is_in_cooldown(rule.name)
                }
                for rule in self.withdrawal_rules
            ],
            'daily_stats': {
                'date': self.daily_withdrawal_stats['date'].isoformat(),
                'withdrawal_count': self.daily_withdrawal_stats['withdrawal_count'],
                'total_amount_eth': self.daily_withdrawal_stats['total_amount'],
                'remaining_limit': max(0, self.auto_config['daily_withdrawal_limit'] - self.daily_withdrawal_stats['total_amount'])
            },
            'recent_executions': [
                {
                    'rule_name': e.rule_name,
                    'timestamp': e.timestamp.isoformat(),
                    'withdrawal_amount': e.withdrawal_amount,
                    'success': e.success,
                    'tx_hash': e.tx_hash,
                    'error': e.error
                }
                for e in self.execution_history[-10:]  # Last 10 executions
            ],
            'configuration': {
                'check_interval_seconds': self.auto_config['check_interval'],
                'max_concurrent_withdrawals': self.auto_config['max_concurrent_withdrawals'],
                'emergency_stop_loss': self.auto_config['emergency_stop_loss'],
                'daily_withdrawal_limit': self.auto_config['daily_withdrawal_limit']
            }
        }
        
    async def force_withdrawal(self, rule_name: str, amount: float = None) -> Dict[str, Any]:
        """Force a withdrawal for a specific rule"""
        rule = next((r for r in self.withdrawal_rules if r.name == rule_name), None)
        
        if not rule:
            return {'success': False, 'error': f'Rule not found: {rule_name}'}
        
        if not rule.enabled:
            return {'success': False, 'error': f'Rule is disabled: {rule_name}'}
        
        # Use current balance if amount not specified
        if amount is None:
            current_balance = await self.get_current_balance()
            excess = current_balance - rule.threshold_eth
            amount = excess * rule.percentage
        
        # Apply limits
        amount = max(rule.min_amount_eth, min(amount, rule.max_amount_eth))
        
        self.logger.info(f"🔧 Force withdrawal triggered: {rule_name} - {amount:.4f} ETH")
        
        # Execute withdrawal
        current_balance = await self.get_current_balance()
        await self._execute_auto_withdrawal(rule, current_balance, amount)
        
        return {'success': True, 'rule_name': rule_name, 'amount': amount}
        
    async def get_withdrawal_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get withdrawal history for specified number of days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_executions = [
            e for e in self.execution_history 
            if e.timestamp >= cutoff_date
        ]
        
        return [
            {
                'rule_name': e.rule_name,
                'timestamp': e.timestamp.isoformat(),
                'trigger_balance': e.trigger_balance,
                'withdrawal_amount': e.withdrawal_amount,
                'destination_address': e.destination_address[:10] + '...' + e.destination_address[-8:],
                'tx_hash': e.tx_hash,
                'success': e.success,
                'error': e.error
            }
            for e in filtered_executions
        ]

# Global auto withdrawal system instance
_auto_withdrawal_system = None

def get_auto_withdrawal_system(config: Dict[str, Any] = None) -> AutoWithdrawalSystem:
    """Get or create global auto withdrawal system instance"""
    global _auto_withdrawal_system
    if _auto_withdrawal_system is None:
        if config is None:
            config = {
                'enabled': True,
                'check_interval': 3600,
                'max_concurrent_withdrawals': 3,
                'emergency_stop_loss': -1.0,
                'daily_withdrawal_limit': 100.0
            }
        _auto_withdrawal_system = AutoWithdrawalSystem(config)
    return _auto_withdrawal_system