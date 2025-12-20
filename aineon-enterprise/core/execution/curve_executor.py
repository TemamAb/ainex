"""
Curve Stable Swap Executor
Handles stable swap operations for stablecoins with minimal slippage
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal
import math

logger = logging.getLogger(__name__)


class CurveExecutor:
    """
    Curve stable swap executor
    
    Handles:
    - Stable swap calldata generation
    - Stablecoin routing (USDC, USDT, DAI, etc.)
    - Minimal slippage calculations
    - Multi-coin pool support
    """
    
    # Curve Pool addresses
    TRICRYPTO_POOL = "0x7F86bf177dd4F691Ba41e8840881beCD6691C495"
    TRICRYPTO_NG_POOL = "0xcEE98F61E4feCFC87e5b7db49a4f8F10342eB5Db"
    
    # 3CRV pool (DAI/USDC/USDT)
    CURVE_3CRV_POOL = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
    
    # Token indices in 3CRV pool
    TOKEN_INDICES = {
        "0x6B175474E89094C44Da98b954EedeAC495271d0F": 0,  # DAI
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": 1,  # USDC
        "0xdAC17F958D2ee523a2206206994597C13D831ec7": 2,  # USDT
    }
    
    # Stablecoins (1:1 ratio)
    STABLECOINS = {
        "0x6B175474E89094C44Da98b954EedeAC495271d0F": "DAI",   # 18 decimals
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48": "USDC",  # 6 decimals
        "0xdAC17F958D2ee523a2206206994597C13D831ec7": "USDT",  # 6 decimals
    }
    
    # Slippage tolerance (typically <0.05% for stables)
    DEFAULT_SLIPPAGE = 0.0005  # 0.05%
    
    def __init__(self):
        """Initialize Curve executor"""
        self.metrics = {
            "total_swaps": 0,
            "successful_swaps": 0,
            "failed_swaps": 0,
            "total_volume": Decimal(0),
            "average_slippage": Decimal(0),
            "slippages": []
        }
    
    def build_stable_swap_calldata(
        self,
        pool_address: str,
        i: int,
        j: int,
        dx: int,
        min_dy: int,
        use_eth: bool = False
    ) -> Tuple[bool, str]:
        """
        Build Curve stable swap calldata
        
        Args:
            pool_address: Curve pool contract address
            i: Input token index in pool
            j: Output token index in pool
            dx: Input amount in wei
            min_dy: Minimum output (slippage protection)
            use_eth: Whether to use ETH (for wrapped pools)
        
        Returns:
            (success: bool, calldata: str)
        """
        try:
            # Validate indices
            if i < 0 or j < 0 or i == j:
                logger.error(f"Invalid token indices: i={i}, j={j}")
                return False, ""
            
            if dx <= 0:
                logger.error("Invalid input amount")
                return False, ""
            
            # exchange(i, j, dx, min_dy) function selector
            # Real implementation uses Curve's ABI encoding
            if use_eth:
                # exchange_with_eth(i, j, dx, min_dy, use_eth)
                function_selector = "0x0b4c7e3d"
                calldata = self._encode_exchange_with_eth(i, j, dx, min_dy)
            else:
                # exchange(i, j, dx, min_dy)
                function_selector = "0x3df02124"
                calldata = self._encode_exchange(i, j, dx, min_dy)
            
            logger.info(
                f"Built Curve swap: token[{i}] → token[{j}], "
                f"amount {dx}, min output {min_dy}"
            )
            
            return True, calldata
        
        except Exception as e:
            logger.error(f"Error building stable swap calldata: {e}")
            return False, ""
    
    def estimate_stable_swap_output(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        pool_address: str = CURVE_3CRV_POOL
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate output for stablecoin swap (minimal slippage)
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in wei
            pool_address: Curve pool address
        
        Returns:
            {
                "amount_in": int,
                "amount_out": int,
                "min_amount_out": int (with slippage),
                "expected_slippage": float,
                "pool_address": str,
                "gas_estimate": int
            }
        """
        try:
            # Get token indices
            i = self.TOKEN_INDICES.get(token_in.lower())
            j = self.TOKEN_INDICES.get(token_out.lower())
            
            if i is None or j is None:
                logger.error(f"Token not found in pool")
                return None
            
            # Normalize for decimal differences
            # DAI: 18 decimals, USDC/USDT: 6 decimals
            token_in_name = self.STABLECOINS.get(token_in.lower())
            token_out_name = self.STABLECOINS.get(token_out.lower())
            
            # Estimate output (approximation for stables: very close to 1:1)
            # Real implementation would call get_dy() on pool
            amount_out = self._estimate_get_dy(i, j, amount_in, pool_address)
            
            if amount_out is None:
                return None
            
            # Slippage for stables is minimal (0.05%)
            slippage = self.DEFAULT_SLIPPAGE
            min_amount_out = int(amount_out * (1 - slippage))
            
            # Gas estimate (stable swap: 60k-80k gas)
            gas_estimate = 70000
            
            estimate = {
                "amount_in": amount_in,
                "amount_out": int(amount_out),
                "min_amount_out": min_amount_out,
                "expected_slippage": float(slippage * 100),
                "pool_address": pool_address,
                "gas_estimate": gas_estimate,
                "token_in": token_in_name,
                "token_out": token_out_name,
                "token_in_index": i,
                "token_out_index": j
            }
            
            logger.info(
                f"Stable swap estimate: {amount_in} {token_in_name} → "
                f"{int(amount_out)} {token_out_name} "
                f"(min {min_amount_out}, slippage {slippage*100:.3f}%)"
            )
            
            return estimate
        
        except Exception as e:
            logger.error(f"Error estimating stable swap output: {e}")
            return None
    
    def calculate_fee_impact(
        self,
        amount_in: int,
        base_fee: float = 0.0004  # 0.04% typical
    ) -> Tuple[int, float]:
        """
        Calculate Curve pool fee impact
        
        Args:
            amount_in: Input amount
            base_fee: Base trading fee (default 0.04%)
        
        Returns:
            (fee_amount: int, fee_percentage: float)
        """
        fee_amount = int(amount_in * base_fee)
        fee_percentage = base_fee * 100
        
        logger.info(f"Fee impact: {fee_amount} wei ({fee_percentage:.3f}%)")
        
        return fee_amount, fee_percentage
    
    def estimate_multihop_swap(
        self,
        token_path: List[str],
        amount_in: int
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate output for multi-hop swap across pools
        
        Example: USDC → 3CRV → other pool → output token
        
        Args:
            token_path: List of token addresses (start to end)
            amount_in: Input amount
        
        Returns:
            Multihop swap estimate with cumulative slippage
        """
        try:
            if len(token_path) < 2:
                logger.error("Path must contain at least 2 tokens")
                return None
            
            current_amount = amount_in
            cumulative_slippage = 0
            hops = []
            
            # Estimate each hop
            for i in range(len(token_path) - 1):
                hop_estimate = self.estimate_stable_swap_output(
                    token_path[i],
                    token_path[i + 1],
                    int(current_amount)
                )
                
                if hop_estimate is None:
                    return None
                
                hops.append(hop_estimate)
                current_amount = hop_estimate["amount_out"]
                cumulative_slippage += hop_estimate["expected_slippage"]
            
            return {
                "hops": hops,
                "amount_in": amount_in,
                "amount_out": current_amount,
                "cumulative_slippage": cumulative_slippage,
                "min_amount_out": int(
                    current_amount * (1 - cumulative_slippage / 100)
                ),
                "total_gas_estimate": sum(h["gas_estimate"] for h in hops),
                "num_hops": len(hops)
            }
        
        except Exception as e:
            logger.error(f"Error estimating multihop swap: {e}")
            return None
    
    def validate_slippage_bounds(
        self,
        amount_out: int,
        min_amount_out: int,
        max_slippage_pct: float = 0.1
    ) -> Dict[str, Any]:
        """
        Validate slippage is within acceptable bounds
        
        Args:
            amount_out: Actual output amount
            min_amount_out: Minimum acceptable output
            max_slippage_pct: Maximum slippage percentage allowed
        
        Returns:
            {
                "valid": bool,
                "actual_slippage": float,
                "max_slippage": float,
                "reason": str
            }
        """
        if amount_out == 0:
            return {
                "valid": False,
                "actual_slippage": 100.0,
                "max_slippage": max_slippage_pct,
                "reason": "Zero output amount"
            }
        
        actual_slippage = ((amount_out - min_amount_out) / amount_out) * 100
        valid = actual_slippage <= max_slippage_pct
        
        result = {
            "valid": valid,
            "actual_slippage": actual_slippage,
            "max_slippage": max_slippage_pct,
            "reason": (
                f"Slippage {actual_slippage:.3f}% is within limit"
                if valid
                else f"Slippage {actual_slippage:.3f}% exceeds {max_slippage_pct}% limit"
            )
        }
        
        logger.info(f"Slippage validation: {'✓' if valid else '✗'} - {result['reason']}")
        
        return result
    
    def _estimate_get_dy(
        self,
        i: int,
        j: int,
        dx: int,
        pool_address: str
    ) -> Optional[int]:
        """
        Estimate output amount (get_dy)
        
        In production, would call pool.get_dy(i, j, dx) view function
        For stables, output ≈ input * (1 - fee)
        """
        try:
            # For stablecoins: minimal price movement
            # Approximate: output = input * (1 - 0.04% fee)
            fee = 0.0004
            dy = int(dx * (1 - fee))
            
            return dy
        
        except Exception as e:
            logger.error(f"Error estimating get_dy: {e}")
            return None
    
    def _encode_exchange(self, i: int, j: int, dx: int, min_dy: int) -> str:
        """Encode exchange() call - simplified"""
        # Real: use eth_abi.encode_abi(['uint256', 'uint256', 'uint256', 'uint256'], [i, j, dx, min_dy])
        return "0x3df02124" + "0" * 256  # Placeholder
    
    def _encode_exchange_with_eth(
        self,
        i: int,
        j: int,
        dx: int,
        min_dy: int
    ) -> str:
        """Encode exchange_with_eth() call - simplified"""
        return "0x0b4c7e3d" + "0" * 256  # Placeholder
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics"""
        avg_slippage = (
            sum(self.metrics["slippages"]) / len(self.metrics["slippages"])
            if self.metrics["slippages"] else 0
        )
        
        return {
            "total_swaps": self.metrics["total_swaps"],
            "successful_swaps": self.metrics["successful_swaps"],
            "failed_swaps": self.metrics["failed_swaps"],
            "success_rate": (
                self.metrics["successful_swaps"] / max(1, self.metrics["total_swaps"]) * 100
            ),
            "total_volume": float(self.metrics["total_volume"]),
            "average_slippage": avg_slippage
        }


def initialize_curve_executor() -> CurveExecutor:
    """Factory function to initialize executor"""
    executor = CurveExecutor()
    logger.info("Curve executor initialized")
    return executor
