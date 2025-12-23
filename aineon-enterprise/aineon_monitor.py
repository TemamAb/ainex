#!/usr/bin/env python3
"""
AINEON Real-time Terminal Monitor
Shows live profit data and system status
"""

import requests
import json
import time
from datetime import datetime

def format_currency(amount_usd):
    """Format currency with proper commas and decimals"""
    return f"${amount_usd:,.2f}"

def format_eth(amount_eth):
    """Format ETH amount"""
    return f"{amount_eth:.6f} ETH"

def get_status():
    """Get current aineon status"""
    try:
        response = requests.get('http://0.0.0.0:54112/status', timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_profit():
    """Get current profit data"""
    try:
        response = requests.get('http://0.0.0.0:54112/profit', timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def monitor():
    """Main monitoring loop"""
    print("=" * 80)
    print("AINEON ENTERPRISE TRADING ENGINE - LIVE MONITOR")
    print("=" * 80)
    print("Press Ctrl+C to stop monitoring")
    print("=" * 80)
    
    while True:
        try:
            # Get current data
            status = get_status()
            profit = get_profit()
            
            # Clear screen and show header
            print("\033[H\033[J")  # ANSI clear screen
            print("=" * 80)
            print("AINEON ENTERPRISE TRADING ENGINE - LIVE MONITOR")
            print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            if "error" not in status:
                # Display key metrics
                eth_price = 2500
                total_profit_usd = status.get('total_profit_eth', 0) * eth_price
                daily_profit_usd = status.get('daily_profit', 0) * eth_price
                
                print(f"Engine Status: {status.get('status', 'UNKNOWN')}")
                print(f"Total Profit: {format_eth(status.get('total_profit_eth', 0))} ({format_currency(total_profit_usd)})")
                print(f"Today's Profit: {format_eth(status.get('daily_profit', 0))} ({format_currency(daily_profit_usd)})")
                print(f"Success Rate: {status.get('success_rate', 0):.1f}%")
                print(f"Active Trades: {status.get('active_trades', 0)}")
                print(f"System Uptime: {status.get('uptime', 'UNKNOWN')}")
                print("-" * 80)
                
                # Profit generation indicator
                profit_change = status.get('daily_profit', 0)
                if profit_change > 0:
                    print(f"+ PROFIT ACCUMULATING: {format_eth(profit_change)} earned today")
                else:
                    print("No profit accumulation detected")
                    
            else:
                print("ERROR: Could not connect to AINEON server")
                print(f"Error: {status['error']}")
            
            print("-" * 80)
            print("Dashboard: http://0.0.0.0:54112")
            print("API Status: http://0.0.0.0:54112/status")
            print("Press Ctrl+C to exit")
            
            time.sleep(5)  # Update every 5 seconds
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor()