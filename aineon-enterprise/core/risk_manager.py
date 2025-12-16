"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON ENTERPRISE RISK MANAGER                             ║
║              Position limits, loss caps, circuit breaker enforcement           ║
║                                                                                ║
║  Phase 1: Risk Management Implementation                                      ║
║  Status: Production-ready                                                     ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time

logger = logging.getLogger(__name__)


class BreacherType(Enum):
    """Circuit breaker breach types"""
    POSITION_LIMIT = "position_limit"
    DAILY_LOSS = "daily_loss"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    MODEL_ACCURACY = "model_accuracy"
    SLIPPAGE_EXCESSIVE = "slippage_excessive"


@dataclass
class Trade:
    """Trade execution record"""
    trade_id: str
    token_in: str
    token_out: str
    amount: Decimal
    executed_price: Decimal
    profit: Decimal
    status: str  # PENDING, CONFIRMED, FAILED, REVERTED
    timestamp: float
    execution_time_ms: float = 0.0
    slippage_pct: float = 0.0
    gas_cost: Decimal = Decimal('0')
    
    @property
    def is_profitable(self) -> bool:
        return self.profit > 0


@dataclass
class RiskBreachEvent:
    """Risk limit breach event"""
    breach_type: BreacherType
    severity: str  # INFO, WARNING, CRITICAL
    message: str
    timestamp: float
    limit_value: float
    actual_value: float
    action_taken: str = "NONE"


class PortfolioState:
    """Real-time portfolio state tracking"""
    
    def __init__(self, initial_capital: Decimal, max_daily_loss: Decimal):
        self.total_capital = initial_capital
        self.max_daily_loss = max_daily_loss
        
        self.trades = []
        self.daily_trades = []
        self.daily_losses = Decimal('0')
        self.daily_profits = Decimal('0')
        
        self.day_start = datetime.utcnow().date()
        self.positions = {}  # Open positions by trade_id
    
    def reset_daily(self):
        """Reset daily counters (called at UTC 00:00)"""
        self.daily_trades = []
        self.daily_losses = Decimal('0')
        self.daily_profits = Decimal('0')
        self.day_start = datetime.utcnow().date()
        logger.info("✓ Daily counters reset")
    
    def add_trade(self, trade: Trade):
        """Record trade execution"""
        self.trades.append(trade)
        self.daily_trades.append(trade)
        
        if trade.is_profitable:
            self.daily_profits += trade.profit
        else:
            self.daily_losses += abs(trade.profit)
        
        if trade.status == "PENDING":
            self.positions[trade.trade_id] = trade
        elif trade.trade_id in self.positions:
            del self.positions[trade.trade_id]
    
    @property
    def idle_capital(self) -> Decimal:
        """Capital not deployed"""
        deployed = sum(t.amount for t in self.positions.values())
        return self.total_capital - deployed
    
    @property
    def utilization_pct(self) -> float:
        """Capital utilization percentage"""
        deployed = sum(t.amount for t in self.positions.values())
        return float(deployed / self.total_capital * 100)
    
    @property
    def daily_pnl(self) -> Decimal:
        """Daily profit/loss"""
        return self.daily_profits - self.daily_losses
    
    @property
    def daily_win_rate(self) -> float:
        """Win rate for today"""
        if not self.daily_trades:
            return 0.0
        wins = sum(1 for t in self.daily_trades if t.is_profitable)
        return wins / len(self.daily_trades) * 100
    
    @property
    def daily_sharpe_ratio(self) -> float:
        """Sharpe ratio for daily trades (simplified)"""
        if len(self.daily_trades) < 2:
            return 0.0
        
        returns = [float(t.profit / t.amount) for t in self.daily_trades]
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        
        if variance == 0:
            return 0.0
        
        std_dev = variance ** 0.5
        return mean_return / std_dev if std_dev > 0 else 0.0


