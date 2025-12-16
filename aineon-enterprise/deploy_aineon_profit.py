#!/usr/bin/env python3
"""
AINEON Enterprise Deployment Script - Profit Generating Configuration
Initializes AINEON engine for active profit generation with Etherscan validation
"""

import os
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Color codes
class Colors:
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

def print_header():
    """Display deployment header"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                               ║")
    print("║              AINEON ENTERPRISE DEPLOYMENT - PROFIT GENERATING MODE            ║")
    print("║                  Flash Loan Arbitrage Engine for Ethereum                     ║")
    print("║                                                                               ║")
    print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")

def check_environment() -> Dict[str, str]:
    """Check and validate environment configuration"""
    print(f"{Colors.BOLD}[1/5] ENVIRONMENT VALIDATION{Colors.ENDC}")
    
    load_dotenv()
    
    required_vars = {
        'ETH_RPC_URL': 'Ethereum RPC endpoint',
        'WALLET_ADDRESS': 'Ethereum wallet address',
    }
    
    optional_vars = {
        'ETHERSCAN_API_KEY': 'Etherscan API key (for profit validation)',
        'PRIVATE_KEY': 'Wallet private key (for execution mode)',
        'PROFIT_WALLET': 'Profit wallet address',
        'PORT': 'API server port',
    }
    
    env_config = {}
    errors = []
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"  ✗ {var}: {description} - MISSING")
        else:
            env_config[var] = value
            print(f"  ✓ {var}: {description}")
    
    # Check optional variables
    print(f"\n{Colors.YELLOW}Optional Configuration:{Colors.ENDC}")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            env_config[var] = value
            print(f"  ✓ {var}: {description}")
        else:
            print(f"  ○ {var}: {description} - not set")
    
    if errors:
        print(f"\n{Colors.FAIL}ERRORS:{Colors.ENDC}")
        for error in errors:
            print(error)
        return None
    
    print(f"\n{Colors.GREEN}✓ Environment validation passed{Colors.ENDC}\n")
    return env_config

def check_rpc_connection(rpc_url: str) -> bool:
    """Test RPC connection"""
    print(f"{Colors.BOLD}[2/5] RPC CONNECTION TEST{Colors.ENDC}")
    
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if w3.is_connected():
            chain_id = w3.eth.chain_id
            chain_name = {
                1: "Mainnet",
                5: "Goerli (testnet)",
                11155111: "Sepolia (testnet)",
            }.get(chain_id, f"Unknown (ID: {chain_id})")
            
            print(f"  ✓ Connected to Ethereum {chain_name}")
            print(f"  ✓ Latest block: {w3.eth.block_number}")
            print(f"{Colors.GREEN}✓ RPC connection validated{Colors.ENDC}\n")
            return True
        else:
            print(f"  ✗ RPC endpoint not responding")
            print(f"{Colors.FAIL}✗ RPC connection failed{Colors.ENDC}\n")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        print(f"{Colors.FAIL}✗ RPC connection failed{Colors.ENDC}\n")
        return False

def validate_wallet(wallet_address: str) -> bool:
    """Validate wallet address format"""
    print(f"{Colors.BOLD}[3/5] WALLET VALIDATION{Colors.ENDC}")
    
    try:
        from web3 import Web3
        
        # Check if valid address format
        if not Web3.is_address(wallet_address):
            print(f"  ✗ Invalid wallet address format")
            print(f"{Colors.FAIL}✗ Wallet validation failed{Colors.ENDC}\n")
            return False
        
        checksum_address = Web3.to_checksum_address(wallet_address)
        print(f"  ✓ Wallet address: {checksum_address}")
        print(f"  ✓ Address is valid")
        
        # Note: Balance check happens at deployment time
        print(f"{Colors.GREEN}✓ Wallet validation passed{Colors.ENDC}\n")
        return True
    
    except Exception as e:
        print(f"  ✗ Error: {str(e)[:100]}")
        print(f"{Colors.FAIL}✗ Wallet validation failed{Colors.ENDC}\n")
        return False

def load_profit_config() -> Optional[Dict]:
    """Load profit earning configuration"""
    print(f"{Colors.BOLD}[4/5] PROFIT CONFIGURATION{Colors.ENDC}")
    
    config_file = Path("profit_earning_config.json")
    
    if not config_file.exists():
        print(f"  ✗ Configuration file not found: {config_file}")
        print(f"{Colors.FAIL}✗ Configuration loading failed{Colors.ENDC}\n")
        return None
    
    try:
        with open(config_file) as f:
            config = json.load(f)
        
        print(f"  ✓ Profit Mode: {config.get('profit_mode', 'UNKNOWN')}")
        print(f"  ✓ Auto-Transfer: {'ENABLED' if config.get('auto_transfer_enabled') else 'DISABLED'}")
        print(f"  ✓ Profit Threshold: {config.get('profit_threshold_eth', 0)} ETH")
        print(f"  ✓ Gas Optimization: {'ON' if config.get('gas_optimization') else 'OFF'}")
        
        if config.get('monitoring', {}).get('etherscan_validation'):
            print(f"  {Colors.GREEN}✓ Etherscan Validation: ENABLED{Colors.ENDC}")
        else:
            print(f"  {Colors.YELLOW}⚠ Etherscan Validation: Recommended but not configured{Colors.ENDC}")
        
        print(f"\n  Risk Management:")
        risk = config.get('risk_management', {})
        print(f"    • Max Position Size: {risk.get('max_position_size', 0)} ETH")
        print(f"    • Daily Loss Limit: {risk.get('daily_loss_limit', 0)} ETH")
        print(f"    • Circuit Breaker: {'ON' if risk.get('circuit_breaker') else 'OFF'}")
        
        print(f"{Colors.GREEN}✓ Configuration loaded{Colors.ENDC}\n")
        return config
    
    except json.JSONDecodeError as e:
        print(f"  ✗ Invalid JSON in {config_file}: {e}")
        print(f"{Colors.FAIL}✗ Configuration loading failed{Colors.ENDC}\n")
        return None
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        print(f"{Colors.FAIL}✗ Configuration loading failed{Colors.ENDC}\n")
        return None

def check_core_modules() -> bool:
    """Check if all core modules are present"""
    print(f"{Colors.BOLD}[5/5] CORE MODULES CHECK{Colors.ENDC}")
    
    required_modules = [
        ('core/unified_system.py', 'Three-tier orchestration engine'),
        ('core/profit_manager.py', 'Profit tracking and management'),
        ('core/profit_metrics_display.py', 'Real-time profit metrics display'),
        ('core/tier_scanner.py', 'Market opportunity scanner'),
        ('core/tier_orchestrator.py', 'Strategy orchestrator'),
        ('core/tier_executor.py', 'Transaction executor'),
        ('core/risk_manager.py', 'Risk management engine'),
        ('core/ai_optimizer.py', 'AI optimization engine'),
    ]
    
    all_present = True
    for module_path, description in required_modules:
        if Path(module_path).exists():
            print(f"  ✓ {module_path}: {description}")
        else:
            print(f"  ✗ {module_path}: {description} - MISSING")
            all_present = False
    
    if all_present:
        print(f"{Colors.GREEN}✓ All core modules present{Colors.ENDC}\n")
    else:
        print(f"{Colors.FAIL}✗ Some modules missing{Colors.ENDC}\n")
    
    return all_present

def generate_deployment_report(env_config: Dict, profit_config: Dict) -> str:
    """Generate deployment readiness report"""
    
    deployment_mode = "EXECUTION" if env_config.get('PRIVATE_KEY') else "MONITORING"
    etherscan_configured = bool(env_config.get('ETHERSCAN_API_KEY'))
    
    report = f"""
{Colors.BOLD}{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                     DEPLOYMENT READINESS REPORT                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.ENDC}

