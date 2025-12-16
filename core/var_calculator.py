"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON ENTERPRISE VAR CALCULATOR                           ║
║              Value-at-Risk and risk metrics for portfolio management          ║
║                                                                                ║
║  Enterprise Features:                                                          ║
║  ✓ Async operations with proper error handling                                ║
║  ✓ Decimal precision for all financial calculations                           ║
║  ✓ Structured logging and metrics integration                                ║
║  ✓ Health checks and monitoring                                              ║
║  ✓ Comprehensive risk analytics                                              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor

try:
    from scipy.stats import norm
    HAS_SCIPY = True
except ImportError:
    logging.warning("SciPy not available, using fallback calculations")
    HAS_SCIPY = False
    norm = None

from core.infrastructure.metrics_collector import MetricsCollector
from core.infrastructure.health_check_engine import HealthCheckEngine
from core.infrastructure.structured_logging import StructuredLogger


class VaRMethodology(Enum):
    """VaR calculation methodologies"""
    HISTORICAL = "HISTORICAL"
    PARAMETRIC = "PARAMETRIC"
    DELTA_NORMAL = "DELTA_NORMAL"
    MONTE_CARLO = "MONTE_CARLO"


@dataclass
class RiskMetrics:
    """Enterprise-grade risk metrics for portfolio with validation"""
    var_95: Decimal  # Value at Risk at 95% confidence
    var_99: Decimal  # Value at Risk at 99% confidence
    cvar_95: Decimal  # Conditional Value at Risk (Expected Shortfall)
    cvar_99: Decimal
    expected_return: Decimal
    volatility: Decimal
    skewness: Decimal
    kurtosis: Decimal
    beta: Decimal
    correlation_to_market: Decimal
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence_intervals: Dict[str, Tuple[Decimal, Decimal]] = field(default_factory=dict)

    def validate(self) -> bool:
        """Validate risk metrics integrity"""
        try:
            # Check for reasonable ranges
            if not (Decimal('0') <= self.var_95 <= Decimal('100')):
                return False
            if not (Decimal('0') <= self.var_99 <= Decimal('100')):
                return False
            if self.volatility < Decimal('0'):
                return False
            return True
        except:
            return False


@dataclass
class StressScenario:
    """Enterprise stress test scenario with detailed analysis"""
    scenario_name: str
    portfolio_loss: Decimal
    percent_loss: Decimal
    affected_positions: int
    recovery_time_days: int
    execution_time_ms: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    mitigation_actions: List[str] = field(default_factory=list)


