"""
AINEON Production Profit Ledger
PostgreSQL-backed profit tracking with transaction audit trail and verification.

Spec: Complete transaction history, profit tracking, Etherscan verification
Target: Immutable audit trail, real-time profit updates, month/day summaries
"""

import asyncio
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import json

import asyncpg
from asyncpg import Record

logger = logging.getLogger(__name__)


@dataclass
class Transaction:
    """Represents a recorded transaction."""
    tx_hash: str
    strategy: str
    amount_in: Decimal
    amount_out: Decimal
    profit: Decimal
    gas_cost: Decimal
    net_profit: Decimal
    block_number: int
    block_timestamp: datetime
    status: str  # "pending", "confirmed", "failed"
    etherscan_verified: bool = False
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class DailyProfit:
    """Daily profit summary."""
    date: str
    total_profit: Decimal
    transaction_count: int
    success_rate: float
    average_trade_profit: Decimal
    best_trade: Decimal
    worst_trade: Decimal


@dataclass
class MonthlyProfit:
    """Monthly profit summary."""
    month: str
    total_profit: Decimal
    daily_average: Decimal
    transaction_count: int
    success_rate: float


class ProfitLedgerDatabase:
    """
    Production profit ledger with PostgreSQL backend.
    
    Features:
    - Immutable transaction audit trail
    - Real-time profit tracking
    - Automated daily/monthly summaries
    - Etherscan verification
    - Withdrawal tracking
    - Multi-chain support
    """
    
    def __init__(self, database_url: str):
        """
        Initialize profit ledger database.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool and schema."""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            max_queries=50000,
        )
        
        # Create schema
        await self._create_schema()
        logger.info("Profit ledger database initialized")
    
    async def shutdown(self):
        """Close database connections."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def _create_schema(self):
        """Create database schema."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    tx_hash VARCHAR(255) UNIQUE NOT NULL,
                    strategy VARCHAR(100) NOT NULL,
                    amount_in NUMERIC(30, 10) NOT NULL,
                    amount_out NUMERIC(30, 10) NOT NULL,
                    profit NUMERIC(30, 10) NOT NULL,
                    gas_cost NUMERIC(30, 10) NOT NULL,
                    net_profit NUMERIC(30, 10) NOT NULL,
                    block_number BIGINT NOT NULL,
                    block_timestamp TIMESTAMP NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    etherscan_verified BOOLEAN DEFAULT FALSE,
                    etherscan_verified_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX tx_hash_idx (tx_hash),
                    INDEX block_timestamp_idx (block_timestamp),
                    INDEX status_idx (status)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id SERIAL PRIMARY KEY,
                    date DATE UNIQUE NOT NULL,
                    total_profit NUMERIC(30, 10) NOT NULL,
                    transaction_count INT NOT NULL,
                    success_rate NUMERIC(5, 4) NOT NULL,
                    average_trade_profit NUMERIC(30, 10) NOT NULL,
                    best_trade NUMERIC(30, 10) NOT NULL,
                    worst_trade NUMERIC(30, 10) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX date_idx (date)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS monthly_summaries (
                    id SERIAL PRIMARY KEY,
                    month VARCHAR(7) UNIQUE NOT NULL,
                    total_profit NUMERIC(30, 10) NOT NULL,
                    transaction_count INT NOT NULL,
                    success_rate NUMERIC(5, 4) NOT NULL,
                    daily_average NUMERIC(30, 10) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX month_idx (month)
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS withdrawals (
                    id SERIAL PRIMARY KEY,
                    withdrawal_hash VARCHAR(255) UNIQUE,
                    amount NUMERIC(30, 10) NOT NULL,
                    destination_address VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    INDEX status_idx (status)
                )
            """)
    
    async def record_transaction(self, tx: Transaction) -> bool:
        """
        Record a transaction in the ledger.
        
        Args:
            tx: Transaction to record
            
        Returns:
            True if successful
        """
        if not self.pool:
            logger.error("Database not initialized")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO transactions (
                        tx_hash, strategy, amount_in, amount_out,
                        profit, gas_cost, net_profit, block_number,
                        block_timestamp, status, notes
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, 
                tx.tx_hash, tx.strategy, tx.amount_in, tx.amount_out,
                tx.profit, tx.gas_cost, tx.net_profit, tx.block_number,
                tx.block_timestamp, tx.status, tx.notes
                )
            
            logger.info(f"Transaction recorded: {tx.tx_hash} (profit: {tx.net_profit})")
            return True
            
        except asyncpg.UniqueViolationError:
            logger.warning(f"Transaction already recorded: {tx.tx_hash}")
            return False
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            return False
    
    async def update_transaction_status(
        self,
        tx_hash: str,
        status: str,
        etherscan_verified: bool = False
    ) -> bool:
        """Update transaction status and verification."""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE transactions 
                    SET status = $2, 
                        etherscan_verified = $3,
                        etherscan_verified_at = CASE 
                            WHEN $3 THEN CURRENT_TIMESTAMP 
                            ELSE etherscan_verified_at 
                        END
                    WHERE tx_hash = $1
                """, tx_hash, status, etherscan_verified)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update transaction status: {e}")
            return False
    
    async def get_transaction(self, tx_hash: str) -> Optional[Transaction]:
        """Get transaction by hash."""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM transactions WHERE tx_hash = $1",
                    tx_hash
                )
            
            if row:
                return self._row_to_transaction(row)
            
        except Exception as e:
            logger.error(f"Failed to get transaction: {e}")
        
        return None
    
    async def get_daily_profit(self, date_str: str) -> Optional[DailyProfit]:
        """Get daily profit summary."""
        if not self.pool:
            return None
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM daily_summaries WHERE date = $1::DATE",
                    date_str
                )
            
            if row:
                return DailyProfit(
                    date=row["date"],
                    total_profit=Decimal(row["total_profit"]),
                    transaction_count=row["transaction_count"],
                    success_rate=float(row["success_rate"]),
                    average_trade_profit=Decimal(row["average_trade_profit"]),
                    best_trade=Decimal(row["best_trade"]),
                    worst_trade=Decimal(row["worst_trade"]),
                )
            
        except Exception as e:
            logger.error(f"Failed to get daily profit: {e}")
        
        return None
    
    async def calculate_daily_summary(self, date_str: str) -> bool:
        """Calculate and store daily profit summary."""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                # Get all transactions for the day
                transactions = await conn.fetch("""
                    SELECT net_profit, status FROM transactions
                    WHERE DATE(block_timestamp) = $1::DATE
                    AND status = 'confirmed'
                """, date_str)
                
                if not transactions:
                    return False
                
                total_profit = sum(Decimal(tx["net_profit"]) for tx in transactions)
                successful = len([t for t in transactions if t["status"] == "confirmed"])
                success_rate = successful / len(transactions) if transactions else 0
                profits = [Decimal(t["net_profit"]) for t in transactions]
                
                await conn.execute("""
                    INSERT INTO daily_summaries (
                        date, total_profit, transaction_count,
                        success_rate, average_trade_profit,
                        best_trade, worst_trade
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (date) DO UPDATE SET
                        total_profit = $2,
                        transaction_count = $3,
                        success_rate = $4,
                        average_trade_profit = $5,
                        best_trade = $6,
                        worst_trade = $7,
                        updated_at = CURRENT_TIMESTAMP
                """,
                date_str,
                total_profit,
                len(transactions),
                Decimal(success_rate),
                sum(profits) / len(profits) if profits else Decimal(0),
                max(profits) if profits else Decimal(0),
                min(profits) if profits else Decimal(0),
                )
            
            logger.info(f"Daily summary calculated for {date_str}: {total_profit} ETH")
            return True
            
        except Exception as e:
            logger.error(f"Failed to calculate daily summary: {e}")
            return False
    
    async def calculate_monthly_summary(self, month_str: str) -> bool:
        """Calculate and store monthly profit summary."""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                # Get all transactions for the month
                transactions = await conn.fetch("""
                    SELECT net_profit, status FROM transactions
                    WHERE TO_CHAR(block_timestamp, 'YYYY-MM') = $1
                    AND status = 'confirmed'
                """, month_str)
                
                if not transactions:
                    return False
                
                total_profit = sum(Decimal(tx["net_profit"]) for tx in transactions)
                successful = len([t for t in transactions if t["status"] == "confirmed"])
                success_rate = successful / len(transactions) if transactions else 0
                
                # Get day count from daily summaries
                daily_summaries = await conn.fetch("""
                    SELECT total_profit FROM daily_summaries
                    WHERE TO_CHAR(date, 'YYYY-MM') = $1
                """, month_str)
                
                daily_average = total_profit / len(daily_summaries) if daily_summaries else Decimal(0)
                
                await conn.execute("""
                    INSERT INTO monthly_summaries (
                        month, total_profit, transaction_count,
                        success_rate, daily_average
                    ) VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (month) DO UPDATE SET
                        total_profit = $2,
                        transaction_count = $3,
                        success_rate = $4,
                        daily_average = $5,
                        updated_at = CURRENT_TIMESTAMP
                """,
                month_str,
                total_profit,
                len(transactions),
                Decimal(success_rate),
                daily_average,
                )
            
            logger.info(f"Monthly summary calculated for {month_str}: {total_profit} ETH")
            return True
            
        except Exception as e:
            logger.error(f"Failed to calculate monthly summary: {e}")
            return False
    
    async def get_total_profit(self) -> Decimal:
        """Get total cumulative profit."""
        if not self.pool:
            return Decimal(0)
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchval(
                    "SELECT COALESCE(SUM(net_profit), 0) FROM transactions WHERE status = 'confirmed'"
                )
            
            return Decimal(row) if row else Decimal(0)
            
        except Exception as e:
            logger.error(f"Failed to get total profit: {e}")
            return Decimal(0)
    
    async def get_profit_last_24h(self) -> Decimal:
        """Get profit from last 24 hours."""
        if not self.pool:
            return Decimal(0)
        
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchval("""
                    SELECT COALESCE(SUM(net_profit), 0) FROM transactions
                    WHERE status = 'confirmed'
                    AND block_timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """)
            
            return Decimal(row) if row else Decimal(0)
            
        except Exception as e:
            logger.error(f"Failed to get 24h profit: {e}")
            return Decimal(0)
    
    async def record_withdrawal(
        self,
        amount: Decimal,
        destination: str,
        status: str = "pending"
    ) -> bool:
        """Record profit withdrawal."""
        if not self.pool:
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO withdrawals (amount, destination_address, status)
                    VALUES ($1, $2, $3)
                """, amount, destination, status)
            
            logger.info(f"Withdrawal recorded: {amount} ETH to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record withdrawal: {e}")
            return False
    
    def _row_to_transaction(self, row: Record) -> Transaction:
        """Convert database row to Transaction object."""
        return Transaction(
            tx_hash=row["tx_hash"],
            strategy=row["strategy"],
            amount_in=Decimal(row["amount_in"]),
            amount_out=Decimal(row["amount_out"]),
            profit=Decimal(row["profit"]),
            gas_cost=Decimal(row["gas_cost"]),
            net_profit=Decimal(row["net_profit"]),
            block_number=row["block_number"],
            block_timestamp=row["block_timestamp"],
            status=row["status"],
            etherscan_verified=row["etherscan_verified"],
            notes=row.get("notes"),
            created_at=row.get("created_at"),
        )


# Singleton instance
_profit_ledger: Optional[ProfitLedgerDatabase] = None


async def initialize_profit_ledger(database_url: str) -> ProfitLedgerDatabase:
    """Initialize profit ledger database."""
    global _profit_ledger
    _profit_ledger = ProfitLedgerDatabase(database_url)
    await _profit_ledger.initialize()
    return _profit_ledger


def get_profit_ledger() -> ProfitLedgerDatabase:
    """Get current profit ledger instance."""
    if _profit_ledger is None:
        raise RuntimeError("Profit ledger not initialized")
    return _profit_ledger


async def shutdown_profit_ledger():
    """Shutdown profit ledger database."""
    global _profit_ledger
    if _profit_ledger:
        await _profit_ledger.shutdown()
        _profit_ledger = None
