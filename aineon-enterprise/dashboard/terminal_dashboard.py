"""
AINEON Terminal Dashboard - Real-time monitoring and profit verification
Connects to running AINEON engine and displays live metrics
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional
import time

# Try to import rich for beautiful terminal output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = None


class AineonDashboard:
    """Real-time dashboard for AINEON monitoring"""
    
    def __init__(self, api_url: str = "http://localhost:8082", refresh_interval: int = 5):
        self.api_url = api_url
        self.refresh_interval = refresh_interval
        self.session = None
        self.start_time = time.time()
        self.previous_stats = {}
        self.profit_history = []
        self.error_count = 0
        self.max_errors = 10
        
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def fetch_metrics(self) -> Optional[Dict]:
        """Fetch metrics from AINEON API"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(f"{self.api_url}/stats", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception as e:
            self.error_count += 1
            if self.error_count % 5 == 0:
                print(f"Warning: Error fetching metrics: {e}")
        
        return None
    
    async def fetch_profit(self) -> Optional[Dict]:
        """Fetch profit metrics"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(f"{self.api_url}/profit", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception:
            pass
        
        return None
    
    async def fetch_risk(self) -> Optional[Dict]:
        """Fetch risk metrics"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(f"{self.api_url}/risk", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception:
            pass
        
        return None
    
    async def fetch_health(self) -> Optional[Dict]:
        """Fetch health status"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(f"{self.api_url}/health", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception:
            pass
        
        return None
    
    def render_text_dashboard(self, health: Dict, stats: Dict, profit: Dict, risk: Dict):
        """Render dashboard using plain text"""
        uptime = time.time() - self.start_time
        uptime_str = str(timedelta(seconds=int(uptime)))
        
        print("\n" + "="*120)
        print("AINEON REAL-TIME DASHBOARD - PROFIT VERIFICATION".center(120))
        print("="*120)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Uptime: {uptime_str}")
        print("="*120)
        
        # Health Status
        print("\n[SYSTEM HEALTH]")
        if health:
            rpc_status = "CONNECTED" if health.get("rpc_connected") else "DISCONNECTED"
            print(f"  RPC Status: {rpc_status}")
            print(f"  System Status: {health.get('status', 'N/A').upper()}")
            print(f"  Uptime: {health.get('uptime_seconds', 0):.0f}s")
        else:
            print("  Health check failed")
        
        # System Statistics
        print("\n[SYSTEM STATISTICS]")
        if stats:
            print(f"  Total Scans (Tier 1): {stats.get('tier1_scans', 0)}")
            print(f"  Total Signals (Tier 2): {stats.get('tier2_signals', 0)}")
            print(f"  Total Executions (Tier 3): {stats.get('tier3_executions', 0)}")
            print(f"  AI Optimizations: {stats.get('ai_optimizations', 0)}")
        else:
            print("  ✗ Stats unavailable")
        
        # Profit Metrics
        print("\n[PROFIT VERIFICATION] KEY METRIC")
        if profit and profit.get('etherscan_enabled'):
            eth_accumulated = profit.get('accumulated_eth', 0)
            usd_accumulated = profit.get('accumulated_usd', 0)
            eth_price = profit.get('eth_price', 0)

            # Track history for trend
            self.profit_history.append({
                'timestamp': datetime.now(),
                'eth': eth_accumulated,
                'usd': usd_accumulated
            })
            if len(self.profit_history) > 100:
                self.profit_history.pop(0)

            # Calculate profit change
            if len(self.profit_history) > 1:
                prev_eth = self.profit_history[-2]['eth']
                eth_change = eth_accumulated - prev_eth
                change_str = f"+{eth_change:.6f} ETH" if eth_change > 0 else f"{eth_change:.6f} ETH"
            else:
                change_str = "—"

            print(f"  Accumulated ETH: {eth_accumulated:.6f} ETH {change_str}")
            print(f"  Accumulated USD: ${usd_accumulated:,.2f}")
            print(f"  ETH Price: ${eth_price:,.2f}")
            print(f"  Auto-Transfer: {'ENABLED' if profit.get('auto_transfer_enabled') else 'DISABLED'}")
            print(f"  Etherscan Validation: ENABLED")

            # Profit status
            if eth_accumulated > 0.1:
                status = "GENERATING PROFIT"
            elif eth_accumulated > 0:
                status = "ACCUMULATING (< 0.1 ETH)"
            else:
                status = "AWAITING OPPORTUNITIES"
            print(f"  Status: {status}")
        elif profit:
            print("  Profit data pending Etherscan validation")
        else:
            print("  Profit data unavailable")
        
        # Risk Management
        print("\n[RISK MANAGEMENT]")
        if risk:
            active_positions = risk.get('active_positions', 0)
            daily_pnl = risk.get('daily_pnl_usd', 0)
            risk_status = risk.get('risk_status', 'UNKNOWN')
            circuit_breaker = risk.get('circuit_breaker_triggered', False)
            
            print(f"  Active Positions: {active_positions}")
            print(f"  Daily P&L: ${daily_pnl:,.2f}")
            print(f"  Daily Loss Capacity: ${risk.get('remaining_daily_loss_capacity', 0):,.2f}")
            print(f"  Risk Status: {risk_status}")
            
            if circuit_breaker:
                print(f"  Circuit Breaker: TRIGGERED (TRADING HALTED)")
            else:
                print(f"  Circuit Breaker: ACTIVE (Ready)")
        else:
            print("  ✗ Risk metrics unavailable")
        
        # Performance Indicators
        print("\n[PERFORMANCE INDICATORS]")
        print(f"  API Errors: {self.error_count}")
        print(f"  Dashboard Uptime: {uptime_str}")
        print(f"  Refresh Interval: {self.refresh_interval}s")
        
        print("\n" + "="*120)
    
    def render_rich_dashboard(self, health: Dict, stats: Dict, profit: Dict, risk: Dict):
        """Render dashboard using Rich library"""
        if not self.console:
            return
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=2)
        )
        
        # Header
        title = Text("AINEON REAL-TIME DASHBOARD - PROFIT VERIFICATION", style="bold cyan")
        layout["header"].update(Panel(title, border_style="blue"))
        
        # Body
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Left side - Core Metrics
        left_content = ""
        if health:
            left_content += f"[bold]System Health[/bold]\n"
            rpc = "✓" if health.get("rpc_connected") else "✗"
            left_content += f"{rpc} RPC: {health.get('status', 'unknown').upper()}\n"
        
        if stats:
            left_content += f"\n[bold]Activity[/bold]\n"
            left_content += f"Scans: {stats.get('tier1_scans', 0)}\n"
            left_content += f"Signals: {stats.get('tier2_signals', 0)}\n"
            left_content += f"Executions: {stats.get('tier3_executions', 0)}\n"
        
        layout["left"].update(Panel(left_content or "Loading...", title="Metrics"))
        
        # Right side - Profit (KEY METRIC)
        right_content = ""
        if profit:
            eth = profit.get('accumulated_eth', 0)
            usd = profit.get('accumulated_usd', 0)
            
            if eth > 0.1:
                profit_style = "bold green"
                status = "GENERATING"
            elif eth > 0:
                profit_style = "yellow"
                status = "ACCUMULATING"
            else:
                profit_style = "dim"
                status = "WAITING"
            
            right_content += f"[{profit_style}]ETH: {eth:.6f}[/{profit_style}]\n"
            right_content += f"[{profit_style}]USD: ${usd:,.2f}[/{profit_style}]\n"
            right_content += f"Status: {status}\n"
        
        if risk:
            right_content += f"\n[bold]Risk Status[/bold]\n"
            right_content += f"Positions: {risk.get('active_positions', 0)}\n"
            right_content += f"Daily P&L: ${risk.get('daily_pnl_usd', 0):,.2f}\n"
            cb = "TRIGGERED" if risk.get('circuit_breaker_triggered') else "ACTIVE"
            right_content += f"CB: {cb}\n"
        
        layout["right"].update(Panel(right_content or "Loading...", title="Profit", border_style="green"))
        
        # Footer
        uptime = time.time() - self.start_time
        footer_text = f"Uptime: {str(timedelta(seconds=int(uptime)))} | Errors: {self.error_count} | Last Updated: {datetime.now().strftime('%H:%M:%S')}"
        layout["footer"].update(Panel(footer_text, style="dim"))
        
        self.console.print(layout)
    
    async def run(self):
        """Main dashboard loop"""
        print("Starting AINEON Dashboard...")
        print(f"   Connecting to {self.api_url}")
        
        await self.initialize()
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Fetch all metrics
                health = await self.fetch_health()
                stats = await self.fetch_metrics()
                profit = await self.fetch_profit()
                risk = await self.fetch_risk()
                
                # Clear screen and render
                if sys.platform == "win32":
                    os.system('cls')
                else:
                    os.system('clear')
                
                # Choose rendering method
                if HAS_RICH and self.console:
                    self.render_rich_dashboard(health, stats, profit, risk)
                else:
                    self.render_text_dashboard(health, stats, profit, risk)
                
                # Wait before next update
                await asyncio.sleep(self.refresh_interval)
        
        except KeyboardInterrupt:
            print("\n\nDashboard stopped by user")
        except Exception as e:
            print(f"\nDashboard error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.close()


async def main():
    """Main entry point"""
    api_url = os.getenv("AINEON_API_URL", "http://localhost:8082")
    refresh_interval = int(os.getenv("REFRESH_INTERVAL", "5"))
    
    dashboard = AineonDashboard(api_url=api_url, refresh_interval=refresh_interval)
    await dashboard.run()


if __name__ == "__main__":
    asyncio.run(main())
