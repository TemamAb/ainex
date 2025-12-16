"""
Order Book Analyzer - Liquidity & Slippage Analysis
Real-time order book monitoring with depth profiling and IL estimation
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque, defaultdict
import statistics

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    """Order side"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class OrderLevel:
    """Single order level"""
    price: float
    quantity: float
    
    def value(self) -> float:
        """Total value at this level"""
        return self.price * self.quantity


@dataclass
class OrderBook:
    """Represents an order book"""
    token_pair: str
    exchange: str
    timestamp: datetime
    bids: List[OrderLevel] = field(default_factory=list)
    asks: List[OrderLevel] = field(default_factory=list)
    
    def mid_price(self) -> Optional[float]:
        """Calculate mid price"""
        if not self.bids or not self.asks:
            return None
        return (self.bids[0].price + self.asks[0].price) / 2
    
    def spread_bps(self) -> Optional[float]:
        """Calculate spread in basis points"""
        if not self.bids or not self.asks:
            return None
        mid = self.mid_price()
        if mid is None or mid == 0:
            return None
        spread = (self.asks[0].price - self.bids[0].price) / mid
        return spread * 10000  # Convert to bps
    
    def total_bid_liquidity(self, depth: float) -> float:
        """Total liquidity available at bid side to given price depth"""
        total = 0.0
        threshold = self.mid_price() * (1 - depth / 100) if self.mid_price() else 0
        
        for level in self.bids:
            if level.price >= threshold:
                total += level.value()
            else:
                break
        
        return total
    
    def total_ask_liquidity(self, depth: float) -> float:
        """Total liquidity available at ask side to given price depth"""
        total = 0.0
        threshold = self.mid_price() * (1 + depth / 100) if self.mid_price() else 0
        
        for level in self.asks:
            if level.price <= threshold:
                total += level.value()
            else:
                break
        
        return total


@dataclass
class LiquidityAnalysis:
    """Analysis of liquidity"""
    token_pair: str
    timestamp: datetime
    exchange: str
    mid_price: float
    spread_bps: float
    bid_liquidity_1pct: float  # Liquidity within 1% depth
    ask_liquidity_1pct: float
    bid_liquidity_5pct: float  # Liquidity within 5% depth
    ask_liquidity_5pct: float
    order_book_imbalance: float  # Bid liquidity / ask liquidity
    depth_of_market: Dict[str, float] = field(default_factory=dict)
    
    def is_liquid(self) -> bool:
        """Check if market is sufficiently liquid"""
        min_liquidity = 10000  # $10K threshold
        return (self.bid_liquidity_1pct > min_liquidity and 
                self.ask_liquidity_1pct > min_liquidity)


@dataclass
class ImpermanentLoss:
    """Impermanent loss estimation"""
    token_pair: str
    price_ratio: float  # New price / Old price
    il_percentage: float
    estimated_loss_usd: float
    timestamp: datetime


