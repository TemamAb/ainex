"""
Circuit Breaker - Risk Management & Loss Limits
Hard stop at 100 ETH daily loss
Status: Production-Ready
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitStatus(Enum):
    OPEN = "OPEN"  # Trading allowed
    TRIPPED = "TRIPPED"  # Stop trading, cooling down
    LOCKED = "LOCKED"  # Hard stop, manual review needed

@dataclass
class DailyLossTracker:
    date: str
    total_loss: Decimal
    loss_count: int
    last_loss_time: datetime
    status: CircuitStatus

class CircuitBreaker:
    """
    Risk management circuit breaker
    Prevents catastrophic losses
    """
    
    def __init__(
        self,
        daily_loss_limit_eth: float = 100.0,
        hourly_loss_limit_eth: float = 20.0,
        cooldown_minutes: int = 15,
        consecutive_loss_limit: int = 5,
    ):
        self.daily_loss_limit = Decimal(str(daily_loss_limit_eth))
        self.hourly_loss_limit = Decimal(str(hourly_loss_limit_eth))
        self.cooldown_period = timedelta(minutes=cooldown_minutes)
        self.consecutive_loss_limit = consecutive_loss_limit
        
        self.status = CircuitStatus.OPEN
        self.daily_loss = Decimal(0)
        self.hourly_loss = Decimal(0)
        self.consecutive_losses = 0
        self.trip_time: Optional[datetime] = None
        self.daily_loss_history: Dict[str, DailyLossTracker] = {}
        
    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        
        # Check circuit status
        if self.status == CircuitStatus.LOCKED:
            logger.error("🛑 Circuit locked - trading disabled")
            return False
        
        if self.status == CircuitStatus.TRIPPED:
            # Check if cooldown expired
            if self.trip_time and datetime.now() < self.trip_time + self.cooldown_period:
                time_remaining = (self.trip_time + self.cooldown_period - datetime.now()).total_seconds()
                logger.warning(
                    f"⏳ Circuit tripped | Cooldown: {time_remaining:.0f}s remaining"
                )
                return False
            else:
                # Cooldown expired, reset
                self.status = CircuitStatus.OPEN
                self.consecutive_losses = 0
                logger.info("✅ Circuit cooldown expired, resuming trading")
        
        return True
    
    def record_loss(self, loss_amount: Decimal) -> None:
        """Record a trading loss"""
        
        if loss_amount <= 0:
            return  # Not a loss
        
        self.daily_loss += loss_amount
        self.hourly_loss += loss_amount
        self.consecutive_losses += 1
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update daily tracker
        if today not in self.daily_loss_history:
            self.daily_loss_history[today] = DailyLossTracker(
                date=today,
                total_loss=Decimal(0),
                loss_count=0,
                last_loss_time=datetime.now(),
                status=CircuitStatus.OPEN,
            )
        
        tracker = self.daily_loss_history[today]
        tracker.total_loss += loss_amount
        tracker.loss_count += 1
        tracker.last_loss_time = datetime.now()
        
        logger.warning(
            f"📉 Loss recorded | "
            f"Amount: {loss_amount} ETH | "
            f"Daily total: {self.daily_loss} / {self.daily_loss_limit} | "
            f"Consecutive: {self.consecutive_losses}"
        )
        
        # Check limits
        self._check_limits()
    
    def record_profit(self, profit_amount: Decimal) -> None:
        """Record a trading profit"""
        
        if profit_amount <= 0:
            return
        
        # Reset consecutive loss counter on profit
        self.consecutive_losses = 0
        
        logger.info(f"📈 Profit recorded | Amount: {profit_amount} ETH")
    
    def _check_limits(self) -> None:
        """Check and enforce loss limits"""
        
        # Check consecutive loss limit
        if self.consecutive_losses >= self.consecutive_loss_limit:
            logger.error(
                f"❌ Consecutive loss limit reached | "
                f"Limit: {self.consecutive_loss_limit}"
            )
            self._trip_circuit()
            return
        
        # Check hourly loss limit
        if self.hourly_loss > self.hourly_loss_limit:
            logger.error(
                f"❌ Hourly loss limit exceeded | "
                f"Loss: {self.hourly_loss} / {self.hourly_loss_limit}"
            )
            self._trip_circuit()
            return
        
        # Check daily loss limit (hard stop)
        if self.daily_loss >= self.daily_loss_limit:
            logger.error(
                f"🛑 DAILY LOSS LIMIT HIT | "
                f"Loss: {self.daily_loss} >= {self.daily_loss_limit} | "
                f"TRADING STOPPED"
            )
            self._lock_circuit()
            return
    
    def _trip_circuit(self) -> None:
        """Trip circuit (cooldown period)"""
        self.status = CircuitStatus.TRIPPED
        self.trip_time = datetime.now()
        logger.error(f"⚠️ Circuit tripped | Cooldown: {self.cooldown_period.total_seconds():.0f}s")
    
    def _lock_circuit(self) -> None:
        """Lock circuit (hard stop)"""
        self.status = CircuitStatus.LOCKED
        self.trip_time = datetime.now()
        logger.error("🛑 CIRCUIT LOCKED - MANUAL INTERVENTION REQUIRED")
    
    def reset_hourly(self) -> None:
        """Reset hourly counters (call every hour)"""
        self.hourly_loss = Decimal(0)
        logger.debug("🔄 Hourly loss counter reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit status"""
        return {
            "status": self.status.value,
            "daily_loss": float(self.daily_loss),
            "daily_limit": float(self.daily_loss_limit),
            "hourly_loss": float(self.hourly_loss),
            "hourly_limit": float(self.hourly_loss_limit),
            "consecutive_losses": self.consecutive_losses,
            "consecutive_limit": self.consecutive_loss_limit,
            "can_trade": self.can_trade(),
            "trip_time": self.trip_time.isoformat() if self.trip_time else None,
        }
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily loss summary"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in self.daily_loss_history:
            return {
                "date": today,
                "total_loss": 0,
                "loss_count": 0,
                "status": CircuitStatus.OPEN.value,
            }
        
        tracker = self.daily_loss_history[today]
        return {
            "date": tracker.date,
            "total_loss": float(tracker.total_loss),
            "loss_count": tracker.loss_count,
            "last_loss_time": tracker.last_loss_time.isoformat(),
            "status": tracker.status.value,
            "percentage_of_limit": float((tracker.total_loss / self.daily_loss_limit) * 100),
        }


