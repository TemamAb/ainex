"""
AINEON Enterprise: Feature Engineering Module
Phase 3A: AI/ML Intelligence - Market Data Feature Preparation

Transforms raw market data into ML-ready features with technical indicators,
statistical aggregations, and cross-asset correlations.

Author: AINEON Chief Architect
Version: 1.0
Date: December 14, 2025
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator


# ============================================================================
# DATA MODELS
# ============================================================================

class OHLCV(BaseModel):
    """OHLCV candlestick data."""
    timestamp: datetime
    open: Decimal = Field(..., decimal_places=8)
    high: Decimal = Field(..., decimal_places=8)
    low: Decimal = Field(..., decimal_places=8)
    close: Decimal = Field(..., decimal_places=8)
    volume: Decimal = Field(..., decimal_places=18)


class TechnicalIndicators(BaseModel):
    """Computed technical indicators."""
    # Trend
    sma_20: Optional[Decimal] = None  # 20-period SMA
    sma_50: Optional[Decimal] = None  # 50-period SMA
    sma_200: Optional[Decimal] = None  # 200-period SMA
    ema_12: Optional[Decimal] = None  # 12-period EMA
    ema_26: Optional[Decimal] = None  # 26-period EMA
    
    # Momentum
    rsi_14: Optional[Decimal] = None  # 14-period RSI
    macd: Optional[Decimal] = None  # MACD line
    macd_signal: Optional[Decimal] = None  # Signal line
    macd_histogram: Optional[Decimal] = None  # MACD histogram
    
    # Volatility
    bollinger_high: Optional[Decimal] = None
    bollinger_low: Optional[Decimal] = None
    atr_14: Optional[Decimal] = None  # 14-period ATR
    
    # Volume
    obv: Optional[Decimal] = None  # On-Balance Volume
    ad_line: Optional[Decimal] = None  # Accumulation/Distribution


class FeatureVector(BaseModel):
    """ML-ready feature vector."""
    timestamp: datetime
    
    # Price features
    close_price: Decimal
    price_change_1h: Decimal  # % change
    price_change_24h: Decimal  # % change
    price_momentum_5: Decimal  # 5-period momentum
    price_momentum_20: Decimal  # 20-period momentum
    
    # Volatility features
    volatility_1h: Decimal
    volatility_24h: Decimal
    volatility_ratio: Decimal  # Current vol / 20-day avg
    
    # Volume features
    volume_current: Decimal
    volume_sma_20: Decimal
    volume_ratio: Decimal  # Current / 20-day average
    
    # Technical indicators
    rsi_14: Decimal  # Relative Strength Index
    macd_signal: Decimal  # MACD momentum
    sma_ratio: Decimal  # Close / 50-SMA
    
    # Liquidity features
    bid_ask_spread: Optional[Decimal] = None  # %
    liquidity_depth: Optional[Decimal] = None  # $ at 0.1% slippage
    
    # Cross-asset features
    correlation_eth_usdc: Optional[Decimal] = None
    correlation_eth_dai: Optional[Decimal] = None
    
    # Market regime
    market_regime: str  # "bull", "bear", "sideways"
    trend_strength: Decimal  # 0-1 strength indicator


class FeatureSet(BaseModel):
    """Collection of feature vectors for a single asset."""
    token: str
    features: List[FeatureVector]
    last_update: datetime
    feature_count: int


# ============================================================================
# FEATURE ENGINEERING ENGINE
# ============================================================================

class FeatureEngineer:
    """
    Transforms raw market data into ML-ready features.
    
    Processes:
    - Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
    - Momentum indicators
    - Volatility measures
    - Volume analysis
    - Cross-asset correlations
    - Market regime detection
    """
    
    def __init__(
        self,
        lookback_periods: int = 200,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize feature engineer.
        
        Args:
            lookback_periods: Historical periods to retain
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.lookback_periods = lookback_periods
        
        # Cache for historical data
        self._ohlcv_cache: Dict[str, List[OHLCV]] = {}
        self._feature_cache: Dict[str, List[FeatureVector]] = {}
        self._correlation_matrix: Optional[pd.DataFrame] = None
        
        self.logger.info("✅ FeatureEngineer initialized")
    
    # ========================================================================
    # TECHNICAL INDICATORS
    # ========================================================================
    
    def _sma(self, values: List[Decimal], period: int) -> Optional[Decimal]:
        """Calculate Simple Moving Average."""
        if len(values) < period:
            return None
        return sum(values[-period:]) / period
    
    def _ema(self, values: List[Decimal], period: int) -> Optional[Decimal]:
        """Calculate Exponential Moving Average."""
        if len(values) < period:
            return None
        
        multiplier = Decimal(2) / (period + 1)
        ema = values[0]
        
        for value in values[1:]:
            ema = value * multiplier + ema * (1 - multiplier)
        
        return ema
    
    def _rsi(self, closes: List[Decimal], period: int = 14) -> Optional[Decimal]:
        """Calculate Relative Strength Index."""
        if len(closes) < period + 1:
            return None
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [d if d > 0 else Decimal(0) for d in deltas]
        losses = [abs(d) if d < 0 else Decimal(0) for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return Decimal(100) if avg_gain > 0 else Decimal(50)
        
        rs = avg_gain / avg_loss
        rsi = Decimal(100) - (Decimal(100) / (1 + rs))
        
        return rsi
    
    def _macd(
        self,
        closes: List[Decimal],
    ) -> Tuple[Optional[Decimal], Optional[Decimal], Optional[Decimal]]:
        """Calculate MACD, Signal line, and Histogram."""
        if len(closes) < 26:
            return None, None, None
        
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)
        
        if ema_12 is None or ema_26 is None:
            return None, None, None
        
        macd = ema_12 - ema_26
        
        # Signal is 9-period EMA of MACD
        # (simplified - would need full MACD history for exact calculation)
        signal = macd * Decimal("0.7")  # Placeholder
        histogram = macd - signal
        
        return macd, signal, histogram
    
    def _atr(
        self,
        ohlcv_data: List[OHLCV],
        period: int = 14,
    ) -> Optional[Decimal]:
        """Calculate Average True Range."""
        if len(ohlcv_data) < period:
            return None
        
        true_ranges = []
        for i in range(1, len(ohlcv_data)):
            curr = ohlcv_data[i]
            prev = ohlcv_data[i-1]
            
            tr1 = curr.high - curr.low
            tr2 = abs(curr.high - prev.close)
            tr3 = abs(curr.low - prev.close)
            
            tr = max(tr1, tr2, tr3)
            true_ranges.append(tr)
        
        atr = sum(true_ranges[-period:]) / period
        return atr
    
    def _bollinger_bands(
        self,
        closes: List[Decimal],
        period: int = 20,
        std_dev: Decimal = Decimal("2"),
    ) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """Calculate Bollinger Bands."""
        if len(closes) < period:
            return None, None
        
        sma = self._sma(closes, period)
        if sma is None:
            return None, None
        
        # Calculate standard deviation
        recent = closes[-period:]
        variance = sum((x - sma) ** 2 for x in recent) / period
        std = variance ** Decimal("0.5")
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, lower
    
    # ========================================================================
    # FEATURE CALCULATION
    # ========================================================================
    
    def calculate_technical_indicators(
        self,
        ohlcv_data: List[OHLCV],
    ) -> TechnicalIndicators:
        """Calculate all technical indicators from OHLCV data."""
        closes = [candle.close for candle in ohlcv_data]
        highs = [candle.high for candle in ohlcv_data]
        lows = [candle.low for candle in ohlcv_data]
        volumes = [candle.volume for candle in ohlcv_data]
        
        return TechnicalIndicators(
            sma_20=self._sma(closes, 20),
            sma_50=self._sma(closes, 50),
            sma_200=self._sma(closes, 200),
            ema_12=self._ema(closes, 12),
            ema_26=self._ema(closes, 26),
            rsi_14=self._rsi(closes, 14),
            macd=self._macd(closes)[0],
            macd_signal=self._macd(closes)[1],
            macd_histogram=self._macd(closes)[2],
            atr_14=self._atr(ohlcv_data, 14),
        )
    
    def calculate_price_momentum(
        self,
        closes: List[Decimal],
        period: int,
    ) -> Decimal:
        """Calculate price momentum (% change over period)."""
        if len(closes) < period:
            return Decimal("0")
        
        current = closes[-1]
        previous = closes[-period-1]
        
        if previous == 0:
            return Decimal("0")
        
        return ((current - previous) / previous) * Decimal("100")
    
    def calculate_volatility(
        self,
        closes: List[Decimal],
        period: int,
    ) -> Decimal:
        """Calculate volatility (standard deviation of returns)."""
        if len(closes) < period:
            return Decimal("0")
        
        recent = closes[-period:]
        returns = [
            (recent[i] - recent[i-1]) / recent[i-1] if recent[i-1] > 0 else Decimal("0")
            for i in range(1, len(recent))
        ]
        
        if not returns:
            return Decimal("0")
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** Decimal("0.5")
        
        return volatility * Decimal("100")  # Convert to percentage
    
    def calculate_volume_features(
        self,
        ohlcv_data: List[OHLCV],
        period: int = 20,
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate volume features.
        
        Returns:
            (current_volume, sma_volume)
        """
        if not ohlcv_data:
            return Decimal("0"), Decimal("0")
        
        current_volume = ohlcv_data[-1].volume
        
        if len(ohlcv_data) < period:
            sma_volume = sum(c.volume for c in ohlcv_data) / len(ohlcv_data)
        else:
            volumes = [c.volume for c in ohlcv_data[-period:]]
            sma_volume = sum(volumes) / period
        
        return current_volume, sma_volume
    
    def detect_market_regime(
        self,
        sma_20: Optional[Decimal],
        sma_50: Optional[Decimal],
        sma_200: Optional[Decimal],
        close_price: Decimal,
    ) -> Tuple[str, Decimal]:
        """
        Detect market regime (bull, bear, sideways).
        
        Returns:
            (regime, trend_strength)
        """
        if sma_20 is None or sma_50 is None:
            return "sideways", Decimal("0.5")
        
        # Simple regime detection
        if sma_20 > sma_50 > sma_200:
            regime = "bull"
            # Trend strength = how far above 200-SMA
            if sma_200 > 0:
                strength = min(
                    Decimal("1"),
                    (close_price - sma_200) / sma_200
                )
            else:
                strength = Decimal("0.5")
        elif sma_20 < sma_50 < sma_200:
            regime = "bear"
            if sma_200 > 0:
                strength = min(
                    Decimal("1"),
                    (sma_200 - close_price) / sma_200
                )
            else:
                strength = Decimal("0.5")
        else:
            regime = "sideways"
            strength = Decimal("0.5")
        
        return regime, strength
    
    # ========================================================================
    # FEATURE VECTOR GENERATION
    # ========================================================================
    
    def create_feature_vector(
        self,
        token: str,
        ohlcv_data: List[OHLCV],
        bid_ask_spread: Optional[Decimal] = None,
        liquidity_depth: Optional[Decimal] = None,
    ) -> Optional[FeatureVector]:
        """
        Create ML-ready feature vector from OHLCV data.
        
        Args:
            token: Token identifier
            ohlcv_data: Historical OHLCV data (chronologically ordered)
            bid_ask_spread: Current bid-ask spread %
            liquidity_depth: Liquidity at 0.1% slippage
            
        Returns:
            Feature vector or None if insufficient data
        """
        if len(ohlcv_data) < 50:
            self.logger.warning(f"⚠️  Insufficient data for {token}: need 50+, have {len(ohlcv_data)}")
            return None
        
        # Extract price data
        closes = [c.close for c in ohlcv_data]
        current_price = closes[-1]
        
        # Calculate technical indicators
        indicators = self.calculate_technical_indicators(ohlcv_data)
        
        # Price momentum
        momentum_5 = self.calculate_price_momentum(closes, 5)
        momentum_20 = self.calculate_price_momentum(closes, 20)
        change_1h = self.calculate_price_momentum(closes[-12:], 1) if len(closes) >= 12 else Decimal("0")
        change_24h = self.calculate_price_momentum(closes, 24)
        
        # Volatility
        vol_1h = self.calculate_volatility(closes[-12:], 12) if len(closes) >= 12 else Decimal("0")
        vol_24h = self.calculate_volatility(closes[-24:], 24) if len(closes) >= 24 else Decimal("0")
        vol_20d = self.calculate_volatility(closes, 20)
        vol_ratio = vol_1h / vol_20d if vol_20d > 0 else Decimal("1")
        
        # Volume features
        current_vol, sma_vol = self.calculate_volume_features(ohlcv_data, 20)
        vol_ratio = current_vol / sma_vol if sma_vol > 0 else Decimal("1")
        
        # Market regime
        regime, trend_strength = self.detect_market_regime(
            indicators.sma_20,
            indicators.sma_50,
            indicators.sma_200,
            current_price,
        )
        
        # SMA ratio
        sma_ratio = Decimal("1")
        if indicators.sma_50 and indicators.sma_50 > 0:
            sma_ratio = current_price / indicators.sma_50
        
        # Create feature vector
        return FeatureVector(
            timestamp=datetime.utcnow(),
            close_price=current_price,
            price_change_1h=change_1h,
            price_change_24h=change_24h,
            price_momentum_5=momentum_5,
            price_momentum_20=momentum_20,
            volatility_1h=vol_1h,
            volatility_24h=vol_24h,
            volatility_ratio=vol_ratio,
            volume_current=current_vol,
            volume_sma_20=sma_vol,
            volume_ratio=vol_ratio,
            rsi_14=indicators.rsi_14 or Decimal("50"),
            macd_signal=indicators.macd_signal or Decimal("0"),
            sma_ratio=sma_ratio,
            bid_ask_spread=bid_ask_spread,
            liquidity_depth=liquidity_depth,
            market_regime=regime,
            trend_strength=trend_strength,
        )
    
    def create_feature_set(
        self,
        token: str,
        ohlcv_data: List[OHLCV],
        **kwargs,
    ) -> Optional[FeatureSet]:
        """
        Create feature set for a token.
        
        Args:
            token: Token identifier
            ohlcv_data: Historical OHLCV data
            **kwargs: Additional parameters (spread, liquidity, etc.)
            
        Returns:
            Feature set or None if creation failed
        """
        # Keep only lookback_periods
        if len(ohlcv_data) > self.lookback_periods:
            ohlcv_data = ohlcv_data[-self.lookback_periods:]
        
        # Create feature vector
        feature_vector = self.create_feature_vector(token, ohlcv_data, **kwargs)
        
        if feature_vector is None:
            return None
        
        # Store in cache
        if token not in self._feature_cache:
            self._feature_cache[token] = []
        
        self._feature_cache[token].append(feature_vector)
        
        # Keep only recent features
        if len(self._feature_cache[token]) > self.lookback_periods:
            self._feature_cache[token] = self._feature_cache[token][-self.lookback_periods:]
        
        return FeatureSet(
            token=token,
            features=[feature_vector],
            last_update=datetime.utcnow(),
            feature_count=1,
        )
    
    # ========================================================================
    # CROSS-ASSET FEATURES
    # ========================================================================
    
    def calculate_correlation(
        self,
        token_1_prices: List[Decimal],
        token_2_prices: List[Decimal],
        period: int = 20,
    ) -> Optional[Decimal]:
        """
        Calculate correlation between two token price series.
        
        Args:
            token_1_prices: Token 1 prices
            token_2_prices: Token 2 prices
            period: Lookback period
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(token_1_prices) < period or len(token_2_prices) < period:
            return None
        
        recent_1 = token_1_prices[-period:]
        recent_2 = token_2_prices[-period:]
        
        # Calculate returns
        returns_1 = [
            (recent_1[i] - recent_1[i-1]) / recent_1[i-1] if recent_1[i-1] > 0 else Decimal("0")
            for i in range(1, len(recent_1))
        ]
        returns_2 = [
            (recent_2[i] - recent_2[i-1]) / recent_2[i-1] if recent_2[i-1] > 0 else Decimal("0")
            for i in range(1, len(recent_2))
        ]
        
        if not returns_1 or not returns_2:
            return None
        
        # Calculate correlation
        mean_1 = sum(returns_1) / len(returns_1)
        mean_2 = sum(returns_2) / len(returns_2)
        
        covariance = sum(
            (returns_1[i] - mean_1) * (returns_2[i] - mean_2)
            for i in range(len(returns_1))
        ) / len(returns_1)
        
        var_1 = sum((r - mean_1) ** 2 for r in returns_1) / len(returns_1)
        var_2 = sum((r - mean_2) ** 2 for r in returns_2) / len(returns_2)
        
        if var_1 == 0 or var_2 == 0:
            return None
        
        correlation = covariance / (var_1 ** Decimal("0.5") * var_2 ** Decimal("0.5"))
        
        return min(Decimal("1"), max(Decimal("-1"), correlation))
    
    # ========================================================================
    # CACHING & QUERYING
    # ========================================================================
    
    def get_feature_vector(self, token: str) -> Optional[FeatureVector]:
        """Get latest feature vector for a token."""
        features = self._feature_cache.get(token, [])
        return features[-1] if features else None
    
    def get_all_feature_vectors(self, token: str) -> List[FeatureVector]:
        """Get all cached feature vectors for a token."""
        return self._feature_cache.get(token, [])
    
    def clear_cache(self):
        """Clear all cached features."""
        self._feature_cache.clear()
        self.logger.info("🗑️  Feature cache cleared")


# ============================================================================
# INITIALIZATION
# ============================================================================

def create_feature_engineer() -> FeatureEngineer:
    """Factory function to create feature engineer."""
    logger = logging.getLogger("feature_engineering")
    return FeatureEngineer(logger=logger)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    engineer = create_feature_engineer()
    
    # Example: Create sample OHLCV data
    now = datetime.utcnow()
    ohlcv_data = [
        OHLCV(
            timestamp=now - timedelta(hours=i),
            open=Decimal("1800"),
            high=Decimal("1850"),
            low=Decimal("1790"),
            close=Decimal("1820"),
            volume=Decimal("1000"),
        )
        for i in range(100)
    ]
    
    # Calculate features
    feature_set = engineer.create_feature_set(
        token="ETH",
        ohlcv_data=ohlcv_data,
    )
    
    if feature_set:
        print(f"✅ Feature set created for {feature_set.token}")
        print(feature_set.features[-1])
    else:
        print("❌ Failed to create feature set")
