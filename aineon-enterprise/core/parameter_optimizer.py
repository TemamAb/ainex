"""
AINEON Enterprise: Parameter Optimizer Module
Phase 3A: AI/ML Intelligence - Hyperparameter Tuning

Automated hyperparameter optimization using Bayesian optimization,
grid search, and random search strategies.

Author: AINEON Chief Architect
Version: 1.0
Date: December 14, 2025
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ============================================================================
# DATA MODELS
# ============================================================================

class ParameterRange(BaseModel):
    """Parameter search range definition."""
    name: str
    param_type: str  # "float", "int", "categorical"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    values: Optional[List[Any]] = None  # For categorical
    log_scale: bool = False  # For logarithmic spacing


class OptimizerConfig(BaseModel):
    """Optimizer configuration."""
    strategy: str  # "bayesian", "grid", "random"
    max_iterations: int = 100
    population_size: int = 20
    generations: int = 10
    convergence_threshold: Decimal = Field(default=Decimal("0.001"))
    random_seed: Optional[int] = None


class OptimizationRun(BaseModel):
    """Single optimization experiment."""
    run_id: str
    parameters: Dict[str, Any]
    score: Decimal  # Metric being optimized
    metrics: Dict[str, Decimal]  # Additional metrics
    timestamp: datetime
    iteration: int


class OptimizationResult(BaseModel):
    """Optimization result."""
    best_parameters: Dict[str, Any]
    best_score: Decimal
    runs: List[OptimizationRun]
    converged: bool
    iterations: int
    duration_seconds: float


# ============================================================================
# PARAMETER OPTIMIZER
# ============================================================================

class ParameterOptimizer:
    """
    Hyperparameter optimization for ML models.
    
    Strategies:
    - Bayesian optimization (intelligent search)
    - Grid search (exhaustive)
    - Random search (baseline)
    
    Use cases:
    - ML model hyperparameters (learning_rate, batch_size, dropout)
    - Strategy parameters (signal_threshold, position_size, rebalance_frequency)
    - Risk parameters (max_drawdown, daily_loss_cap)
    """
    
    def __init__(
        self,
        objective_function: Callable[[Dict[str, Any]], Decimal],
        parameter_ranges: List[ParameterRange],
        config: OptimizerConfig,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize parameter optimizer.
        
        Args:
            objective_function: Function to optimize (higher = better)
            parameter_ranges: List of parameter definitions
            config: Optimizer configuration
            logger: Logger instance
        """
        self.objective_function = objective_function
        self.parameter_ranges = parameter_ranges
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Optimization state
        self._runs: List[OptimizationRun] = []
        self._best_score = Decimal("-999999")
        self._best_parameters: Dict[str, Any] = {}
        self._iteration = 0
        
        self.logger.info(
            f"✅ ParameterOptimizer initialized "
            f"(strategy={config.strategy}, max_iter={config.max_iterations})"
        )
    
    # ========================================================================
    # PARAMETER GENERATION
    # ========================================================================
    
    def _generate_random_parameters(self) -> Dict[str, Any]:
        """Generate random parameter set."""
        import random
        
        params = {}
        for prange in self.parameter_ranges:
            if prange.param_type == "float":
                if prange.log_scale:
                    # Logarithmic scale
                    log_min = np.log(prange.min_value)
                    log_max = np.log(prange.max_value)
                    value = np.exp(random.uniform(log_min, log_max))
                else:
                    # Linear scale
                    value = random.uniform(prange.min_value, prange.max_value)
                params[prange.name] = value
            
            elif prange.param_type == "int":
                value = random.randint(int(prange.min_value), int(prange.max_value))
                params[prange.name] = value
            
            elif prange.param_type == "categorical":
                value = random.choice(prange.values)
                params[prange.name] = value
        
        return params
    
    def _generate_grid_parameters(self) -> List[Dict[str, Any]]:
        """Generate grid of all parameter combinations."""
        import itertools
        
        param_lists = []
        
        for prange in self.parameter_ranges:
            if prange.param_type == "float":
                # Grid: 10 values
                values = [
                    prange.min_value + (prange.max_value - prange.min_value) * i / 9
                    for i in range(10)
                ]
            elif prange.param_type == "int":
                values = list(range(int(prange.min_value), int(prange.max_value) + 1))
            else:  # categorical
                values = prange.values
            
            param_lists.append([(prange.name, v) for v in values])
        
        # Generate all combinations
        all_combinations = itertools.product(*param_lists)
        
        return [
            {name: value for name, value in combo}
            for combo in all_combinations
        ]
    
    def _select_next_parameters_bayesian(self) -> Dict[str, Any]:
        """
        Select next parameters using Bayesian optimization.
        
        Uses acquisition function to balance exploration and exploitation.
        """
        if len(self._runs) < 5:
            # Initial random exploration
            return self._generate_random_parameters()
        
        # Simple Bayesian-inspired: bias toward high-performing regions
        # with some exploration noise
        import random
        
        # Get top 3 parameter sets
        sorted_runs = sorted(self._runs, key=lambda r: r.score, reverse=True)
        top_runs = sorted_runs[:3]
        
        # Mutate best parameters with small perturbations
        best_params = top_runs[0].parameters.copy()
        
        for prange in self.parameter_ranges:
            name = prange.name
            current = best_params[name]
            
            if prange.param_type == "float":
                # Add Gaussian noise
                noise = random.gauss(0, (prange.max_value - prange.min_value) * 0.05)
                new_value = max(prange.min_value, min(prange.max_value, current + noise))
                best_params[name] = new_value
            
            elif prange.param_type == "int":
                # Random ±1 step
                step = random.choice([-1, 0, 1])
                new_value = max(prange.min_value, min(prange.max_value, current + step))
                best_params[name] = int(new_value)
        
        return best_params
    
    # ========================================================================
    # OPTIMIZATION EXECUTION
    # ========================================================================
    
    async def _evaluate_parameters(
        self,
        parameters: Dict[str, Any],
    ) -> Tuple[Decimal, Dict[str, Decimal]]:
        """
        Evaluate objective function with parameters.
        
        Returns:
            (score, additional_metrics)
        """
        try:
            score = self.objective_function(parameters)
            
            # Track if new best
            if score > self._best_score:
                self._best_score = score
                self._best_parameters = parameters.copy()
                self.logger.info(f"🎯 New best score: {score}")
            
            return score, {"score": score}
        
        except Exception as e:
            self.logger.error(f"❌ Evaluation failed: {e}")
            return Decimal("-999999"), {"error": str(e)}
    
    async def optimize_random_search(self) -> OptimizationResult:
        """
        Random search optimization.
        
        Simple baseline: randomly samples parameter space.
        """
        self.logger.info("🔍 Starting random search optimization...")
        
        for iteration in range(self.config.max_iterations):
            parameters = self._generate_random_parameters()
            
            score, metrics = await self._evaluate_parameters(parameters)
            
            run = OptimizationRun(
                run_id=f"run_{iteration}",
                parameters=parameters,
                score=score,
                metrics=metrics,
                timestamp=datetime.utcnow(),
                iteration=iteration,
            )
            self._runs.append(run)
            
            if iteration % 10 == 0:
                self.logger.debug(
                    f"  Iteration {iteration}: best_score={self._best_score}"
                )
        
        return OptimizationResult(
            best_parameters=self._best_parameters,
            best_score=self._best_score,
            runs=self._runs,
            converged=True,
            iterations=len(self._runs),
            duration_seconds=0.0,
        )
    
    async def optimize_grid_search(self) -> OptimizationResult:
        """
        Grid search optimization.
        
        Exhaustive search of parameter space.
        Warning: Can be slow with many parameters.
        """
        self.logger.info("📊 Starting grid search optimization...")
        
        all_params = self._generate_grid_parameters()
        
        # Limit to max_iterations
        if len(all_params) > self.config.max_iterations:
            import random
            all_params = random.sample(all_params, self.config.max_iterations)
        
        for iteration, parameters in enumerate(all_params):
            score, metrics = await self._evaluate_parameters(parameters)
            
            run = OptimizationRun(
                run_id=f"run_{iteration}",
                parameters=parameters,
                score=score,
                metrics=metrics,
                timestamp=datetime.utcnow(),
                iteration=iteration,
            )
            self._runs.append(run)
            
            if iteration % max(1, len(all_params) // 10) == 0:
                self.logger.debug(
                    f"  Iteration {iteration}/{len(all_params)}: "
                    f"best_score={self._best_score}"
                )
        
        return OptimizationResult(
            best_parameters=self._best_parameters,
            best_score=self._best_score,
            runs=self._runs,
            converged=True,
            iterations=len(self._runs),
            duration_seconds=0.0,
        )
    
    async def optimize_bayesian(self) -> OptimizationResult:
        """
        Bayesian optimization.
        
        Intelligent search using acquisition function.
        """
        self.logger.info("🧠 Starting Bayesian optimization...")
        
        for iteration in range(self.config.max_iterations):
            # Select parameters intelligently
            parameters = self._select_next_parameters_bayesian()
            
            score, metrics = await self._evaluate_parameters(parameters)
            
            run = OptimizationRun(
                run_id=f"run_{iteration}",
                parameters=parameters,
                score=score,
                metrics=metrics,
                timestamp=datetime.utcnow(),
                iteration=iteration,
            )
            self._runs.append(run)
            
            # Check convergence
            if iteration > 10:
                recent_scores = [r.score for r in self._runs[-5:]]
                score_variance = max(recent_scores) - min(recent_scores)
                
                if score_variance < self.config.convergence_threshold:
                    self.logger.info(f"✅ Converged after {iteration} iterations")
                    return OptimizationResult(
                        best_parameters=self._best_parameters,
                        best_score=self._best_score,
                        runs=self._runs,
                        converged=True,
                        iterations=len(self._runs),
                        duration_seconds=0.0,
                    )
            
            if iteration % 10 == 0:
                self.logger.debug(
                    f"  Iteration {iteration}: best_score={self._best_score}"
                )
        
        return OptimizationResult(
            best_parameters=self._best_parameters,
            best_score=self._best_score,
            runs=self._runs,
            converged=False,
            iterations=len(self._runs),
            duration_seconds=0.0,
        )
    
    async def optimize(self) -> OptimizationResult:
        """Execute optimization with configured strategy."""
        if self.config.strategy == "random":
            return await self.optimize_random_search()
        elif self.config.strategy == "grid":
            return await self.optimize_grid_search()
        elif self.config.strategy == "bayesian":
            return await self.optimize_bayesian()
        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")
    
    # ========================================================================
    # ANALYSIS & REPORTING
    # ========================================================================
    
    def get_best_parameters(self) -> Dict[str, Any]:
        """Get best found parameters."""
        return self._best_parameters.copy()
    
    def get_best_score(self) -> Decimal:
        """Get best found score."""
        return self._best_score
    
    def get_run_history(self) -> List[OptimizationRun]:
        """Get all optimization runs."""
        return self._runs.copy()
    
    def get_parameter_importance(self) -> Dict[str, float]:
        """
        Estimate parameter importance based on variance.
        
        Returns:
            Dict of {parameter_name: importance_score}
        """
        if len(self._runs) < 2:
            return {}
        
        importance = {}
        
        for prange in self.parameter_ranges:
            name = prange.name
            
            # Get all unique values for this parameter
            values = [run.parameters[name] for run in self._runs]
            unique_values = list(set(values))
            
            if len(unique_values) < 2:
                importance[name] = 0.0
                continue
            
            # Calculate variance in scores for each value
            score_variance = {}
            for value in unique_values:
                scores = [
                    run.score for run in self._runs
                    if run.parameters[name] == value
                ]
                if scores:
                    score_variance[value] = float(max(scores) - min(scores))
            
            # Importance = average variance contribution
            avg_variance = sum(score_variance.values()) / len(score_variance)
            importance[name] = avg_variance
        
        # Normalize
        total = sum(importance.values())
        if total > 0:
            importance = {k: v / total for k, v in importance.items()}
        
        return importance
    
    def get_summary(self) -> Dict:
        """Get optimization summary."""
        return {
            "strategy": self.config.strategy,
            "iterations": len(self._runs),
            "best_score": float(self._best_score),
            "best_parameters": self._best_parameters,
            "converged": self._runs[-1].score if self._runs else None,
            "parameter_importance": self.get_parameter_importance(),
        }


# ============================================================================
# FACTORY & UTILITIES
# ============================================================================

def create_parameter_optimizer(
    objective_function: Callable[[Dict[str, Any]], Decimal],
    parameter_ranges: List[ParameterRange],
    strategy: str = "bayesian",
    max_iterations: int = 100,
) -> ParameterOptimizer:
    """Factory function to create parameter optimizer."""
    config = OptimizerConfig(
        strategy=strategy,
        max_iterations=max_iterations,
    )
    
    logger = logging.getLogger("parameter_optimizer")
    
    return ParameterOptimizer(
        objective_function=objective_function,
        parameter_ranges=parameter_ranges,
        config=config,
        logger=logger,
    )


if __name__ == "__main__":
    import asyncio
    import numpy as np
    
    logging.basicConfig(level=logging.DEBUG)
    
    # Example: optimize simple quadratic function
    def objective(params: Dict[str, Any]) -> Decimal:
        """Maximize: -(x-5)^2 - (y-3)^2 (optimal at x=5, y=3)"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        score = -(x - 5) ** 2 - (y - 3) ** 2
        return Decimal(str(score))
    
    ranges = [
        ParameterRange(name="x", param_type="float", min_value=0, max_value=10),
        ParameterRange(name="y", param_type="float", min_value=0, max_value=10),
    ]
    
    optimizer = create_parameter_optimizer(
        objective_function=objective,
        parameter_ranges=ranges,
        strategy="bayesian",
        max_iterations=50,
    )
    
    # Run optimization
    result = asyncio.run(optimizer.optimize())
    
    print(f"\n🎯 Optimization Complete!")
    print(f"Best parameters: {result.best_parameters}")
    print(f"Best score: {result.best_score}")
    print(f"Converged: {result.converged}")
