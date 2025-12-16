"""
AINEON Enterprise: Position Tracker Module
Phase 3B: Risk Management - Position State Management

Real-time position tracking with on-chain reconciliation.
Monitors open positions, calculates P&L, and verifies blockchain state.

Author: AINEON Chief Architect
Version: 1.0
Date: December 14, 2025
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, validator


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class PositionState(str, Enum):
    """Position lifecycle states."""
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class DEXType(str, Enum):
    """Supported DEX platforms."""
    UNISWAP_V3 = "uniswap_v3"
    UNISWAP_V2 = "uniswap_v2"
    CURVE = "curve"
    BALANCER = "balancer"
    DODO = "dodo"


# ============================================================================
# DATA MODELS
# ============================================================================

class PositionUpdate(BaseModel):
    """Single position state update."""
    timestamp: datetime
    current_price: Decimal = Field(..., decimal_places=8)
    quantity: Decimal = Field(..., decimal_places=18)
    gas_used: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    notes: Optional[str] = None


class Position(BaseModel):
    """Open position tracking."""
    position_id: str = Field(default_factory=lambda: str(uuid4()))
    status: PositionState = PositionState.OPEN
    
    # Asset info
    token_a: str  # Contract address
    token_b: str  # Contract address
    token_a_symbol: str
    token_b_symbol: str
    
    # Entry info
    entry_timestamp: datetime
    entry_price: Decimal = Field(..., decimal_places=8)
    entry_quantity: Decimal = Field(..., decimal_places=18)
    entry_dex: DEXType
    entry_gas_cost: Decimal = Field(default=Decimal("0"), decimal_places=8)
    entry_slippage: Decimal = Field(default=Decimal("0"), decimal_places=6)
    
    # Exit info (if closed)
    exit_timestamp: Optional[datetime] = None
    exit_price: Optional[Decimal] = None
    exit_quantity: Optional[Decimal] = None
    exit_dex: Optional[DEXType] = None
    exit_gas_cost: Optional[Decimal] = Decimal("0")
    exit_slippage: Optional[Decimal] = Decimal("0")
    
    # Current state
    current_price: Decimal = Field(..., decimal_places=8)
    current_quantity: Decimal = Field(..., decimal_places=18)
    last_update: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracking
    updates: List[PositionUpdate] = Field(default_factory=list)
    blockchain_verified: bool = False
    verification_timestamp: Optional[datetime] = None
    
    # Metadata
    strategy: str  # e.g., "arbitrage", "liquidity_farming"
    risk_level: str = Field(default="medium")  # low, medium, high
    notes: str = ""


class PortfolioSnapshot(BaseModel):
    """Portfolio state at a point in time."""
    timestamp: datetime
    total_value_usd: Decimal = Field(..., decimal_places=2)
    total_cost_basis: Decimal = Field(..., decimal_places=2)
    realized_pnl: Decimal = Field(..., decimal_places=2)
    unrealized_pnl: Decimal = Field(..., decimal_places=2)
    total_pnl: Decimal = Field(..., decimal_places=2)
    position_count: int
    open_positions: int
    closed_positions: int
    gas_spent_total: Decimal = Field(..., decimal_places=2)
    blockchain_verified: bool
    reconciliation_status: str  # "verified", "warning", "error"


# ============================================================================
# POSITION TRACKER
# ============================================================================

class PositionTracker:
    """
    Real-time position tracking and lifecycle management.
    
    Responsibilities:
    - Track open/closed positions
    - Calculate P&L (realized and unrealized)
    - Verify on-chain state
    - Reconcile with blockchain
    - Monitor risk metrics
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize position tracker."""
        self.logger = logger or logging.getLogger(__name__)
        
        # Position storage
        self._positions: Dict[str, Position] = {}
        self._closed_positions: List[Position] = []
        self._position_history: List[PositionUpdate] = []
        
        # Daily tracking
        self._daily_snapshots: Dict[str, PortfolioSnapshot] = {}
        self._current_day: Optional[str] = None
        
        # Reconciliation state
        self._last_blockchain_sync: Optional[datetime] = None
        self._reconciliation_errors: List[str] = []
        
        self.logger.info("✅ PositionTracker initialized")
    
    # ========================================================================
    # POSITION OPENING
    # ========================================================================
    
    def open_position(
        self,
        token_a: str,
        token_b: str,
        token_a_symbol: str,
        token_b_symbol: str,
        quantity: Decimal,
        entry_price: Decimal,
        dex: DEXType,
        strategy: str,
        gas_cost: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
        risk_level: str = "medium",
        notes: str = "",
    ) -> str:
        """
        Open a new position.
        
        Args:
            token_a: Token A contract address
            token_b: Token B contract address
            token_a_symbol: Token A symbol (e.g., "ETH")
            token_b_symbol: Token B symbol (e.g., "USDC")
            quantity: Amount of token_a
            entry_price: Entry price (token_b per token_a)
            dex: DEX where trade occurred
            strategy: Strategy name
            gas_cost: Gas cost in USD
            slippage: Slippage percentage
            risk_level: Risk classification
            notes: Additional notes
            
        Returns:
            Position ID
        """
        position = Position(
            token_a=token_a,
            token_b=token_b,
            token_a_symbol=token_a_symbol,
            token_b_symbol=token_b_symbol,
            entry_timestamp=datetime.utcnow(),
            entry_price=entry_price,
            entry_quantity=quantity,
            entry_dex=dex,
            entry_gas_cost=gas_cost,
            entry_slippage=slippage,
            current_price=entry_price,
            current_quantity=quantity,
            strategy=strategy,
            risk_level=risk_level,
            notes=notes,
        )
        
        self._positions[position.position_id] = position
        
        self.logger.info(
            f"📍 Position opened: {position.position_id} "
            f"({token_a_symbol}/{token_b_symbol}) qty={quantity} "
            f"price={entry_price} on {dex.value}"
        )
        
        return position.position_id
    
    # ========================================================================
    # POSITION UPDATES
    # ========================================================================
    
    def update_position_price(
        self,
        position_id: str,
        current_price: Decimal,
    ) -> bool:
        """
        Update position current price.
        
        Args:
            position_id: Position identifier
            current_price: New current price
            
        Returns:
            True if updated, False if position not found
        """
        if position_id not in self._positions:
            self.logger.warning(f"❌ Position not found: {position_id}")
            return False
        
        position = self._positions[position_id]
        old_price = position.current_price
        position.current_price = current_price
        position.last_update = datetime.utcnow()
        
        # Record update
        update = PositionUpdate(
            timestamp=datetime.utcnow(),
            current_price=current_price,
            quantity=position.current_quantity,
        )
        position.updates.append(update)
        
        self.logger.debug(
            f"💰 Position {position_id} price updated: "
            f"{old_price} → {current_price}"
        )
        return True
    
    def update_position_quantity(
        self,
        position_id: str,
        new_quantity: Decimal,
        current_price: Decimal,
    ) -> bool:
        """
        Update position quantity (partial exit/entry).
        
        Args:
            position_id: Position identifier
            new_quantity: New quantity
            current_price: Current price
            
        Returns:
            True if updated, False if position not found
        """
        if position_id not in self._positions:
            self.logger.warning(f"❌ Position not found: {position_id}")
            return False
        
        position = self._positions[position_id]
        old_qty = position.current_quantity
        position.current_quantity = new_quantity
        position.current_price = current_price
        position.last_update = datetime.utcnow()
        
        # Record update
        update = PositionUpdate(
            timestamp=datetime.utcnow(),
            current_price=current_price,
            quantity=new_quantity,
        )
        position.updates.append(update)
        
        self.logger.info(
            f"📊 Position {position_id} quantity updated: "
            f"{old_qty} → {new_quantity}"
        )
        return True
    
    # ========================================================================
    # POSITION CLOSING
    # ========================================================================
    
    def close_position(
        self,
        position_id: str,
        exit_price: Decimal,
        exit_quantity: Optional[Decimal] = None,
        dex: Optional[DEXType] = None,
        gas_cost: Decimal = Decimal("0"),
        slippage: Decimal = Decimal("0"),
    ) -> bool:
        """
        Close an open position.
        
        Args:
            position_id: Position identifier
            exit_price: Exit price
            exit_quantity: Quantity exited (None = full exit)
            dex: DEX used for exit
            gas_cost: Gas cost in USD
            slippage: Slippage percentage
            
        Returns:
            True if closed, False if position not found
        """
        if position_id not in self._positions:
            self.logger.warning(f"❌ Position not found: {position_id}")
            return False
        
        position = self._positions[position_id]
        
        # Default to full exit
        exit_qty = exit_quantity or position.current_quantity
        
        position.exit_timestamp = datetime.utcnow()
        position.exit_price = exit_price
        position.exit_quantity = exit_qty
        position.exit_dex = dex
        position.exit_gas_cost = gas_cost
        position.exit_slippage = slippage
        position.current_quantity = position.current_quantity - exit_qty
        
        # Mark as closed if fully exited
        if position.current_quantity == Decimal("0"):
            position.status = PositionState.CLOSED
            self._closed_positions.append(position)
            del self._positions[position_id]
        else:
            position.status = PositionState.CLOSING
        
        self.logger.info(
            f"✅ Position {position_id} closed: "
            f"qty={exit_qty} price={exit_price} pnl={self.calculate_position_pnl(position)}"
        )
        
        return True
    
    # ========================================================================
    # P&L CALCULATIONS
    # ========================================================================
    
    def calculate_position_pnl(self, position: Position) -> Tuple[Decimal, Decimal]:
        """
        Calculate position P&L.
        
        Returns:
            (realized_pnl, unrealized_pnl) in USD
        """
        realized = Decimal("0")
        unrealized = Decimal("0")
        
        # Realized from closed positions
        if position.status in (PositionState.CLOSED, PositionState.LIQUIDATED):
            if position.exit_price and position.exit_quantity:
                exit_value = position.exit_price * position.exit_quantity
                entry_cost = position.entry_price * position.entry_quantity
                realized = exit_value - entry_cost
                realized -= position.entry_gas_cost + position.exit_gas_cost
        
        # Unrealized from open positions
        if position.current_quantity > Decimal("0"):
            current_value = position.current_price * position.current_quantity
            entry_cost = position.entry_price * position.entry_quantity
            unrealized = current_value - entry_cost
            unrealized -= position.entry_gas_cost
        
        return (realized, unrealized)
    
    def get_open_position_pnl(self, position_id: str) -> Optional[Decimal]:
        """Get unrealized P&L for an open position."""
        if position_id not in self._positions:
            return None
        
        position = self._positions[position_id]
        _, unrealized = self.calculate_position_pnl(position)
        return unrealized
    
    def get_portfolio_pnl(self) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Get total portfolio P&L.
        
        Returns:
            (realized_pnl, unrealized_pnl, total_pnl)
        """
        realized_total = Decimal("0")
        unrealized_total = Decimal("0")
        
        # Open positions
        for position in self._positions.values():
            realized, unrealized = self.calculate_position_pnl(position)
            realized_total += realized
            unrealized_total += unrealized
        
        # Closed positions
        for position in self._closed_positions:
            realized, _ = self.calculate_position_pnl(position)
            realized_total += realized
        
        return (realized_total, unrealized_total, realized_total + unrealized_total)
    
    # ========================================================================
    # QUERYING
    # ========================================================================
    
    def get_open_positions(self) -> Dict[str, Position]:
        """Get all open positions."""
        return self._positions.copy()
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get specific position."""
        return self._positions.get(position_id)
    
    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions."""
        return self._closed_positions.copy()
    
    def get_position_by_tokens(
        self,
        token_a: str,
        token_b: str,
    ) -> List[Position]:
        """Get all positions for a token pair."""
        return [
            p for p in self._positions.values()
            if (p.token_a == token_a and p.token_b == token_b)
               or (p.token_a == token_b and p.token_b == token_a)
        ]
    
    def get_positions_by_strategy(self, strategy: str) -> List[Position]:
        """Get all positions for a strategy."""
        return [p for p in self._positions.values() if p.strategy == strategy]
    
    def get_positions_by_risk_level(self, risk_level: str) -> List[Position]:
        """Get all positions at a risk level."""
        return [p for p in self._positions.values() if p.risk_level == risk_level]
    
    # ========================================================================
    # PORTFOLIO SNAPSHOTS
    # ========================================================================
    
    def create_portfolio_snapshot(
        self,
        total_value_usd: Decimal,
        blockchain_verified: bool = False,
    ) -> PortfolioSnapshot:
        """
        Create a portfolio state snapshot.
        
        Args:
            total_value_usd: Total portfolio value in USD
            blockchain_verified: Whether on-chain state is verified
            
        Returns:
            Portfolio snapshot
        """
        realized, unrealized, total_pnl = self.get_portfolio_pnl()
        cost_basis = Decimal("0")
        
        # Calculate cost basis from open positions
        for position in self._positions.values():
            cost_basis += position.entry_price * position.entry_quantity
            cost_basis += position.entry_gas_cost
        
        # Add cost basis from closed positions
        for position in self._closed_positions:
            if position.status == PositionState.CLOSED:
                cost_basis += position.entry_price * position.entry_quantity
                cost_basis += position.entry_gas_cost
        
        total_gas = Decimal("0")
        for position in self._positions.values():
            total_gas += position.entry_gas_cost
        for position in self._closed_positions:
            total_gas += position.entry_gas_cost
            if position.exit_gas_cost:
                total_gas += position.exit_gas_cost
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.utcnow(),
            total_value_usd=total_value_usd,
            total_cost_basis=cost_basis,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            total_pnl=total_pnl,
            position_count=len(self._positions) + len(self._closed_positions),
            open_positions=len(self._positions),
            closed_positions=len(self._closed_positions),
            gas_spent_total=total_gas,
            blockchain_verified=blockchain_verified,
            reconciliation_status="verified" if blockchain_verified else "unverified",
        )
        
        # Store daily snapshot
        day_key = datetime.utcnow().strftime("%Y-%m-%d")
        self._daily_snapshots[day_key] = snapshot
        
        self.logger.info(
            f"📸 Portfolio snapshot: value=${total_value_usd} "
            f"pnl={total_pnl} positions={snapshot.position_count}"
        )
        
        return snapshot
    
    # ========================================================================
    # BLOCKCHAIN RECONCILIATION
    # ========================================================================
    
    async def verify_position_on_chain(
        self,
        position_id: str,
        blockchain_balance: Decimal,
    ) -> bool:
        """
        Verify position state on blockchain.
        
        Args:
            position_id: Position identifier
            blockchain_balance: Balance from blockchain query
            
        Returns:
            True if verified, False if mismatch
        """
        if position_id not in self._positions:
            self.logger.warning(f"❌ Position not found: {position_id}")
            return False
        
        position = self._positions[position_id]
        
        # Check if quantities match
        if position.current_quantity != blockchain_balance:
            error_msg = (
                f"⚠️  Position {position_id} balance mismatch: "
                f"tracked={position.current_quantity} "
                f"blockchain={blockchain_balance}"
            )
            self.logger.error(error_msg)
            self._reconciliation_errors.append(error_msg)
            return False
        
        position.blockchain_verified = True
        position.verification_timestamp = datetime.utcnow()
        
        self.logger.debug(f"✅ Position {position_id} verified on-chain")
        return True
    
    async def reconcile_blockchain_balance(
        self,
        positions_to_verify: Dict[str, Decimal],
    ) -> Tuple[bool, List[str]]:
        """
        Reconcile all positions with blockchain state.
        
        Args:
            positions_to_verify: Dict of {position_id: blockchain_balance}
            
        Returns:
            (all_verified, list_of_errors)
        """
        self.logger.info(f"🔄 Starting blockchain reconciliation for {len(positions_to_verify)} positions...")
        
        all_verified = True
        errors = []
        
        for position_id, blockchain_balance in positions_to_verify.items():
            verified = await self.verify_position_on_chain(position_id, blockchain_balance)
            if not verified:
                all_verified = False
                if position_id in self._positions:
                    error = (
                        f"Position {position_id}: "
                        f"tracked={self._positions[position_id].current_quantity} "
                        f"blockchain={blockchain_balance}"
                    )
                    errors.append(error)
        
        self._last_blockchain_sync = datetime.utcnow()
        
        if all_verified:
            self.logger.info("✅ All positions reconciled successfully")
        else:
            self.logger.warning(f"⚠️  {len(errors)} positions failed reconciliation")
        
        return (all_verified, errors)
    
    def get_reconciliation_status(self) -> Dict:
        """Get blockchain reconciliation status."""
        verified_count = sum(
            1 for p in self._positions.values() if p.blockchain_verified
        )
        total_open = len(self._positions)
        
        return {
            "verified_positions": verified_count,
            "total_open": total_open,
            "last_sync": self._last_blockchain_sync,
            "recent_errors": self._reconciliation_errors[-5:],  # Last 5 errors
            "status": "good" if verified_count == total_open else "warning",
        }
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def get_daily_pnl(self, date: Optional[str] = None) -> Optional[Decimal]:
        """Get daily P&L for a specific date."""
        date_key = date or datetime.utcnow().strftime("%Y-%m-%d")
        snapshot = self._daily_snapshots.get(date_key)
        return snapshot.total_pnl if snapshot else None
    
    def get_daily_snapshot(self, date: Optional[str] = None) -> Optional[PortfolioSnapshot]:
        """Get daily portfolio snapshot."""
        date_key = date or datetime.utcnow().strftime("%Y-%m-%d")
        return self._daily_snapshots.get(date_key)
    
    def export_positions_csv(self) -> str:
        """Export open positions as CSV string."""
        lines = [
            "position_id,token_a,token_b,entry_price,current_price,"
            "quantity,pnl,status,dex,strategy"
        ]
        
        for position in self._positions.values():
            _, unrealized = self.calculate_position_pnl(position)
            lines.append(
                f"{position.position_id},"
                f"{position.token_a_symbol},{position.token_b_symbol},"
                f"{position.entry_price},{position.current_price},"
                f"{position.current_quantity},{unrealized},"
                f"{position.status.value},{position.entry_dex.value},"
                f"{position.strategy}"
            )
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict:
        """Get position tracker summary."""
        realized, unrealized, total = self.get_portfolio_pnl()
        
        return {
            "open_positions": len(self._positions),
            "closed_positions": len(self._closed_positions),
            "realized_pnl": float(realized),
            "unrealized_pnl": float(unrealized),
            "total_pnl": float(total),
            "blockchain_verified": self.get_reconciliation_status()["status"],
            "last_update": max(
                [p.last_update for p in self._positions.values()],
                default=None
            ),
        }


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_position_tracker() -> PositionTracker:
    """Factory function to create position tracker."""
    logger = logging.getLogger("position_tracker")
    return PositionTracker(logger)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)
    
    tracker = create_position_tracker()
    
    # Open a position
    pos_id = tracker.open_position(
        token_a="0x1234...",
        token_b="0x5678...",
        token_a_symbol="ETH",
        token_b_symbol="USDC",
        quantity=Decimal("10"),
        entry_price=Decimal("1800"),
        dex=DEXType.UNISWAP_V3,
        strategy="arbitrage",
        gas_cost=Decimal("50"),
        slippage=Decimal("0.01"),
    )
    
    # Update price
    tracker.update_position_price(pos_id, Decimal("1850"))
    
    # Create snapshot
    snapshot = tracker.create_portfolio_snapshot(
        total_value_usd=Decimal("18500"),
        blockchain_verified=True,
    )
    
    print(tracker.get_summary())
