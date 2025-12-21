#!/usr/bin/env python3
"""
REAL-TIME PROFIT MONITORING CARD
Chief Architect - Live Profit Display with Green Metrics

This script displays real-time profit generation from the flash loan engine
in a formatted card with green styling for profit metrics.
"""

import time
import os
import subprocess
import threading
import re
from datetime import datetime

class RealTimeProfitMonitor:
    """Real-time profit monitoring and display system"""
    
    def __init__(self):
        self.total_profit = 0.0
        self.transaction_count = 0
        self.last_profits = []
        self.running = True
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_profit_card(self):
        """Display the profit monitoring card"""
        while self.running:
            self.clear_screen()
            
            # Calculate recent profit data
            recent_profit = sum(self.last_profits[-5:]) if self.last_profits else 0
            avg_profit = sum(self.last_profits) / len(self.last_profits) if self.last_profits else 0
            
            print("\033[92m" + "=" * 80 + "\033[0m")  # Green border
            print("\033[92m" + "🚀 AINEON FLASH LOAN ENGINE - REAL-TIME PROFIT MONITORING" + "\033[0m")
            print("\033[92m" + "=" * 80 + "\033[0m")
            
            print(f"\033[92m💰 TOTAL PROFIT GENERATED:\033[0m \033[92m${self.total_profit:.2f} USD\033[0m")
            print(f"\033[92m📊 TRANSACTIONS COMPLETED:\033[0m \033[92m{self.transaction_count}\033[0m")
            print(f"\033[92m⚡ RECENT PROFIT (Last 5):\033[0m \033[92m${recent_profit:.2f} USD\033[0m")
            print(f"\033[92m📈 AVERAGE PROFIT PER TRADE:\033[0m \033[92m${avg_profit:.2f} USD\033[0m")
            
            # Current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\033[92m🕐 LAST UPDATE:\033[0m \033[92m{current_time}\033[0m")
            
            print("\033[92m" + "-" * 80 + "\033[0m")
            print("\033[92m📋 RECENT PROFITABLE TRANSACTIONS:\033[0m")
            
            # Display recent transactions
            for i, profit in enumerate(reversed(self.last_profits[-10:]), 1):
                profit_color = "\033[92m" if profit > 0 else "\033[91m"
                print(f"\033[92m{len(self.last_profits)-i+1:2d}.\033[0m {profit_color}+${profit:.2f} USD\033[0m")
            
            print("\033[92m" + "=" * 80 + "\033[0m")
            print("\033[93m⚠️  Live monitoring active - Press Ctrl+C to stop\033[0m")
            
            time.sleep(2)  # Update every 2 seconds
    
    def parse_terminal_output(self):
        """Parse terminal output for profit data"""
        try:
            # Try to read from the enhanced flash loan engine process
            process = subprocess.Popen(
                ["python", "flash_loan_live_deployment_enhanced.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            for line in iter(process.stdout.readline, ''):
                if not self.running:
                    break
                    
                # Parse profit from SUCCESS messages
                if "SUCCESS:" in line and "Profit:" in line:
                    # Extract profit amount using regex
                    profit_match = re.search(r'Profit: \$(\d+\.?\d*)', line)
                    if profit_match:
                        profit = float(profit_match.group(1))
                        self.total_profit += profit
                        self.transaction_count += 1
                        self.last_profits.append(profit)
                        
                        # Keep only last 50 profits
                        if len(self.last_profits) > 50:
                            self.last_profits.pop(0)
                
                # Parse opportunity messages for real-time updates
                elif "New Opportunity:" in line:
                    # Could be used to show opportunity scanning
                    pass
                    
        except Exception as e:
            print(f"Error parsing terminal output: {e}")
    
    def start_monitoring(self):
        """Start the real-time monitoring"""
        print("Starting AINEON Real-Time Profit Monitor...")
        
        # Start display thread
        display_thread = threading.Thread(target=self.display_profit_card, daemon=True)
        display_thread.start()
        
        # Start parsing thread
        parse_thread = threading.Thread(target=self.parse_terminal_output, daemon=True)
        parse_thread.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping profit monitor...")
            self.running = False

def main():
    """Main function"""
    monitor = RealTimeProfitMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()