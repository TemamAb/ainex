#!/usr/bin/env python3
"""
AINEON Manual Withdrawal Setup
Reads your .env file and configures the system for manual profit withdrawal mode
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ManualWithdrawalSetup:
    def __init__(self):
        self.env_file = '.env'
        self.config_file = 'profit_earning_config_manual.json'
        self.env_vars = {}
        
    def load_env(self) -> bool:
        """Load environment from .env file"""
        print(f"{Colors.BLUE}[1/5] Loading environment configuration...{Colors.ENDC}")
        
        if not os.path.exists(self.env_file):
            print(f"{Colors.RED}✗ .env file not found{Colors.ENDC}")
            return False
        
        load_dotenv(self.env_file)
        
        # Load all variables from .env
        self.env_vars = {
            'ETH_RPC_URL': os.getenv('ETH_RPC_URL', ''),
            'WALLET_ADDRESS': os.getenv('WALLET_ADDRESS', ''),
            'PRIVATE_KEY': os.getenv('PRIVATE_KEY', ''),
            'PROFIT_WALLET': os.getenv('PROFIT_WALLET', ''),
            'ETHERSCAN_API_KEY': os.getenv('ETHERSCAN_API_KEY', ''),
            'PAYMASTER_URL': os.getenv('PAYMASTER_URL', ''),
            'PORT': os.getenv('PORT', '8081'),
        }
        
        print(f"{Colors.GREEN}✓ Environment loaded from .env{Colors.ENDC}")
        return True

    def validate_env(self) -> bool:
        """Validate required environment variables"""
        print(f"\n{Colors.BLUE}[2/5] Validating configuration...{Colors.ENDC}")
        
        required = ['ETH_RPC_URL', 'WALLET_ADDRESS']
        missing = []
        
        for var in required:
            if not self.env_vars.get(var):
                missing.append(var)
        
        if missing:
            print(f"{Colors.RED}✗ Missing required variables: {', '.join(missing)}{Colors.ENDC}")
            return False
        
        # Show configuration
        rpc_short = self.env_vars['ETH_RPC_URL'][:50] + "..." if len(self.env_vars['ETH_RPC_URL']) > 50 else self.env_vars['ETH_RPC_URL']
        wallet_short = self.env_vars['WALLET_ADDRESS'][:10] + "..." if len(self.env_vars['WALLET_ADDRESS']) > 10 else self.env_vars['WALLET_ADDRESS']
        
        print(f"\n{Colors.CYAN}Configuration Summary:{Colors.ENDC}")
        print(f"  RPC URL:             {rpc_short}")
        print(f"  Wallet Address:      {wallet_short}")
        print(f"  Profit Wallet:       {self.env_vars['PROFIT_WALLET'] or 'Same as WALLET_ADDRESS'}")
        print(f"  Etherscan API:       {'✓ Configured' if self.env_vars['ETHERSCAN_API_KEY'] else '⚠ Not configured'}")
        print(f"  Paymaster URL:       {'✓ Configured' if self.env_vars['PAYMASTER_URL'] else '⚠ Not configured'}")
        print(f"  API Port:            {self.env_vars['PORT']}")
        
        print(f"\n{Colors.GREEN}✓ Configuration validated{Colors.ENDC}")
        return True

    def test_rpc_connection(self) -> bool:
        """Test RPC connection"""
        print(f"\n{Colors.BLUE}[3/5] Testing RPC connection...{Colors.ENDC}")
        
        try:
            from web3 import Web3
            
            w3 = Web3(Web3.HTTPProvider(self.env_vars['ETH_RPC_URL']))
            
            if w3.is_connected():
                chain_id = w3.eth.chain_id
                latest_block = w3.eth.block_number
                print(f"{Colors.GREEN}✓ RPC Connection successful{Colors.ENDC}")
                print(f"  Chain ID:            {chain_id}")
                print(f"  Latest Block:        {latest_block:,}")
                return True
            else:
                print(f"{Colors.RED}✗ RPC connection failed{Colors.ENDC}")
                return False
        
        except Exception as e:
            print(f"{Colors.RED}✗ RPC test error: {e}{Colors.ENDC}")
            return False

    def create_manual_config(self) -> bool:
        """Create manual withdrawal configuration"""
        print(f"\n{Colors.BLUE}[4/5] Creating manual withdrawal configuration...{Colors.ENDC}")
        
        config = {
            "profit_mode": "ENTERPRISE_TIER_0.001%",
            "auto_transfer_enabled": False,
            "transfer_mode": "MANUAL_ONLY",
            "manual_withdrawal_trigger": "on_demand",
            "profit_threshold_eth": 5.0,
            "min_profit_per_trade": 0.5,
            "max_slippage_pct": 0.001,
            "gas_optimization": True,
            "flash_loan_enabled": True,
            "multi_dex_arbitrage": True,
            "multi_strategy_concurrent": 6,
            "ai_optimization": True,
            "execution_speed_ms": "<0.5",
            "risk_management": {
                "max_position_size": 1000.0,
                "daily_loss_limit": 100.0,
                "circuit_breaker": True,
                "max_drawdown_pct": 2.5,
                "profit_protection": True
            },
            "monitoring": {
                "real_time_dashboard": True,
                "profit_verification": True,
                "etherscan_validation": True,
                "microsecond_tracking": True,
                "terminal_metrics_display": True,
                "refresh_interval_seconds": 5,
                "alert_thresholds": {
                    "profit_per_hour": 10.0,
                    "profit_per_minute": 0.25,
                    "daily_profit_minimum": 100.0,
                    "monthly_profit_target": 2500.0,
                    "manual_withdrawal_alert": 5.0
                }
            },
            "withdrawal_settings": {
                "mode": "MANUAL",
                "auto_transfer": False,
                "requires_confirmation": True,
                "notification_on_ready": True,
                "ready_threshold_eth": 5.0,
                "max_withdrawal_per_tx": "unlimited",
                "gas_price_optimization": True,
                "destination_wallet": self.env_vars['PROFIT_WALLET'] or self.env_vars['WALLET_ADDRESS']
            },
            "enterprise_tier": {
                "classification": "TOP_0.001%",
                "minimum_eth_capacity": 5000.0,
                "flash_loan_size_eth": "unlimited",
                "concurrent_trades": 6,
                "strategies_deployed": [
                    "multi_dex_arbitrage",
                    "flash_loan_sandwich",
                    "mev_extraction",
                    "liquidity_sweep",
                    "curve_bridge_arb",
                    "advanced_liquidation"
                ]
            },
            "environment": {
                "rpc_url_configured": bool(self.env_vars['ETH_RPC_URL']),
                "wallet_address": self.env_vars['WALLET_ADDRESS'][:10] + "...",
                "etherscan_enabled": bool(self.env_vars['ETHERSCAN_API_KEY']),
                "paymaster_enabled": bool(self.env_vars['PAYMASTER_URL']),
                "setup_timestamp": str(__import__('datetime').datetime.now())
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"{Colors.GREEN}✓ Configuration file created: {self.config_file}{Colors.ENDC}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to create config: {e}{Colors.ENDC}")
            return False

    def create_startup_script(self) -> bool:
        """Create startup script for terminal monitor"""
        print(f"\n{Colors.BLUE}[5/5] Creating startup configuration...{Colors.ENDC}")
        
        startup_config = f"""# AINEON Terminal Profit Monitor - Auto-generated startup config
