"""
Phase 3 Module 6: Drift Detector
Concept drift detection and model performance monitoring

Provides:
- Statistical drift detection (KL divergence, Wasserstein)
- Performance drift monitoring
- Concept drift detection (market regime changes)
- Automatic retraining trigger
- A/B testing framework

Target: Detect drift with 90%+ precision, <5% false positives
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class DriftType(Enum):
    """Types of drift detected"""
    STATISTICAL = "statistical"  # Input distribution changed
    PERFORMANCE = "performance"  # Model accuracy degraded
    CONCEPT = "concept"          # Market regime changed
    NO_DRIFT = "no_drift"        # No drift detected


@dataclass
class DriftSignal:
    """Drift detection signal"""
    drift_type: DriftType
    severity: float  # 0-1, confidence in drift
    metric_name: str
    metric_value: float
    baseline_value: float
    threshold: float
    timestamp: str
    recommendation: str  # Action to take


@dataclass
class DriftDetectorConfig:
    """Drift detector configuration"""
    # Statistical drift
    kl_divergence_threshold: float = 0.05
    wasserstein_threshold: float = 0.1
    statistical_window_size: int = 100
    
    # Performance drift
    accuracy_drop_threshold: float = 0.05  # 5% drop
    performance_window_size: int = 100
    
    # Concept drift
    adwin_delta: float = 0.002
    concept_threshold: float = 0.1
    
    # Retraining
    auto_retrain_enabled: bool = True
    retrain_frequency: int = 1000  # Check every 1000 predictions
    
    # A/B testing
    ab_test_sample_size: int = 100
    ab_test_significance_level: float = 0.05


# ============================================================================
# STATISTICAL DRIFT DETECTION
# ============================================================================

class StatisticalDriftDetector:
    """Statistical distribution drift detection"""
    
    def __init__(self, config: DriftDetectorConfig):
        self.config = config
        self.baseline_data = None
        self.baseline_mean = None
        self.baseline_std = None
    
    def set_baseline(self, data: np.ndarray):
        """Set baseline distribution
        
        Args:
            data: Baseline feature distribution
        """
        self.baseline_data = data
        self.baseline_mean = np.mean(data, axis=0)
        self.baseline_std = np.std(data, axis=0)
        logger.info(f"Baseline set: mean={self.baseline_mean[:5]}, std={self.baseline_std[:5]}")
    
    def kl_divergence(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Calculate KL divergence between two distributions
        
        Args:
            data1: Baseline data (or predicted baseline dist)
            data2: Current data
            
        Returns:
            KL divergence (average across features)
        """
        # Discretize into bins for KL calculation
        n_bins = 10
        kl_values = []
        
        for i in range(data1.shape[1] if data1.ndim > 1 else 1):
            if data1.ndim > 1:
                d1 = data1[:, i]
                d2 = data2[:, i]
            else:
                d1 = data1
                d2 = data2
            
            # Create histograms
            hist1, bin_edges = np.histogram(d1, bins=n_bins)
            hist2, _ = np.histogram(d2, bins=bin_edges)
            
            # Normalize
            hist1 = hist1 / (np.sum(hist1) + 1e-8)
            hist2 = hist2 / (np.sum(hist2) + 1e-8)
            
            # KL divergence
            kl = np.sum(hist1 * np.log((hist1 + 1e-8) / (hist2 + 1e-8)))
            kl_values.append(kl)
        
        return np.mean(kl_values)
    
    def wasserstein_distance(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Calculate Wasserstein distance between distributions
        
        Args:
            data1: Baseline data
            data2: Current data
            
        Returns:
            Wasserstein distance
        """
        if data1.ndim == 1:
            data1 = data1.reshape(-1, 1)
        if data2.ndim == 1:
            data2 = data2.reshape(-1, 1)
        
        # Simple 1D Wasserstein per feature
        distances = []
        for i in range(data1.shape[1]):
            d1 = np.sort(data1[:, i])
            d2 = np.sort(data2[:, i])
            
            # Align lengths
            if len(d1) > len(d2):
                d1 = d1[:len(d2)]
            elif len(d2) > len(d1):
                d2 = d2[:len(d1)]
            
            distance = np.mean(np.abs(d1 - d2))
            distances.append(distance)
        
        return np.mean(distances)
    
    def detect_drift(self, data: np.ndarray) -> Optional[DriftSignal]:
        """Detect statistical drift
        
        Args:
            data: New data to check
            
        Returns:
            Drift signal if drift detected, None otherwise
        """
        if self.baseline_data is None:
            return None
        
        # Calculate KL divergence
        kl_div = self.kl_divergence(self.baseline_data, data)
        
        if kl_div > self.config.kl_divergence_threshold:
            return DriftSignal(
                drift_type=DriftType.STATISTICAL,
                severity=min(kl_div / (self.config.kl_divergence_threshold * 2), 1.0),
                metric_name='kl_divergence',
                metric_value=kl_div,
                baseline_value=0.0,
                threshold=self.config.kl_divergence_threshold,
                timestamp=datetime.now().isoformat(),
                recommendation='Retrain model on new data distribution'
            )
        
        return None


# ============================================================================
# PERFORMANCE DRIFT DETECTION
# ============================================================================

class PerformanceDriftDetector:
    """Model performance degradation detection"""
    
    def __init__(self, config: DriftDetectorConfig):
        self.config = config
        self.baseline_accuracy = None
        self.accuracy_history = deque(maxlen=config.performance_window_size)
    
    def set_baseline(self, accuracy: float):
        """Set baseline accuracy
        
        Args:
            accuracy: Baseline model accuracy
        """
        self.baseline_accuracy = accuracy
        logger.info(f"Baseline accuracy set: {accuracy:.4f}")
    
    def record_accuracy(self, accuracy: float):
        """Record prediction accuracy
        
        Args:
            accuracy: Current accuracy
        """
        self.accuracy_history.append(accuracy)
    
    def detect_drift(self) -> Optional[DriftSignal]:
        """Detect performance drift
        
        Returns:
            Drift signal if drift detected, None otherwise
        """
        if self.baseline_accuracy is None or len(self.accuracy_history) < 10:
            return None
        
        # Calculate moving average accuracy
        current_avg_accuracy = np.mean(list(self.accuracy_history))
        accuracy_drop = self.baseline_accuracy - current_avg_accuracy
        
        if accuracy_drop > self.config.accuracy_drop_threshold:
            severity = min(accuracy_drop / (self.config.accuracy_drop_threshold * 2), 1.0)
            
            return DriftSignal(
                drift_type=DriftType.PERFORMANCE,
                severity=severity,
                metric_name='accuracy_drop',
                metric_value=current_avg_accuracy,
                baseline_value=self.baseline_accuracy,
                threshold=self.config.accuracy_drop_threshold,
                timestamp=datetime.now().isoformat(),
                recommendation='Retrain model immediately'
            )
        
        return None


# ============================================================================
# CONCEPT DRIFT DETECTION (ADWIN)
# ============================================================================

class ConceptDriftDetector:
    """Market regime/concept drift detection using ADWIN"""
    
    def __init__(self, config: DriftDetectorConfig):
        self.config = config
        self.win = deque()
        self.total = 0.0
        self.width = 0
    
    def add(self, value: float):
        """Add new value to stream
        
        Args:
            value: New observation (0 or 1 for binary)
        """
        self.win.append(value)
        self.total += value
        self.width += 1
        
        # Check for drift
        if self.width % 50 == 0:  # Check periodically
            self._compress_window()
    
    def _compress_window(self):
        """Compress window using ADWIN algorithm"""
        if self.width < 10:
            return
        
        # Check buckets for significant change
        n0 = self.width
        m = 1
        
        changed = True
        while changed:
            changed = False
            
            if n0 > 1:
                n1 = n0 - m
                if n1 > 0:
                    p0 = self.total / n0
                    p1 = (self.total - sum(list(self.win)[-m:])) / n1
                    
                    # Calculate distance
                    m_est = (1.0 / p0 + 1.0 / (1.0 - p0)) if p0 > 0 and p0 < 1 else 1
                    distance = np.abs(p0 - p1)
                    
                    if distance > self.config.concept_threshold:
                        # Drift detected, remove old bucket
                        for _ in range(m):
                            if self.win:
                                val = self.win.popleft()
                                self.total -= val
                                self.width -= 1
                        changed = True
                        break
                
                m *= 2
                n0 = n1
    
    def detect_drift(self) -> Optional[DriftSignal]:
        """Detect concept drift based on window compression
        
        Returns:
            Drift signal if drift detected, None otherwise
        """
        # Drift is implicit in window compression
        # Return signal if window size changed significantly
        if self.width < 100:
            return None
        
        # Simplified: detect drift if window compressed >30%
        expected_width = 200
        compression_ratio = (expected_width - self.width) / expected_width
        
        if compression_ratio > 0.3:
            return DriftSignal(
                drift_type=DriftType.CONCEPT,
                severity=min(compression_ratio, 1.0),
                metric_name='window_compression',
                metric_value=self.width,
                baseline_value=expected_width,
                threshold=expected_width * 0.7,
                timestamp=datetime.now().isoformat(),
                recommendation='Market regime changed, consider strategy adjustment'
            )
        
        return None


# ============================================================================
# DRIFT DETECTOR ORCHESTRATOR
# ============================================================================

class DriftDetector:
    """Main drift detection orchestrator"""
    
    def __init__(self, config: Optional[DriftDetectorConfig] = None):
        """Initialize drift detector
        
        Args:
            config: Drift detection configuration
        """
        self.config = config or DriftDetectorConfig()
        self.statistical_detector = StatisticalDriftDetector(self.config)
        self.performance_detector = PerformanceDriftDetector(self.config)
        self.concept_detector = ConceptDriftDetector(self.config)
        
        self.drift_history: List[DriftSignal] = []
        self.retraining_triggered = False
        self.prediction_count = 0
        
        logger.info("Drift Detector initialized")
    
    def set_baseline(self, data: np.ndarray, accuracy: float):
        """Set baseline for all detectors
        
        Args:
            data: Baseline feature distribution
            accuracy: Baseline model accuracy
        """
        self.statistical_detector.set_baseline(data)
        self.performance_detector.set_baseline(accuracy)
        logger.info("Baseline set for all detectors")
    
    def detect(self, new_data: np.ndarray, predictions: np.ndarray,
              actual: np.ndarray) -> Optional[DriftSignal]:
        """Detect drift across all methods
        
        Args:
            new_data: New feature data
            predictions: Model predictions
            actual: Actual labels
            
        Returns:
            Strongest drift signal if any drift detected
        """
        drift_signals = []
        
        # Statistical drift
        stat_drift = self.statistical_detector.detect_drift(new_data)
        if stat_drift:
            drift_signals.append(stat_drift)
        
        # Performance drift
        accuracy = np.mean(predictions == actual)
        self.performance_detector.record_accuracy(accuracy)
        perf_drift = self.performance_detector.detect_drift()
        if perf_drift:
            drift_signals.append(perf_drift)
        
        # Concept drift
        self.concept_detector.add(float(predictions[0] == actual[0]))
        concept_drift = self.concept_detector.detect_drift()
        if concept_drift:
            drift_signals.append(concept_drift)
        
        # Select strongest signal
        if drift_signals:
            strongest = max(drift_signals, key=lambda x: x.severity)
            self.drift_history.append(strongest)
            
            # Check if retraining needed
            if self.config.auto_retrain_enabled:
                self.prediction_count += 1
                if self.prediction_count >= self.config.retrain_frequency:
                    self.retraining_triggered = True
                    self.prediction_count = 0
            
            logger.warning(f"Drift detected: {strongest.drift_type.value}, "
                          f"severity={strongest.severity:.2f}, "
                          f"recommendation={strongest.recommendation}")
            return strongest
        
        return None
    
    def should_retrain(self) -> bool:
        """Check if model retraining is recommended
        
        Returns:
            True if retraining recommended
        """
        return self.retraining_triggered
    
    def reset_retraining_flag(self):
        """Reset retraining trigger flag"""
        self.retraining_triggered = False
    
    def get_drift_summary(self) -> Dict:
        """Get drift detection summary"""
        if not self.drift_history:
            return {'total_drifts': 0, 'recent_drifts': []}
        
        recent = self.drift_history[-10:]
        drift_types = {}
        
        for drift in self.drift_history:
            drift_type = drift.drift_type.value
            drift_types[drift_type] = drift_types.get(drift_type, 0) + 1
        
        return {
            'total_drifts': len(self.drift_history),
            'drift_types': drift_types,
            'recent_drifts': [asdict(d) for d in recent],
            'needs_retraining': self.should_retrain(),
        }


# ============================================================================
# A/B TESTING
# ============================================================================

class ABTestFramework:
    """A/B testing for model comparison"""
    
    def __init__(self, config: DriftDetectorConfig):
        self.config = config
        self.model_a_results = []
        self.model_b_results = []
    
    def add_comparison(self, model_a_pred: int, model_b_pred: int, actual: int):
        """Add A/B test observation
        
        Args:
            model_a_pred: Model A prediction
            model_b_pred: Model B prediction
            actual: Actual label
        """
        self.model_a_results.append(int(model_a_pred == actual))
        self.model_b_results.append(int(model_b_pred == actual))
    
    def get_results(self) -> Dict:
        """Get A/B test results
        
        Returns:
            Statistical comparison results
        """
        if len(self.model_a_results) < self.config.ab_test_sample_size:
            return {'status': 'insufficient_samples'}
        
        a_accuracy = np.mean(self.model_a_results[-self.config.ab_test_sample_size:])
        b_accuracy = np.mean(self.model_b_results[-self.config.ab_test_sample_size:])
        
        # Simple z-test
        a_std = np.std(self.model_a_results[-self.config.ab_test_sample_size:])
        b_std = np.std(self.model_b_results[-self.config.ab_test_sample_size:])
        
        se = np.sqrt(a_std**2/self.config.ab_test_sample_size + b_std**2/self.config.ab_test_sample_size)
        z_score = (a_accuracy - b_accuracy) / (se + 1e-8)
        
        return {
            'model_a_accuracy': float(a_accuracy),
            'model_b_accuracy': float(b_accuracy),
            'accuracy_difference': float(a_accuracy - b_accuracy),
            'z_score': float(z_score),
            'significant': abs(z_score) > 1.96,  # 95% confidence
            'winner': 'A' if a_accuracy > b_accuracy else 'B',
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Production module - drift detection available for production use
# No demo/test execution - all synthetic data and drift simulation removed