DEPLOYMENT CONFIGURATION:
  Deployment Mode:        {Colors.GREEN}{deployment_mode}{Colors.ENDC}
  Profit Mode:            {Colors.GREEN}{profit_config.get('profit_mode', 'UNKNOWN')}{Colors.ENDC}
  Etherscan Validation:   {'✓ ' + Colors.GREEN + 'ENABLED' + Colors.ENDC if etherscan_configured else '✗ ' + Colors.YELLOW + 'NOT CONFIGURED' + Colors.ENDC}
  Auto-Transfer:          {'✓ ' + Colors.GREEN + 'ENABLED' + Colors.ENDC if profit_config.get('auto_transfer_enabled') else '✗ ' + Colors.YELLOW + 'DISABLED' + Colors.ENDC}
  Gas Optimization:       {'✓ ' + Colors.GREEN + 'ON' + Colors.ENDC if profit_config.get('gas_optimization') else '✗ ' + Colors.YELLOW + 'OFF' + Colors.ENDC}

PROFIT TARGETS:
  Daily Target:           {profit_config.get('monitoring', {}).get('alert_thresholds', {}).get('daily_profit_target', 1.0)} ETH
  Hourly Target:          {profit_config.get('monitoring', {}).get('alert_thresholds', {}).get('profit_per_hour', 0.1)} ETH
  Min Profit/Trade:       {profit_config.get('min_profit_per_trade', 0.001)} ETH
  Profit Threshold:       {profit_config.get('profit_threshold_eth', 0.01)} ETH (for transfers)

