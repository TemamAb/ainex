"""
Mempool Monitor - MEV & Sandwich Attack Detection
Real-time mempool transaction monitoring with opportunity detection
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

import aiohttp
from web3 import Web3

logger = logging.getLogger(__name__)


class TransactionType(Enum):
    """Types of transactions detected"""
    SWAP = "swap"
    LIQUIDATION = "liquidation"
    FLASH_LOAN = "flash_loan"
    MEV_OPPORTUNITY = "mev_opportunity"
    SANDWICH_ATTACK = "sandwich_attack"
    LARGE_TRANSFER = "large_transfer"
    UNKNOWN = "unknown"


@dataclass
class Transaction:
    """Mempool transaction"""
    tx_hash: str
    from_address: str
    to_address: str
    value: float
    gas_price: int
    gas_limit: int
    data: str
    tx_type: TransactionType
    detected_at: datetime
    confidence: float = 1.0
    estimated_mev: float = 0.0
    tokens: List[str] = field(default_factory=list)
    amounts: List[float] = field(default_factory=list)
    
    def get_priority_fee(self) -> int:
        """Get priority fee in wei"""
        return self.gas_price


@dataclass
class MEVOpportunity:
    """Detected MEV opportunity"""
    opportunity_id: str
    opportunity_type: str  # sandwich, liquidation, arbitrage, etc.
    detected_at: datetime
    confidence: float
    estimated_profit_eth: float
    transactions: List[Transaction]
    execution_window_ms: int
    risk_level: str  # low, medium, high


class MempoolMonitor:
    """Monitors mempool for MEV opportunities"""
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.pending_transactions: Dict[str, Transaction] = {}
        self.transaction_history: deque = deque(maxlen=50000)
        self.mev_opportunities: deque = deque(maxlen=10000)
        self.opportunity_callbacks: List[Callable] = []
        self.sandwich_patterns: List[str] = []
        self.monitoring = False
        self.update_interval = 1  # seconds
        self.min_profit_threshold = 0.01  # ETH
        self.detection_confidence_threshold = 0.7
    
    async def initialize(self) -> bool:
        """Initialize mempool monitor"""
        try:
            rpc_url = os.getenv('WEB3_PROVIDER_URL', 'http://localhost:8545')
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                logger.error("Failed to connect to Web3 provider")
                return False
            
            logger.info("Mempool monitor initialized")
            
            # Start monitoring
            asyncio.create_task(self._monitor_loop())
            self.monitoring = True
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                await self._check_pending_transactions()
                await self._detect_mev_opportunities()
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_pending_transactions(self):
        """Check pending transactions in mempool"""
        try:
            # Get pending block
            pending_block = self.w3.eth.get_block('pending')
            
            for tx_hash in pending_block.get('transactions', []):
                if tx_hash not in self.pending_transactions:
                    # New transaction
                    try:
                        tx = self.w3.eth.get_transaction(tx_hash)
                        await self._process_transaction(tx)
                    except Exception as e:
                        logger.debug(f"Error processing tx {tx_hash}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to check pending transactions: {e}")
    
    async def _process_transaction(self, tx: Dict):
        """Process a transaction"""
        try:
            tx_hash = tx.get('hash', '').hex() if hasattr(tx.get('hash'), 'hex') else str(tx.get('hash', ''))
            
            # Decode transaction
            tx_type = await self._detect_transaction_type(tx)
            tokens, amounts = await self._extract_token_amounts(tx)
            
            transaction = Transaction(
                tx_hash=tx_hash,
                from_address=tx.get('from', ''),
                to_address=tx.get('to', ''),
                value=float(tx.get('value', 0)) / 1e18,  # Convert from wei
                gas_price=tx.get('gasPrice', 0),
                gas_limit=tx.get('gas', 0),
                data=tx.get('input', ''),
                tx_type=tx_type,
                detected_at=datetime.utcnow(),
                tokens=tokens,
                amounts=amounts,
                confidence=0.8,
            )
            
            # Store
            self.pending_transactions[tx_hash] = transaction
            self.transaction_history.append(transaction)
            
            logger.debug(f"Detected {tx_type.value} transaction: {tx_hash[:16]}...")
            
        except Exception as e:
            logger.error(f"Transaction processing error: {e}")
    
    async def _detect_transaction_type(self, tx: Dict) -> TransactionType:
        """Detect type of transaction"""
        try:
            data = tx.get('input', '')
            to_address = tx.get('to', '')
            value = float(tx.get('value', 0))
            
            # Check function signature
            if len(data) >= 10:
                sig = data[:10]
                
                # Swap signatures (0x - prefix + 8 char signature)
                if sig in ['0xa9059cbb', '0x23b872dd', '0xd9627aa4']:
                    return TransactionType.SWAP
                
                # Flash loan signature
                if sig == '0xd0e30db0':
                    return TransactionType.FLASH_LOAN
                
                # Liquidation
                if sig in ['0xec6c1bc9', '0x00000000']:
                    return TransactionType.LIQUIDATION
            
            # Large transfer
            if value > 10.0:
                return TransactionType.LARGE_TRANSFER
            
            return TransactionType.UNKNOWN
            
        except Exception as e:
            logger.debug(f"Type detection error: {e}")
            return TransactionType.UNKNOWN
    
    async def _extract_token_amounts(self, tx: Dict) -> tuple:
        """Extract token and amounts from transaction"""
        try:
            tokens = []
            amounts = []
            
            # This would decode calldata in production
            # For now, return empty
            
            return tokens, amounts
            
        except Exception:
            return [], []
    
    async def _detect_mev_opportunities(self):
        """Detect MEV opportunities in pending transactions"""
        try:
            # Look for sandwich patterns
            swaps = [t for t in self.pending_transactions.values() 
                    if t.tx_type == TransactionType.SWAP]
            
            if len(swaps) >= 2:
                # Check for sandwich opportunities
                for i, tx1 in enumerate(swaps):
                    for tx2 in swaps[i+1:]:
                        # Simple heuristic: same token pair, similar amounts
                        if self._is_sandwich_opportunity(tx1, tx2):
                            opportunity = MEVOpportunity(
                                opportunity_id=f"sandwich_{tx1.tx_hash[:8]}_{tx2.tx_hash[:8]}",
                                opportunity_type="sandwich",
                                detected_at=datetime.utcnow(),
                                confidence=0.85,
                                estimated_profit_eth=await self._estimate_sandwich_profit(tx1, tx2),
                                transactions=[tx1, tx2],
                                execution_window_ms=100,
                                risk_level="medium",
                            )
                            
                            if opportunity.estimated_profit_eth >= self.min_profit_threshold:
                                if opportunity.confidence >= self.detection_confidence_threshold:
                                    await self._notify_opportunity(opportunity)
        
        except Exception as e:
            logger.error(f"MEV detection error: {e}")
    
    def _is_sandwich_opportunity(self, tx1: Transaction, tx2: Transaction) -> bool:
        """Check if two transactions form sandwich opportunity"""
        try:
            # Same tokens?
            if set(tx1.tokens) & set(tx2.tokens):
                # Similar amounts?
                if tx1.amounts and tx2.amounts:
                    ratio = max(tx1.amounts[0], tx2.amounts[0]) / min(tx1.amounts[0], tx2.amounts[0])
                    return 0.8 < ratio < 1.2
        
        except Exception:
            pass
        
        return False
    
    async def _estimate_sandwich_profit(self, tx1: Transaction, tx2: Transaction) -> float:
        """Estimate profit from sandwich opportunity"""
        try:
            # Simplified estimation
            if tx1.amounts and tx2.amounts:
                avg_amount = (tx1.amounts[0] + tx2.amounts[0]) / 2
                slippage = 0.01  # 1% estimated slippage
                estimated_profit = avg_amount * slippage / 1e18
                return estimated_profit
        
        except Exception:
            pass
        
        return 0.0
    
    def register_opportunity_callback(self, callback: Callable):
        """Register callback for MEV opportunities"""
        self.opportunity_callbacks.append(callback)
    
    async def _notify_opportunity(self, opportunity: MEVOpportunity):
        """Notify about MEV opportunity"""
        self.mev_opportunities.append(opportunity)
        
        for callback in self.opportunity_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(opportunity)
                else:
                    callback(opportunity)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"MEV opportunity detected: {opportunity.opportunity_type} ({opportunity.estimated_profit_eth:.4f} ETH)")
    
    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        return {
            'monitoring': self.monitoring,
            'pending_transactions': len(self.pending_transactions),
            'recent_mev_opportunities': len(self.mev_opportunities),
            'total_transactions_monitored': len(self.transaction_history),
            'last_check': datetime.utcnow().isoformat(),
        }
    
    async def get_recent_opportunities(self, limit: int = 100) -> List[MEVOpportunity]:
        """Get recent MEV opportunities"""
        return list(self.mev_opportunities)[-limit:]
    
    async def shutdown(self):
        """Shutdown monitor"""
        self.monitoring = False
        logger.info("Mempool monitor shutdown complete")


# Global instance
_monitor: Optional[MempoolMonitor] = None


async def init_mempool_monitor() -> MempoolMonitor:
    """Initialize global mempool monitor"""
    global _monitor
    _monitor = MempoolMonitor()
    await _monitor.initialize()
    return _monitor


async def get_monitor() -> MempoolMonitor:
    """Get global monitor"""
    global _monitor
    if not _monitor:
        _monitor = await init_mempool_monitor()
    return _monitor
