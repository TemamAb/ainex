"""
Volume Predictor - ML-Based Trading Volume Forecast
Predicts future trading volumes and volatility using historical patterns
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import statistics
import math

logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """Time frames for prediction"""
    ONE_MINUTE = 60
    FIVE_MINUTES = 300
    FIFTEEN_MINUTES = 900
    ONE_HOUR = 3600
    FOUR_HOURS = 14400
    ONE_DAY = 86400


@dataclass
class VolumeCandle:
    """Volume data for a time period"""
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    token_pair: str
    exchange: str


@dataclass
class VolumePrediction:
    """Volume prediction"""
    token_pair: str
    prediction_time: datetime
    forecast_period: TimeFrame
    predicted_volume: float
    predicted_volatility: float
    confidence: float
    factors: Dict[str, float]  # Contributing factors
    reasoning: str


class VolumePredictor:
    """Predicts trading volume using ML patterns"""
    
    def __init__(self):
        self.volume_history: Dict[str, deque] = {}  # token_pair -> candles
        self.volatility_history: Dict[str, deque] = {}
        self.prediction_cache: Dict[str, VolumePrediction] = {}
        self.cache_ttl_seconds = 300
        self.min_history_periods = 20  # Need 20 periods to predict
    
    async def add_volume_data(self, candle: VolumeCandle) -> bool:
        """Add volume data point"""
        try:
            key = f"{candle.token_pair}:{candle.exchange}"
            
            if key not in self.volume_history:
                self.volume_history[key] = deque(maxlen=5000)
                self.volatility_history[key] = deque(maxlen=5000)
            
            # Store candle
            self.volume_history[key].append(candle)
            
            # Calculate volatility
            volatility = self._calculate_volatility(candle)
            self.volatility_history[key].append(volatility)
            
            logger.debug(f"Added volume data: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add volume data: {e}")
            return False
    
    def _calculate_volatility(self, candle: VolumeCandle) -> float:
        """Calculate volatility from candle"""
        try:
            if candle.close_price == 0:
                return 0.0
            
            # High-low range as percentage of close
            range_pct = (candle.high_price - candle.low_price) / candle.close_price
            return range_pct * 100  # As percentage
            
        except Exception:
            return 0.0
    
    async def predict_volume(self, token_pair: str, exchange: str,
                            timeframe: TimeFrame = TimeFrame.FIFTEEN_MINUTES) -> Optional[VolumePrediction]:
        """Predict next period volume"""
        try:
            key = f"{token_pair}:{exchange}"
            
            # Check cache
            cache_key = f"{key}:{timeframe.value}"
            if cache_key in self.prediction_cache:
                cached = self.prediction_cache[cache_key]
                age = (datetime.utcnow() - cached.prediction_time).total_seconds()
                if age < self.cache_ttl_seconds:
                    return cached
            
            # Get history
            if key not in self.volume_history:
                logger.warning(f"No history for {key}")
                return None
            
            history = list(self.volume_history[key])
            if len(history) < self.min_history_periods:
                logger.warning(f"Insufficient history for {key}")
                return None
            
            # Extract features
            volumes = [c.volume for c in history[-self.min_history_periods:]]
            volatilities = list(self.volatility_history[key])[-self.min_history_periods:]
            
            # Calculate features
            avg_volume = statistics.mean(volumes)
            recent_volume = volumes[-1]
            volume_trend = self._calculate_trend(volumes)
            vol_acceleration = self._calculate_acceleration(volumes)
            
            # Predict
            predicted_volume = await self._predict_with_ma(volumes, volatilities)
            predicted_volatility = await self._predict_volatility(volatilities)
            
            # Confidence scoring
            confidence = self._calculate_confidence(volumes, volatilities)
            
            factors = {
                'trend': volume_trend,
                'acceleration': vol_acceleration,
                'recent_ratio': recent_volume / max(avg_volume, 1),
                'historical_volatility': statistics.stdev(volatilities) if len(volatilities) > 1 else 0,
            }
            
            prediction = VolumePrediction(
                token_pair=token_pair,
                prediction_time=datetime.utcnow(),
                forecast_period=timeframe,
                predicted_volume=predicted_volume,
                predicted_volatility=predicted_volatility,
                confidence=confidence,
                factors=factors,
                reasoning=f"Volume trend: {volume_trend:.2f}%, Acceleration: {vol_acceleration:.2f}%",
            )
            
            # Cache
            self.prediction_cache[cache_key] = prediction
            
            logger.info(f"Predicted volume for {key}: {predicted_volume:.2f} (confidence: {confidence:.1%})")
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def _calculate_trend(self, volumes: List[float]) -> float:
        """Calculate volume trend as percentage change"""
        if len(volumes) < 2:
            return 0.0
        
        try:
            old_avg = statistics.mean(volumes[-10:-5]) if len(volumes) >= 10 else statistics.mean(volumes[:len(volumes)//2])
            new_avg = statistics.mean(volumes[-5:])
            
            if old_avg == 0:
                return 0.0
            
            trend = (new_avg - old_avg) / old_avg * 100
            return trend
            
        except Exception:
            return 0.0
    
    def _calculate_acceleration(self, volumes: List[float]) -> float:
        """Calculate volume acceleration"""
        try:
            if len(volumes) < 3:
                return 0.0
            
            # Rate of change of trend
            mid_point = len(volumes) // 2
            early_trend = self._calculate_trend(volumes[:mid_point + 1])
            late_trend = self._calculate_trend(volumes[mid_point:])
            
            acceleration = late_trend - early_trend
            return acceleration
            
        except Exception:
            return 0.0
    
    async def _predict_with_ma(self, volumes: List[float], volatilities: List[float]) -> float:
        """Predict volume using moving average + volatility adjustment"""
        try:
            # Weighted moving average (recent data weighted more)
            weights = list(range(1, len(volumes) + 1))
            weighted_sum = sum(v * w for v, w in zip(volumes, weights))
            weight_sum = sum(weights)
            wma = weighted_sum / weight_sum if weight_sum > 0 else 0
            
            # Adjust for recent volatility
            recent_vol = statistics.mean(volatilities[-5:]) if len(volatilities) >= 5 else statistics.mean(volatilities)
            vol_multiplier = 1.0 + (recent_vol / 100)  # Higher vol = higher volume expected
            
            predicted = wma * vol_multiplier
            
            # Sanity check: don't predict more than 5x or less than 0.2x
            predicted = max(predicted, wma * 0.2)
            predicted = min(predicted, wma * 5.0)
            
            return predicted
            
        except Exception:
            return statistics.mean(volumes) if volumes else 0.0
    
    async def _predict_volatility(self, volatilities: List[float]) -> float:
        """Predict next period volatility"""
        try:
            if not volatilities:
                return 1.0
            
            # Use exponential smoothing
            alpha = 0.3
            forecast = volatilities[-1]
            
            for vol in reversed(volatilities[-5:]):
                forecast = alpha * vol + (1 - alpha) * forecast
            
            return forecast
            
        except Exception:
            return statistics.mean(volatilities) if volatilities else 1.0
    
    def _calculate_confidence(self, volumes: List[float], volatilities: List[float]) -> float:
        """Calculate prediction confidence"""
        try:
            # Factors that increase confidence
            stability = 1.0 / (1.0 + statistics.stdev(volumes) / statistics.mean(volumes)) if statistics.mean(volumes) > 0 else 0
            history_quality = min(1.0, len(volumes) / 100)  # More history = higher quality
            
            # Combine
            confidence = (stability * 0.7) + (history_quality * 0.3)
            
            return max(0.1, min(0.95, confidence))  # Between 10% and 95%
            
        except Exception:
            return 0.5
    
    async def get_volume_pattern(self, token_pair: str, exchange: str) -> Optional[Dict]:
        """Get volume patterns (intraday, weekly, etc)"""
        try:
            key = f"{token_pair}:{exchange}"
            history = self.volume_history.get(key)
            
            if not history or len(history) < 100:
                return None
            
            # Group by hour of day
            hourly_volumes = {}
            for candle in history:
                hour = candle.timestamp.hour
                if hour not in hourly_volumes:
                    hourly_volumes[hour] = []
                hourly_volumes[hour].append(candle.volume)
            
            hourly_patterns = {
                hour: {
                    'avg_volume': statistics.mean(vols),
                    'max_volume': max(vols),
                    'min_volume': min(vols),
                    'count': len(vols),
                }
                for hour, vols in hourly_volumes.items()
            }
            
            return {
                'token_pair': token_pair,
                'exchange': exchange,
                'hourly_patterns': hourly_patterns,
                'overall_avg_volume': statistics.mean([c.volume for c in history]),
                'overall_volatility': statistics.mean(list(self.volatility_history[key])),
                'timestamp': datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Pattern analysis error: {e}")
            return None
    
    def get_predictor_status(self) -> Dict[str, Any]:
        """Get predictor status"""
        return {
            'pairs_tracked': len(self.volume_history),
            'cached_predictions': len(self.prediction_cache),
            'timestamp': datetime.utcnow().isoformat(),
        }


# Global instance
_predictor: Optional[VolumePredictor] = None


def init_volume_predictor() -> VolumePredictor:
    """Initialize global predictor"""
    global _predictor
    _predictor = VolumePredictor()
    return _predictor


def get_predictor() -> VolumePredictor:
    """Get global predictor"""
    global _predictor
    if not _predictor:
        _predictor = init_volume_predictor()
    return _predictor