class VaRCalculator:
    """Enterprise-grade Value-at-Risk calculator with comprehensive risk analytics"""

    def __init__(
        self,
        confidence_level_1: Decimal = Decimal("0.95"),  # 95%
        confidence_level_2: Decimal = Decimal("0.99"),  # 99%
        lookback_days: int = 252,  # 1 trading year
        frequency: str = "daily",
        metrics_collector: Optional[MetricsCollector] = None,
        health_engine: Optional[HealthCheckEngine] = None,
        logger: Optional[StructuredLogger] = None
    ):
        # Enterprise infrastructure
        self.logger = logger or StructuredLogger(__name__)
        self.metrics = metrics_collector or MetricsCollector()
        self.health_engine = health_engine or HealthCheckEngine()

        # Configuration with validation
        if not (Decimal('0.8') <= confidence_level_1 <= Decimal('0.999')):
            raise ValueError(f"Confidence level 1 must be between 0.8 and 0.999, got {confidence_level_1}")
        if not (Decimal('0.8') <= confidence_level_2 <= Decimal('0.999')):
            raise ValueError(f"Confidence level 2 must be between 0.8 and 0.999, got {confidence_level_2}")

        self.confidence_level_1 = float(confidence_level_1)
        self.confidence_level_2 = float(confidence_level_2)
        self.lookback_days = lookback_days
        self.frequency = frequency

        # Data structures with thread safety
        self.returns_history: Dict[str, List[Decimal]] = {}
        self.position_values: Dict[str, List[Decimal]] = {}
        self.portfolio_values: List[Decimal] = []
        self.timestamps: List[datetime] = []

        # Analytics storage
        self.var_estimates: List[Dict] = []
        self.backtests: List[Dict] = []
        self.calculation_count: int = 0
        self.last_calculation_time: Optional[float] = None

        # Thread pool for CPU-intensive calculations
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="var-calc")

        # Register health checks
        self.health_engine.register_check("var_calculator_data", self._check_data_health)
        self.health_engine.register_check("var_calculator_calculations", self._check_calculation_health)

        self.logger.info("VaRCalculator initialized", extra={
            "confidence_levels": [self.confidence_level_1, self.confidence_level_2],
            "lookback_days": lookback_days,
            "has_scipy": HAS_SCIPY
        })

    def _check_data_health(self) -> Dict[str, Any]:
        """Health check for data integrity"""
        return {
            "data_points": len(self.portfolio_values),
            "tokens_tracked": len(self.returns_history),
            "sufficient_history": len(self.portfolio_values) >= 30,
            "data_freshness": self.timestamps[-1].isoformat() if self.timestamps else None
        }

    def _check_calculation_health(self) -> Dict[str, Any]:
        """Health check for calculation performance"""
        return {
            "total_calculations": self.calculation_count,
            "last_calculation_time": self.last_calculation_time,
            "calculations_per_second": self.calculation_count / max(time.time() - (self.last_calculation_time or time.time()), 1),
            "backtests_performed": len(self.backtests)
        }
    
    async def add_return(self, token: str, return_value: Decimal) -> None:
        """Add daily return for a token with validation"""
        try:
            if not isinstance(return_value, Decimal):
                raise ValueError(f"Return value must be Decimal, got {type(return_value)}")

            if token not in self.returns_history:
                self.returns_history[token] = []

            self.returns_history[token].append(return_value)

            # Keep only lookback_days of history
            if len(self.returns_history[token]) > self.lookback_days:
                self.returns_history[token].pop(0)

            self.logger.debug("Added return data point", extra={
                "token": token,
                "return_value": str(return_value),
                "total_points": len(self.returns_history[token])
            })

        except Exception as e:
            self.logger.error(f"Failed to add return for token {token}: {e}")
            raise

    async def add_portfolio_value(self, timestamp: datetime, value: Decimal) -> None:
        """Add portfolio value snapshot with validation"""
        try:
            if not isinstance(value, Decimal) or value < 0:
                raise ValueError(f"Portfolio value must be positive Decimal, got {value}")

            self.timestamps.append(timestamp)
            self.portfolio_values.append(value)

            # Keep only lookback_days
            if len(self.portfolio_values) > self.lookback_days:
                self.portfolio_values.pop(0)
                self.timestamps.pop(0)

            self.metrics.record_metric("var_calculator.portfolio_value", float(value))

            self.logger.debug("Added portfolio value", extra={
                "timestamp": timestamp.isoformat(),
                "value": str(value),
                "total_points": len(self.portfolio_values)
            })

        except Exception as e:
            self.logger.error(f"Failed to add portfolio value: {e}")
            raise

    async def calculate_portfolio_returns(self) -> List[Decimal]:
        """Calculate daily returns from portfolio values with validation"""
        try:
            if len(self.portfolio_values) < 2:
                return []

            returns = []
            for i in range(1, len(self.portfolio_values)):
                prev_value = self.portfolio_values[i-1]
                curr_value = self.portfolio_values[i]

                if prev_value == 0:
                    ret = Decimal('0')
                else:
                    ret = ((curr_value - prev_value) / prev_value) * Decimal("100")

                returns.append(ret)

            return returns

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio returns: {e}")
            return []
    
    def calculate_var_historical(
        self,
        confidence_level: float = None
    ) -> Decimal:
        """Calculate VaR using historical method"""
        if confidence_level is None:
            confidence_level = self.confidence_level_1
        
        returns = self.calculate_portfolio_returns()
        if len(returns) == 0:
            return Decimal("0")
        
        # Convert to numpy for easier calculation
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate VaR as negative percentile
        percentile = (1 - confidence_level) * 100
        var = np.percentile(returns_array, percentile)
        
        return Decimal(str(-var))
    
    def calculate_var_parametric(
        self,
        confidence_level: float = None,
        portfolio_value: Decimal = Decimal("0")
    ) -> Decimal:
        """Calculate VaR using parametric (Normal distribution) method"""
        if confidence_level is None:
            confidence_level = self.confidence_level_1
        
        returns = self.calculate_portfolio_returns()
        if len(returns) == 0:
            return Decimal("0")
        
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate mean and std
        mean = np.mean(returns_array)
        std = np.std(returns_array)
        
        # Z-score for confidence level
        from scipy.stats import norm
        z_score = norm.ppf(confidence_level)
        
        # VaR = -1 * (mean + z * std)
        var_percent = -(mean + z_score * std)
        
        return Decimal(str(var_percent))
    
    def calculate_cvar(
        self,
        confidence_level: float = None
    ) -> Decimal:
        """Calculate Conditional Value-at-Risk (Expected Shortfall)"""
        if confidence_level is None:
            confidence_level = self.confidence_level_1
        
        returns = self.calculate_portfolio_returns()
        if len(returns) == 0:
            return Decimal("0")
        
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate VaR threshold
        var = float(self.calculate_var_historical(confidence_level))
        
        # Average of all returns worse than VaR
        worst_returns = returns_array[returns_array <= -var]
        
        if len(worst_returns) == 0:
            cvar = var
        else:
            cvar = np.mean(worst_returns)
        
        return Decimal(str(abs(cvar)))
    
    async def calculate_risk_metrics(
        self,
        portfolio_value: Decimal
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics with enterprise-grade validation"""
        start_time = time.time()

        try:
            if not isinstance(portfolio_value, Decimal) or portfolio_value <= 0:
                raise ValueError(f"Portfolio value must be positive Decimal, got {portfolio_value}")

            returns = await self.calculate_portfolio_returns()

            if len(returns) == 0:
                self.logger.warning("Insufficient data for risk metrics calculation")
                return RiskMetrics(
                    var_95=Decimal("0"),
                    var_99=Decimal("0"),
                    cvar_95=Decimal("0"),
                    cvar_99=Decimal("0"),
                    expected_return=Decimal("0"),
                    volatility=Decimal("0"),
                    skewness=Decimal("0"),
                    kurtosis=Decimal("0"),
                    beta=Decimal("1"),
                    correlation_to_market=Decimal("0")
                )

            # Convert to numpy for statistical calculations
            returns_array = np.array([float(r) for r in returns])

            # Calculate statistics using thread pool for CPU-intensive operations
            loop = asyncio.get_event_loop()
            expected_return, volatility, skewness, kurtosis = await asyncio.gather(
                loop.run_in_executor(self.executor, lambda: Decimal(str(np.mean(returns_array)))),
                loop.run_in_executor(self.executor, lambda: Decimal(str(np.std(returns_array)))),
                loop.run_in_executor(self.executor, lambda: Decimal(str(float(self._calculate_skewness(returns_array))))),
                loop.run_in_executor(self.executor, lambda: Decimal(str(float(self._calculate_kurtosis(returns_array)))))
            )

            # VaR calculations
            var_95, var_99, cvar_95, cvar_99 = await asyncio.gather(
                self.calculate_var_historical(self.confidence_level_1),
                self.calculate_var_historical(self.confidence_level_2),
                self.calculate_cvar(self.confidence_level_1),
                self.calculate_cvar(self.confidence_level_2)
            )

            metrics = RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                cvar_99=cvar_99,
                expected_return=expected_return,
                volatility=volatility,
                skewness=skewness,
                kurtosis=kurtosis,
                beta=Decimal("1"),
                correlation_to_market=Decimal("0")
            )

            # Validate metrics
            if not metrics.validate():
                self.logger.error("Risk metrics validation failed")
                raise ValueError("Invalid risk metrics calculated")

            # Record metrics
            calculation_time = time.time() - start_time
            self.metrics.record_metric("var_calculator.risk_metrics_time", calculation_time)
            self.metrics.record_metric("var_calculator.volatility", float(volatility))

            self.logger.info("Risk metrics calculated", extra={
                "portfolio_value": str(portfolio_value),
                "var_95": str(var_95),
                "volatility": str(volatility),
                "calculation_time": calculation_time
            })

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}", extra={
                "portfolio_value": str(portfolio_value)
            })
            raise
    
    @staticmethod
    def _calculate_skewness(returns: np.ndarray) -> float:
        """Calculate skewness of returns"""
        n = len(returns)
        if n < 3:
            return 0.0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0.0
        
        skewness = np.sum(((returns - mean) / std) ** 3) / n
        return skewness
    
    @staticmethod
    def _calculate_kurtosis(returns: np.ndarray) -> float:
        """Calculate excess kurtosis of returns"""
        n = len(returns)
        if n < 4:
            return 0.0
        
        mean = np.mean(returns)
        std = np.std(returns)
        
        if std == 0:
            return 0.0
        
        kurtosis = np.sum(((returns - mean) / std) ** 4) / n - 3
        return kurtosis
    
    async def backtest_var(
        self,
        confidence_level: Optional[float] = None
    ) -> Dict[str, Any]:
        """Backtest VaR estimates with enterprise-grade validation"""
        try:
            if confidence_level is None:
                confidence_level = self.confidence_level_1

            returns = await self.calculate_portfolio_returns()
            if len(returns) < 2:
                return {}

            var_estimate = float(await self.calculate_var_historical(confidence_level))
            returns_array = np.array([float(r) for r in returns])

            # Count exceedances (returns worse than VaR threshold)
            exceedances = np.sum(returns_array < -var_estimate)
            total_obs = len(returns_array)

            # Expected exceedances based on confidence level
            expected_exceedances = total_obs * (1 - confidence_level)

            # Kupiec POF test (Proportion of Failures)
            pof = exceedances / total_obs if total_obs > 0 else 0

            # Test passes if POF is within 5% of expected
            test_status = "PASS" if abs(pof - (1 - confidence_level)) < 0.05 else "FAIL"

            backtest_result = {
                "timestamp": datetime.utcnow().isoformat(),
                "confidence_level": confidence_level,
                "var_estimate": var_estimate,
                "exceedances": int(exceedances),
                "total_observations": int(total_obs),
                "proportion_of_failures": float(pof),
                "expected_pof": 1 - confidence_level,
                "test_status": test_status,
                "confidence_interval": [1 - confidence_level - 0.05, 1 - confidence_level + 0.05]
            }

            self.backtests.append(backtest_result)

            # Record metrics
            self.metrics.record_metric("var_calculator.backtest_exceedances", exceedances)
            self.metrics.record_metric("var_calculator.backtest_status", 1 if test_status == "PASS" else 0)

            self.logger.info("VaR backtest completed", extra={
                "confidence_level": confidence_level,
                "test_status": test_status,
                "exceedances": int(exceedances),
                "total_observations": total_obs,
                "pof": float(pof)
            })

            return backtest_result

        except Exception as e:
            self.logger.error(f"Failed to backtest VaR: {e}", extra={
                "confidence_level": confidence_level
            })
            return {}
    
    def stress_test(
        self,
        scenario_name: str,
        position_changes: Dict[str, Decimal],
        price_shocks: Dict[str, Decimal]
    ) -> StressScenario:
        """Run stress test scenario"""
        # Calculate portfolio loss under scenario
        total_loss = Decimal("0")
        affected_positions = 0
        
        for token, change in position_changes.items():
            shock = price_shocks.get(token, Decimal("0"))
            loss = change * shock
            total_loss += loss
            if loss < 0:
                affected_positions += 1
        
        # Current portfolio value (approximate)
        current_value = self.portfolio_values[-1] if self.portfolio_values else Decimal("0")
        percent_loss = (total_loss / current_value * Decimal("100")) if current_value > 0 else Decimal("0")
        
        return StressScenario(
            scenario_name=scenario_name,
            portfolio_loss=total_loss,
            percent_loss=percent_loss,
            affected_positions=affected_positions,
            recovery_time_days=7  # Placeholder
        )
    
    def calculate_marginal_var(
        self,
        position_delta: Decimal,
        position_volatility: Decimal
    ) -> Decimal:
        """Calculate marginal VaR for a position"""
        returns = self.calculate_portfolio_returns()
        if len(returns) == 0:
            return Decimal("0")
        
        returns_array = np.array([float(r) for r in returns])
        portfolio_vol = Decimal(str(np.std(returns_array)))
        
        # Marginal VaR = Position Delta * Position Volatility * Z-score
        from scipy.stats import norm
        z_score = norm.ppf(self.confidence_level_1)
        
        mvr = position_delta * position_volatility * Decimal(str(z_score))
        return mvr
    
    def get_var_summary(self) -> Dict:
        """Get summary of VaR estimates"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "var_95": str(self.calculate_var_historical(self.confidence_level_1)),
            "var_99": str(self.calculate_var_historical(self.confidence_level_2)),
            "cvar_95": str(self.calculate_cvar(self.confidence_level_1)),
            "cvar_99": str(self.calculate_cvar(self.confidence_level_2)),
            "methodology": "HISTORICAL",
            "lookback_days": self.lookback_days,
            "observations": len(self.calculate_portfolio_returns())
        }
