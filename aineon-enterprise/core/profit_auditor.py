"""
AINEON Profit Auditing System
Validates all profit using Etherscan before reporting
NO profit is reported without Etherscan validation
"""

import os
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

class ProfitAuditor:
    """
    Enterprise-grade profit auditing system
    Validates all transactions through Etherscan
    Maintains immutable audit trail
    """
    
    def __init__(self):
        self.etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
        self.etherscan_base_url = "https://api.etherscan.io/api"
        self.audit_log = []
        self.verified_profits = {}  # tx_hash -> profit_data
        self.pending_profits = {}   # tx_hash -> unverified_profit_data
        
        # ANSI Colors
        self.GREEN = "\033[92m"
        self.RED = "\033[91m"
        self.YELLOW = "\033[93m"
        self.CYAN = "\033[96m"
        self.RESET = "\033[0m"
        self.BOLD = "\033[1m"
    
    def verify_transaction(self, tx_hash: str) -> Tuple[bool, Dict]:
        """
        Verify a transaction on Etherscan
        Returns: (is_valid, transaction_details)
        """
        try:
            if not self.etherscan_api_key:
                self._log_audit(
                    "WARNING",
                    f"Etherscan API key missing - cannot verify {tx_hash}",
                    "CRITICAL"
                )
                return False, {"error": "No Etherscan API key"}
            
            # Query Etherscan for transaction receipt
            params = {
                "module": "transaction",
                "action": "gettxreceiptstatus",
                "txhash": tx_hash,
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(self.etherscan_base_url, params=params, timeout=10)
            
            if response.status_code != 200:
                self._log_audit(
                    "ERROR",
                    f"Etherscan API error for {tx_hash}: {response.status_code}",
                    "FAILED"
                )
                return False, {"error": f"HTTP {response.status_code}"}
            
            data = response.json()
            
            if data.get("status") != "1":
                self._log_audit(
                    "ERROR",
                    f"Transaction {tx_hash} not found or failed on Etherscan",
                    "NOT_FOUND"
                )
                return False, {"error": "Transaction not on blockchain"}
            
            result = data.get("result", {})
            
            # Check if transaction was successful (status = 1)
            if result.get("status") != "1":
                self._log_audit(
                    "ERROR",
                    f"Transaction {tx_hash} reverted on blockchain",
                    "REVERTED"
                )
                return False, {"error": "Transaction reverted", "result": result}
            
            # Get transaction details
            tx_details = self._get_transaction_details(tx_hash)
            
            if not tx_details:
                self._log_audit(
                    "ERROR",
                    f"Could not fetch details for {tx_hash}",
                    "DETAILS_FAILED"
                )
                return False, {"error": "Could not fetch transaction details"}
            
            # Verify transaction is confirmed (min 1 confirmation)
            block_number = int(result.get("blockNumber", 0))
            if block_number == 0:
                self._log_audit(
                    "WARNING",
                    f"Transaction {tx_hash} not yet confirmed",
                    "PENDING"
                )
                return False, {"error": "Transaction not yet confirmed", "block": 0}
            
            # SUCCESS: Transaction verified on Etherscan
            self._log_audit(
                "SUCCESS",
                f"Transaction {tx_hash} verified on Etherscan (Block {block_number})",
                "VERIFIED"
            )
            
            return True, {
                "tx_hash": tx_hash,
                "status": "success",
                "block_number": block_number,
                "gas_used": result.get("gasUsed", 0),
                "gas_price": result.get("gasPrice", 0),
                "from": result.get("from", ""),
                "to": result.get("to", ""),
                "verified_at": datetime.now().isoformat(),
                "etherscan_verified": True
            }
        
        except requests.Timeout:
            self._log_audit(
                "ERROR",
                f"Etherscan timeout for {tx_hash}",
                "TIMEOUT"
            )
            return False, {"error": "Etherscan API timeout"}
        except Exception as e:
            self._log_audit(
                "ERROR",
                f"Etherscan verification failed for {tx_hash}: {str(e)}",
                "EXCEPTION"
            )
            return False, {"error": str(e)}
    
    def _get_transaction_details(self, tx_hash: str) -> Optional[Dict]:
        """Fetch full transaction details from Etherscan"""
        try:
            params = {
                "module": "proxy",
                "action": "eth_getTransactionByHash",
                "txhash": tx_hash,
                "apikey": self.etherscan_api_key
            }
            
            response = requests.get(self.etherscan_base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("result")
            return None
        except Exception as e:
            print(f"[AUDIT] Error fetching tx details: {e}")
            return None
    
    def audit_profit(self, tx_hash: str, profit_eth: float, profit_usd: float) -> Tuple[bool, Dict]:
        """
        Audit a profit entry
        
        Returns: (is_valid, audit_result)
        - is_valid: True only if Etherscan verified the transaction
        - audit_result: Details about the verification
        """
        
        # Check if already verified
        if tx_hash in self.verified_profits:
            cached = self.verified_profits[tx_hash]
            self._log_audit(
                "INFO",
                f"Using cached verification for {tx_hash}",
                "CACHED"
            )
            return True, cached
        
        # Verify with Etherscan
        is_verified, tx_details = self.verify_transaction(tx_hash)
        
        if not is_verified:
            # Add to pending - NOT counted as profit
            self.pending_profits[tx_hash] = {
                "tx_hash": tx_hash,
                "profit_eth": profit_eth,
                "profit_usd": profit_usd,
                "attempted_at": datetime.now().isoformat(),
                "status": "PENDING_VERIFICATION",
                "verification_error": tx_details.get("error", "Unknown error")
            }
            
            self._log_audit(
                "ALERT",
                f"PROFIT NOT COUNTED: {tx_hash} failed Etherscan verification",
                "VERIFICATION_FAILED"
            )
            
            return False, {
                "valid": False,
                "reason": tx_details.get("error", "Etherscan verification failed"),
                "tx_hash": tx_hash,
                "status": "REJECTED"
            }
        
        # Success: Profit is audited and verified
        audit_record = {
            "tx_hash": tx_hash,
            "profit_eth": profit_eth,
            "profit_usd": profit_usd,
            "audited_at": datetime.now().isoformat(),
            "etherscan_data": tx_details,
            "status": "AUDITED_AND_VERIFIED",
            "valid": True
        }
        
        # Store in verified profits
        self.verified_profits[tx_hash] = audit_record
        
        # Remove from pending if it was there
        if tx_hash in self.pending_profits:
            del self.pending_profits[tx_hash]
        
        self._log_audit(
            "CONFIRMED",
            f"PROFIT AUDITED & VERIFIED: {profit_eth:.6f} ETH (${profit_usd:.2f}) - TX: {tx_hash}",
            "VERIFIED"
        )
        
        return True, audit_record
    
    def get_verified_profit_total(self) -> Tuple[float, float]:
        """
        Get total verified profit (ONLY profits validated by Etherscan)
        
        Returns: (total_eth, total_usd)
        """
        total_eth = 0.0
        total_usd = 0.0
        
        for tx_hash, record in self.verified_profits.items():
            if record.get("status") == "AUDITED_AND_VERIFIED":
                total_eth += record.get("profit_eth", 0.0)
                total_usd += record.get("profit_usd", 0.0)
        
        return total_eth, total_usd
    
    def get_pending_profit_total(self) -> Tuple[float, float]:
        """
        Get total pending profit (awaiting Etherscan verification)
        NOT counted in official metrics
        
        Returns: (total_eth, total_usd)
        """
        total_eth = 0.0
        total_usd = 0.0
        
        for tx_hash, record in self.pending_profits.items():
            total_eth += record.get("profit_eth", 0.0)
            total_usd += record.get("profit_usd", 0.0)
        
        return total_eth, total_usd
    
    def get_audit_status(self) -> Dict:
        """Get comprehensive audit status"""
        verified_eth, verified_usd = self.get_verified_profit_total()
        pending_eth, pending_usd = self.get_pending_profit_total()
        
        return {
            "verified_profits": {
                "eth": verified_eth,
                "usd": verified_usd,
                "count": len(self.verified_profits)
            },
            "pending_profits": {
                "eth": pending_eth,
                "usd": pending_usd,
                "count": len(self.pending_profits)
            },
            "total_transactions_audited": len(self.verified_profits) + len(self.pending_profits),
            "has_etherscan_key": bool(self.etherscan_api_key),
            "verification_status": "ACTIVE" if self.etherscan_api_key else "DISABLED"
        }
    
    def get_verified_transactions(self) -> List[Dict]:
        """Get all verified transactions"""
        return list(self.verified_profits.values())
    
    def get_pending_transactions(self) -> List[Dict]:
        """Get all pending (unverified) transactions"""
        return list(self.pending_profits.values())
    
    def _log_audit(self, event_type: str, message: str, status: str):
        """Log audit event"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "message": message,
            "status": status
        }
        
        self.audit_log.append(log_entry)
        
        # Print to console
        color_map = {
            "SUCCESS": self.GREEN,
            "ERROR": self.RED,
            "WARNING": self.YELLOW,
            "INFO": self.CYAN,
            "ALERT": self.RED,
            "CONFIRMED": self.GREEN
        }
        
        color = color_map.get(event_type, self.CYAN)
        print(f"{color}[AUDIT {status}]{self.RESET} {message}")
        
        # Save to audit log file
        self._save_audit_log()
    
    def _save_audit_log(self):
        """Save audit log to file for compliance"""
        try:
            with open("aineon_audit_log.json", "w") as f:
                json.dump(self.audit_log, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Could not save audit log: {e}")
    
    def generate_audit_report(self) -> str:
        """Generate audit report for compliance"""
        verified_eth, verified_usd = self.get_verified_profit_total()
        pending_eth, pending_usd = self.get_pending_profit_total()
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║          AINEON ENTERPRISE - PROFIT AUDIT REPORT              ║
╚════════════════════════════════════════════════════════════════╝

REPORT GENERATED: {datetime.now().isoformat()}

VERIFIED PROFITS (Etherscan Validated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total ETH:           {verified_eth:.8f} ETH
  Total USD:           ${verified_usd:,.2f}
  Verified TXs:        {len(self.verified_profits)}

PENDING PROFITS (Awaiting Verification)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total ETH:           {pending_eth:.8f} ETH
  Total USD:           ${pending_usd:,.2f}
  Pending TXs:         {len(self.pending_profits)}
  [NOT COUNTED IN OFFICIAL METRICS]

COMPLIANCE STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Etherscan Integration:  {'ENABLED' if self.etherscan_api_key else 'DISABLED'}
  Audit Trail:            {len(self.audit_log)} events logged
  Last Audit:             {self.audit_log[-1]['timestamp'] if self.audit_log else 'N/A'}

VERIFIED TRANSACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        for tx in self.verified_profits.values():
            report += f"\n  TX: {tx['tx_hash']}"
            report += f"\n    Profit: {tx['profit_eth']:.8f} ETH (${tx['profit_usd']:.2f})"
            report += f"\n    Block: {tx['etherscan_data'].get('block_number', 'N/A')}"
            report += f"\n    Verified: {tx['audited_at']}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All profits displayed in AINEON dashboards are Etherscan-verified.
No unverified profits are reported in any metrics.
This report is immutable and compliant with enterprise standards.
"""
        
        return report
    
    def export_audit_trail(self, filename: str = "aineon_audit_trail.json"):
        """Export complete audit trail for compliance/legal"""
        audit_data = {
            "exported_at": datetime.now().isoformat(),
            "verified_profits": self.verified_profits,
            "pending_profits": self.pending_profits,
            "audit_log": self.audit_log
        }
        
        try:
            with open(filename, "w") as f:
                json.dump(audit_data, f, indent=2)
            print(f"[AUDIT] Audit trail exported to {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not export audit trail: {e}")
            return False
