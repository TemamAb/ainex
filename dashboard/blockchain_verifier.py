"""
Week 2: Blockchain Verification Layer
Verifies all dashboard metrics against actual blockchain state
"""

import aiohttp
import asyncio
import logging
from typing import Optional, Tuple, Dict, List
from decimal import Decimal
from datetime import datetime, timedelta
from web3 import Web3
import json

logger = logging.getLogger(__name__)


class BlockchainVerificationError(Exception):
    """Blockchain verification failed"""
    pass


class BlockchainVerifier:
    """Verifies metrics against actual blockchain state"""
    
    def __init__(self, rpc_url: str, etherscan_api_key: str = "", etherscan_enabled: bool = False):
        """
        Initialize blockchain verifier.
        
        Args:
            rpc_url: RPC endpoint URL
            etherscan_api_key: Etherscan API key
            etherscan_enabled: Enable Etherscan verification
        """
        self.rpc_url = rpc_url
        self.etherscan_api_key = etherscan_api_key
        self.etherscan_enabled = etherscan_enabled
        self.etherscan_url = "https://api.etherscan.io/api"
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.is_connected = False
        self.last_block = 0
        self._verify_connection()
    
    def _verify_connection(self) -> None:
        """Verify RPC connection"""
        try:
            self.is_connected = self.w3.is_connected()
            if self.is_connected:
                self.last_block = self.w3.eth.block_number
                logger.info(f"✅ Blockchain connected (block {self.last_block})")
            else:
                logger.error("❌ Blockchain RPC not connected")
        except Exception as e:
            logger.error(f"❌ Blockchain connection error: {e}")
            self.is_connected = False
    
    async def verify_eth_balance(self, wallet_address: str) -> Decimal:
        """
        Get actual ETH balance from blockchain.
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Balance in ETH (Decimal)
            
        Raises:
            BlockchainVerificationError: If verification fails
        """
        if not self.is_connected:
            raise BlockchainVerificationError("Blockchain not connected")
        
        try:
            # Validate address
            if not Web3.is_address(wallet_address):
                raise BlockchainVerificationError(f"Invalid wallet address: {wallet_address}")
            
            # Get balance in wei
            balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(wallet_address))
            balance_eth = Web3.from_wei(balance_wei, 'ether')
            
            logger.info(f"Balance verified: {balance_eth} ETH")
            return Decimal(str(balance_eth))
        
        except Exception as e:
            logger.error(f"Balance verification failed: {e}")
            raise BlockchainVerificationError(f"Cannot verify balance: {e}")
    
    async def verify_transaction(self, tx_hash: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify transaction exists and is confirmed.
        
        Args:
            tx_hash: Transaction hash to verify
            
        Returns:
            (is_confirmed, status_message, receipt_data)
            
        Raises:
            BlockchainVerificationError: If verification fails
        """
        if not self.is_connected:
            raise BlockchainVerificationError("Blockchain not connected")
        
        try:
            # Validate hash format
            if not tx_hash.startswith('0x') or len(tx_hash) != 66:
                raise BlockchainVerificationError(f"Invalid tx hash: {tx_hash}")
            
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt is None:
                logger.warning(f"Transaction not found: {tx_hash}")
                return False, "Transaction not found or still pending", None
            
            # Check confirmation status
            current_block = self.w3.eth.block_number
            tx_block = receipt['blockNumber']
            confirmations = current_block - tx_block
            
            # Check if successful
            is_successful = receipt['status'] == 1
            
            if not is_successful:
                logger.warning(f"Transaction failed: {tx_hash}")
                return False, f"Transaction reverted (block {tx_block})", receipt
            
            # Check if confirmed (12+ blocks)
            is_confirmed = confirmations >= 12
            
            status = f"Confirmed ({confirmations} blocks)" if is_confirmed else f"Pending ({confirmations} blocks)"
            logger.info(f"TX verified: {tx_hash} - {status}")
            
            return is_confirmed, status, receipt
        
        except Exception as e:
            logger.error(f"TX verification failed: {e}")
            raise BlockchainVerificationError(f"Cannot verify transaction: {e}")
    
    async def verify_profit_against_balance(self, 
                                           wallet: str,
                                           claimed_profit: Decimal) -> Tuple[bool, str, Decimal]:
        """
        Verify claimed profit doesn't exceed actual balance.
        
        Args:
            wallet: Wallet address
            claimed_profit: Claimed profit in ETH
            
        Returns:
            (is_valid, message, actual_balance)
        """
        try:
            actual_balance = await self.verify_eth_balance(wallet)
            
            if actual_balance >= claimed_profit:
                discrepancy = actual_balance - claimed_profit
                msg = f"Balance {actual_balance} ETH >= Claimed {claimed_profit} ETH"
                if discrepancy > 0:
                    msg += f" (Extra: {discrepancy} ETH)"
                logger.info(f"✅ Profit verified: {msg}")
                return True, msg, actual_balance
            else:
                shortfall = claimed_profit - actual_balance
                msg = f"Balance {actual_balance} ETH < Claimed {claimed_profit} ETH (Missing: {shortfall} ETH)"
                logger.error(f"❌ Profit mismatch: {msg}")
                return False, msg, actual_balance
        
        except Exception as e:
            logger.error(f"Profit verification error: {e}")
            return False, f"Verification error: {e}", Decimal('0')
    
    async def get_etherscan_balance_history(self, wallet: str) -> List[Dict]:
        """
        Get balance history from Etherscan.
        
        Args:
            wallet: Wallet address
            
        Returns:
            List of balance history records
        """
        if not self.etherscan_enabled or not self.etherscan_api_key:
            logger.warning("Etherscan not enabled or no API key")
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'module': 'account',
                    'action': 'balance',
                    'address': wallet,
                    'tag': 'latest',
                    'apikey': self.etherscan_api_key,
                }
                
                async with session.get(self.etherscan_url, params=params) as resp:
                    if resp.status != 200:
                        raise BlockchainVerificationError(f"Etherscan API error: {resp.status}")
                    
                    data = await resp.json()
                    if data['status'] != '1':
                        raise BlockchainVerificationError(f"Etherscan error: {data.get('message', 'Unknown')}")
                    
                    balance_wei = int(data['result'])
                    balance_eth = Web3.from_wei(balance_wei, 'ether')
                    
                    logger.info(f"Etherscan balance: {balance_eth} ETH")
                    return [{
                        'balance': Decimal(str(balance_eth)),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'etherscan'
                    }]
        
        except Exception as e:
            logger.error(f"Etherscan verification error: {e}")
            return []
    
    async def verify_dex_price(self, token_address: str, dex: str) -> Optional[Decimal]:
        """
        Verify DEX price for a token.
        
        Args:
            token_address: Token contract address
            dex: DEX name (uniswap, sushiswap, etc)
            
        Returns:
            Price or None if verification fails
        """
        # This is a placeholder - actual implementation would query DEX contracts
        # For now, return None to indicate not verified
        logger.debug(f"DEX price verification for {token_address} on {dex}")
        return None
    
    async def verify_contract_state(self, contract_address: str, method_name: str) -> Optional[any]:
        """
        Verify smart contract state.
        
        Args:
            contract_address: Contract address
            method_name: Method to call
            
        Returns:
            Method result or None if fails
        """
        if not self.is_connected:
            raise BlockchainVerificationError("Blockchain not connected")
        
        try:
            if not Web3.is_address(contract_address):
                raise BlockchainVerificationError(f"Invalid contract address: {contract_address}")
            
            # This is a placeholder - actual implementation would use contract ABI
            logger.debug(f"Contract state verification for {contract_address}")
            return None
        
        except Exception as e:
            logger.error(f"Contract state verification error: {e}")
            return None
    
    def get_connection_status(self) -> Dict:
        """Get connection status"""
        return {
            'connected': self.is_connected,
            'rpc_url': self.rpc_url,
            'last_block': self.last_block,
            'etherscan_enabled': self.etherscan_enabled,
            'last_check': datetime.now().isoformat(),
        }


class EtherscanVerifier:
    """Verifies transactions and addresses on Etherscan"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
        self.cache = {}  # Simple cache
        self.cache_ttl = 3600  # 1 hour
    
    async def verify_address(self, address: str) -> Tuple[bool, str]:
        """Verify Ethereum address is valid"""
        try:
            if not Web3.is_address(address):
                return False, "Invalid address format"
            return True, "Valid address"
        except Exception as e:
            return False, f"Address verification error: {e}"
    
    async def get_transaction_info(self, tx_hash: str) -> Optional[Dict]:
        """Get transaction info from Etherscan"""
        if not self.api_key:
            logger.warning("Etherscan API key not set")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'module': 'proxy',
                    'action': 'eth_getTransactionByHash',
                    'txhash': tx_hash,
                    'apikey': self.api_key,
                }
                
                async with session.get(self.base_url, params=params) as resp:
                    data = await resp.json()
                    if 'result' in data and data['result']:
                        return data['result']
                    return None
        
        except Exception as e:
            logger.error(f"Etherscan TX lookup error: {e}")
            return None
    
    async def get_latest_transactions(self, address: str, count: int = 10) -> List[Dict]:
        """Get latest transactions for address"""
        if not self.api_key:
            logger.warning("Etherscan API key not set")
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'module': 'account',
                    'action': 'txlist',
                    'address': address,
                    'startblock': 0,
                    'endblock': 99999999,
                    'page': 1,
                    'offset': count,
                    'sort': 'desc',
                    'apikey': self.api_key,
                }
                
                async with session.get(self.base_url, params=params) as resp:
                    data = await resp.json()
                    if data['status'] == '1':
                        return data['result'][:count]
                    return []
        
        except Exception as e:
            logger.error(f"Etherscan transactions lookup error: {e}")
            return []


class PriceVerifier:
    """Verifies prices from DEXes"""
    
    def __init__(self):
        self.dex_prices = {}
        self.last_update = None
    
    async def verify_uniswap_price(self, token_address: str, base_token: str = "WETH") -> Optional[Decimal]:
        """Verify price from Uniswap V3"""
        # Placeholder - would implement actual Uniswap querying
        return None
    
    async def verify_price_consistency(self, token: str, prices: Dict[str, Decimal]) -> Tuple[bool, str]:
        """Verify price is consistent across DEXes"""
        if not prices or len(prices) < 2:
            return True, "Not enough price sources to verify consistency"
        
        price_list = list(prices.values())
        max_price = max(price_list)
        min_price = min(price_list)
        
        if max_price == 0:
            return False, "All prices are zero"
        
        variance = ((max_price - min_price) / min_price) * 100
        
        # If variance > 5%, flag as inconsistent
        if variance > 5:
            return False, f"Price variance too high ({variance:.2f}%)"
        
        return True, f"Prices consistent (variance: {variance:.2f}%)"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test blockchain verifier
    verifier = BlockchainVerifier("http://localhost:8545")
    print(f"Connection status: {verifier.get_connection_status()}")
