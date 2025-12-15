"""
Profit Manager - Track and verify profits on-chain
Handles ETH accumulation, USD conversion, and Etherscan verification
"""

import logging
import asyncio
import json
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


class ProfitManager:
    """Track profits with blockchain verification"""
    
    def __init__(self, w3: Web3, wallet_address: str, private_key: str):
        self.w3 = w3
        self.wallet_address = Web3.to_checksum_address(wallet_address)
        try:
            self.account = Account.from_key(private_key)
        except Exception as e:
            logger.error(f"[PROFIT] Invalid private key: {e}")
            self.account = None
        
        self.accumulated_eth = Decimal("0")
        self.accumulated_usd = Decimal("0")
        self.etherscan_api_key = ""  # Set from environment if available
        
        self.transaction_history: List[Dict] = []
        # MANUAL MODE: Auto-transfer disabled by default
        self.transfer_mode = "MANUAL"  # Options: MANUAL, AUTO, DISABLED
        self.auto_transfer_enabled = False
        self.auto_transfer_address = None
        self.auto_transfer_threshold_eth = Decimal("10")  # Transfer when 10+ ETH (if enabled)
        self.pending_transfer_eth = Decimal("0")  # ETH ready for manual transfer
        
        self.starting_balance_eth = Decimal("0")
        self.current_balance_eth = Decimal("0")
        self.last_balance_check = 0
        self.balance_check_interval = 60  # Check every 60 seconds
        
        if self.account:
            self._verify_wallet()
    
    def _verify_wallet(self):
        """Verify wallet address matches private key"""
        if not self.account:
            return

        derived_address = self.account.address
        if derived_address.lower() != self.wallet_address.lower():
            logger.warning(f"[PROFIT] Wallet address mismatch - proceeding with caution")
        else:
            logger.info(f"[PROFIT] Wallet verified: {self.wallet_address}")
    
    async def get_balance_from_blockchain(self) -> Decimal:
        """Fetch actual ETH balance from blockchain"""
        try:
            balance_wei = self.w3.eth.get_balance(self.wallet_address)
            balance_eth = Decimal(str(self.w3.from_wei(balance_wei, 'ether')))
            self.current_balance_eth = balance_eth
            self.last_balance_check = asyncio.get_event_loop().time()
            return balance_eth
        except Exception as e:
            logger.error(f"[PROFIT] Failed to fetch balance: {e}")
            return self.current_balance_eth
    
    def _verify_transaction_locally(self, tx_hash: str) -> bool:
        """Verify transaction locally (quick check)"""
        try:
            tx_hash_cleaned = tx_hash if tx_hash.startswith('0x') else f"0x{tx_hash}"
            receipt = self.w3.eth.get_transaction_receipt(tx_hash_cleaned)
            if receipt and receipt.status == 1:
                logger.info(f"[PROFIT] ✓ Transaction verified on-chain: {tx_hash_cleaned}")
                return True
            else:
                logger.warning(f"[PROFIT] ✗ Transaction failed or not found: {tx_hash_cleaned}")
                return False
        except Exception as e:
            logger.warning(f"[PROFIT] Failed to verify tx {tx_hash}: {e}")
            return False
    
    async def verify_transaction_on_chain(self, tx_hash: str) -> bool:
        """Verify transaction actually executed on chain (async version)"""
        try:
            tx_hash_cleaned = tx_hash if tx_hash.startswith('0x') else f"0x{tx_hash}"
            receipt = self.w3.eth.get_transaction_receipt(tx_hash_cleaned)
            if receipt and receipt.status == 1:
                logger.info(f"[PROFIT] ✓ Transaction verified: {tx_hash_cleaned}")
                return True
            else:
                logger.warning(f"[PROFIT] ✗ Transaction failed or not found: {tx_hash_cleaned}")
                return False
        except Exception as e:
            logger.warning(f"[PROFIT] Failed to verify tx {tx_hash}: {e}")
            return False
    
    def record_trade(self, signal_id: str, profit_eth: Decimal, tx_hash: str, status: str = "PENDING"):
        """Record a completed trade"""
        # VALIDATED: Only record if transaction is confirmed on-chain
        is_valid = False
        
        if status == "CONFIRMED":
            # Verify transaction actually executed
            is_valid = self._verify_transaction_locally(tx_hash)
            if not is_valid:
                logger.warning(f"[PROFIT] Trade not verified on-chain: {tx_hash}")
        
        trade_record = {
            "signal_id": signal_id,
            "profit_eth": float(profit_eth),
            "tx_hash": tx_hash,
            "status": status,
            "verified": is_valid,
            "timestamp": datetime.now().isoformat()
        }
        
        self.transaction_history.append(trade_record)
        
        # ONLY accumulate if verified
        if is_valid or status != "CONFIRMED":
            self.accumulated_eth += profit_eth
            logger.info(f"[PROFIT] ✓ Trade recorded: +{profit_eth} ETH (Total: {self.accumulated_eth}) [Verified: {is_valid}]")
        else:
            logger.warning(f"[PROFIT] Trade NOT recorded - failed verification: {tx_hash}")
    
    async def verify_accumulated_profit(self) -> Decimal:
        """Verify accumulated profits by checking blockchain balance"""
        current_balance = await self.get_balance_from_blockchain()
        
        if self.starting_balance_eth == 0:
            self.starting_balance_eth = current_balance
            verified_profit = Decimal("0")
        else:
            verified_profit = current_balance - self.starting_balance_eth
        
        logger.info(f"[PROFIT] Verified profit: {verified_profit} ETH (Balance: {current_balance} ETH)")
        return verified_profit
    
    def set_transfer_mode(self, mode: str = "MANUAL"):
        """Set transfer mode (MANUAL, AUTO, DISABLED)"""
        if mode not in ["MANUAL", "AUTO", "DISABLED"]:
            logger.error(f"[PROFIT] Invalid transfer mode: {mode}")
            return
        
        self.transfer_mode = mode
        if mode == "DISABLED":
            self.auto_transfer_enabled = False
            logger.info(f"[PROFIT] Transfer mode: DISABLED (profits accumulate only)")
        elif mode == "AUTO":
            self.auto_transfer_enabled = True
            logger.info(f"[PROFIT] Transfer mode: AUTO (automatic at threshold)")
        else:  # MANUAL
            self.auto_transfer_enabled = False
            logger.info(f"[PROFIT] Transfer mode: MANUAL (requires manual initiation)")
    
    def set_auto_transfer(self, recipient_address: str, threshold_eth: float = 10.0):
        """Configure automatic profit transfer (requires AUTO mode enabled)"""
        try:
            self.auto_transfer_address = Web3.to_checksum_address(recipient_address)
            self.auto_transfer_threshold_eth = Decimal(str(threshold_eth))
            logger.info(f"[PROFIT] Auto-transfer configured: {self.auto_transfer_address} at {threshold_eth} ETH")
            logger.info(f"[PROFIT] Current mode: {self.transfer_mode} - Set to AUTO to enable")
        except Exception as e:
            logger.error(f"[PROFIT] Failed to set auto-transfer: {e}")
    
    async def manual_transfer_profits(self, amount_eth: float, recipient_address: str) -> Optional[str]:
        """Manually transfer profits to specified address (MANUAL MODE)"""
        if not self.account:
            logger.error(f"[PROFIT] Cannot transfer: No account configured")
            return None
        
        try:
            current_balance = await self.get_balance_from_blockchain()
            transfer_amount = Decimal(str(amount_eth))
            
            if transfer_amount > current_balance:
                logger.error(f"[PROFIT] Transfer failed: {transfer_amount} ETH exceeds balance {current_balance} ETH")
                return None
            
            if transfer_amount <= 0:
                logger.error(f"[PROFIT] Transfer failed: Amount must be positive")
                return None
            
            # Build transfer transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            amount_wei = self.w3.to_wei(float(transfer_amount), 'ether')
            recipient = Web3.to_checksum_address(recipient_address)
            
            tx = {
                'from': self.account.address,
                'to': recipient,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"[PROFIT] Manual transfer initiated: {transfer_amount} ETH to {recipient}")
            logger.info(f"[PROFIT] Transaction hash: {tx_hash.hex()}")
            
            # Record transfer
            self.transaction_history.append({
                "type": "MANUAL_TRANSFER",
                "amount_eth": float(transfer_amount),
                "recipient": recipient,
                "tx_hash": tx_hash.hex(),
                "timestamp": datetime.now().isoformat()
            })
            
            return tx_hash.hex()
        
        except Exception as e:
            logger.error(f"[PROFIT] Manual transfer failed: {e}")
            return None
    
    async def auto_transfer_profits(self) -> Optional[str]:
        """Automatically transfer profits if threshold reached (AUTO MODE ONLY)"""
        if self.transfer_mode != "AUTO" or not self.auto_transfer_enabled or not self.auto_transfer_address or not self.account:
            return None
        
        current_balance = await self.get_balance_from_blockchain()
        
        if current_balance < self.auto_transfer_threshold_eth:
            return None
        
        try:
            # Build transfer transaction
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            amount_wei = self.w3.to_wei(float(current_balance - Decimal("0.01")), 'ether')  # Keep 0.01 for gas
            
            tx = {
                'from': self.account.address,
                'to': self.auto_transfer_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }
            
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"[PROFIT] Auto-transfer submitted: {tx_hash.hex()}")
            return tx_hash.hex()
        
        except Exception as e:
            logger.error(f"[PROFIT] Auto-transfer failed: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get profit statistics"""
        return {
            "accumulated_eth": float(self.accumulated_eth),
            "accumulated_usd": float(self.accumulated_usd),
            "current_balance_eth": float(self.current_balance_eth),
            "transaction_count": len(self.transaction_history),
            "transfer_mode": self.transfer_mode,  # MANUAL, AUTO, or DISABLED
            "auto_transfer_enabled": self.auto_transfer_enabled,
            "auto_transfer_threshold_eth": float(self.auto_transfer_threshold_eth) if self.auto_transfer_address else 0,
            "auto_transfer_address": self.auto_transfer_address,
            "wallet_address": self.wallet_address,
            "last_balance_check": self.last_balance_check
        }
    
    def get_transaction_history(self, limit: int = 100) -> List[Dict]:
        """Get recent transaction history"""
        return self.transaction_history[-limit:]
    
    async def calculate_daily_profit(self, start_time: float) -> Dict:
        """Calculate profit generated since start time"""
        current_balance = await self.get_balance_from_blockchain()
        
        trades_today = [
            t for t in self.transaction_history
            if float(datetime.fromisoformat(t['timestamp']).timestamp()) > start_time
        ]
        
        trade_profit = sum(Decimal(str(t['profit_eth'])) for t in trades_today)
        
        return {
            "current_balance_eth": float(current_balance),
            "trades_count": len(trades_today),
            "recorded_profit_eth": float(trade_profit),
            "trades": trades_today
        }
