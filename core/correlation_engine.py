"""
Correlation Engine - Token & Cross-DEX Correlation Analysis
Tracks token price correlations and cross-market dependencies
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import statistics
import math

logger = logging.getLogger(__name__)


@dataclass
class PricePoint:
    """A single price data point"""
    token: str
    price: float
    timestamp: datetime
    exchange: str
    source: str


@dataclass
class CorrelationMatrix:
    """Correlation matrix between tokens"""
    timestamp: datetime
    correlations: Dict[str, Dict[str, float]]  # token1 -> token2 -> correlation
    confidence_scores: Dict[str, float]  # token -> confidence
    period_hours: int = 24
    
    def get_correlation(self, token1: str, token2: str) -> Optional[float]:
        """Get correlation between two tokens"""
        if token1 not in self.correlations:
            return None
        return self.correlations[token1].get(token2)
    
    def is_correlated(self, token1: str, token2: str, threshold: float = 0.7) -> bool:
        """Check if tokens are correlated above threshold"""
        corr = self.get_correlation(token1, token2)
        return corr is not None and abs(corr) >= threshold


@dataclass
class CorrelationBreakdown:
    """Detects when historical correlations break"""
    tokens: List[str]
    expected_correlation: float
    actual_correlation: float
    deviation_std: float
    severity: str  # low, medium, high
    timestamp: datetime
    reasoning: str


class CorrelationEngine:
    """Analyzes token and cross-DEX correlations"""
    
    def __init__(self):
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.correlation_cache: Dict[str, CorrelationMatrix] = {}
        self.correlation_lookback_hours = 24
        self.min_data_points = 20
        self.breakdown_alerts: deque = deque(maxlen=1000)
        self.historical_correlations: Dict[str, float] = {}  # For detecting breakdowns
    
    async def add_price_point(self, price_point: PricePoint) -> bool:
        """Add price data point"""
        try:
            key = f"{price_point.token}:{price_point.exchange}"
            self.price_history[key].append(price_point)
            logger.debug(f"Added price point: {key} @ {price_point.price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add price point: {e}")
            return False
    
    async def calculate_correlations(self, tokens: List[str],
                                    exchange: Optional[str] = None) -> Optional[CorrelationMatrix]:
        """Calculate correlations between tokens"""
        try:
            # Get price histories
            price_series = {}
            
            for token in tokens:
                if exchange:
                    key = f"{token}:{exchange}"
                else:
                    # Try to find any exchange
                    matching = [k for k in self.price_history.keys() if k.startswith(f"{token}:")]
                    if not matching:
                        logger.warning(f"No price history for {token}")
                        continue
                    key = matching[0]
                
                points = list(self.price_history[key])
                if len(points) < self.min_data_points:
                    logger.warning(f"Insufficient history for {token}")
                    continue
                
                # Get recent points within lookback window
                cutoff = datetime.utcnow() - timedelta(hours=self.correlation_lookback_hours)
                recent_points = [p for p in points if p.timestamp >= cutoff]
                
                if len(recent_points) < self.min_data_points:
                    continue
                
                # Normalize prices to returns
                prices = [p.price for p in recent_points]
                returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                          for i in range(1, len(prices))]
                
                price_series[token] = returns
            
            if len(price_series) < 2:
                logger.warning("Need at least 2 tokens to calculate correlation")
                return None
            
            # Calculate correlation matrix
            correlations = {}
            confidence_scores = {}
            
            for token1 in price_series:
                correlations[token1] = {}
                
                for token2 in price_series:
                    if token1 == token2:
                        correlations[token1][token2] = 1.0
                    else:
                        corr = self._pearson_correlation(price_series[token1], 
                                                        price_series[token2])
                        correlations[token1][token2] = corr
                
                # Confidence based on data quality
                confidence = min(1.0, len(price_series[token1]) / 100)
                confidence_scores[token1] = confidence
            
            matrix = CorrelationMatrix(
                timestamp=datetime.utcnow(),
                correlations=correlations,
                confidence_scores=confidence_scores,
                period_hours=self.correlation_lookback_hours,
            )
            
            # Cache
            cache_key = f"{'_'.join(sorted(tokens))}:{exchange}"
            self.correlation_cache[cache_key] = matrix
            
            logger.info(f"Calculated correlations for {len(tokens)} tokens")
            return matrix
            
        except Exception as e:
            logger.error(f"Correlation calculation error: {e}")
            return None
    
    def _pearson_correlation(self, series1: List[float], series2: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        try:
            if len(series1) != len(series2) or len(series1) < 2:
                return 0.0
            
            mean1 = statistics.mean(series1)
            mean2 = statistics.mean(series2)
            
            numerator = sum((x - mean1) * (y - mean2) for x, y in zip(series1, series2))
            
            std1 = statistics.stdev(series1) if len(set(series1)) > 1 else 0
            std2 = statistics.stdev(series2) if len(set(series2)) > 1 else 0
            
            if std1 == 0 or std2 == 0:
                return 0.0
            
            denominator = std1 * std2 * len(series1)
            
            correlation = numerator / denominator if denominator > 0 else 0
            
            return max(-1.0, min(1.0, correlation))
            
        except Exception:
            return 0.0
    
    async def detect_correlation_breakdown(self, token1: str, token2: str,
                                          expected_correlation: Optional[float] = None) -> Optional[CorrelationBreakdown]:
        """Detect when correlation breaks historical pattern"""
        try:
            # Get current correlation
            current_corr = await self._get_current_correlation(token1, token2)
            if current_corr is None:
                return None
            
            # Get expected (historical)
            hist_key = f"{token1}_{token2}"
            expected = expected_correlation or self.historical_correlations.get(hist_key, current_corr)
            
            # Calculate deviation
            deviation = abs(current_corr - expected)
            
            # Estimate standard deviation of correlations
            std_dev = 0.1  # Typical stdev for correlations
            deviation_in_stds = deviation / std_dev if std_dev > 0 else 0
            
            # Determine severity
            if deviation_in_stds > 2.0:
                severity = "high"
            elif deviation_in_stds > 1.5:
                severity = "medium"
            else:
                severity = "low"
            
            breakdown = CorrelationBreakdown(
                tokens=[token1, token2],
                expected_correlation=expected,
                actual_correlation=current_corr,
                deviation_std=deviation_in_stds,
                severity=severity,
                timestamp=datetime.utcnow(),
                reasoning=f"Expected {expected:.3f}, got {current_corr:.3f} ({deviation_in_stds:.2f} std deviations)",
            )
            
            # Alert if significant
            if severity in ["medium", "high"]:
                self.breakdown_alerts.append(breakdown)
                logger.warning(f"Correlation breakdown detected: {breakdown.reasoning}")
            
            # Update historical if current is more stable
            if deviation_in_stds < 0.5:
                self.historical_correlations[hist_key] = current_corr
            
            return breakdown
            
        except Exception as e:
            logger.error(f"Breakdown detection error: {e}")
            return None
    
    async def _get_current_correlation(self, token1: str, token2: str) -> Optional[float]:
        """Get current correlation between two tokens"""
        matrix = await self.calculate_correlations([token1, token2])
        if matrix:
            return matrix.get_correlation(token1, token2)
        return None
    
    async def get_cross_dex_correlation(self, token: str,
                                       exchanges: List[str]) -> Optional[Dict]:
        """Get correlation of same token across different exchanges"""
        try:
            price_series = {}
            
            for exchange in exchanges:
                key = f"{token}:{exchange}"
                points = list(self.price_history[key])
                
                if len(points) < self.min_data_points:
                    continue
                
                prices = [p.price for p in points]
                returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                          for i in range(1, len(prices))]
                
                price_series[exchange] = returns
            
            if len(price_series) < 2:
                return None
            
            # Calculate correlations
            correlations = {}
            for ex1 in price_series:
                correlations[ex1] = {}
                for ex2 in price_series:
                    if ex1 != ex2:
                        corr = self._pearson_correlation(price_series[ex1], price_series[ex2])
                        correlations[ex1][ex2] = corr
            
            return {
                'token': token,
                'exchanges': exchanges,
                'cross_dex_correlations': correlations,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Cross-DEX correlation error: {e}")
            return None
    
    async def get_sector_correlation(self, tokens: List[str]) -> Optional[Dict]:
        """Get overall sector correlation health"""
        try:
            matrix = await self.calculate_correlations(tokens)
            if not matrix:
                return None
            
            # Calculate average correlation
            all_correlations = []
            for token1 in matrix.correlations:
                for token2 in matrix.correlations[token1]:
                    if token1 != token2:
                        all_correlations.append(matrix.correlations[token1][token2])
            
            if not all_correlations:
                return None
            
            avg_corr = statistics.mean(all_correlations)
            std_corr = statistics.stdev(all_correlations) if len(all_correlations) > 1 else 0
            
            return {
                'tokens': tokens,
                'average_correlation': avg_corr,
                'correlation_std': std_corr,
                'breakdown_alerts': len(self.breakdown_alerts),
                'health': 'healthy' if abs(avg_corr) < 0.5 else 'correlated' if avg_corr > 0.7 else 'mixed',
                'timestamp': datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Sector correlation error: {e}")
            return None
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'tokens_tracked': len(self.price_history),
            'breakdown_alerts': len(self.breakdown_alerts),
            'cached_matrices': len(self.correlation_cache),
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global instance
_engine: Optional[CorrelationEngine] = None


def init_correlation_engine() -> CorrelationEngine:
    """Initialize global engine"""
    global _engine
    _engine = CorrelationEngine()
    return _engine


def get_engine() -> CorrelationEngine:
    """Get global engine"""
    global _engine
    if not _engine:
        _engine = init_correlation_engine()
    return _engine
