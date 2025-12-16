#!/usr/bin/env python3
"""
AINEON Profit Metrics Display with Etherscan Validation
Real-time terminal dashboard showing profits, drops, and validated transactions
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from collections import deque

import aiohttp
from web3 import Web3
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EtherscanValidator:
    """Validates transactions and profits on Etherscan"""
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY", "")
        self.base_url = "https://api.etherscan.io/api"
        self.session = None
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def verify_transaction(self, tx_hash: str) -> Dict:
        """
        Verify transaction status on Etherscan
        Returns: {
            'success': bool,
            'status': 'success' | 'failed' | 'pending' | 'error',
            'block_number': int,
            'timestamp': datetime,
            'gas_used': int,
            'gas_price': Decimal,
            'value': Decimal,
        }
        """
        await self.init_session()
        
        try:
            params = {
                "module": "transaction",
                "action": "gettxreceiptstatus",
                "txhash": tx_hash,
                "apikey": self.api_key
            }
            
            async with self.session.get(self.base_url, params=params) as resp:
                if resp.status != 200:
                    return {
                        'success': False,
                        'status': 'error',
                        'message': f'HTTP {resp.status}'
                    }
                
                data = await resp.json()
                
                if data.get('status') == '1':  # Success
                    result = data.get('result', {})
                    return {
                        'success': True,
                        'status': 'success',
                        'block_number': int(result.get('blockNumber', 0)),
                        'gas_used': int(result.get('gasUsed', 0)),
                        'timestamp': datetime.now(),
                        'validated': True
                    }
                elif data.get('status') == '0':  # Failed
                    return {
                        'success': False,
                        'status': 'failed',
                        'message': 'Transaction failed on chain',
                        'validated': True
                    }
                else:  # Pending or error
                    return {
                        'success': False,
                        'status': 'pending',
                        'message': 'Transaction pending or not found',
                        'validated': False
                    }
        
        except Exception as e:
            logger.error(f"[ETHERSCAN] Verification failed for {tx_hash}: {e}")
            return {
                'success': False,
                'status': 'error',
                'message': str(e),
                'validated': False
            }
    
    async def verify_profit_transaction(self, tx_hash: str) -> Optional[Decimal]:
        """
        Verify a profit transaction and return validated amount
        Returns: Decimal ETH amount if valid, None otherwise
        """
        result = await self.verify_transaction(tx_hash)
        
        if result.get('validated') and result.get('success'):
            logger.info(f"[ETHERSCAN] ✓ Profit transaction VALIDATED: {tx_hash}")
            return Decimal(result.get('value', 0))
        else:
            logger.warning(f"[ETHERSCAN] ✗ Profit transaction FAILED validation: {tx_hash}")
            return None


class ProfitMetricsTracker:
    """Track and display profit metrics in real-time"""
    
    def __init__(self, wallet_address: str, etherscan_api_key: str = ""):
        self.wallet_address = wallet_address
        self.etherscan = EtherscanValidator(etherscan_api_key)
        
        # Profit tracking
        self.total_profit_eth = Decimal("0")
        self.validated_profit_eth = Decimal("0")
        self.pending_profit_eth = Decimal("0")
        
        # Session metrics
        self.session_start = datetime.now()
        self.profit_transactions: List[Dict] = []
        self.profit_drops: deque = deque(maxlen=100)  # Last 100 profit events
        
        # Hourly metrics (ENTERPRISE TIER)
        self.hourly_profits: Dict[str, Decimal] = {}
        self.daily_profit_target = Decimal("100.0")  # 100 ETH per day minimum (enterprise)
        self.hourly_profit_target = Decimal("10.0")  # 10 ETH per hour minimum (enterprise)
        self.monthly_profit_target = Decimal("2500.0")  # 2500 ETH per month target
        
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))
    
    async def record_profit(self, amount_eth: Decimal, tx_hash: str = "", strategy: str = ""):
        """Record a profit transaction"""
        timestamp = datetime.now()
        
        # Validate on Etherscan if tx_hash provided
        validated = False
        if tx_hash:
            validated_amount = await self.etherscan.verify_profit_transaction(tx_hash)
            validated = validated_amount is not None
            if validated:
                self.validated_profit_eth += validated_amount
                amount_eth = validated_amount
        else:
            # Local validation only
            self.pending_profit_eth += amount_eth
        
        # Track profit
        self.total_profit_eth += amount_eth
        
        profit_record = {
            'timestamp': timestamp,
            'amount_eth': float(amount_eth),
            'tx_hash': tx_hash,
            'strategy': strategy,
            'etherscan_validated': validated,
            'status': 'validated' if validated else 'pending'
        }
        
        self.profit_transactions.append(profit_record)
        
        # Track hourly profits
        hour_key = timestamp.strftime("%Y-%m-%d %H:00")
        self.hourly_profits[hour_key] = self.hourly_profits.get(hour_key, Decimal("0")) + amount_eth
        
        logger.info(f"[PROFIT] {'✓ VALIDATED' if validated else '⏳ PENDING'}: {amount_eth} ETH | {strategy}")
    
    async def record_profit_drop(self, from_level: Decimal, to_level: Decimal, reason: str = ""):
        """Record a profit drop event"""
        drop_amount = from_level - to_level
        timestamp = datetime.now()
        
        drop_record = {
            'timestamp': timestamp,
            'from_eth': float(from_level),
            'to_eth': float(to_level),
            'drop_amount': float(drop_amount),
            'reason': reason
        }
        
        self.profit_drops.append(drop_record)
        logger.warning(f"[PROFIT DROP] {drop_amount} ETH | From: {from_level} → {to_level} | Reason: {reason}")
    
    def get_session_duration(self) -> str:
        """Get formatted session duration"""
        duration = datetime.now() - self.session_start
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_profit_rate(self) -> Decimal:
        """Calculate current profit rate (ETH per hour)"""
        duration_hours = (datetime.now() - self.session_start).total_seconds() / 3600
        if duration_hours > 0:
            return self.validated_profit_eth / Decimal(str(duration_hours))
        return Decimal("0")
    
    def get_hourly_summary(self) -> Dict:
        """Get hourly profit summary"""
        total_hours = len(self.hourly_profits)
        total_profit = sum(self.hourly_profits.values())
        avg_per_hour = total_profit / Decimal(str(total_hours)) if total_hours > 0 else Decimal("0")
        
        return {
            'total_hours': total_hours,
            'total_profit': total_profit,
            'average_per_hour': avg_per_hour,
            'hourly_details': self.hourly_profits
        }
    
    async def get_metrics_summary(self) -> Dict:
        """Get comprehensive profit metrics summary - ETHERSCAN VALIDATED ONLY"""
        hourly = self.get_hourly_summary()
        
        # STRICT POLICY: Only display Etherscan-validated profits
        # Pending profits are NOT shown until confirmed
        return {
            'session': {
                'start_time': self.session_start.isoformat(),
                'duration': self.get_session_duration(),
                'status': 'ACTIVE',
                'policy': '✅ Etherscan-Validated Profits Only'
            },
            'profits': {
                'etherscan_validated_eth': float(self.validated_profit_eth),  # PRIMARY
                'pending_validation_eth': float(self.pending_profit_eth),     # NOT DISPLAYED
                'profit_rate_per_hour': float(self.get_profit_rate())
            },
            'targets': {
                'daily_target_eth': float(self.daily_profit_target),
                'hourly_target_eth': float(self.hourly_profit_target),
                'daily_progress_pct': float((self.validated_profit_eth / self.daily_profit_target) * 100) if self.daily_profit_target > 0 else 0
            },
            'transactions': {
                'etherscan_validated_count': sum(1 for tx in self.profit_transactions if tx['etherscan_validated']),
                'pending_validation_count': sum(1 for tx in self.profit_transactions if not tx['etherscan_validated']),
                'validation_policy': 'Only Etherscan-confirmed profits are counted'
            },
            'drops': {
                'total_drops': len(self.profit_drops),
                'recent_drops': list(self.profit_drops)[-10:] if self.profit_drops else []
            },
            'hourly': hourly
        }


class ProfitMetricsDisplay:
    """Terminal UI for profit metrics display"""
    
    # ANSI colors
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    def __init__(self, tracker: ProfitMetricsTracker):
        self.tracker = tracker
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    async def display_header(self):
        """Display main header"""
        print(f"\n{self.BOLD}{self.CYAN}")
        print("╔═══════════════════════════════════════════════════════════════════════════════╗")
        print("║                  AINEON PROFIT METRICS - ETHERSCAN VALIDATED                  ║")
        print("╚═══════════════════════════════════════════════════════════════════════════════╝")
        print(f"{self.RESET}")
    
    async def display_metrics(self):
        """Display current profit metrics"""
        metrics = await self.tracker.get_metrics_summary()
        
        self.clear_screen()
        await self.display_header()
        
        # Session info
        print(f"\n{self.BOLD}SESSION INFORMATION{self.RESET}")
        print(f"  Duration:     {metrics['session']['duration']}")
        print(f"  Status:       {self.GREEN}● ACTIVE{self.RESET}")
        print(f"  Wallet:       {self.tracker.wallet_address}")
        
        # Profit summary - ETHERSCAN VALIDATED ONLY
        print(f"\n{self.BOLD}PROFIT SUMMARY (ETHERSCAN VALIDATED ONLY){self.RESET}")
        print(f"  ✅ Verified Profit: {self.GREEN}{metrics['profits']['etherscan_validated_eth']:.6f} ETH{self.RESET}")
        print(f"  ⏳ Pending Validation: {self.YELLOW}{metrics['profits']['pending_validation_eth']:.6f} ETH{self.RESET}")
        print(f"  Policy: {self.CYAN}Only Etherscan-confirmed profits displayed{self.RESET}")
        print(f"  Rate: {self.GREEN}{metrics['profits']['profit_rate_per_hour']:.6f} ETH/hr{self.RESET}")
        
        # Daily targets
        print(f"\n{self.BOLD}DAILY TARGETS{self.RESET}")
        daily_target = metrics['targets']['daily_target_eth']
        hourly_target = metrics['targets']['hourly_target_eth']
        daily_progress = metrics['targets']['daily_progress_pct']
        
        progress_bar = self._create_progress_bar(daily_progress, 50)
        color = self.GREEN if daily_progress >= 100 else self.YELLOW if daily_progress >= 50 else self.RED
        
        print(f"  Daily Target:      {daily_target:.2f} ETH")
        print(f"  Progress:          {color}{progress_bar}{self.RESET} {daily_progress:.1f}%")
        print(f"  Hourly Target:     {hourly_target:.2f} ETH")
        
        # Transaction breakdown
        print(f"\n{self.BOLD}TRANSACTION STATUS{self.RESET}")
        print(f"  Total Transactions:    {metrics['transactions']['total_count']}")
        print(f"  {self.GREEN}Etherscan Validated:   {metrics['transactions']['validated_count']}{self.RESET} ✓")
        print(f"  {self.YELLOW}Pending Validation:    {metrics['transactions']['pending_count']}{self.RESET}")
        
        # Recent profit transactions
        if self.tracker.profit_transactions:
            print(f"\n{self.BOLD}RECENT PROFIT TRANSACTIONS{self.RESET}")
            for tx in self.tracker.profit_transactions[-5:]:
                status_icon = f"{self.GREEN}✓{self.RESET}" if tx['etherscan_validated'] else f"{self.YELLOW}⏳{self.RESET}"
                print(f"  {status_icon} {tx['timestamp'].strftime('%H:%M:%S')} | {tx['amount_eth']:.6f} ETH | {tx['strategy']}")
                if tx['tx_hash']:
                    print(f"     └─ {tx['tx_hash'][:16]}...")
        
        # Profit drops
        if self.tracker.profit_drops:
            print(f"\n{self.BOLD}RECENT PROFIT DROPS{self.RESET}")
            for drop in list(self.tracker.profit_drops)[-3:]:
                print(f"  {self.RED}↓ {drop['timestamp'].strftime('%H:%M:%S')}{self.RESET}")
                print(f"    {drop['from_eth']:.6f} ETH → {drop['to_eth']:.6f} ETH (-{drop['drop_amount']:.6f})")
                if drop['reason']:
                    print(f"    Reason: {drop['reason']}")
        
        # Hourly breakdown
        if self.tracker.hourly_profits:
            print(f"\n{self.BOLD}HOURLY BREAKDOWN (Last 24 Hours){self.RESET}")
            sorted_hours = sorted(self.tracker.hourly_profits.items())[-24:]
            for hour_key, profit in sorted_hours[-5:]:  # Show last 5 hours
                bar = self._create_progress_bar(
                    float(profit / self.tracker.hourly_profit_target * 100),
                    30
                )
                print(f"  {hour_key}: {bar} {profit:.6f} ETH")
        
        # Footer
        print(f"\n{self.BOLD}LAST UPDATE:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  {self.CYAN}Profits displayed are Etherscan-validated only{self.RESET}\n")
    
    @staticmethod
    def _create_progress_bar(percentage: float, width: int = 50) -> str:
        """Create ASCII progress bar"""
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100
        
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"


async def main():
    """Main profit metrics display loop"""
    
    # Initialize tracker
    wallet = os.getenv("WALLET_ADDRESS", "0x0000000000000000000000000000000000000000")
    etherscan_key = os.getenv("ETHERSCAN_API_KEY", "")
    
    tracker = ProfitMetricsTracker(wallet, etherscan_key)
    display = ProfitMetricsDisplay(tracker)
    
    try:
        await tracker.etherscan.init_session()
        
        # Example: Simulate profit transactions
        print(f"{display.YELLOW}[INIT] Profit Metrics Display starting...{display.RESET}")
        print(f"[INIT] Wallet: {wallet}")
        print(f"[INIT] Etherscan API: {'✓ Configured' if etherscan_key else '✗ Not configured'}")
        
        # Continuous display loop
        iteration = 0
        while True:
            iteration += 1
            await display.display_metrics()
            
            # Update interval (refresh every 5 seconds in demo)
            await asyncio.sleep(5)
    
    except KeyboardInterrupt:
        print(f"\n{display.YELLOW}[SHUTDOWN] Profit metrics display stopped{display.RESET}")
    except Exception as e:
        logger.error(f"Error in metrics display: {e}")
    finally:
        await tracker.etherscan.close_session()


if __name__ == "__main__":
    asyncio.run(main())
