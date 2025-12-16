"""
Flash Loan Detector - Flash Loan Opportunity Identification
Detects and analyzes flash loan arbitrage opportunities
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class FlashLoanProvider(Enum):
    """Flash loan providers"""
    AAVE = "aave"
    DYDX = "dydx"
    UNISWAP_V3 = "uniswap_v3"
    BALANCER = "balancer"


@dataclass
class FlashLoanOpportunity:
    """Flash loan arbitrage opportunity"""
    opportunity_id: str
    provider: FlashLoanProvider
    loan_token: str
    loan_amount: float
    flash_fee_percent: float  # Fee as percentage
    arbitrage_path: List[str]  # Token swap path
    entry_exchange: str
    exit_exchange: str
    entry_price: float
    exit_price: float
    slippage_estimate: float  # Percentage
    execution_time_ms: float  # Estimated execution time
    estimated_profit_eth: float
    confidence: float
    detected_at: datetime
    expiration_seconds: int = 300  # 5 minutes


@dataclass
class FlashLoanRoute:
    """Detailed flash loan execution route"""
    opportunity_id: str
    steps: List[Dict[str, Any]]  # [borrow, swap1, swap2, ..., repay]
    total_gas_estimate: float
    total_fee: float
    net_profit: float
    safety_checks: List[str]  # Safety validations


class FlashLoanDetector:
    """Detects flash loan arbitrage opportunities"""
    
    def __init__(self):
        self.opportunities: deque = deque(maxlen=10000)
        self.executed_loans: List[str] = []
        self.provider_fees: Dict[FlashLoanProvider, float] = {
            FlashLoanProvider.AAVE: 0.09,  # 0.09%
            FlashLoanProvider.DYDX: 0.0,   # Free
            FlashLoanProvider.UNISWAP_V3: 0.05,  # 0.05%
            FlashLoanProvider.BALANCER: 0.0,  # Free (for certain pools)
        }
        self.min_profit_threshold_eth = 0.1  # Minimum 0.1 ETH profit
        self.max_execution_time_ms = 1000  # Must execute within 1 second
    
    async def detect_opportunities(self, price_data: Dict[str, float],
                                   liquidity_data: Dict[str, float]) -> List[FlashLoanOpportunity]:
        """Detect flash loan opportunities"""
        opportunities = []
        
        try:
            # Scan for price discrepancies across exchanges
            token_pairs = self._get_token_pairs(price_data)
            
            for token_pair in token_pairs:
                # Get prices across exchanges
                prices = self._get_cross_exchange_prices(token_pair, price_data)
                
                if len(prices) < 2:
                    continue
                
                # Find best arbitrage path
                sorted_prices = sorted(prices.items(), key=lambda x: x[1]['price'])
                entry_exchange = sorted_prices[0][0]
                exit_exchange = sorted_prices[-1][0]
                entry_price = sorted_prices[0][1]['price']
                exit_price = sorted_prices[-1][1]['price']
                
                price_spread = (exit_price - entry_price) / entry_price * 100
                
                if price_spread < 0.5:  # Need at least 0.5% spread
                    continue
                
                # Calculate optimal loan amount
                optimal_amount = self._calculate_optimal_loan_amount(
                    token_pair,
                    liquidity_data
                )
                
                if optimal_amount <= 0:
                    continue
                
                # Estimate profit
                for provider in FlashLoanProvider:
                    opportunity = await self._calculate_opportunity(
                        provider=provider,
                        token_pair=token_pair,
                        loan_amount=optimal_amount,
                        entry_exchange=entry_exchange,
                        exit_exchange=exit_exchange,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        price_spread=price_spread,
                        liquidity=liquidity_data.get(token_pair, 0),
                    )
                    
                    if opportunity and opportunity.estimated_profit_eth >= self.min_profit_threshold_eth:
                        opportunities.append(opportunity)
                        self.opportunities.append(opportunity)
                        logger.info(f"Flash loan opportunity detected: {opportunity.opportunity_id}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return opportunities
    
    async def _calculate_opportunity(self, provider: FlashLoanProvider,
                                    token_pair: str, loan_amount: float,
                                    entry_exchange: str, exit_exchange: str,
                                    entry_price: float, exit_price: float,
                                    price_spread: float,
                                    liquidity: float) -> Optional[FlashLoanOpportunity]:
        """Calculate specific opportunity"""
        try:
            fee_percent = self.provider_fees.get(provider, 0.09)
            fee_amount = loan_amount * (fee_percent / 100)
            
            # Estimate slippage
            slippage_percent = self._estimate_slippage(loan_amount, liquidity)
            adjusted_exit_price = exit_price * (1 - slippage_percent / 100)
            
            # Calculate profit
            purchase_cost = loan_amount * entry_price
            sale_proceeds = loan_amount * adjusted_exit_price
            gross_profit = sale_proceeds - purchase_cost
            net_profit = gross_profit - fee_amount
            
            # Convert to ETH (assuming base token)
            profit_eth = net_profit / 1e18 if loan_amount > 0 else 0
            
            if profit_eth < self.min_profit_threshold_eth:
                return None
            
            # Estimate execution time
            execution_time = self._estimate_execution_time(
                entry_exchange,
                exit_exchange,
                loan_amount
            )
            
            if execution_time > self.max_execution_time_ms:
                return None
            
            opportunity = FlashLoanOpportunity(
                opportunity_id=f"fl_{provider.value}_{token_pair}_{datetime.utcnow().timestamp()}",
                provider=provider,
                loan_token=token_pair,
                loan_amount=loan_amount,
                flash_fee_percent=fee_percent,
                arbitrage_path=[entry_exchange, exit_exchange],
                entry_exchange=entry_exchange,
                exit_exchange=exit_exchange,
                entry_price=entry_price,
                exit_price=exit_price,
                slippage_estimate=slippage_percent,
                execution_time_ms=execution_time,
                estimated_profit_eth=profit_eth,
                confidence=self._calculate_confidence(price_spread, liquidity, execution_time),
                detected_at=datetime.utcnow(),
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Opportunity calculation error: {e}")
            return None
    
    def _get_token_pairs(self, price_data: Dict) -> List[str]:
        """Extract unique token pairs from price data"""
        pairs = set()
        for key in price_data.keys():
            if ':' in key:
                pair = key.split(':')[0]
                pairs.add(pair)
        return list(pairs)
    
    def _get_cross_exchange_prices(self, token_pair: str, price_data: Dict) -> Dict:
        """Get prices for token pair across exchanges"""
        prices = {}
        for key, price in price_data.items():
            if key.startswith(f"{token_pair}:"):
                exchange = key.split(':')[1]
                prices[exchange] = {'price': price, 'timestamp': datetime.utcnow()}
        return prices
    
    def _calculate_optimal_loan_amount(self, token_pair: str, liquidity_data: Dict) -> float:
        """Calculate optimal flash loan amount"""
        try:
            liquidity = liquidity_data.get(token_pair, 0)
            
            # Optimal is 10% of available liquidity
            optimal = liquidity * 0.1
            
            # Cap at reasonable amount
            optimal = min(optimal, 10000000)  # Max 10M
            
            return max(optimal, 100000)  # Min 100K
            
        except Exception:
            return 0
    
    def _estimate_slippage(self, amount: float, liquidity: float) -> float:
        """Estimate slippage based on amount and liquidity"""
        if liquidity <= 0:
            return 1.0
        
        ratio = amount / liquidity
        
        # Simple slippage model
        if ratio < 0.05:
            return 0.05
        elif ratio < 0.1:
            return 0.1
        elif ratio < 0.2:
            return 0.25
        else:
            return 0.5
    
    def _estimate_execution_time(self, entry_exchange: str, exit_exchange: str, amount: float) -> float:
        """Estimate execution time in milliseconds"""
        base_time = 100  # Base 100ms
        
        # Add time based on amount
        if amount > 1000000:
            base_time += 50
        
        # Exchange-specific time
        if entry_exchange != exit_exchange:
            base_time += 100  # Cross-exchange penalty
        
        return float(base_time)
    
    def _calculate_confidence(self, price_spread: float, liquidity: float, execution_time: float) -> float:
        """Calculate opportunity confidence score"""
        confidence = 0.5
        
        # Price spread factor (0-50%)
        confidence += min(0.3, price_spread / 100)
        
        # Liquidity factor (0-20%)
        if liquidity > 1000000:
            confidence += 0.2
        elif liquidity > 100000:
            confidence += 0.1
        
        # Execution time factor (0-10%)
        if execution_time < 500:
            confidence += 0.1
        
        return min(0.99, max(0.1, confidence))
    
    async def build_execution_route(self, opportunity: FlashLoanOpportunity) -> Optional[FlashLoanRoute]:
        """Build detailed execution route"""
        try:
            steps = [
                {
                    'step': 'borrow',
                    'provider': opportunity.provider.value,
                    'token': opportunity.loan_token,
                    'amount': opportunity.loan_amount,
                    'fee_percent': opportunity.flash_fee_percent,
                    'gas_estimate': 150000,  # Typical flash borrow cost
                },
                {
                    'step': 'swap_in',
                    'exchange': opportunity.entry_exchange,
                    'token_in': 'ETH',
                    'token_out': opportunity.loan_token,
                    'amount': opportunity.loan_amount,
                    'expected_price': opportunity.entry_price,
                    'gas_estimate': 200000,  # Swap gas cost
                },
                {
                    'step': 'swap_out',
                    'exchange': opportunity.exit_exchange,
                    'token_in': opportunity.loan_token,
                    'token_out': 'ETH',
                    'amount': opportunity.loan_amount,
                    'expected_price': opportunity.exit_price,
                    'gas_estimate': 200000,
                },
                {
                    'step': 'repay',
                    'provider': opportunity.provider.value,
                    'token': opportunity.loan_token,
                    'amount': opportunity.loan_amount,
                    'fee': opportunity.loan_amount * (opportunity.flash_fee_percent / 100),
                    'gas_estimate': 100000,
                },
            ]
            
            total_gas = sum(step.get('gas_estimate', 0) for step in steps)
            gas_cost_eth = total_gas * 0.000000001  # At 1 gwei (rough estimate)
            
            route = FlashLoanRoute(
                opportunity_id=opportunity.opportunity_id,
                steps=steps,
                total_gas_estimate=total_gas,
                total_fee=opportunity.loan_amount * (opportunity.flash_fee_percent / 100),
                net_profit=opportunity.estimated_profit_eth - (gas_cost_eth),
                safety_checks=[
                    'Verify liquidity available',
                    'Check flash fee',
                    'Validate slippage',
                    'Confirm gas price',
                    'Check for reentrancy',
                ],
            )
            
            return route
            
        except Exception as e:
            logger.error(f"Route building error: {e}")
            return None
    
    async def get_recent_opportunities(self, limit: int = 100) -> List[FlashLoanOpportunity]:
        """Get recent opportunities"""
        return list(self.opportunities)[-limit:]
    
    def get_detector_status(self) -> Dict[str, Any]:
        """Get detector status"""
        return {
            'opportunities_detected': len(self.opportunities),
            'executed_loans': len(self.executed_loans),
            'min_profit_threshold': self.min_profit_threshold_eth,
            'max_execution_time_ms': self.max_execution_time_ms,
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global instance
_detector: Optional[FlashLoanDetector] = None


def init_flash_loan_detector() -> FlashLoanDetector:
    """Initialize global detector"""
    global _detector
    _detector = FlashLoanDetector()
    return _detector


def get_detector() -> FlashLoanDetector:
    """Get global detector"""
    global _detector
    if not _detector:
        _detector = init_flash_loan_detector()
    return _detector
