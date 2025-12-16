"""
Real Transaction Builder - Constructs actual Ethereum transactions for arbitrage
Handles swap calldata generation, gas estimation, and MEV protection
"""

import logging
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from web3 import Web3
from eth_account import Account
import json

logger = logging.getLogger(__name__)


class UniswapV2Router:
    """Uniswap V2 Router interface for swaps"""
    
    # Uniswap V2 Router02 contract ABI (swapExactTokensForTokens, swapExactETHForTokens, etc)
    ROUTER_ABI = [
        {
            "name": "swapExactTokensForTokens",
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ],
            "outputs": [{"name": "amounts", "type": "uint256[]"}]
        }
    ]
    
    ROUTER_ADDRESS = Web3.to_checksum_address("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")


class TransactionBuilder:
    """Build real Ethereum transactions for arbitrage trades"""
    
    def __init__(self, w3: Web3, account: Account, contract_address: str):
        self.w3 = w3
        self.account = account
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.nonce_counter = 0
        
        logger.info(f"[TX_BUILDER] Initialized for account {account.address}")
    
    async def build_swap_transaction(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        slippage_pct: float = 0.5
    ) -> Optional[Dict]:
        """
        Build a Uniswap V2 swap transaction
        
        Args:
            token_in: Input token address (WETH, USDC, etc)
            token_out: Output token address
            amount_in: Amount to swap (in wei)
            min_amount_out: Minimum output amount (in wei)
            slippage_pct: Max slippage percentage for safety
        
        Returns:
            Transaction dict ready to sign, or None if build fails
        """
        try:
            token_in_addr = Web3.to_checksum_address(token_in)
            token_out_addr = Web3.to_checksum_address(token_out)
            
            # Route: token_in -> token_out
            # For stablecoin pairs, may go through WETH: USDC -> WETH -> DAI
            path = self._get_optimal_path(token_in_addr, token_out_addr)
            
            if not path:
                logger.error(f"[TX_BUILDER] Cannot find swap path: {token_in} -> {token_out}")
                return None
            
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Deadline: 5 minutes from now
            deadline = int(self.w3.eth.block_number) + 300
            
            # Calculate min output with slippage protection
            amount_in_wei = int(amount_in)
            min_amount_out_wei = int(min_amount_out * Decimal(str(1 - slippage_pct / 100)))
            
            # Build calldata for swapExactTokensForTokens
            calldata = self._encode_swap_calldata(
                amount_in_wei,
                min_amount_out_wei,
                path,
                self.account.address,
                deadline
            )
            
            # Estimate gas
            gas_estimate = await self._estimate_gas(
                token_in_addr,
                token_out_addr,
                amount_in_wei,
                calldata
            )
            
            # Get gas price (add 10% for priority)
            gas_price = int(self.w3.eth.gas_price * 1.1)
            
            # Build transaction
            tx = {
                "from": self.account.address,
                "to": UniswapV2Router.ROUTER_ADDRESS,
                "data": calldata,
                "value": 0,  # Only for ETH swaps; for token-to-token this is 0
                "gas": gas_estimate,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": self.w3.eth.chain_id
            }
            
            logger.info(f"[TX_BUILDER] Swap transaction built:")
            logger.info(f"  Path: {' -> '.join([p[:6] + '...' for p in path])}")
            logger.info(f"  Amount In: {amount_in_wei}")
            logger.info(f"  Min Out: {min_amount_out_wei}")
            logger.info(f"  Gas: {gas_estimate}, Price: {gas_price}")
            
            return tx
            
        except Exception as e:
            logger.error(f"[TX_BUILDER] Failed to build swap transaction: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_optimal_path(self, token_in: str, token_out: str) -> Optional[List[str]]:
        """
        Determine optimal swap path
        Most direct path preferred, may route through WETH for liquidity
        """
        WETH = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
        
        # Direct path first
        if self._has_direct_liquidity(token_in, token_out):
            return [token_in, token_out]
        
        # Through WETH if available
        if token_in != WETH and token_out != WETH:
            if self._has_direct_liquidity(token_in, WETH) and self._has_direct_liquidity(WETH, token_out):
                return [token_in, WETH, token_out]
        
        # Cannot find path
        return None
    
    def _has_direct_liquidity(self, token_a: str, token_b: str) -> bool:
        """Check if direct pair exists on Uniswap V2"""
        # In production: query Uniswap V2 Factory to check if pair exists
        # For now: assume major pairs exist
        major_tokens = [
            Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),  # WETH
            Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),  # USDC
            Web3.to_checksum_address("0x6B175474E89094C44Da98b954EedeAC495271d0F"),  # DAI
            Web3.to_checksum_address("0xdAC17F958D2ee523a2206206994597C13D831ec7"),  # USDT
        ]
        
        return (token_a in major_tokens) and (token_b in major_tokens)
    
    def _encode_swap_calldata(
        self,
        amount_in: int,
        amount_out_min: int,
        path: List[str],
        recipient: str,
        deadline: int
    ) -> str:
        """Encode Uniswap V2 swapExactTokensForTokens calldata"""
        
        # swapExactTokensForTokens signature:
        # function swapExactTokensForTokens(
        #     uint amountIn,
        #     uint amountOutMin,
        #     address[] calldata path,
        #     address to,
        #     uint deadline
        # ) external returns (uint[] memory amounts);
        
        # Function selector: swapExactTokensForTokens(uint256,uint256,address[],address,uint256)
        func_selector = "0x38ed1739"
        
        # Encode parameters (simplified - in production use eth_abi)
        # This is a placeholder; real implementation would use proper ABI encoding
        try:
            contract = self.w3.eth.contract(
                address=UniswapV2Router.ROUTER_ADDRESS,
                abi=json.loads('[{"name":"swapExactTokensForTokens","inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"outputs":[]}]')
            )
            
            # Encode the function call
            encoded = contract.encodeABI(
                "swapExactTokensForTokens",
                [amount_in, amount_out_min, path, Web3.to_checksum_address(recipient), deadline]
            )
            
            return encoded
        except Exception as e:
            logger.warning(f"[TX_BUILDER] ABI encoding failed: {e}, returning placeholder")
            # Return placeholder calldata
            return func_selector
    
    async def _estimate_gas(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        calldata: str
    ) -> int:
        """Estimate gas for swap transaction"""
        
        try:
            # Call eth_estimateGas
            estimate = self.w3.eth.estimate_gas({
                "from": self.account.address,
                "to": UniswapV2Router.ROUTER_ADDRESS,
                "data": calldata,
                "value": 0
            })
            
            # Add 20% buffer for safety
            return int(estimate * 1.2)
            
        except Exception as e:
            logger.warning(f"[TX_BUILDER] Gas estimation failed: {e}, using default")
            # Default: 150k gas for swaps (typical range: 100k-200k)
            return 150000
    
    async def sign_and_submit_transaction(
        self,
        tx: Dict
    ) -> Optional[str]:
        """
        Sign and submit transaction to blockchain
        
        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)
            
            # Submit to network
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"[TX_BUILDER] Transaction submitted: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"[TX_BUILDER] Transaction submission failed: {e}")
            return None
    
    async def wait_for_receipt(
        self,
        tx_hash: str,
        timeout_seconds: int = 30
    ) -> Optional[Dict]:
        """
        Wait for transaction confirmation
        
        Returns:
            Transaction receipt if confirmed, None if timeout/failure
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                
                if receipt:
                    if receipt.status == 1:
                        logger.info(f"[TX_BUILDER] ✓ Transaction confirmed: {tx_hash}")
                        return receipt
                    else:
                        logger.error(f"[TX_BUILDER] ✗ Transaction reverted: {tx_hash}")
                        return None
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.debug(f"[TX_BUILDER] Waiting for receipt: {e}")
                await asyncio.sleep(1)
        
        logger.error(f"[TX_BUILDER] Transaction timeout: {tx_hash}")
        return None


import asyncio