class OrderBookAnalyzer:
    """Analyzes order books for liquidity and slippage"""
    
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.analysis_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.liquidity_alerts: deque = deque(maxlen=1000)
        self.min_spread_bps = 0.5  # Alert if spread < 0.5 bps
        self.max_spread_bps = 500  # Alert if spread > 500 bps
    
    async def update_order_book(self, token_pair: str, exchange: str,
                               bids: List[Tuple[float, float]],
                               asks: List[Tuple[float, float]]) -> Optional[OrderBook]:
        """Update order book from feed"""
        try:
            bid_levels = [OrderLevel(price=p, quantity=q) for p, q in bids]
            ask_levels = [OrderLevel(price=p, quantity=q) for p, q in asks]
            
            order_book = OrderBook(
                token_pair=token_pair,
                exchange=exchange,
                timestamp=datetime.utcnow(),
                bids=bid_levels,
                asks=ask_levels,
            )
            
            # Sort by price
            order_book.bids.sort(key=lambda x: x.price, reverse=True)
            order_book.asks.sort(key=lambda x: x.price)
            
            # Store
            key = f"{token_pair}:{exchange}"
            self.order_books[key] = order_book
            
            # Analyze
            analysis = await self._analyze_order_book(order_book)
            if analysis:
                self.analysis_history[key].append(analysis)
            
            return order_book
            
        except Exception as e:
            logger.error(f"Failed to update order book: {e}")
            return None
    
    async def _analyze_order_book(self, order_book: OrderBook) -> Optional[LiquidityAnalysis]:
        """Analyze order book"""
        try:
            mid_price = order_book.mid_price()
            spread_bps = order_book.spread_bps()
            
            if mid_price is None or spread_bps is None:
                return None
            
            analysis = LiquidityAnalysis(
                token_pair=order_book.token_pair,
                timestamp=datetime.utcnow(),
                exchange=order_book.exchange,
                mid_price=mid_price,
                spread_bps=spread_bps,
                bid_liquidity_1pct=order_book.total_bid_liquidity(1.0),
                ask_liquidity_1pct=order_book.total_ask_liquidity(1.0),
                bid_liquidity_5pct=order_book.total_bid_liquidity(5.0),
                ask_liquidity_5pct=order_book.total_ask_liquidity(5.0),
                order_book_imbalance=order_book.total_bid_liquidity(1.0) / 
                                    max(order_book.total_ask_liquidity(1.0), 1),
            )
            
            # Check alerts
            if spread_bps < self.min_spread_bps:
                self.liquidity_alerts.append({
                    'type': 'tight_spread',
                    'token_pair': order_book.token_pair,
                    'spread_bps': spread_bps,
                    'timestamp': datetime.utcnow().isoformat(),
                })
            
            if spread_bps > self.max_spread_bps:
                self.liquidity_alerts.append({
                    'type': 'wide_spread',
                    'token_pair': order_book.token_pair,
                    'spread_bps': spread_bps,
                    'timestamp': datetime.utcnow().isoformat(),
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return None
    
    async def estimate_slippage(self, token_pair: str, exchange: str,
                               side: OrderSide, amount_usd: float) -> Optional[Dict]:
        """Estimate slippage for a trade"""
        try:
            key = f"{token_pair}:{exchange}"
            order_book = self.order_books.get(key)
            
            if not order_book:
                logger.warning(f"Order book not found: {key}")
                return None
            
            mid_price = order_book.mid_price()
            if not mid_price:
                return None
            
            # Calculate quantity needed
            quantity_needed = amount_usd / mid_price
            
            # Walk the order book
            if side == OrderSide.SELL:
                levels = order_book.bids
            else:
                levels = order_book.asks
            
            executed_quantity = 0.0
            average_price = 0.0
            total_value = 0.0
            
            for level in levels:
                if executed_quantity >= quantity_needed:
                    break
                
                quantity_to_execute = min(level.quantity, quantity_needed - executed_quantity)
                total_value += quantity_to_execute * level.price
                executed_quantity += quantity_to_execute
            
            if executed_quantity > 0:
                average_price = total_value / executed_quantity
                slippage_bps = abs(average_price - mid_price) / mid_price * 10000
            else:
                slippage_bps = float('inf')
            
            return {
                'token_pair': token_pair,
                'side': side.value,
                'requested_amount_usd': amount_usd,
                'executed_quantity': executed_quantity,
                'average_execution_price': average_price,
                'mid_price': mid_price,
                'slippage_bps': slippage_bps,
                'slippage_usd': amount_usd * (slippage_bps / 10000),
                'timestamp': datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Slippage estimation error: {e}")
            return None
    
    async def estimate_il(self, token_pair: str, old_price: float,
                         new_price: float, liquidity_usd: float) -> Optional[ImpermanentLoss]:
        """Estimate impermanent loss"""
        try:
            price_ratio = new_price / old_price if old_price > 0 else 1.0
            
            # IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
            # (simplified formula for 50/50 pools)
            import math
            
            if price_ratio <= 0:
                return None
            
            sqrt_ratio = math.sqrt(price_ratio)
            il_percentage = (2 * sqrt_ratio / (1 + price_ratio) - 1) * 100
            
            estimated_loss_usd = liquidity_usd * abs(il_percentage) / 100
            
            return ImpermanentLoss(
                token_pair=token_pair,
                price_ratio=price_ratio,
                il_percentage=il_percentage,
                estimated_loss_usd=estimated_loss_usd,
                timestamp=datetime.utcnow(),
            )
            
        except Exception as e:
            logger.error(f"IL estimation error: {e}")
            return None
    
    async def get_depth_profile(self, token_pair: str, exchange: str,
                               price_levels: int = 20) -> Optional[Dict]:
        """Get market depth profile"""
        try:
            key = f"{token_pair}:{exchange}"
            order_book = self.order_books.get(key)
            
            if not order_book:
                return None
            
            mid_price = order_book.mid_price()
            if not mid_price:
                return None
            
            depth = {
                'token_pair': token_pair,
                'exchange': exchange,
                'mid_price': mid_price,
                'timestamp': datetime.utcnow().isoformat(),
                'bid_depth': [],
                'ask_depth': [],
            }
            
            # Bid side
            cumulative = 0.0
            for i, level in enumerate(order_book.bids[:price_levels]):
                cumulative += level.value()
                depth['bid_depth'].append({
                    'price': level.price,
                    'quantity': level.quantity,
                    'value': level.value(),
                    'cumulative_value': cumulative,
                })
            
            # Ask side
            cumulative = 0.0
            for i, level in enumerate(order_book.asks[:price_levels]):
                cumulative += level.value()
                depth['ask_depth'].append({
                    'price': level.price,
                    'quantity': level.quantity,
                    'value': level.value(),
                    'cumulative_value': cumulative,
                })
            
            return depth
            
        except Exception as e:
            logger.error(f"Depth profile error: {e}")
            return None
    
    async def get_liquidity_analysis(self, token_pair: str, exchange: str) -> Optional[LiquidityAnalysis]:
        """Get latest liquidity analysis"""
        key = f"{token_pair}:{exchange}"
        history = self.analysis_history.get(key)
        
        if history:
            return list(history)[-1]
        
        return None
    
    def get_analyzer_status(self) -> Dict[str, Any]:
        """Get analyzer status"""
        return {
            'order_books_tracked': len(self.order_books),
            'liquidity_alerts': len(self.liquidity_alerts),
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global instance
_analyzer: Optional[OrderBookAnalyzer] = None


def init_order_book_analyzer() -> OrderBookAnalyzer:
    """Initialize global analyzer"""
    global _analyzer
    _analyzer = OrderBookAnalyzer()
    return _analyzer


def get_analyzer() -> OrderBookAnalyzer:
    """Get global analyzer"""
    global _analyzer
    if not _analyzer:
        _analyzer = init_order_book_analyzer()
    return _analyzer