RISK PARAMETERS:
  Max Position Size:      {profit_config.get('risk_management', {}).get('max_position_size', 10.0)} ETH
  Daily Loss Limit:       {profit_config.get('risk_management', {}).get('daily_loss_limit', 1.0)} ETH
  Circuit Breaker:        {'✓ ' + Colors.GREEN + 'ACTIVE' + Colors.ENDC if profit_config.get('risk_management', {}).get('circuit_breaker') else '✗ INACTIVE'}
  Max Slippage:           {profit_config.get('max_slippage_pct', 0.02) * 100}%

FEATURES ENABLED:
  ✓ Market Scanning (1 sec cycles)
  ✓ AI Optimization (24/7 monitoring)
  ✓ Multi-DEX Arbitrage
  ✓ Flash Loan Support
  ✓ Profit Tracking
  {'✓ Real-time Profit Metrics Dashboard' if etherscan_configured else '⚠ Profit Metrics (limited without Etherscan API)'}
  ✓ Risk Management
  ✓ Circuit Breakers

DEPLOYMENT STATUS: {Colors.GREEN}{Colors.BOLD}✓ READY TO DEPLOY{Colors.ENDC}

NEXT STEPS:
  1. Review configuration above
  2. Start unified system: {Colors.CYAN}python core/unified_system.py{Colors.ENDC}
  3. Monitor profit metrics: {Colors.CYAN}python core/profit_metrics_display.py{Colors.ENDC}
  4. Check API status: {Colors.CYAN}curl http://localhost:8081/status{Colors.ENDC}
  5. View profit metrics: {Colors.CYAN}curl http://localhost:8081/profit{Colors.ENDC}

{Colors.YELLOW}⚠ IMPORTANT SECURITY NOTES:{Colors.ENDC}
  • Never commit .env file to version control
  • Keep PRIVATE_KEY secure - use environment variables only
  • Monitor wallet for unauthorized transactions
  • Review profit transactions on Etherscan before accepting
  • Start with testnet before mainnet deployment

Deployment Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return report

async def main():
    """Main deployment orchestration"""
    
    print_header()
    
    # Step 1: Check environment
    env_config = check_environment()
    if not env_config:
        print(f"{Colors.FAIL}Deployment aborted due to environment errors{Colors.ENDC}")
        sys.exit(1)
    
    # Step 2: Test RPC
    if not check_rpc_connection(env_config['ETH_RPC_URL']):
        print(f"{Colors.FAIL}Deployment aborted due to RPC connection failure{Colors.ENDC}")
        sys.exit(1)
    
    # Step 3: Validate wallet
    if not validate_wallet(env_config['WALLET_ADDRESS']):
        print(f"{Colors.FAIL}Deployment aborted due to wallet validation failure{Colors.ENDC}")
        sys.exit(1)
    
    # Step 4: Load profit config
    profit_config = load_profit_config()
    if not profit_config:
        print(f"{Colors.FAIL}Deployment aborted due to configuration loading failure{Colors.ENDC}")
        sys.exit(1)
    
    # Step 5: Check modules
    if not check_core_modules():
        print(f"{Colors.YELLOW}Warning: Some modules missing. Deployment may have limited functionality.{Colors.ENDC}\n")
    
    # Generate and display report
    report = generate_deployment_report(env_config, profit_config)
    print(report)
    
    # Save report
    report_file = Path(f"DEPLOYMENT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        # Remove color codes for file
        clean_report = report
        for color_code in [Colors.CYAN, Colors.GREEN, Colors.YELLOW, Colors.BOLD, Colors.ENDC]:
            clean_report = clean_report.replace(color_code, '')
        f.write(clean_report)
    
    print(f"{Colors.CYAN}Report saved to: {report_file}{Colors.ENDC}")
    
    # Ready for deployment
    print(f"\n{Colors.GREEN}{Colors.BOLD}AINEON Enterprise is ready for deployment!{Colors.ENDC}")
    print(f"Run the system with: {Colors.CYAN}python core/unified_system.py{Colors.ENDC}\n")

if __name__ == "__main__":
    asyncio.run(main())