class EnterpriseRiskManager:
    """Enterprise-grade risk management"""
    
    def __init__(self, 
                 max_per_trade: Decimal,
                 max_daily_loss: Decimal,
                 max_concurrent_positions: int,
                 max_slippage_pct: float,
                 min_confidence: float,
                 circuit_breaker_failures: int):
        
        self.max_per_trade = max_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_concurrent_positions = max_concurrent_positions
        self.max_slippage_pct = max_slippage_pct
        self.min_confidence = min_confidence
        self.circuit_breaker_failures = circuit_breaker_failures
        
        # State tracking
        self.portfolio = PortfolioState(Decimal('100000000'), max_daily_loss)
        self.breach_events: List[RiskBreachEvent] = []
        self.consecutive_failures = 0
        self.circuit_breaker_active = False
        self.model_accuracy = 0.88
    
    def validate_trade(self, amount: Decimal, confidence: float, 
                      slippage_estimate: float) -> tuple[bool, Optional[str]]:
        """
        Validate trade against risk limits
        
        Returns: (is_valid, error_message)
        """
        
        # Check 1: Per-trade limit
        if amount > self.max_per_trade:
            msg = f"Trade ${amount} exceeds limit ${self.max_per_trade}"
            self._record_breach(BreacherType.POSITION_LIMIT, "WARNING", msg, 
                              float(amount), float(self.max_per_trade))
            return False, msg
        
        # Check 2: Concurrent positions
        if len(self.portfolio.positions) >= self.max_concurrent_positions:
            msg = f"Too many open positions ({len(self.portfolio.positions)})"
            self._record_breach(BreacherType.POSITION_LIMIT, "WARNING", msg,
                              len(self.portfolio.positions), self.max_concurrent_positions)
            return False, msg
        
        # Check 3: Daily loss cap
        if self.portfolio.daily_losses + amount > self.max_daily_loss:
            msg = f"Daily loss would exceed ${self.max_daily_loss}"
            self._record_breach(BreacherType.DAILY_LOSS, "CRITICAL", msg,
                              float(self.portfolio.daily_losses + amount), 
                              float(self.max_daily_loss))
            return False, msg
        
        # Check 4: Minimum confidence
        if confidence < self.min_confidence:
            msg = f"Confidence {confidence:.2%} below minimum {self.min_confidence:.2%}"
            return False, msg
        
        # Check 5: Slippage limit
        if slippage_estimate > self.max_slippage_pct:
            msg = f"Estimated slippage {slippage_estimate:.2%} exceeds max {self.max_slippage_pct:.2%}"
            self._record_breach(BreacherType.SLIPPAGE_EXCESSIVE, "WARNING", msg,
                              slippage_estimate, self.max_slippage_pct)
            return False, msg
        
        # Check 6: Circuit breaker
        if self.circuit_breaker_active:
            msg = "Circuit breaker is active - trading halted"
            return False, msg
        
        return True, None
    
    def record_trade_result(self, trade: Trade):
        """Record trade result and update risk state"""
        
        self.portfolio.add_trade(trade)
        
        # Update consecutive failures counter
        if trade.is_profitable:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1
        
        # Check circuit breaker conditions
        self._check_circuit_breaker()
        
        # Log trade
        logger.info(
            f"Trade {trade.trade_id}: "
            f"${trade.profit:+.2f} ({trade.status}) | "
            f"Daily: ${self.portfolio.daily_pnl:+.2f} | "
            f"Win rate: {self.portfolio.daily_win_rate:.1f}%"
        )
    
    def _check_circuit_breaker(self):
        """Check if circuit breaker should activate"""
        
        # Check 1: Consecutive failures
        if self.consecutive_failures >= self.circuit_breaker_failures:
            self._activate_circuit_breaker(
                BreacherType.CONSECUTIVE_FAILURES,
                f"Too many consecutive failures ({self.consecutive_failures})"
            )
        
        # Check 2: Daily loss exceeded
        if self.portfolio.daily_losses > self.max_daily_loss:
            self._activate_circuit_breaker(
                BreacherType.DAILY_LOSS,
                f"Daily loss exceeded: ${self.portfolio.daily_losses} > ${self.max_daily_loss}"
            )
        
        # Check 3: Model accuracy dropped
        if self.model_accuracy < 0.65:
            self._activate_circuit_breaker(
                BreacherType.MODEL_ACCURACY,
                f"Model accuracy critical: {self.model_accuracy:.2%}"
            )
    
    def _activate_circuit_breaker(self, breach_type: BreacherType, message: str):
        """Activate circuit breaker"""
        if not self.circuit_breaker_active:
            self.circuit_breaker_active = True
            logger.critical(f"🛑 CIRCUIT BREAKER ACTIVATED: {message}")
            self._record_breach(breach_type, "CRITICAL", message, 0, 0, "HALT_TRADING")
    
    def deactivate_circuit_breaker(self):
        """Manually deactivate circuit breaker"""
        if self.circuit_breaker_active:
            self.circuit_breaker_active = False
            logger.warning("⚠️  Circuit breaker manually deactivated")
    
    def _record_breach(self, breach_type: BreacherType, severity: str, message: str,
                      actual_value: float, limit_value: float, action: str = "NONE"):
        """Record risk breach event"""
        event = RiskBreachEvent(
            breach_type=breach_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            limit_value=limit_value,
            actual_value=actual_value,
            action_taken=action,
        )
        
        self.breach_events.append(event)
        
        log_func = {
            'INFO': logger.info,
            'WARNING': logger.warning,
            'CRITICAL': logger.critical,
        }.get(severity, logger.info)
        
        log_func(f"[{breach_type.value}] {message}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary for monitoring"""
        return {
            'total_capital': float(self.portfolio.total_capital),
            'idle_capital': float(self.portfolio.idle_capital),
            'deployed_capital': float(self.portfolio.total_capital - self.portfolio.idle_capital),
            'utilization_pct': self.portfolio.utilization_pct,
            'daily_pnl': float(self.portfolio.daily_pnl),
            'daily_profit': float(self.portfolio.daily_profits),
            'daily_loss': float(self.portfolio.daily_losses),
            'daily_trades': len(self.portfolio.daily_trades),
            'daily_win_rate': self.portfolio.daily_win_rate,
            'daily_sharpe_ratio': self.portfolio.daily_sharpe_ratio,
            'open_positions': len(self.portfolio.positions),
            'consecutive_failures': self.consecutive_failures,
            'circuit_breaker_active': self.circuit_breaker_active,
            'model_accuracy': self.model_accuracy,
            'breach_events': len(self.breach_events),
        }
    
    def get_breach_events(self, limit: int = 100) -> List[Dict]:
        """Get recent breach events"""
        return [
            {
                'timestamp': e.timestamp,
                'breach_type': e.breach_type.value,
                'severity': e.severity,
                'message': e.message,
                'actual': e.actual_value,
                'limit': e.limit_value,
                'action': e.action_taken,
            }
            for e in self.breach_events[-limit:]
        ]
