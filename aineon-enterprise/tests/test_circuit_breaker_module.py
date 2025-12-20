"""
Unit tests for Circuit Breaker
Tests: loss limits, circuit trips, trading restrictions
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from core.risk.circuit_breaker import (
    CircuitBreaker,
    CircuitStatus,
    RiskManager,
)

class TestCircuitBreaker:
    
    @pytest.fixture
    def circuit_breaker(self):
        return CircuitBreaker(
            daily_loss_limit_eth=100.0,
            hourly_loss_limit_eth=20.0,
            cooldown_minutes=1,  # Short for testing
            consecutive_loss_limit=3,
        )
    
    def test_initial_state(self, circuit_breaker):
        """Test initial circuit state"""
        assert circuit_breaker.status == CircuitStatus.OPEN
        assert circuit_breaker.daily_loss == Decimal(0)
        assert circuit_breaker.can_trade() is True
    
    def test_can_trade_when_open(self, circuit_breaker):
        """Test can_trade returns True when circuit is OPEN"""
        assert circuit_breaker.can_trade() is True
    
    def test_record_loss(self, circuit_breaker):
        """Test recording a loss"""
        loss = Decimal("5.0")
        circuit_breaker.record_loss(loss)
        
        assert circuit_breaker.daily_loss == loss
        assert circuit_breaker.consecutive_losses == 1
    
    def test_daily_loss_limit_exceeded(self, circuit_breaker):
        """Test hard stop when daily loss limit exceeded"""
        # Record losses approaching limit
        for i in range(10):
            circuit_breaker.record_loss(Decimal("11.0"))
        
        # Should be locked after exceeding 100 ETH
        assert circuit_breaker.status == CircuitStatus.LOCKED
        assert circuit_breaker.can_trade() is False
    
    def test_hourly_loss_limit_exceeded(self, circuit_breaker):
        """Test circuit trip when hourly loss limit exceeded"""
        # Record losses exceeding hourly limit (20 ETH)
        circuit_breaker.record_loss(Decimal("15.0"))
        circuit_breaker.record_loss(Decimal("6.0"))
        
        # Should be tripped, not locked
        assert circuit_breaker.status == CircuitStatus.TRIPPED
        assert circuit_breaker.can_trade() is False
    
    def test_consecutive_loss_limit(self, circuit_breaker):
        """Test circuit trip on consecutive losses"""
        # Record 3 consecutive losses (limit)
        circuit_breaker.record_loss(Decimal("1.0"))
        circuit_breaker.record_loss(Decimal("1.0"))
        circuit_breaker.record_loss(Decimal("1.0"))
        
        # Should be tripped
        assert circuit_breaker.status == CircuitStatus.TRIPPED
    
    def test_profit_resets_consecutive_losses(self, circuit_breaker):
        """Test profit resets consecutive loss counter"""
        circuit_breaker.record_loss(Decimal("1.0"))
        circuit_breaker.record_loss(Decimal("1.0"))
        assert circuit_breaker.consecutive_losses == 2
        
        # Record a profit
        circuit_breaker.record_profit(Decimal("5.0"))
        assert circuit_breaker.consecutive_losses == 0
    
    def test_cooldown_period(self, circuit_breaker):
        """Test circuit cooldown period"""
        # Trip the circuit
        circuit_breaker.record_loss(Decimal("15.0"))
        circuit_breaker.record_loss(Decimal("6.0"))
        
        assert circuit_breaker.status == CircuitStatus.TRIPPED
        assert circuit_breaker.can_trade() is False
        
        # Wait for cooldown to expire (1 minute in fixture)
        # In real test, would use time machine or mock datetime
        # For now, manually set trip time to past
        circuit_breaker.trip_time = datetime.now() - timedelta(minutes=2)
        
        assert circuit_breaker.can_trade() is True
        assert circuit_breaker.status == CircuitStatus.OPEN
    
    def test_get_status(self, circuit_breaker):
        """Test status reporting"""
        circuit_breaker.record_loss(Decimal("5.0"))
        
        status = circuit_breaker.get_status()
        
        assert status["status"] == CircuitStatus.OPEN.value
        assert float(status["daily_loss"]) == 5.0
        assert float(status["daily_limit"]) == 100.0
        assert status["consecutive_losses"] == 1
        assert status["can_trade"] is True
    
    def test_get_daily_summary(self, circuit_breaker):
        """Test daily summary reporting"""
        circuit_breaker.record_loss(Decimal("5.0"))
        circuit_breaker.record_loss(Decimal("3.0"))
        
        summary = circuit_breaker.get_daily_summary()
        
        assert summary["total_loss"] == 8.0
        assert summary["loss_count"] == 2
        assert summary["status"] == CircuitStatus.OPEN.value
        assert 7.0 < summary["percentage_of_limit"] < 9.0  # ~8%


class TestRiskManager:
    
    @pytest.fixture
    def risk_manager(self):
        cb = CircuitBreaker(daily_loss_limit_eth=100.0)
        return RiskManager(
            circuit_breaker=cb,
            max_position_size_eth=1000.0,
            max_concentration_pct=0.1,
            min_profit_threshold_eth=0.5,
        )
    
    def test_validate_trade_valid(self, risk_manager):
        """Test validation of valid trade"""
        is_valid, error = risk_manager.validate_trade(
            amount=Decimal("100.0"),
            expected_profit=Decimal("1.0"),
            pool_liquidity=Decimal("10000.0"),
            current_position_size=Decimal("0.0"),
        )
        
        assert is_valid is True
        assert error is None
    
    def test_validate_trade_exceeds_max_position(self, risk_manager):
        """Test validation rejects oversized position"""
        is_valid, error = risk_manager.validate_trade(
            amount=Decimal("2000.0"),  # Exceeds max of 1000
            expected_profit=Decimal("1.0"),
            pool_liquidity=Decimal("10000.0"),
            current_position_size=Decimal("0.0"),
        )
        
        assert is_valid is False
        assert "exceeds max" in error.lower()
    
    def test_validate_trade_concentration_limit(self, risk_manager):
        """Test validation respects pool concentration limit"""
        is_valid, error = risk_manager.validate_trade(
            amount=Decimal("2000.0"),  # 20% of pool
            expected_profit=Decimal("1.0"),
            pool_liquidity=Decimal("10000.0"),  # Max 10% = 1000
            current_position_size=Decimal("0.0"),
        )
        
        assert is_valid is False
        assert "concentration" in error.lower()
    
    def test_validate_trade_profit_threshold(self, risk_manager):
        """Test validation rejects low-profit trades"""
        is_valid, error = risk_manager.validate_trade(
            amount=Decimal("100.0"),
            expected_profit=Decimal("0.1"),  # Below 0.5 threshold
            pool_liquidity=Decimal("10000.0"),
            current_position_size=Decimal("0.0"),
        )
        
        assert is_valid is False
        assert "below threshold" in error.lower()
    
    def test_open_and_close_position(self, risk_manager):
        """Test opening and closing positions"""
        pos_id = "trade_001"
        
        risk_manager.open_position(
            position_id=pos_id,
            amount=Decimal("100.0"),
            entry_price=Decimal("2000.0"),
        )
        
        assert pos_id in risk_manager.open_positions
        assert risk_manager.open_positions[pos_id]["status"] == "OPEN"
        
        # Close with profit
        pnl = risk_manager.close_position(
            position_id=pos_id,
            exit_price=Decimal("2100.0"),
        )
        
        assert pnl == Decimal("10000.0")  # (2100-2000) * 100
        assert risk_manager.open_positions[pos_id]["status"] == "CLOSED"
    
    def test_position_stop_loss(self, risk_manager):
        """Test stop loss on position"""
        pos_id = "trade_002"
        
        risk_manager.open_position(
            position_id=pos_id,
            amount=Decimal("100.0"),
            entry_price=Decimal("2000.0"),
            stop_loss=Decimal("1950.0"),  # 2.5% below entry
        )
        
        position = risk_manager.open_positions[pos_id]
        assert position["stop_loss"] == Decimal("1950.0")
    
    def test_get_position_summary(self, risk_manager):
        """Test position summary reporting"""
        risk_manager.open_position(
            position_id="trade_001",
            amount=Decimal("300.0"),
            entry_price=Decimal("2000.0"),
        )
        risk_manager.open_position(
            position_id="trade_002",
            amount=Decimal("200.0"),
            entry_price=Decimal("2000.0"),
        )
        
        summary = risk_manager.get_position_summary()
        
        assert summary["open_count"] == 2
        assert summary["total_exposure_eth"] == 500.0
        assert summary["max_exposure_eth"] == 1000.0
        assert summary["utilization_pct"] == 50.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