class RiskManager:
    """
    Comprehensive risk management
    Includes: position sizing, concentration limits, stop losses
    """
    
    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        max_position_size_eth: float = 1000.0,
        max_concentration_pct: float = 0.1,  # 10% of pool
        min_profit_threshold_eth: float = 0.5,
    ):
        self.circuit_breaker = circuit_breaker
        self.max_position_size = Decimal(str(max_position_size_eth))
        self.max_concentration = max_concentration_pct
        self.min_profit_threshold = Decimal(str(min_profit_threshold_eth))
        
        self.open_positions: Dict[str, Dict[str, Any]] = {}
    
    def validate_trade(
        self,
        amount: Decimal,
        expected_profit: Decimal,
        pool_liquidity: Decimal,
        current_position_size: Decimal,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate trade before execution
        Returns: (is_valid, error_message)
        """
        
        # Check circuit breaker
        if not self.circuit_breaker.can_trade():
            return False, "Circuit breaker active"
        
        # Check position size limit
        if amount > self.max_position_size:
            return False, f"Position exceeds max ({self.max_position_size} ETH)"
        
        # Check concentration limit
        concentration = amount / pool_liquidity if pool_liquidity > 0 else Decimal(1)
        if concentration > Decimal(str(self.max_concentration)):
            return False, f"Pool concentration limit exceeded ({concentration:.2%})"
        
        # Check profit threshold
        if expected_profit < self.min_profit_threshold:
            return False, f"Profit below threshold ({self.min_profit_threshold} ETH)"
        
        # Check cumulative position
        total_position = current_position_size + amount
        if total_position > self.max_position_size:
            return False, f"Cumulative position exceeds limit"
        
        return True, None
    
    def open_position(
        self,
        position_id: str,
        amount: Decimal,
        entry_price: Decimal,
        stop_loss: Optional[Decimal] = None,
    ) -> None:
        """Open a new position"""
        
        self.open_positions[position_id] = {
            "amount": amount,
            "entry_price": entry_price,
            "stop_loss": stop_loss or (entry_price * Decimal("0.95")),  # 5% default SL
            "entry_time": datetime.now(),
            "status": "OPEN",
        }
        
        logger.info(f"📍 Position opened | ID: {position_id} | Amount: {amount} ETH")
    
    def close_position(
        self,
        position_id: str,
        exit_price: Decimal,
    ) -> Optional[Decimal]:
        """Close a position and calculate P&L"""
        
        if position_id not in self.open_positions:
            logger.warning(f"⚠️ Position not found: {position_id}")
            return None
        
        position = self.open_positions[position_id]
        pnl = (exit_price - position["entry_price"]) * position["amount"]
        
        position["status"] = "CLOSED"
        position["exit_price"] = exit_price
        position["pnl"] = pnl
        
        if pnl >= 0:
            logger.info(f"✅ Position closed | ID: {position_id} | P&L: +{pnl} ETH")
            self.circuit_breaker.record_profit(pnl)
        else:
            logger.warning(f"❌ Position closed | ID: {position_id} | P&L: {pnl} ETH")
            self.circuit_breaker.record_loss(abs(pnl))
        
        return pnl
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        
        open_positions = [p for p in self.open_positions.values() if p["status"] == "OPEN"]
        total_exposure = sum(p["amount"] for p in open_positions)
        
        return {
            "open_count": len(open_positions),
            "total_exposure_eth": float(total_exposure),
            "max_exposure_eth": float(self.max_position_size),
            "utilization_pct": float((total_exposure / self.max_position_size) * 100),
        }
