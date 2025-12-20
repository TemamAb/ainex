import asyncio
import time
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class RiskManagerV2:
    def __init__(self):
        # TIGHTENED LIMITS (Phase 1 improvement)
        self.position_limits = {
            "max_per_trade": 1000.0,           # 1000 ETH max per trade
            "max_concentration": 0.10,         # 10% per pool (was 20%)
            "daily_loss_limit": 100.0,         # 100 ETH hard stop
            "circuit_breaker_latency_seconds": 1.0,  # 1 second (was 5s)
            "max_drawdown_pct": 0.025,         # 2.5% (will be 1.5-2% in Phase 5)
            "slippage_tolerance_bps": 10,      # 0.1% (0.001% in Phase 5)
        }
        
        self.daily_loss = 0
        self.circuit_breaker_active = False
        self.daily_loss_check_interval = 0.1  # 100ms (vs manual 5s)
        self.daily_trades = []
    
    async def validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate opportunity against risk limits"""
        # Check 1: Position concentration
        pool_liquidity = opportunity.get("pool_liquidity_usd", 1_000_000)
        position_usd = opportunity["amount_eth"] * 2500  # USD value (example rate)
        position_pct = position_usd / pool_liquidity
        
        if position_pct > self.position_limits["max_concentration"]:
            logger.warning(f"Opportunity rejected: concentration {position_pct:.2%} > limit {self.position_limits['max_concentration']:.2%}")
            return False  # Reject - too concentrated
        
        # Check 2: Daily loss
        if self.daily_loss >= self.position_limits["daily_loss_limit"]:
            self.circuit_breaker_active = True
            logger.warning(f"Circuit breaker active: daily loss {self.daily_loss} ETH >= limit {self.position_limits['daily_loss_limit']} ETH")
            return False  # Halt all trading
        
        # Check 3: Slippage tolerance
        estimated_slippage = opportunity.get("estimated_slippage_bps", 0)
        if estimated_slippage > self.position_limits["slippage_tolerance_bps"]:
            logger.warning(f"Opportunity rejected: slippage {estimated_slippage} bps > limit {self.position_limits['slippage_tolerance_bps']} bps")
            return False  # Reject - too much slippage
        
        # Check 4: Max per trade
        if opportunity["amount_eth"] > self.position_limits["max_per_trade"]:
            logger.warning(f"Opportunity rejected: amount {opportunity['amount_eth']} ETH > max {self.position_limits['max_per_trade']} ETH")
            return False
        
        return True
    
    async def start_circuit_breaker(self):
        """Sub-second circuit breaker monitoring"""
        while True:
            try:
                # Check daily loss every 100ms (not manually every 5s)
                current_loss = await self.get_daily_loss()
                
                if current_loss >= self.position_limits["daily_loss_limit"]:
                    self.circuit_breaker_active = True
                    await self.notify_alert(
                        "CIRCUIT_BREAKER_TRIGGERED",
                        f"Daily loss: {current_loss} ETH >= {self.position_limits['daily_loss_limit']} ETH"
                    )
                else:
                    self.circuit_breaker_active = False
                
                await asyncio.sleep(self.daily_loss_check_interval)  # 100ms check
                
            except Exception as e:
                logger.error(f"Circuit breaker error: {e}")
                await asyncio.sleep(0.5)
    
    async def get_daily_loss(self) -> float:
        """Calculate current daily P&L loss"""
        # Sum of all losing trades today
        daily_trades = await self.get_trades_since_midnight()
        losses = sum(trade["pnl"] for trade in daily_trades if trade["pnl"] < 0)
        self.daily_loss = abs(losses)
        return self.daily_loss
    
    async def get_trades_since_midnight(self) -> List[Dict]:
        """Get all trades since midnight UTC"""
        # Filter trades from today
        import datetime
        midnight = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_trades = [t for t in self.daily_trades if datetime.datetime.fromisoformat(t["timestamp"]) >= midnight]
        return today_trades
    
    async def record_trade(self, trade_result: Dict):
        """Record a trade result"""
        trade_result["timestamp"] = time.time()
        self.daily_trades.append(trade_result)
    
    async def notify_alert(self, alert_type: str, message: str):
        """Send alert (Slack, PagerDuty, etc)"""
        logger.critical(f"[{alert_type}] {message}")
        # TODO: Integrate with Slack/PagerDuty
    
    def get_risk_report(self) -> Dict:
        """Get current risk status"""
        return {
            "daily_loss": self.daily_loss,
            "circuit_breaker_active": self.circuit_breaker_active,
            "daily_trades_count": len(self.daily_trades),
            "position_limits": self.position_limits,
        }
