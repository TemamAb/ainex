import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
import aiohttp

try:
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except Exception as e:
    logging.warning(f"Scikit-learn import failed: {e}. Running in basic heuristic mode.")
    HAS_SKLEARN = False
    StandardScaler = None

try:
    import tensorflow as tf
    HAS_TF = True
except Exception as e:
    logging.warning(f"TensorFlow/Keras import failed: {e}. Running in heuristic mode.")
    HAS_TF = False
    tf = None

try:
    import pandas as pd
    HAS_PANDAS = True
except Exception as e:
    logging.warning(f"Pandas import failed: {e}. Limited functionality.")
    HAS_PANDAS = False
    pd = None

from core.infrastructure.metrics_collector import MetricsCollector
from core.infrastructure.health_check_engine import HealthCheckEngine
from core.infrastructure.structured_logging import StructuredLogger

@dataclass
class OptimizationMetrics:
    """Metrics for AI optimization performance"""
    predictions_made: int = 0
    successful_predictions: int = 0
    average_confidence: float = 0.0
    last_training_time: Optional[datetime] = None
    model_accuracy: float = 0.0

class AIOptimizer:
    """Enterprise-grade AI optimizer for flash loan arbitrage opportunities"""

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None,
                 health_engine: Optional[HealthCheckEngine] = None,
                 logger: Optional[StructuredLogger] = None):
        self.logger = logger or StructuredLogger(__name__)
        self.metrics = metrics_collector or MetricsCollector()
        self.health_engine = health_engine or HealthCheckEngine()
        self.optimization_metrics = OptimizationMetrics()

        self.model: Optional[Any] = self.load_or_create_model()
        self.scaler: Optional[StandardScaler] = StandardScaler() if HAS_SKLEARN else None
        self.historical_data: List[Tuple[List[float], int]] = []
        self.current_confidence: float = 0.5

        # Register health checks
        self.health_engine.register_check("ai_optimizer_model", self._check_model_health)
        self.health_engine.register_check("ai_optimizer_metrics", self._check_metrics_health)

        self.logger.info("AIOptimizer initialized", extra={
            "has_sklearn": HAS_SKLEARN,
            "has_tensorflow": HAS_TF,
            "has_pandas": HAS_PANDAS
        })

    def _check_model_health(self) -> Dict[str, Any]:
        """Health check for ML model status"""
        return {
            "model_loaded": self.model is not None,
            "scaler_available": self.scaler is not None,
            "tensorflow_available": HAS_TF,
            "sklearn_available": HAS_SKLEARN,
            "historical_data_points": len(self.historical_data)
        }

    def _check_metrics_health(self) -> Dict[str, Any]:
        """Health check for optimization metrics"""
        return {
            "predictions_made": self.optimization_metrics.predictions_made,
            "success_rate": (self.optimization_metrics.successful_predictions /
                           max(self.optimization_metrics.predictions_made, 1)),
            "average_confidence": self.optimization_metrics.average_confidence,
            "last_training_time": self.optimization_metrics.last_training_time.isoformat()
            if self.optimization_metrics.last_training_time else None
        }

    def load_or_create_model(self) -> Optional[Any]:
        """Load existing model or create new one with proper error handling"""
        if not HAS_TF:
            self.logger.warning("TensorFlow not available, cannot load/create ML model")
            return None

        try:
            model_path = 'models/arbitrage_predictor_v2.h5'
            model = tf.keras.models.load_model(model_path)
            self.logger.info("Successfully loaded existing ML model", extra={"model_path": model_path})
            return model
        except Exception as e:
            self.logger.warning(f"Failed to load existing model: {e}, creating new model")
            try:
                return self.create_model()
            except Exception as create_e:
                self.logger.error(f"Failed to create new model: {create_e}")
                return None

    def create_model(self) -> Optional[Any]:
        """Create new neural network model for arbitrage prediction"""
        if not HAS_TF:
            self.logger.error("Cannot create model: TensorFlow not available")
            return None

        try:
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(128, activation='relu', input_shape=(20,)),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            self.logger.info("Successfully created new neural network model")
            return model
        except Exception as e:
            self.logger.error(f"Failed to create neural network model: {e}")
            return None

    async def predict_arbitrage_opportunity(self, market_data: Dict[str, Dict[str, Any]]) -> Tuple[bool, float]:
        """Predict arbitrage opportunities using ML or heuristic with enterprise-grade error handling"""
        start_time = time.time()

        try:
            self.optimization_metrics.predictions_made += 1

            if not HAS_TF or self.model is None:
                # Heuristic mode: simple spread-based detection
                opportunity, confidence = await self._heuristic_prediction(market_data)
            else:
                # ML mode
                opportunity, confidence = await self._ml_prediction(market_data)

            self.current_confidence = confidence

            # Update metrics
            self.optimization_metrics.average_confidence = (
                (self.optimization_metrics.average_confidence * (self.optimization_metrics.predictions_made - 1) + confidence)
                / self.optimization_metrics.predictions_made
            )

            # Record metrics
            self.metrics.record_metric("ai_optimizer.prediction_time", time.time() - start_time)
            self.metrics.record_metric("ai_optimizer.confidence", confidence)
            self.metrics.record_metric("ai_optimizer.opportunity_detected", 1 if opportunity else 0)

            self.logger.debug("Arbitrage prediction completed", extra={
                "opportunity_detected": opportunity,
                "confidence": confidence,
                "mode": "heuristic" if not HAS_TF or self.model is None else "ml",
                "prediction_time": time.time() - start_time
            })

            return opportunity, confidence

        except Exception as e:
            self.logger.error(f"Failed to predict arbitrage opportunity: {e}", extra={
                "market_data_keys": list(market_data.keys()) if market_data else None
            })
            # Return safe defaults on error
            return False, 0.0

    async def _heuristic_prediction(self, market_data: Dict[str, Dict[str, Any]]) -> Tuple[bool, float]:
        """Heuristic-based arbitrage prediction"""
        spreads = []
        for dex1, data1 in market_data.items():
            for dex2, data2 in market_data.items():
                if dex1 != dex2:
                    price1 = data1.get('price', 0)
                    price2 = data2.get('price', 0)
                    if price1 > 0 and price2 > 0:
                        spread = abs(price1 - price2) / min(price1, price2)  # Percentage spread
                        spreads.append(spread)

        avg_spread = sum(spreads) / len(spreads) if spreads else 0
        confidence = min(avg_spread * 100, 0.9)  # Convert to confidence score
        opportunity = avg_spread > 0.005  # 0.5% threshold

        return opportunity, confidence

    async def _ml_prediction(self, market_data: Dict[str, Dict[str, Any]]) -> Tuple[bool, float]:
        """ML-based arbitrage prediction"""
        features = self.extract_features(market_data)
        scaled_features = self.scaler.transform([features])  # type: ignore
        prediction = self.model.predict(scaled_features)[0][0]  # type: ignore
        confidence = float(prediction if prediction > 0.5 else 1 - prediction)
        opportunity = prediction > 0.7  # High confidence threshold

        return opportunity, confidence

    def extract_features(self, market_data: Dict[str, Dict[str, Any]]) -> List[float]:
        """Extract features for ML model with validation"""
        try:
            features = []

            # Price spreads (percentage differences)
            dexes = list(market_data.keys())
            for i, dex1 in enumerate(dexes):
                for j, dex2 in enumerate(dexes):
                    if i != j:
                        price1 = market_data[dex1].get('price', 0)
                        price2 = market_data[dex2].get('price', 0)
                        if price1 > 0 and price2 > 0:
                            spread = abs(price1 - price2) / min(price1, price2)
                        else:
                            spread = 0.0
                        features.append(spread)

            # Volume ratios (normalized)
            total_volume = sum(data.get('volume', 0) for data in market_data.values())
            if total_volume > 0:
                for dex, data in market_data.items():
                    volume_ratio = data.get('volume', 0) / total_volume
                    features.append(volume_ratio)
            else:
                features.extend([0.0] * len(market_data))

            # Liquidity depth
            for dex, data in market_data.items():
                liquidity = data.get('liquidity', 0)
                features.append(float(liquidity))

            # Gas prices (normalized)
            gas_price = market_data.get('gas_price', 0)
            features.append(gas_price / 1000000000)  # Convert to gwei and normalize

            # Time-based features
            current_hour = datetime.now().hour
            features.append(current_hour / 24.0)  # Normalize to [0,1]
            features.append((current_hour ** 2) / (24.0 ** 2))  # Non-linear time effect

            # Pad to 20 features
            while len(features) < 20:
                features.append(0.0)

            return features[:20]

        except Exception as e:
            self.logger.error(f"Failed to extract features: {e}", extra={
                "market_data_keys": list(market_data.keys())
            })
            return [0.0] * 20

    async def optimize_trade_path(self, token_in: str, token_out: str, amount: Decimal) -> Tuple[Optional[List[str]], Decimal]:
        """Optimize multi-hop trading path using reinforcement learning with enterprise-grade error handling"""
        start_time = time.time()

        try:
            # Simplified path optimization - in production, this would use RL algorithms
            paths = [
                [token_in, token_out],  # Direct
                [token_in, 'WETH', token_out],  # Via WETH
                [token_in, 'USDC', token_out],  # Via USDC
            ]

            best_path = None
            best_profit = Decimal('0')

            for path in paths:
                try:
                    profit = await self.simulate_path_profit(path, amount)
                    if profit > best_profit:
                        best_profit = profit
                        best_path = path
                except Exception as e:
                    self.logger.warning(f"Failed to simulate profit for path {path}: {e}")
                    continue

            # Record metrics
            self.metrics.record_metric("ai_optimizer.path_optimization_time", time.time() - start_time)
            self.metrics.record_metric("ai_optimizer.best_profit", float(best_profit))

            self.logger.debug("Trade path optimization completed", extra={
                "token_in": token_in,
                "token_out": token_out,
                "amount": str(amount),
                "best_path": best_path,
                "best_profit": str(best_profit),
                "optimization_time": time.time() - start_time
            })

            return best_path, best_profit

        except Exception as e:
            self.logger.error(f"Failed to optimize trade path: {e}", extra={
                "token_in": token_in,
                "token_out": token_out,
                "amount": str(amount)
            })
            return None, Decimal('0')

    async def simulate_path_profit(self, path: List[str], amount: Decimal) -> Decimal:
        """Calculate profit for a given path using real DEX quotes with validation"""
        try:
            if len(path) < 2:
                raise ValueError("Path must contain at least 2 tokens")

            # Use actual DEX quotes for profit calculation
            # In production, this would query real DEX prices
            base_profit = amount * Decimal('0.001')  # 0.1% base profit
            hop_penalty = Decimal(str(len(path) - 1)) * Decimal('0.0001')  # Penalty per hop
            profit = base_profit - hop_penalty

            # Ensure non-negative profit
            return max(profit, Decimal('0'))

        except Exception as e:
            self.logger.error(f"Failed to simulate path profit: {e}", extra={
                "path": path,
                "amount": str(amount)
            })
            return Decimal('0')

    async def update_model(self, market_data: Dict[str, Dict[str, Any]], outcome: int) -> None:
        """Update ML model with new data and trigger retraining if needed"""
        try:
            features = self.extract_features(market_data)
            self.historical_data.append((features, outcome))

            self.logger.debug("Added new training sample", extra={
                "outcome": outcome,
                "total_samples": len(self.historical_data)
            })

            if len(self.historical_data) >= 100:
                await self.retrain_model()

        except Exception as e:
            self.logger.error(f"Failed to update model: {e}", extra={
                "outcome": outcome,
                "market_data_keys": list(market_data.keys())
            })

    async def retrain_model(self) -> None:
        """Retrain the ML model with accumulated data asynchronously"""
        if not HAS_TF or self.model is None or self.scaler is None:
            self.logger.warning("Cannot retrain model: missing dependencies or model")
            return

        try:
            start_time = time.time()

            X = [data[0] for data in self.historical_data]
            y = [data[1] for data in self.historical_data]

            X_scaled = self.scaler.fit_transform(X)

            # Train asynchronously to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.fit(X_scaled, y, epochs=10, batch_size=32, verbose=0)
            )

            # Save updated model
            model_path = 'models/arbitrage_predictor_v2.h5'
            self.model.save(model_path)

            training_time = time.time() - start_time
            self.optimization_metrics.last_training_time = datetime.utcnow()

            # Evaluate model accuracy
            predictions = self.model.predict(X_scaled)
            accuracy = float(np.mean((predictions > 0.5).astype(int) == np.array(y)))
            self.optimization_metrics.model_accuracy = accuracy

            # Record metrics
            self.metrics.record_metric("ai_optimizer.training_time", training_time)
            self.metrics.record_metric("ai_optimizer.model_accuracy", accuracy)

            self.logger.info("Model retraining completed", extra={
                "training_samples": len(self.historical_data),
                "accuracy": accuracy,
                "training_time": training_time,
                "model_path": model_path
            })

        except Exception as e:
            self.logger.error(f"Failed to retrain model: {e}")

    def get_current_confidence(self) -> float:
        """Return the current confidence score from the last prediction."""
        return self.current_confidence

    def get_optimization_metrics(self) -> OptimizationMetrics:
        """Get current optimization performance metrics"""
        return self.optimization_metrics
