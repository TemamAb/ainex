"""
AINEON Enterprise: Correlation Monitor Module
Phase 3B: Risk Management - Cross-Asset Correlation Tracking

Real-time monitoring of asset correlations to detect concentration risk,
tail risk, and liquidity constraints.

Author: AINEON Chief Architect
Version: 1.0
Date: December 14, 2025
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class CorrelationMatrix(BaseModel):
    """Pairwise correlation matrix."""
    timestamp: datetime
    assets: List[str]
    correlations: Dict[str, Dict[str, Decimal]]  # {asset1: {asset2: correlation}}
    lookback_days: int
    update_frequency_hours: int


class CorrelationAlert(BaseModel):
    """Alert for abnormal correlation."""
    timestamp: datetime
    asset_pair: Tuple[str, str]
    current_correlation: Decimal
    historical_mean: Decimal
    std_dev: Decimal
    z_score: Decimal  # Standard deviations from mean
    alert_type: str  # "spike", "breakdown", "tail_risk"
    severity: str  # "low", "medium", "high", "critical"


class ConcentrationRisk(BaseModel):
    """Portfolio concentration risk metrics."""
    timestamp: datetime
    herfindahl_index: Decimal  # Sum of weight^2, 0-1 scale
    effective_assets: Decimal  # Effective number of assets
    correlation_cluster: Dict[str, List[str]]  # Clustered highly correlated assets
    risk_level: str  # "low", "medium", "high"
    max_correlation: Decimal  # Highest pairwise correlation
    min_correlation: Decimal  # Lowest pairwise correlation


class TailRiskIndicator(BaseModel):
    """Tail risk between asset pairs."""
    asset_pair: Tuple[str, str]
    normal_correlation: Decimal  # Correlation in normal times
    tail_correlation: Decimal  # Correlation in down markets
    tail_risk_ratio: Decimal  # tail_correlation / normal_correlation
    decoupling_score: Decimal  # How well assets diverge in tail (1 = perfect decoupling)


# ============================================================================
# CORRELATION MONITOR
# ============================================================================

class CorrelationMonitor:
    """
    Real-time cross-asset correlation monitoring.
    
    Tracks:
    - Pairwise asset correlations
    - Correlation matrix changes
    - Concentration risk
    - Tail dependencies
    - Correlation spikes/breakdowns
    
    Applications:
    - Portfolio diversification validation
    - Risk concentration detection
    - Liquidity risk monitoring
    - Systemic risk detection
    """
    
    def __init__(
        self,
        min_observations: int = 20,
        alert_z_score_threshold: Decimal = Decimal("2.0"),
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize correlation monitor.
        
        Args:
            min_observations: Minimum observations for calculation
            alert_z_score_threshold: Z-score threshold for alerts
            logger: Logger instance
        """
        self.min_observations = min_observations
        self.alert_z_score_threshold = alert_z_score_threshold
        self.logger = logger or logging.getLogger(__name__)
        
        # Data storage
        self._price_history: Dict[str, List[Tuple[datetime, Decimal]]] = {}
        self._correlation_history: List[CorrelationMatrix] = []
        self._alerts: List[CorrelationAlert] = []
        self._tail_risk_cache: Dict[Tuple[str, str], TailRiskIndicator] = {}
        
        self.logger.info("✅ CorrelationMonitor initialized")
    
    # ========================================================================
    # PRICE TRACKING
    # ========================================================================
    
    def add_price(
        self,
        asset: str,
        price: Decimal,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add price data point."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if asset not in self._price_history:
            self._price_history[asset] = []
        
        self._price_history[asset].append((timestamp, price))
    
    def add_prices(
        self,
        prices: Dict[str, Decimal],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Add multiple prices for same timestamp."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        for asset, price in prices.items():
            self.add_price(asset, price, timestamp)
    
    def get_price_series(
        self,
        asset: str,
        lookback_hours: int = 24,
    ) -> List[Decimal]:
        """Get recent price series for an asset."""
        if asset not in self._price_history:
            return []
        
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
        prices = [
            price for timestamp, price in self._price_history[asset]
            if timestamp >= cutoff
        ]
        
        return prices
    
    # ========================================================================
    # CORRELATION CALCULATION
    # ========================================================================
    
    def calculate_correlation(
        self,
        asset_1: str,
        asset_2: str,
        lookback_hours: int = 24,
    ) -> Optional[Decimal]:
        """
        Calculate correlation between two assets.
        
        Args:
            asset_1: First asset
            asset_2: Second asset
            lookback_hours: Historical period
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        prices_1 = self.get_price_series(asset_1, lookback_hours)
        prices_2 = self.get_price_series(asset_2, lookback_hours)
        
        if len(prices_1) < self.min_observations or len(prices_2) < self.min_observations:
            return None
        
        # Ensure same length (align by timestamp)
        min_len = min(len(prices_1), len(prices_2))
        prices_1 = prices_1[-min_len:]
        prices_2 = prices_2[-min_len:]
        
        # Calculate returns
        returns_1 = [
            (prices_1[i] - prices_1[i-1]) / prices_1[i-1]
            if prices_1[i-1] > 0 else Decimal("0")
            for i in range(1, len(prices_1))
        ]
        
        returns_2 = [
            (prices_2[i] - prices_2[i-1]) / prices_2[i-1]
            if prices_2[i-1] > 0 else Decimal("0")
            for i in range(1, len(prices_2))
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
        
        # Clamp to [-1, 1]
        return max(Decimal("-1"), min(Decimal("1"), correlation))
    
    def calculate_correlation_matrix(
        self,
        assets: List[str],
        lookback_hours: int = 24,
    ) -> Optional[CorrelationMatrix]:
        """
        Calculate full correlation matrix.
        
        Args:
            assets: List of assets
            lookback_hours: Historical lookback period
            
        Returns:
            Correlation matrix
        """
        if len(assets) < 2:
            return None
        
        # Calculate pairwise correlations
        correlations = {}
        
        for asset_1 in assets:
            correlations[asset_1] = {}
            for asset_2 in assets:
                if asset_1 == asset_2:
                    correlations[asset_1][asset_2] = Decimal("1")
                else:
                    corr = self.calculate_correlation(asset_1, asset_2, lookback_hours)
                    correlations[asset_1][asset_2] = corr or Decimal("0")
        
        matrix = CorrelationMatrix(
            timestamp=datetime.utcnow(),
            assets=assets,
            correlations=correlations,
            lookback_days=lookback_hours // 24,
            update_frequency_hours=1,
        )
        
        self._correlation_history.append(matrix)
        
        return matrix
    
    # ========================================================================
    # CONCENTRATION RISK
    # ========================================================================
    
    def calculate_concentration_risk(
        self,
        allocation: Dict[str, Decimal],
        correlation_matrix: Optional[CorrelationMatrix] = None,
    ) -> ConcentrationRisk:
        """
        Calculate portfolio concentration risk.
        
        Args:
            allocation: Portfolio weights
            correlation_matrix: Correlation matrix
            
        Returns:
            Concentration risk metrics
        """
        # Herfindahl index
        herfindahl = sum(w ** 2 for w in allocation.values())
        
        # Effective number of assets
        # N_eff = 1 / Herfindahl
        n_eff = Decimal("1") / (herfindahl + Decimal("0.0001"))
        
        # Find correlation clusters
        clusters = self._find_correlation_clusters(allocation, correlation_matrix)
        
        # Max/min correlations
        correlations_list = []
        if correlation_matrix:
            for asset_1 in correlation_matrix.assets:
                for asset_2 in correlation_matrix.assets:
                    if asset_1 < asset_2:  # Avoid duplicates
                        corr = correlation_matrix.correlations[asset_1][asset_2]
                        if corr is not None:
                            correlations_list.append(corr)
        
        max_corr = max(correlations_list) if correlations_list else Decimal("0")
        min_corr = min(correlations_list) if correlations_list else Decimal("0")
        
        # Risk level
        if herfindahl > Decimal("0.33"):
            risk_level = "high"
        elif herfindahl > Decimal("0.15"):
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return ConcentrationRisk(
            timestamp=datetime.utcnow(),
            herfindahl_index=herfindahl,
            effective_assets=n_eff,
            correlation_cluster=clusters,
            risk_level=risk_level,
            max_correlation=max_corr,
            min_correlation=min_corr,
        )
    
    def _find_correlation_clusters(
        self,
        allocation: Dict[str, Decimal],
        correlation_matrix: Optional[CorrelationMatrix] = None,
        threshold: Decimal = Decimal("0.7"),
    ) -> Dict[str, List[str]]:
        """Find groups of highly correlated assets."""
        if not correlation_matrix:
            return {}
        
        clusters = {}
        visited = set()
        
        for asset in allocation:
            if asset in visited:
                continue
            
            cluster = [asset]
            visited.add(asset)
            
            for other in allocation:
                if other in visited:
                    continue
                
                corr = correlation_matrix.correlations.get(asset, {}).get(other)
                if corr and abs(corr) >= threshold:
                    cluster.append(other)
                    visited.add(other)
            
            if len(cluster) > 1:
                clusters[asset] = cluster
        
        return clusters
    
    # ========================================================================
    # TAIL RISK ANALYSIS
    # ========================================================================
    
    def calculate_tail_risk(
        self,
        asset_1: str,
        asset_2: str,
        normal_threshold: Decimal = Decimal("0.95"),  # 5% downside
    ) -> Optional[TailRiskIndicator]:
        """
        Calculate tail risk correlation.
        
        Correlation is higher in down markets (tail risk).
        """
        prices_1 = self.get_price_series(asset_1)
        prices_2 = self.get_price_series(asset_2)
        
        if len(prices_1) < self.min_observations:
            return None
        
        # Calculate returns
        returns_1 = [
            (prices_1[i] - prices_1[i-1]) / prices_1[i-1]
            if prices_1[i-1] > 0 else Decimal("0")
            for i in range(1, len(prices_1))
        ]
        
        returns_2 = [
            (prices_2[i] - prices_2[i-1]) / prices_2[i-1]
            if prices_2[i-1] > 0 else Decimal("0")
            for i in range(1, len(prices_2))
        ]
        
        # Split into normal and tail periods
        threshold_1 = self._calculate_percentile(returns_1, Decimal("0.05"))
        threshold_2 = self._calculate_percentile(returns_2, Decimal("0.05"))
        
        # Normal period correlations
        normal_corr = self.calculate_correlation(asset_1, asset_2)
        if normal_corr is None:
            normal_corr = Decimal("0")
        
        # Tail period correlation (down markets)
        tail_returns_1 = [r for r in returns_1 if r < threshold_1]
        tail_returns_2 = [r for r in returns_2 if r < threshold_2]
        
        if len(tail_returns_1) > 3 and len(tail_returns_2) > 3:
            tail_corr = self._correlation_from_returns(tail_returns_1, tail_returns_2)
        else:
            tail_corr = normal_corr
        
        # Tail risk ratio
        if normal_corr != 0:
            tail_ratio = tail_corr / (abs(normal_corr) + Decimal("0.0001"))
        else:
            tail_ratio = Decimal("1")
        
        # Decoupling score (how different are they in tails)
        decoupling = Decimal("1") - min(Decimal("1"), abs(tail_corr))
        
        return TailRiskIndicator(
            asset_pair=(asset_1, asset_2),
            normal_correlation=normal_corr,
            tail_correlation=tail_corr,
            tail_risk_ratio=tail_ratio,
            decoupling_score=decoupling,
        )
    
    def _calculate_percentile(
        self,
        values: List[Decimal],
        percentile: Decimal,
    ) -> Decimal:
        """Calculate percentile of values."""
        if not values:
            return Decimal("0")
        
        sorted_vals = sorted(values)
        index = int(len(sorted_vals) * float(percentile))
        return sorted_vals[max(0, index)]
    
    def _correlation_from_returns(
        self,
        returns_1: List[Decimal],
        returns_2: List[Decimal],
    ) -> Decimal:
        """Calculate correlation from return series."""
        if len(returns_1) < 2 or len(returns_2) < 2:
            return Decimal("0")
        
        mean_1 = sum(returns_1) / len(returns_1)
        mean_2 = sum(returns_2) / len(returns_2)
        
        covariance = sum(
            (returns_1[i] - mean_1) * (returns_2[i] - mean_2)
            for i in range(min(len(returns_1), len(returns_2)))
        ) / min(len(returns_1), len(returns_2))
        
        var_1 = sum((r - mean_1) ** 2 for r in returns_1) / len(returns_1)
        var_2 = sum((r - mean_2) ** 2 for r in returns_2) / len(returns_2)
        
        if var_1 == 0 or var_2 == 0:
            return Decimal("0")
        
        return covariance / (var_1 ** Decimal("0.5") * var_2 ** Decimal("0.5"))
    
    # ========================================================================
    # ALERTING
    # ========================================================================
    
    def check_correlation_anomaly(
        self,
        asset_1: str,
        asset_2: str,
        current_correlation: Decimal,
    ) -> Optional[CorrelationAlert]:
        """
        Detect abnormal correlation changes.
        
        Alerts if correlation deviates >2 std dev from historical mean.
        """
        # Get historical correlations
        historical_corrs = []
        for matrix in self._correlation_history:
            if asset_1 in matrix.correlations and asset_2 in matrix.correlations[asset_1]:
                corr = matrix.correlations[asset_1][asset_2]
                if corr is not None:
                    historical_corrs.append(corr)
        
        if len(historical_corrs) < 5:
            return None
        
        mean = sum(historical_corrs) / len(historical_corrs)
        variance = sum((c - mean) ** 2 for c in historical_corrs) / len(historical_corrs)
        std_dev = variance ** Decimal("0.5")
        
        if std_dev == 0:
            return None
        
        z_score = (current_correlation - mean) / std_dev
        
        if abs(z_score) > self.alert_z_score_threshold:
            # Determine alert type
            if z_score > 0:
                alert_type = "spike"
                severity = "high" if z_score > 3 else "medium"
            else:
                alert_type = "breakdown"
                severity = "high" if z_score < -3 else "medium"
            
            alert = CorrelationAlert(
                timestamp=datetime.utcnow(),
                asset_pair=(asset_1, asset_2),
                current_correlation=current_correlation,
                historical_mean=mean,
                std_dev=std_dev,
                z_score=z_score,
                alert_type=alert_type,
                severity=severity,
            )
            
            self._alerts.append(alert)
            self.logger.warning(
                f"⚠️  Correlation anomaly: {asset_1}/{asset_2} "
                f"curr={current_correlation} mean={mean} z={z_score}"
            )
            
            return alert
        
        return None
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def get_alerts(self, hours: int = 24) -> List[CorrelationAlert]:
        """Get recent alerts."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self._alerts if a.timestamp >= cutoff]
    
    def get_correlation_history(self) -> List[CorrelationMatrix]:
        """Get correlation matrix history."""
        return self._correlation_history.copy()
    
    def get_summary(self) -> Dict:
        """Get monitor summary."""
        recent_alerts = self.get_alerts(hours=24)
        
        return {
            "assets_tracked": len(self._price_history),
            "recent_alerts": len(recent_alerts),
            "correlation_updates": len(self._correlation_history),
            "latest_update": self._correlation_history[-1].timestamp if self._correlation_history else None,
        }


# ============================================================================
# FACTORY
# ============================================================================

def create_correlation_monitor() -> CorrelationMonitor:
    """Factory function to create correlation monitor."""
    logger = logging.getLogger("correlation_monitor")
    return CorrelationMonitor(logger=logger)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    monitor = create_correlation_monitor()
    
    # Add sample prices
    now = datetime.utcnow()
    for i in range(50):
        monitor.add_prices({
            "ETH": Decimal("1800") + Decimal(i) * Decimal("10"),
            "USDC": Decimal("1") + Decimal(i) * Decimal("0.001"),
            "DAI": Decimal("1") + Decimal(i) * Decimal("0.0005"),
        }, now - timedelta(hours=50-i))
    
    # Calculate correlation matrix
    matrix = monitor.calculate_correlation_matrix(["ETH", "USDC", "DAI"])
    
    if matrix:
        print(f"\n✅ Correlation matrix calculated")
        print(f"Correlations: {matrix.correlations}")
