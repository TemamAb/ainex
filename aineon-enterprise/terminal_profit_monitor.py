#!/usr/bin/env python3
"""
AINEON Terminal Profit Monitor
Real-time profit metrics display in terminal
Manual withdrawal mode (no auto-transfer)
"""

import os
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from decimal import Decimal
import json

# Load environment
load_dotenv()

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TerminalProfitMonitor:
    def __init__(self, api_url: str = "http://localhost:8081"):
        self.api_url = api_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Profit tracking
        self.accumulated_profit_eth = 0.0
        self.accumulated_profit_usd = 0.0
        self.session_start_time = time.time()
        self.last_update = time.time()
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.opportunities_detected = 0
        
        # Thresholds
        self.manual_withdrawal_threshold_eth = 5.0
        self.daily_loss_limit = 100.0
        self.daily_profit_threshold = 100.0
        
        # History
        self.profit_history = []
        self.trade_history = []

    async def fetch_profit_metrics(self) -> Dict[str, Any]:
        """Fetch current profit metrics from API"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.api_url}/profit", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"[ERROR] Failed to fetch profit metrics: {e}")
        
        return {}

    async def fetch_status(self) -> Dict[str, Any]:
        """Fetch system status"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.api_url}/status", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"[ERROR] Failed to fetch status: {e}")
        
        return {}

    async def fetch_opportunities(self) -> Dict[str, Any]:
        """Fetch recent opportunities"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.api_url}/opportunities", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"[ERROR] Failed to fetch opportunities: {e}")
        
        return {}

    def format_eth(self, value: float) -> str:
        """Format ETH value"""
        if value >= 1:
            return f"{value:.4f} ETH"
        else:
            return f"{value*1000:.2f} mETH"

    def format_usd(self, value: float) -> str:
        """Format USD value"""
        return f"${value:,.2f}"

    def get_uptime(self) -> str:
        """Get system uptime"""
        uptime_seconds = int(time.time() - self.session_start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def draw_profit_bar(self, current: float, target: float, width: int = 40) -> str:
        """Draw ASCII profit progress bar"""
        if target <= 0:
            return "N/A"
        
        percentage = min(100, (current / target) * 100)
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        return f"{bar} {percentage:.1f}%"

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    async def display_dashboard(self, metrics: Dict, status: Dict, opportunities: Dict):
        """Display real-time profit dashboard"""
        self.clear_screen()

        # Header
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║          AINEON FLASH LOAN ENGINE - TERMINAL PROFIT MONITOR        ║")
        print("║                    MANUAL WITHDRAWAL MODE                          ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")

        # Uptime & Session Info
        print(f"{Colors.CYAN}┌─ SESSION INFORMATION ─────────────────────────────────────────┐{Colors.ENDC}")
        print(f"{Colors.BLUE}Uptime:{Colors.ENDC}              {self.get_uptime()}")
        print(f"{Colors.BLUE}Monitoring Mode:{Colors.ENDC}     MANUAL WITHDRAWAL")
        print(f"{Colors.BLUE}Transfer Setting:{Colors.ENDC}    ❌ AUTO-TRANSFER DISABLED")
        print(f"{Colors.BLUE}Current Time:{Colors.ENDC}       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")

        # Main Profit Metrics
        eth_accumulated = float(metrics.get('accumulated_eth_verified', 0))
        usd_accumulated = float(metrics.get('accumulated_usd_verified', 0))
        
        print(f"{Colors.CYAN}┌─ PROFIT METRICS (VERIFIED) ───────────────────────────────────┐{Colors.ENDC}")
        
        # Accumulated profit with color based on amount
        profit_color = Colors.GREEN if eth_accumulated > 0 else Colors.YELLOW
        print(f"{Colors.BOLD}💰 ACCUMULATED PROFIT:{Colors.ENDC}")
        print(f"   {profit_color}ETH: {self.format_eth(eth_accumulated)}{Colors.ENDC}")
        print(f"   {profit_color}USD: {self.format_usd(usd_accumulated)}{Colors.ENDC}")
        
        # Manual withdrawal threshold
        threshold = float(metrics.get('threshold_eth', self.manual_withdrawal_threshold_eth))
        ready_for_withdrawal = eth_accumulated >= threshold
        withdrawal_status = f"{Colors.GREEN}✓ READY FOR WITHDRAWAL{Colors.ENDC}" if ready_for_withdrawal else f"{Colors.YELLOW}⏳ ACCUMULATING{Colors.ENDC}"
        
        print(f"\n{Colors.BOLD}📊 WITHDRAWAL TRACKING:{Colors.ENDC}")
        print(f"   Threshold:          {self.format_eth(threshold)}")
        print(f"   Progress:           {self.draw_profit_bar(eth_accumulated, threshold)}")
        print(f"   Status:             {withdrawal_status}")
        
        # Pending profits
        eth_pending = float(metrics.get('accumulated_eth_pending', 0))
        if eth_pending > 0:
            print(f"\n{Colors.BOLD}⏳ PENDING VERIFICATION:{Colors.ENDC}")
            print(f"   ETH: {self.format_eth(eth_pending)}")
            print(f"   (Awaiting Etherscan confirmation)")
        
        print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")

        # Strategy Performance
        print(f"{Colors.CYAN}┌─ SYSTEM STATUS ───────────────────────────────────────────────┐{Colors.ENDC}")
        
        is_online = status.get('status', 'OFFLINE') == 'ONLINE'
        execution_enabled = status.get('execution_mode', False)
        scanners_active = status.get('scanners_active', False)
        orchestrators_active = status.get('orchestrators_active', False)
        executors_active = status.get('executors_active', False)
        
        online_indicator = f"{Colors.GREEN}● ONLINE{Colors.ENDC}" if is_online else f"{Colors.FAIL}● OFFLINE{Colors.ENDC}"
        print(f"{Colors.BLUE}Status:{Colors.ENDC}              {online_indicator}")
        print(f"{Colors.BLUE}Market Scanning:{Colors.ENDC}     {'✓ ACTIVE' if scanners_active else '✗ INACTIVE'}")
        print(f"{Colors.BLUE}Orchestration:{Colors.ENDC}       {'✓ ACTIVE' if orchestrators_active else '✗ INACTIVE'}")
        print(f"{Colors.BLUE}Execution Ready:{Colors.ENDC}     {'✓ YES' if executors_active else '✗ NO'}")
        print(f"{Colors.BLUE}Flash Loans:{Colors.ENDC}         {'✓ ENABLED' if status.get('flash_loans_active', False) else '✗ DISABLED'}")
        
        # Opportunities
        total_found = opportunities.get('total_found', 0)
        print(f"\n{Colors.BOLD}🎯 OPPORTUNITIES (Last Scan):{Colors.ENDC}")
        print(f"   Total Found:        {total_found} opportunities")
        print(f"   Scan Time:          {datetime.now().strftime('%H:%M:%S')}")
        
        print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")

        # Recent Trades
        recent_opps = opportunities.get('opportunities', [])
        if recent_opps:
            print(f"{Colors.CYAN}┌─ RECENT OPPORTUNITIES ────────────────────────────────────────┐{Colors.ENDC}")
            
            for i, opp in enumerate(recent_opps[:5], 1):
                pair = opp.get('pair', 'UNKNOWN')
                confidence = float(opp.get('confidence', 0))
                profit = float(opp.get('profit', 0))
                timestamp = datetime.fromtimestamp(float(opp.get('timestamp', 0))).strftime('%H:%M:%S')
                
                confidence_color = Colors.GREEN if confidence > 0.8 else Colors.YELLOW if confidence > 0.6 else Colors.WARNING
                
                print(f"   {i}. {pair}")
                print(f"      Confidence: {confidence_color}{confidence:.1%}{Colors.ENDC}")
                print(f"      Time:       {timestamp}")
                if profit > 0:
                    print(f"      Profit:     {Colors.GREEN}{self.format_eth(profit)}{Colors.ENDC}")
            
            print(f"{Colors.CYAN}└────────────────────────────────────────────────────────────────┘{Colors.ENDC}\n")

        # Manual Withdrawal Instructions
        print(f"{Colors.BOLD}{Colors.GREEN}╔════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║                    MANUAL WITHDRAWAL MODE                           ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║                                                                    ║{Colors.ENDC}")
        
        if ready_for_withdrawal:
            print(f"{Colors.BOLD}{Colors.GREEN}║  ✓ THRESHOLD REACHED - WITHDRAWAL READY                            ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║                                                                    ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║  To withdraw manually, execute:                                     ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║  $ curl -X POST http://localhost:8081/withdraw                      ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║                                                                    ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║  Amount: {self.format_eth(eth_accumulated)} ({self.format_usd(usd_accumulated)})                    ║{Colors.ENDC}")
        else:
            remaining = threshold - eth_accumulated
            print(f"{Colors.BOLD}{Colors.GREEN}║  ⏳ ACCUMULATING PROFITS                                             ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║                                                                    ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║  Remaining to threshold: {self.format_eth(remaining):<44} ║{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}║  Estimated time (@ 10 ETH/hr): ~{remaining/10:.1f} hours              ║{Colors.ENDC}")
        
        print(f"{Colors.BOLD}{Colors.GREEN}║                                                                    ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║  Manual Mode Advantages:                                            ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║  • You control ALL withdrawals                                       ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║  • Better gas optimization (batch multiple amounts)                  ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║  • Peace of mind - no automatic transfers                            ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}║  • Withdraw to different addresses as needed                         ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}╚════════════════════════════════════════════════════════════════════╝{Colors.ENDC}\n")

        # Footer
        print(f"{Colors.CYAN}Press Ctrl+C to exit | Updates every 5 seconds{Colors.ENDC}\n")

    async def run(self):
        """Main monitoring loop"""
        try:
            while True:
                # Fetch data
                metrics = await self.fetch_profit_metrics()
                status = await self.fetch_status()
                opportunities = await self.fetch_opportunities()
                
                # Display dashboard
                await self.display_dashboard(metrics, status, opportunities)
                
                # Wait before next update
                await asyncio.sleep(5)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}[MONITOR] Shutting down...{Colors.ENDC}")
            if self.session:
                await self.session.close()
        except Exception as e:
            print(f"{Colors.FAIL}[ERROR] Monitor crashed: {e}{Colors.ENDC}")
            if self.session:
                await self.session.close()

async def main():
    """Main entry point"""
    api_url = os.getenv("API_URL", "http://localhost:8081")
    
    monitor = TerminalProfitMonitor(api_url)
    
    print(f"{Colors.CYAN}Starting AINEON Terminal Profit Monitor...{Colors.ENDC}")
    print(f"{Colors.CYAN}Connecting to API: {api_url}{Colors.ENDC}")
    await asyncio.sleep(2)
    
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())