# Generated: {__import__('datetime').datetime.now()}

# Environment Variables (from your .env)
ETH_RPC_URL={self.env_vars['ETH_RPC_URL']}
WALLET_ADDRESS={self.env_vars['WALLET_ADDRESS']}
PROFIT_WALLET={self.env_vars['PROFIT_WALLET'] or self.env_vars['WALLET_ADDRESS']}
API_PORT={self.env_vars['PORT']}
API_URL=http://0.0.0.0:{self.env_vars['PORT']}

# Manual Withdrawal Settings
TRANSFER_MODE=MANUAL
AUTO_TRANSFER_ENABLED=false
MANUAL_WITHDRAWAL_THRESHOLD=5.0

# Monitoring
REFRESH_INTERVAL=5
DISPLAY_MODE=TERMINAL

# Profit Configuration File
CONFIG_FILE=profit_earning_config_manual.json
"""
        
        try:
            with open('.startup_monitor.env', 'w') as f:
                f.write(startup_config)
            
            print(f"{Colors.GREEN}✓ Startup configuration created{Colors.ENDC}")
            return True
        
        except Exception as e:
            print(f"{Colors.RED}✗ Failed to create startup config: {e}{Colors.ENDC}")
            return False

    def display_summary(self):
        """Display setup summary and next steps"""
        print(f"\n{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}MANUAL WITHDRAWAL SETUP COMPLETE!{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Configuration Summary:{Colors.ENDC}")
        print(f"  Transfer Mode:       {Colors.YELLOW}MANUAL ONLY{Colors.ENDC}")
        print(f"  Auto-Transfer:       {Colors.RED}DISABLED{Colors.ENDC}")
        print(f"  Withdrawal Threshold: 5.0 ETH")
        print(f"  Daily Loss Limit:    100 ETH")
        print(f"  Max Drawdown:        2.5%")
        print(f"  Strategies:          6 concurrent")
        print(f"  Configuration File:  {Colors.CYAN}{self.config_file}{Colors.ENDC}\n")

        print(f"{Colors.BOLD}📊 Start Terminal Profit Monitor:{Colors.ENDC}")
        print(f"  {Colors.GREEN}Windows:{Colors.ENDC}   run-terminal-monitor.bat")
        print(f"  {Colors.GREEN}Linux/Mac:{Colors.ENDC} ./run-terminal-monitor.sh\n")

        print(f"{Colors.BOLD}💰 Manual Withdrawal Instructions:{Colors.ENDC}")
        print(f"  When profit reaches 5.0 ETH, the terminal monitor will show:")
        print(f"  {Colors.GREEN}✓ THRESHOLD REACHED - WITHDRAWAL READY{Colors.ENDC}\n")

        print(f"  Then execute (in another terminal):")
        api_port = self.env_vars['PORT']
        print(f"  {Colors.CYAN}curl -X POST http://0.0.0.0:{api_port}/withdraw{Colors.ENDC}\n")

        print(f"{Colors.BOLD}📈 Profit Tracking Dashboard:{Colors.ENDC}")
        print(f"  Real-time metrics available at:")
        print(f"  {Colors.CYAN}http://0.0.0.0:{api_port}/profit{Colors.ENDC}")
        print(f"  {Colors.CYAN}http://0.0.0.0:{api_port}/opportunities{Colors.ENDC}\n")

        print(f"{Colors.BOLD}🚀 Next Steps:{Colors.ENDC}")
        print(f"  1. Deploy AINEON: ./deploy-production.sh")
        print(f"  2. Start monitor:  ./run-terminal-monitor.sh (or .bat on Windows)")
        print(f"  3. Watch profits accumulate in real-time")
        print(f"  4. When ready, manually withdraw using curl command above\n")

        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.GREEN}✓ System is now configured for MANUAL WITHDRAWAL MODE{Colors.ENDC}")
        print(f"{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

    def run(self):
        """Run complete setup"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║   AINEON MANUAL WITHDRAWAL MODE SETUP                          ║")
        print("║   Reading your .env configuration and configuring the system   ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")

        # Run setup steps
        if not self.load_env():
            return False
        
        if not self.validate_env():
            return False
        
        if not self.test_rpc_connection():
            print(f"{Colors.YELLOW}⚠ RPC test failed, but continuing...{Colors.ENDC}")
        
        if not self.create_manual_config():
            return False
        
        if not self.create_startup_script():
            return False
        
        # Display summary
        self.display_summary()
        
        return True

def main():
    setup = ManualWithdrawalSetup()
    
    try:
        success = setup.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Setup failed: {e}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
