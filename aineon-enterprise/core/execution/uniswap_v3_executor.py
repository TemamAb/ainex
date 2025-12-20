"""
Uniswap V3 Swap Executor
Handles building swap calldata and estimating swap outputs with slippage protection
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class UniswapV3Executor:
    """
    Uniswap V3 swap executor
    
    Handles:
    - Swap calldata generation
    - Output amount estimation
    - Slippage calculation
    - Gas cost estimation
    """
    
    # Uniswap V3 Router addresses
    UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
    UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    
    # Token constants
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    
    # Common pool fees (basis points)
    POOL_FEES = {
        100: 0.01,    # 0.01%
        500: 0.05,    # 0.05%
        3000: 0.30,   # 0.30%
        10000: 1.00   # 1.00%
    }
    
    # Slippage tolerance
    DEFAULT_SLIPPAGE = 0.001  # 0.1%
    
    def __init__(self):
        """Initialize Uniswap V3 executor"""
        self.metrics = {
            "total_swaps": 0,
            "successful_swaps": 0,
            "failed_swaps": 0,
            "total_volume": Decimal(0),
            "average_slippage": Decimal(0),
            "slippages": []
        }
    
    def build_swap_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        pool_fee: int = 3000,
        deadline: int = None
    ) -> Tuple[bool, str]:
        """
        Build swap calldata for Uniswap V3 ExactInputSingle
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in wei
            min_amount_out: Minimum output amount (slippage protection)
            pool_fee: Pool fee (100, 500, 3000, 10000)
            deadline: Transaction deadline (unix timestamp)
        
        Returns:
            (success: bool, calldata: str)
        """
        try:
            # Validate inputs
            if not token_in or not token_out:
                logger.error("Invalid token addresses")
                return False, ""
            
            if amount_in <= 0:
                logger.error("Invalid amount_in")
                return False, ""
            
            if pool_fee not in self.POOL_FEES:
                logger.warning(f"Unusual pool fee: {pool_fee}, using 3000")
                pool_fee = 3000
            
            if deadline is None:
                import time
                deadline = int(time.time()) + 300  # 5 minute default
            
            # Build ExactInputSingle params
            params = {
                "tokenIn": token_in.lower(),
                "tokenOut": token_out.lower(),
                "fee": pool_fee,
                "recipient": "0x",  # Will be filled by executor
                "deadline": deadline,
                "amountIn": amount_in,
                "amountOutMinimum": min_amount_out,
                "sqrtPriceLimitX96": 0
            }
            
            # ExactInputSingle function selector: 0x414bf389
            function_selector = "0x414bf389"
            
            # Encode params (simplified - real implementation would use eth_abi)
            calldata = self._encode_exact_input_single(params)
            
            logger.info(
                f"Built Uniswap V3 swap: {amount_in} {token_in} → {token_out} "
                f"(min {min_amount_out})"
            )
            
            return True, calldata
        
        except Exception as e:
            logger.error(f"Error building swap calldata: {e}")
            return False, ""
    
    def estimate_swap_output(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        pool_fee: int = 3000,
        use_cached: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Estimate output amount for swap
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            pool_fee: Pool fee
            use_cached: Use cached price data
        
        Returns:
            {
                "amount_in": Decimal,
                "amount_out": Decimal,
                "min_amount_out": Decimal (with slippage),
                "expected_slippage": float,
                "price_impact": float,
                "gas_estimate": int
            }
        """
        try:
            # Estimate output (simplified - real would call on-chain)
            # Using approximate formula: output = input * pool_ratio * (1 - fee)
            
            # Get pool price (mocked for now)
            pool_price = self._get_pool_price(token_in, token_out, pool_fee)
            if pool_price is None:
                logger.error(f"Could not get pool price")
                return None
            
            # Calculate output
            fee_ratio = 1 - (self.POOL_FEES.get(pool_fee, 0.30) / 100)
            amount_out = amount_in * pool_price * fee_ratio
            
            # Calculate minimum with slippage protection
            slippage = self.DEFAULT_SLIPPAGE
            min_amount_out = amount_out * (1 - slippage)
            
            # Price impact (simplified)
            price_impact = (amount_in / Decimal(100000)) * 100  # 0.01% per 100k
            
            # Gas estimate (typical swap: 100k-150k gas)
            gas_estimate = 120000
            
            estimate = {
                "amount_in": amount_in,
                "amount_out": amount_out,
                "min_amount_out": min_amount_out,
                "expected_slippage": float(slippage * 100),
                "price_impact": float(price_impact),
                "gas_estimate": gas_estimate,
                "pool_fee": pool_fee,
                "pool_price": float(pool_price)
            }
            
            logger.info(
                f"Swap estimate: {amount_in} → {amount_out:.4f} "
                f"(min {min_amount_out:.4f}, slippage {slippage*100:.2f}%)"
            )
            
            return estimate
        
        except Exception as e:
            logger.error(f"Error estimating swap output: {e}")
            return None
    
    def calculate_slippage_protection(
        self,
        estimated_output: Decimal,
        slippage_tolerance: float = None
    ) -> Decimal:
        """
        Calculate minimum output amount with slippage protection
        
        Args:
            estimated_output: Expected output amount
            slippage_tolerance: Allowed slippage (default 0.1%)
        
        Returns:
            Minimum acceptable output amount
        """
        if slippage_tolerance is None:
            slippage_tolerance = self.DEFAULT_SLIPPAGE
        
        # Validate slippage
        if slippage_tolerance > 0.01:  # Max 1% slippage
            logger.warning(f"Slippage {slippage_tolerance*100}% exceeds 1% limit")
            slippage_tolerance = 0.01
        
        min_output = estimated_output * (1 - slippage_tolerance)
        
        logger.info(
            f"Slippage protection: {estimated_output} → {min_output} "
            f"({slippage_tolerance*100:.2f}% tolerance)"
        )
        
        return min_output
    
    def estimate_gas_cost(
        self,
        gas_limit: int = 120000,
        gas_price_gwei: float = 50.0
    ) -> Decimal:
        """
        Estimate gas cost for swap
        
        Args:
            gas_limit: Gas limit for transaction
            gas_price_gwei: Gas price in gwei
        
        Returns:
            Gas cost in ETH
        """
        # Convert gwei to wei: gwei * 1e9
        gas_price_wei = Decimal(gas_price_gwei) * Decimal(1e9)
        
        # Calculate cost: gas_limit * gas_price
        gas_cost_wei = Decimal(gas_limit) * gas_price_wei
        
        # Convert to ETH: wei / 1e18
        gas_cost_eth = gas_cost_wei / Decimal(1e18)
        
        logger.info(
            f"Gas cost estimate: {gas_limit} gas @ {gas_price_gwei} gwei = "
            f"{gas_cost_eth:.6f} ETH"
        )
        
        return gas_cost_eth
    
    def validate_swap_profitability(
        self,
        amount_out_min: Decimal,
        amount_in: Decimal,
        gas_cost_eth: Decimal,
        exchange_rate: Decimal = Decimal(1)
    ) -> Dict[str, Any]:
        """
        Validate if swap is profitable
        
        Args:
            amount_out_min: Minimum output (in decimals)
            amount_in: Input amount (in decimals)
            gas_cost_eth: Gas cost in ETH
            exchange_rate: Exchange rate (output/input)
        
        Returns:
            {
                "profitable": bool,
                "net_profit": Decimal,
                "roi": float,
                "reason": str
            }
        """
        # Convert amounts to same units for comparison
        profit_amount = amount_out_min - amount_in
        profit_eth = profit_amount / Decimal(1e18)  # Assuming 18 decimals
        
        # Calculate net profit after gas
        net_profit = profit_eth - gas_cost_eth
        
        # Calculate ROI
        roi = float((net_profit / amount_in)) * 100 if amount_in > 0 else 0
        
        # Profitability threshold: 0.5 ETH minimum
        min_profit_threshold = Decimal("0.5")
        profitable = net_profit > min_profit_threshold
        
        result = {
            "profitable": profitable,
            "profit_amount": profit_amount,
            "gas_cost": gas_cost_eth,
            "net_profit": net_profit,
            "roi": roi,
            "reason": (
                "Profit exceeds 0.5 ETH threshold" if profitable 
                else f"Profit {net_profit} ETH below 0.5 ETH threshold"
            )
        }
        
        logger.info(
            f"Profitability check: {'✓' if profitable else '✗'} "
            f"(net profit: {net_profit:.6f} ETH, ROI: {roi:.2f}%)"
        )
        
        return result
    
    def _get_pool_price(
        self,
        token_in: str,
        token_out: str,
        pool_fee: int
    ) -> Optional[Decimal]:
        """
        Get current pool price
        
        In production, this would query the blockchain or price oracle
        """
        try:
            # Mock prices for testing
            # In production: query Uniswap subgraph or call view function
            pool_key = f"{token_in.lower()}-{token_out.lower()}"
            
            # Example: USDC/USDT near 1:1
            if token_out.lower() == self.USDC:
                return Decimal("0.999")  # USDC/USDT
            elif token_out.lower() == self.WETH:
                return Decimal("0.0004")  # USDT/WETH (rough estimate)
            
            # Default: 1:1
            return Decimal("1.0")
        
        except Exception as e:
            logger.error(f"Error getting pool price: {e}")
            return None
    
    def _encode_exact_input_single(self, params: Dict[str, Any]) -> str:
        """
        Encode ExactInputSingle parameters
        
        In production, would use eth_abi.encode_abi()
        For now, return placeholder
        """
        # Real implementation would encode: tokenIn, tokenOut, fee, recipient, deadline, amountIn, amountOutMinimum, sqrtPriceLimitX96
        function_selector = "0x414bf389"
        
        # Placeholder: would contain encoded params
        encoded_params = "0x" + "0" * 256  # Simplified
        
        return function_selector + encoded_params
    
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


def initialize_uniswap_v3_executor() -> UniswapV3Executor:
    """Factory function to initialize executor"""
    executor = UniswapV3Executor()
    logger.info("Uniswap V3 executor initialized")
    return executor
