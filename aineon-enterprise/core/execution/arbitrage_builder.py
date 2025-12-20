"""
Arbitrage Builder - Multi-Step Execution Planning
Builds atomic arbitrage execution plans combining multiple DEXs
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from dataclasses import dataclass, asdict
import json

from core.execution.uniswap_v3_executor import UniswapV3Executor
from core.execution.curve_executor import CurveExecutor

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageStep:
    """Single step in arbitrage execution"""
    step_number: int
    dex: str  # "uniswap_v3" or "curve"
    token_in: str
    token_out: str
    amount_in: int
    amount_out_expected: int
    amount_out_minimum: int
    calldata: str
    gas_estimate: int
    fee_estimate: float


@dataclass
class ArbitrageExecutionPlan:
    """Complete arbitrage execution plan"""
    plan_id: str
    strategy: str
    steps: List[ArbitrageStep]
    total_profit_estimate: Decimal
    total_gas_estimate: int
    net_profit_estimate: Decimal
    cumulative_slippage: float
    roi_percentage: float
    execution_probability: float
    timestamp: int


class ArbitrageBuilder:
    """
    Arbitrage execution plan builder
    
    Constructs atomic execution plans for:
    - Multi-DEX arbitrage (Uniswap ↔ Curve)
    - Path finding and optimization
    - Slippage aggregation
    - Profitability verification
    """
    
    def __init__(self):
        """Initialize builder"""
        self.uniswap_v3 = UniswapV3Executor()
        self.curve = CurveExecutor()
        self.metrics = {
            "plans_created": 0,
            "plans_executed": 0,
            "plans_failed": 0,
            "total_profit": Decimal(0),
            "total_loss": Decimal(0)
        }
    
    def build_two_hop_arbitrage(
        self,
        token_a: str,
        token_b: str,
        amount_in: int,
        dex_path: List[str] = None  # ["uniswap_v3", "curve"]
    ) -> Optional[ArbitrageExecutionPlan]:
        """
        Build simple 2-hop arbitrage plan
        
        Example: USDC → Uniswap V3 → USDT → Curve → USDC
        
        Args:
            token_a: Starting token (e.g., USDC)
            token_b: Intermediate token (e.g., USDT)
            amount_in: Input amount
            dex_path: List of DEXs to use
        
        Returns:
            ArbitrageExecutionPlan or None
        """
        try:
            if dex_path is None:
                dex_path = ["uniswap_v3", "curve"]
            
            if len(dex_path) != 2:
                logger.error("2-hop arbitrage requires exactly 2 DEXs")
                return None
            
            steps: List[ArbitrageStep] = []
            current_amount = amount_in
            cumulative_slippage = 0
            total_gas = 0
            
            # Step 1: Token A → Token B on first DEX
            step1 = self._build_step(
                step_number=1,
                dex=dex_path[0],
                token_in=token_a,
                token_out=token_b,
                amount_in=current_amount
            )
            
            if step1 is None:
                return None
            
            steps.append(step1)
            current_amount = step1.amount_out_minimum
            cumulative_slippage += step1.fee_estimate
            total_gas += step1.gas_estimate
            
            # Step 2: Token B → Token A on second DEX
            step2 = self._build_step(
                step_number=2,
                dex=dex_path[1],
                token_in=token_b,
                token_out=token_a,
                amount_in=current_amount
            )
            
            if step2 is None:
                return None
            
            steps.append(step2)
            current_amount = step2.amount_out_minimum
            cumulative_slippage += step2.fee_estimate
            total_gas += step2.gas_estimate
            
            # Calculate profitability
            profit = current_amount - amount_in
            gas_cost_wei = total_gas * 50 * 1e9  # 50 gwei estimate
            gas_cost_amount = Decimal(gas_cost_wei) / Decimal(1e18)
            net_profit = Decimal(current_amount) - Decimal(amount_in) - gas_cost_amount
            
            # Calculate ROI
            roi = float((net_profit / amount_in) * 100) if amount_in > 0 else 0
            
            # Execution probability (based on slippage and gas costs)
            execution_prob = self._calculate_execution_probability(
                net_profit, cumulative_slippage, roi
            )
            
            import time
            plan = ArbitrageExecutionPlan(
                plan_id=f"arb_{int(time.time())}",
                strategy="multi_dex_arbitrage_2hop",
                steps=steps,
                total_profit_estimate=Decimal(profit),
                total_gas_estimate=total_gas,
                net_profit_estimate=net_profit,
                cumulative_slippage=cumulative_slippage,
                roi_percentage=roi,
                execution_probability=execution_prob,
                timestamp=int(time.time())
            )
            
            logger.info(
                f"Built 2-hop arbitrage: {token_a} → {token_b} → {token_a} | "
                f"Profit: {profit} ({roi:.2f}% ROI) | "
                f"Execution prob: {execution_prob:.1%}"
            )
            
            return plan
        
        except Exception as e:
            logger.error(f"Error building 2-hop arbitrage: {e}")
            return None
    
    def build_three_hop_arbitrage(
        self,
        token_a: str,
        token_b: str,
        token_c: str,
        amount_in: int,
        dex_path: List[str] = None
    ) -> Optional[ArbitrageExecutionPlan]:
        """
        Build 3-hop arbitrage plan
        
        Example: USDC → Uniswap V3 → USDT → Curve → DAI → Uniswap → USDC
        """
        try:
            if dex_path is None:
                dex_path = ["uniswap_v3", "curve", "uniswap_v3"]
            
            if len(dex_path) != 3:
                logger.error("3-hop arbitrage requires exactly 3 DEXs")
                return None
            
            steps: List[ArbitrageStep] = []
            tokens = [token_a, token_b, token_c, token_a]  # Back to start
            current_amount = amount_in
            cumulative_slippage = 0
            total_gas = 0
            
            # Build each step
            for i in range(3):
                step = self._build_step(
                    step_number=i + 1,
                    dex=dex_path[i],
                    token_in=tokens[i],
                    token_out=tokens[i + 1],
                    amount_in=current_amount
                )
                
                if step is None:
                    return None
                
                steps.append(step)
                current_amount = step.amount_out_minimum
                cumulative_slippage += step.fee_estimate
                total_gas += step.gas_estimate
            
            # Calculate profitability
            profit = current_amount - amount_in
            gas_cost_wei = total_gas * 50 * 1e9
            gas_cost_amount = Decimal(gas_cost_wei) / Decimal(1e18)
            net_profit = Decimal(current_amount) - Decimal(amount_in) - gas_cost_amount
            
            roi = float((net_profit / amount_in) * 100) if amount_in > 0 else 0
            execution_prob = self._calculate_execution_probability(
                net_profit, cumulative_slippage, roi
            )
            
            import time
            plan = ArbitrageExecutionPlan(
                plan_id=f"arb_{int(time.time())}",
                strategy="multi_dex_arbitrage_3hop",
                steps=steps,
                total_profit_estimate=Decimal(profit),
                total_gas_estimate=total_gas,
                net_profit_estimate=net_profit,
                cumulative_slippage=cumulative_slippage,
                roi_percentage=roi,
                execution_probability=execution_prob,
                timestamp=int(time.time())
            )
            
            logger.info(
                f"Built 3-hop arbitrage: {token_a} → {token_b} → {token_c} → {token_a} | "
                f"Profit: {profit} ({roi:.2f}% ROI) | "
                f"Execution prob: {execution_prob:.1%}"
            )
            
            return plan
        
        except Exception as e:
            logger.error(f"Error building 3-hop arbitrage: {e}")
            return None
    
    def validate_execution_plan(
        self,
        plan: ArbitrageExecutionPlan,
        min_profit: Decimal = Decimal("0.5"),
        min_probability: float = 0.85
    ) -> Dict[str, Any]:
        """
        Validate if execution plan meets criteria
        
        Args:
            plan: Execution plan to validate
            min_profit: Minimum profit in ETH
            min_probability: Minimum success probability (0-1)
        
        Returns:
            {
                "valid": bool,
                "profit_valid": bool,
                "probability_valid": bool,
                "slippage_valid": bool,
                "reasons": List[str]
            }
        """
        reasons = []
        
        # Check profit
        profit_valid = plan.net_profit_estimate >= min_profit
        if not profit_valid:
            reasons.append(
                f"Profit {plan.net_profit_estimate} ETH < "
                f"minimum {min_profit} ETH"
            )
        
        # Check execution probability
        prob_valid = plan.execution_probability >= min_probability
        if not prob_valid:
            reasons.append(
                f"Probability {plan.execution_probability:.1%} < "
                f"minimum {min_probability:.1%}"
            )
        
        # Check slippage
        max_slippage = 0.001  # 0.1%
        slippage_valid = plan.cumulative_slippage <= (max_slippage * 100)
        if not slippage_valid:
            reasons.append(
                f"Slippage {plan.cumulative_slippage:.3f}% > "
                f"maximum {max_slippage*100:.3f}%"
            )
        
        valid = profit_valid and prob_valid and slippage_valid
        
        result = {
            "valid": valid,
            "profit_valid": profit_valid,
            "probability_valid": prob_valid,
            "slippage_valid": slippage_valid,
            "reasons": reasons,
            "plan_id": plan.plan_id
        }
        
        logger.info(
            f"Plan validation: {'✓' if valid else '✗'} | "
            f"Profit: {plan.net_profit_estimate:.6f} ETH | "
            f"Prob: {plan.execution_probability:.1%} | "
            f"Slippage: {plan.cumulative_slippage:.3f}%"
        )
        
        return result
    
    def _build_step(
        self,
        step_number: int,
        dex: str,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> Optional[ArbitrageStep]:
        """Build single execution step"""
        try:
            if dex == "uniswap_v3":
                estimate = self.uniswap_v3.estimate_swap_output(
                    token_in, token_out, Decimal(amount_in)
                )
            elif dex == "curve":
                estimate = self.curve.estimate_stable_swap_output(
                    token_in, token_out, amount_in
                )
            else:
                logger.error(f"Unknown DEX: {dex}")
                return None
            
            if estimate is None:
                return None
            
            # Build calldata
            if dex == "uniswap_v3":
                success, calldata = self.uniswap_v3.build_swap_calldata(
                    token_in, token_out,
                    amount_in,
                    estimate["min_amount_out"]
                )
            else:
                success, calldata = self.curve.build_stable_swap_calldata(
                    estimate["pool_address"],
                    estimate["token_in_index"],
                    estimate["token_out_index"],
                    amount_in,
                    estimate["min_amount_out"]
                )
            
            if not success:
                return None
            
            step = ArbitrageStep(
                step_number=step_number,
                dex=dex,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out_expected=int(estimate["amount_out"]),
                amount_out_minimum=estimate["min_amount_out"],
                calldata=calldata,
                gas_estimate=estimate["gas_estimate"],
                fee_estimate=estimate["expected_slippage"]
            )
            
            return step
        
        except Exception as e:
            logger.error(f"Error building step: {e}")
            return None
    
    def _calculate_execution_probability(
        self,
        net_profit: Decimal,
        cumulative_slippage: float,
        roi: float
    ) -> float:
        """
        Calculate probability of successful execution
        
        Factors:
        - Positive profit: 0-100%
        - Slippage: -10% per 0.1% over limit
        - ROI: bonus for >0.5% ROI
        """
        if net_profit < 0:
            return 0.0  # No execution if unprofitable
        
        # Base probability: 95%
        prob = 0.95
        
        # Slippage penalty (max 0.1%)
        max_slippage = 0.1
        if cumulative_slippage > max_slippage:
            penalty = (cumulative_slippage - max_slippage) * 0.10
            prob -= penalty
        
        # ROI bonus
        if roi > 0.5:
            bonus = min(0.05, roi * 0.001)  # Max 5% bonus
            prob += bonus
        
        return max(0.0, min(1.0, prob))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get builder statistics"""
        return {
            "plans_created": self.metrics["plans_created"],
            "plans_executed": self.metrics["plans_executed"],
            "plans_failed": self.metrics["plans_failed"],
            "success_rate": (
                self.metrics["plans_executed"] / 
                max(1, self.metrics["plans_created"]) * 100
            ),
            "total_profit": float(self.metrics["total_profit"]),
            "total_loss": float(self.metrics["total_loss"]),
            "net_result": float(self.metrics["total_profit"] - self.metrics["total_loss"])
        }


def initialize_arbitrage_builder() -> ArbitrageBuilder:
    """Factory function to initialize builder"""
    builder = ArbitrageBuilder()
    logger.info("Arbitrage builder initialized")
    return builder
