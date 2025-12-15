"""
Phase 3 Module 3: Ensemble Predictor
3-model voting system for 88%+ accuracy predictions

Combines:
1. Q-Learning predictions (60% weight)
2. Actor-Critic predictions (25% weight)
3. Transformer predictions (15% weight)

Provides:
- Voting mechanism (majority + weighted)
- Confidence scoring
- Prediction aggregation
- Real-time prediction API
- Performance tracking

Target: 88%+ accuracy, <11% false positive rate, <150ms latency
"""

import numpy as np
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class TradingSignal(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class ConfidenceLevel(Enum):
    """Confidence levels for predictions"""
    VERY_LOW = (0.0, 0.3)
    LOW = (0.3, 0.5)
    MEDIUM = (0.5, 0.7)
    HIGH = (0.7, 0.85)
    VERY_HIGH = (0.85, 1.0)


@dataclass
class ModelPrediction:
    """Individual model prediction"""
    model_name: str
    score: float  # 0-1, where >0.65 = BUY, <0.35 = SELL, else HOLD
    signal: TradingSignal
    confidence: float
    latency_ms: float
    timestamp: str


@dataclass
class EnsemblePrediction:
    """Final ensemble prediction"""
    signal: TradingSignal
    confidence: float
    confidence_level: ConfidenceLevel
    
    # Individual model predictions
    q_learning_pred: Optional[ModelPrediction]
    actor_critic_pred: Optional[ModelPrediction]
    transformer_pred: Optional[ModelPrediction]
    
    # Voting details
    votes: Dict[str, int]  # Signal -> vote count
    weighted_votes: Dict[str, float]  # Signal -> weighted votes
    
    # Metrics
    ensemble_score: float
    model_agreement: float  # 0-1, how much models agree
    prediction_strength: float  # How strong the consensus
    
    timestamp: str
    latency_ms: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data['signal'] = self.signal.value
        data['confidence_level'] = self.confidence_level.name
        # Handle nested objects
        if self.q_learning_pred:
            data['q_learning_pred'] = {
                'score': self.q_learning_pred.score,
                'signal': self.q_learning_pred.signal.value,
                'confidence': self.q_learning_pred.confidence,
            }
        return data


@dataclass
class EnsembleConfig:
    """Configuration for ensemble predictor"""
    # Model weights
    q_learning_weight: float = 0.60
    actor_critic_weight: float = 0.25
    transformer_weight: float = 0.15
    
    # Confidence thresholds
    min_confidence_to_trade: float = 0.75
    hold_confidence_range: Tuple[float, float] = (0.4, 0.6)
    
    # Voting settings
    voting_method: str = 'weighted'  # 'weighted' or 'majority'
    majority_threshold: float = 0.5
    
    # Signal thresholds
    buy_threshold: float = 0.65
    sell_threshold: float = 0.35
    
    # Performance tracking
    track_performance: bool = True
    performance_window: int = 100  # Track last N predictions


@dataclass
class PerformanceMetrics:
    """Performance metrics for ensemble"""
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy: float = 0.0
    
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    
    positive_predictions: int = 0
    negative_predictions: int = 0
    
    avg_confidence: float = 0.0
    high_confidence_count: int = 0
    
    correct_buy: int = 0
    correct_sell: int = 0
    correct_hold: int = 0
    
    false_positives: int = 0
    false_negatives: int = 0
    
    def get_precision(self) -> float:
        """Precision = TP / (TP + FP)"""
        positives = self.correct_buy + self.false_positives
        return self.correct_buy / positives if positives > 0 else 0.0
    
    def get_recall(self) -> float:
        """Recall = TP / (TP + FN)"""
        total_actual = self.correct_buy + self.false_negatives
        return self.correct_buy / total_actual if total_actual > 0 else 0.0
    
    def get_f1_score(self) -> float:
        """F1 = 2 * (precision * recall) / (precision + recall)"""
        precision = self.get_precision()
        recall = self.get_recall()
        denominator = precision + recall
        return (2 * precision * recall) / denominator if denominator > 0 else 0.0


# ============================================================================
# VOTING MECHANISM
# ============================================================================

class VotingMechanism:
    """Voting system for ensemble predictions"""
    
    def __init__(self, config: EnsembleConfig):
        self.config = config
    
    def _normalize_score(self, score: float) -> TradingSignal:
        """Convert score to trading signal"""
        if score > self.config.buy_threshold:
            return TradingSignal.BUY
        elif score < self.config.sell_threshold:
            return TradingSignal.SELL
        else:
            return TradingSignal.HOLD
    
    def majority_vote(self, signals: List[TradingSignal]) -> Tuple[TradingSignal, int]:
        """Simple majority voting"""
        vote_counts = {
            TradingSignal.BUY: signals.count(TradingSignal.BUY),
            TradingSignal.SELL: signals.count(TradingSignal.SELL),
            TradingSignal.HOLD: signals.count(TradingSignal.HOLD),
        }
        
        winning_signal = max(vote_counts, key=vote_counts.get)
        return winning_signal, vote_counts[winning_signal]
    
    def weighted_vote(self, predictions: List[Tuple[ModelPrediction, float]]) -> Tuple[TradingSignal, float]:
        """Weighted voting with model weights
        
        Args:
            predictions: List of (ModelPrediction, weight) tuples
            
        Returns:
            Winning signal and weighted vote count
        """
        weighted_scores = {}
        total_weight = 0
        
        for pred, weight in predictions:
            signal = pred.signal
            if signal not in weighted_scores:
                weighted_scores[signal] = 0.0
            
            weighted_scores[signal] += weight
            total_weight += weight
        
        # Normalize by total weight
        for signal in weighted_scores:
            weighted_scores[signal] /= total_weight if total_weight > 0 else 1.0
        
        winning_signal = max(weighted_scores, key=weighted_scores.get)
        return winning_signal, weighted_scores[winning_signal]
    
    def calculate_ensemble_score(self, scores: List[Tuple[float, float]]) -> float:
        """Calculate weighted average ensemble score
        
        Args:
            scores: List of (model_score, model_weight) tuples
            
        Returns:
            Weighted average score (0-1)
        """
        total = 0.0
        total_weight = 0.0
        
        for score, weight in scores:
            total += score * weight
            total_weight += weight
        
        return total / total_weight if total_weight > 0 else 0.5
    
    def calculate_agreement(self, signals: List[TradingSignal]) -> float:
        """Calculate how much models agree (0-1)
        
        0 = all disagree
        1 = all agree
        """
        if not signals:
            return 1.0
        
        vote_counts = {}
        for signal in signals:
            vote_counts[signal] = vote_counts.get(signal, 0) + 1
        
        max_votes = max(vote_counts.values())
        return max_votes / len(signals)


# ============================================================================
# ENSEMBLE PREDICTOR
# ============================================================================

class EnsemblePredictor:
    """3-model ensemble prediction system"""
    
    def __init__(self, config: Optional[EnsembleConfig] = None):
        """Initialize ensemble predictor
        
        Args:
            config: Configuration for ensemble
        """
        self.config = config or EnsembleConfig()
        self.voting = VotingMechanism(self.config)
        
        # Validate weights
        total_weight = (self.config.q_learning_weight + 
                       self.config.actor_critic_weight + 
                       self.config.transformer_weight)
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: {total_weight}")
        
        # Performance tracking
        self.predictions_history: List[EnsemblePrediction] = []
        self.performance = PerformanceMetrics()
        self.correctness_history: List[bool] = []
        
        logger.info(f"Ensemble Predictor initialized with weights: "
                   f"Q-Learning={self.config.q_learning_weight}, "
                   f"Actor-Critic={self.config.actor_critic_weight}, "
                   f"Transformer={self.config.transformer_weight}")
    
    def predict(self, q_learning_score: float,
                actor_critic_score: float,
                transformer_score: float,
                model_latencies: Optional[Dict[str, float]] = None) -> EnsemblePrediction:
        """Make ensemble prediction
        
        Args:
            q_learning_score: Q-Learning model output (0-1)
            actor_critic_score: Actor-Critic model output (0-1)
            transformer_score: Transformer model output (0-1)
            model_latencies: Latencies for each model (optional)
            
        Returns:
            Ensemble prediction with voting results
        """
        start_time = datetime.now()
        
        if model_latencies is None:
            model_latencies = {
                'q_learning': 0.0,
                'actor_critic': 0.0,
                'transformer': 0.0,
            }
        
        # Convert scores to model predictions
        q_learning_pred = ModelPrediction(
            model_name='Q-Learning',
            score=q_learning_score,
            signal=self.voting._normalize_score(q_learning_score),
            confidence=max(q_learning_score, 1 - q_learning_score),
            latency_ms=model_latencies.get('q_learning', 0),
            timestamp=datetime.now().isoformat()
        )
        
        actor_critic_pred = ModelPrediction(
            model_name='Actor-Critic',
            score=actor_critic_score,
            signal=self.voting._normalize_score(actor_critic_score),
            confidence=max(actor_critic_score, 1 - actor_critic_score),
            latency_ms=model_latencies.get('actor_critic', 0),
            timestamp=datetime.now().isoformat()
        )
        
        transformer_pred = ModelPrediction(
            model_name='Transformer',
            score=transformer_score,
            signal=self.voting._normalize_score(transformer_score),
            confidence=max(transformer_score, 1 - transformer_score),
            latency_ms=model_latencies.get('transformer', 0),
            timestamp=datetime.now().isoformat()
        )
        
        # Calculate ensemble score (weighted average)
        ensemble_score = self.voting.calculate_ensemble_score([
            (q_learning_score, self.config.q_learning_weight),
            (actor_critic_score, self.config.actor_critic_weight),
            (transformer_score, self.config.transformer_weight),
        ])
        
        # Perform voting
        predictions_with_weights = [
            (q_learning_pred, self.config.q_learning_weight),
            (actor_critic_pred, self.config.actor_critic_weight),
            (transformer_pred, self.config.transformer_weight),
        ]
        
        if self.config.voting_method == 'weighted':
            final_signal, weighted_vote = self.voting.weighted_vote(predictions_with_weights)
            vote_counts = {
                TradingSignal.BUY: (q_learning_pred.signal == TradingSignal.BUY) * self.config.q_learning_weight +
                                  (actor_critic_pred.signal == TradingSignal.BUY) * self.config.actor_critic_weight +
                                  (transformer_pred.signal == TradingSignal.BUY) * self.config.transformer_weight,
                TradingSignal.SELL: (q_learning_pred.signal == TradingSignal.SELL) * self.config.q_learning_weight +
                                   (actor_critic_pred.signal == TradingSignal.SELL) * self.config.actor_critic_weight +
                                   (transformer_pred.signal == TradingSignal.SELL) * self.config.transformer_weight,
                TradingSignal.HOLD: (q_learning_pred.signal == TradingSignal.HOLD) * self.config.q_learning_weight +
                                   (actor_critic_pred.signal == TradingSignal.HOLD) * self.config.actor_critic_weight +
                                   (transformer_pred.signal == TradingSignal.HOLD) * self.config.transformer_weight,
            }
        else:
            signals = [p.signal for p in [q_learning_pred, actor_critic_pred, transformer_pred]]
            final_signal, _ = self.voting.majority_vote(signals)
            vote_counts = {
                TradingSignal.BUY: signals.count(TradingSignal.BUY),
                TradingSignal.SELL: signals.count(TradingSignal.SELL),
                TradingSignal.HOLD: signals.count(TradingSignal.HOLD),
            }
        
        # Calculate confidence
        confidence = max(vote_counts.values()) if vote_counts else 0.5
        
        # Calculate model agreement
        signals = [q_learning_pred.signal, actor_critic_pred.signal, transformer_pred.signal]
        model_agreement = self.voting.calculate_agreement(signals)
        
        # Calculate prediction strength
        prediction_strength = max(ensemble_score, 1 - ensemble_score)
        
        # Determine confidence level
        confidence_level = ConfidenceLevel.VERY_LOW
        for level in ConfidenceLevel:
            min_conf, max_conf = level.value
            if min_conf <= confidence <= max_conf:
                confidence_level = level
                break
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Create ensemble prediction
        prediction = EnsemblePrediction(
            signal=final_signal,
            confidence=confidence,
            confidence_level=confidence_level,
            q_learning_pred=q_learning_pred,
            actor_critic_pred=actor_critic_pred,
            transformer_pred=transformer_pred,
            votes={s.value: int(v) for s, v in vote_counts.items()},
            weighted_votes={s.value: float(v) for s, v in vote_counts.items()},
            ensemble_score=ensemble_score,
            model_agreement=model_agreement,
            prediction_strength=prediction_strength,
            timestamp=datetime.now().isoformat(),
            latency_ms=latency_ms
        )
        
        # Track prediction
        if self.config.track_performance:
            self.predictions_history.append(prediction)
            # Keep last N predictions
            if len(self.predictions_history) > self.config.performance_window:
                self.predictions_history.pop(0)
        
        return prediction
    
    def should_trade(self, prediction: EnsemblePrediction) -> bool:
        """Determine if prediction confidence is high enough to trade
        
        Args:
            prediction: Ensemble prediction
            
        Returns:
            True if confidence >= min_confidence_to_trade
        """
        return prediction.confidence >= self.config.min_confidence_to_trade
    
    def record_actual_outcome(self, prediction: EnsemblePrediction, actual_signal: TradingSignal):
        """Record actual outcome for performance tracking
        
        Args:
            prediction: Original ensemble prediction
            actual_signal: Actual outcome (BUY/SELL/HOLD or actual price direction)
        """
        if not self.config.track_performance:
            return
        
        # Update metrics
        self.performance.total_predictions += 1
        
        # Count signals
        signal_map = {
            TradingSignal.BUY: 'buy_signals',
            TradingSignal.SELL: 'sell_signals',
            TradingSignal.HOLD: 'hold_signals',
        }
        setattr(self.performance, signal_map.get(prediction.signal, 'hold_signals'),
                getattr(self.performance, signal_map.get(prediction.signal, 'hold_signals')) + 1)
        
        # Check correctness
        is_correct = prediction.signal == actual_signal
        self.correctness_history.append(is_correct)
        
        if is_correct:
            self.performance.correct_predictions += 1
            if prediction.signal == TradingSignal.BUY:
                self.performance.correct_buy += 1
            elif prediction.signal == TradingSignal.SELL:
                self.performance.correct_sell += 1
            else:
                self.performance.correct_hold += 1
        else:
            if prediction.signal == TradingSignal.BUY:
                self.performance.false_positives += 1
            elif prediction.signal == TradingSignal.SELL:
                self.performance.false_negatives += 1
        
        # Update accuracy
        if self.performance.total_predictions > 0:
            self.performance.accuracy = self.performance.correct_predictions / self.performance.total_predictions
        
        # Update confidence tracking
        self.performance.avg_confidence = np.mean([p.confidence for p in self.predictions_history[-100:]])
        self.performance.high_confidence_count = sum(1 for p in self.predictions_history[-100:]
                                                     if p.confidence >= self.config.min_confidence_to_trade)
    
    def get_performance_summary(self) -> Dict:
        """Get performance metrics summary"""
        return {
            'total_predictions': self.performance.total_predictions,
            'accuracy': self.performance.accuracy,
            'precision': self.performance.get_precision(),
            'recall': self.performance.get_recall(),
            'f1_score': self.performance.get_f1_score(),
            'signal_distribution': {
                'buy': self.performance.buy_signals,
                'sell': self.performance.sell_signals,
                'hold': self.performance.hold_signals,
            },
            'correctness': {
                'buy': self.performance.correct_buy,
                'sell': self.performance.correct_sell,
                'hold': self.performance.correct_hold,
            },
            'errors': {
                'false_positives': self.performance.false_positives,
                'false_negatives': self.performance.false_negatives,
            },
            'confidence': {
                'average': self.performance.avg_confidence,
                'high_confidence_trades': self.performance.high_confidence_count,
            },
        }
    
    def get_recent_predictions(self, n: int = 10) -> List[Dict]:
        """Get recent predictions as dictionaries"""
        return [p.to_dict() for p in self.predictions_history[-n:]]


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Demo/test execution"""
    logging.basicConfig(level=logging.INFO)
    
    # Initialize predictor
    config = EnsembleConfig()
    predictor = EnsemblePredictor(config)
    
    # Test predictions
    test_cases = [
        (0.8, 0.75, 0.78),  # Strong BUY signal
        (0.2, 0.25, 0.22),  # Strong SELL signal
        (0.5, 0.52, 0.48),  # HOLD signal
        (0.7, 0.68, 0.65),  # Weak BUY signal
    ]
    
    logger.info("Testing ensemble predictor...")
    for i, (ql_score, ac_score, tf_score) in enumerate(test_cases):
        pred = predictor.predict(ql_score, ac_score, tf_score)
        logger.info(f"Test {i+1}:")
        logger.info(f"  Q-Learning: {ql_score:.2f}")
        logger.info(f"  Actor-Critic: {ac_score:.2f}")
        logger.info(f"  Transformer: {tf_score:.2f}")
        logger.info(f"  Ensemble Score: {pred.ensemble_score:.2f}")
        logger.info(f"  Final Signal: {pred.signal.value}")
        logger.info(f"  Confidence: {pred.confidence:.2f}")
        logger.info(f"  Should Trade: {predictor.should_trade(pred)}")
        logger.info(f"  Model Agreement: {pred.model_agreement:.2f}")
        logger.info("")
    
    # Get summary
    summary = predictor.get_performance_summary()
    logger.info(f"Performance Summary: {json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()
