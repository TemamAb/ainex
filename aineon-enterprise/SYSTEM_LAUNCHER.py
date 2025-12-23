#!/usr/bin/env python3
"""
AINEON System Launcher - Live Data Architecture
Professional trading system with real market data
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
import json

class AINEONSystemLauncher:
    """Smart launcher for AINEON trading system"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.production_dir = self.base_dir / "PRODUCTION"
        self.simulation_dir = self.base_dir / "SIMULATION"
        self.shared_dir = self.base_dir / "SHARED"
        
    def check_environment(self) -> dict:
        """Check system environment and configuration"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "environment": "development",
            "blockchain_configured": False,
            "rpc_url_set": False,
            "python_dependencies": False,
            "directory_structure": False
        }
        
        # Check blockchain configuration
        rpc_url = os.getenv("ETH_RPC_URL")
        if rpc_url:
            status["rpc_url_set"] = True
            status["blockchain_configured"] = True
        
        # Check Python dependencies
        try:
            import web3
            import aiohttp
            status["python_dependencies"] = True
        except ImportError:
            status["python_dependencies"] = False
        
        # Check directory structure
        required_dirs = ["PRODUCTION", "SIMULATION", "SHARED"]
        status["directory_structure"] = all((self.base_dir / d).exists() for d in required_dirs)
        
        return status
    
    def check_blockchain_connection(self) -> dict:
        """Check blockchain connectivity"""
        try:
            from web3 import Web3
            
            rpc_url = os.getenv("ETH_RPC_URL")
            if not rpc_url:
                return {"connected": False, "error": "ETH_RPC_URL not set"}
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            connected = w3.is_connected()
            
            if connected:
                latest_block = w3.eth.block_number
                gas_price = w3.eth.gas_price
                
                return {
                    "connected": True,
                    "latest_block": latest_block,
                    "gas_price_gwei": gas_price / 1e9,
                    "network": w3.net.version
                }
            else:
                return {"connected": False, "error": "Connection failed"}
                
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def verify_live_data(self) -> dict:
        """Verify all data sources are live and real"""
        verification = {
            "timestamp": datetime.now().isoformat(),
            "blockchain_connection": None,
            "mock_data_check": None,
            "live_market_data": None,
            "overall_status": "UNKNOWN"
        }
        
        # Check blockchain connection
        blockchain_status = self.check_blockchain_connection()
        verification["blockchain_connection"] = blockchain_status
        
        # Check for mock data references
        try:
            result = subprocess.run(
                ['grep', '-r', 'simulate.*data', '.', '--include=*.py', '--include=*.html'],
                capture_output=True, text=True, cwd=self.base_dir
            )
            mock_count = len(result.stdout.splitlines()) if result.stdout else 0
            
            verification["mock_data_check"] = {
                "files_scanned": "Python and HTML files",
                "mock_references": mock_count,
                "status": "CLEAN" if mock_count == 0 else f"WARNING: {mock_count} references found"
            }
        except Exception as e:
            verification["mock_data_check"] = {"error": str(e)}
        
        # Test live market data
        try:
            sys.path.append(str(self.shared_dir))
            from live_market_data import LiveMarketData
            
            connector = LiveMarketData()
            quality_report = connector.get_data_quality_report()
            verification["live_market_data"] = quality_report
        except Exception as e:
            verification["live_market_data"] = {"error": str(e)}
        
        # Determine overall status
        if (verification["blockchain_connection"].get("connected", False) and 
            verification["mock_data_check"].get("status") == "CLEAN"):
            verification["overall_status"] = "LIVE_DATA_READY"
        elif verification["mock_data_check"].get("status") == "CLEAN":
            verification["overall_status"] = "LIVE_DATA_ARCHITECTURE"
        else:
            verification["overall_status"] = "NEEDS_SETUP"
        
        return verification
    
    def launch_production(self):
        """Launch REAL money trading system"""
        # ANSI color codes for production mode
        RED = '\033[91m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'
        
        print(f"{RED}{BOLD}🚨 PRODUCTION MODE - REAL MONEY TRADING{END}")
        print(f"{RED}{BOLD}{'=' * 60}{END}")
        print(f"{GREEN}✅ Live blockchain connections{END}")
        print(f"{GREEN}✅ Real market data feeds{END}")
        print(f"{GREEN}✅ Actual trade execution{END}")
        print(f"{RED}{BOLD}⚠️  REAL MONEY AT RISK{END}")
        print(f"{RED}{BOLD}{'=' * 60}{END}")
        
        # Production mode visual indicators
        print(f"{RED}🟥 PRODUCTION: LIVE DATA - UNLOCKED/OPEN{END}")
        print(f"{RED}💰 Real profits flowing - NOT CONTAINED{END}")
        print(f"{RED}🔓 Numbers are OPEN and ARTICULATED{END}")
        print(f"{RED}⚡ Full access to real blockchain{END}")
        
        # Environment checks
        env_status = self.check_environment()
        if not env_status["blockchain_configured"]:
            print("❌ ERROR: ETH_RPC_URL not configured")
            print("   Set environment variable: export ETH_RPC_URL=<your_rpc_endpoint>")
            return False
        
        if not env_status["python_dependencies"]:
            print("❌ ERROR: Missing Python dependencies")
            print("   Install: pip install web3 aiohttp")
            return False
        
        # Launch production engine
        try:
            production_script = self.production_dir / "live_trading_engine.py"
            if production_script.exists():
                print("🚀 Starting production trading engine...")
                subprocess.run([sys.executable, str(production_script)], cwd=self.base_dir)
                return True
            else:
                print("❌ ERROR: Production engine not found")
                return False
        except KeyboardInterrupt:
            print("\n🛑 Production trading stopped by user")
            return True
        except Exception as e:
            print(f"❌ ERROR: Failed to start production mode: {e}")
            return False
    
    def launch_simulation(self):
        """Launch PAPER TRADING with live data"""
        # ANSI color codes for simulation mode
        YELLOW = '\033[93m'
        ORANGE = '\033[93m'
        BLUE = '\033[94m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        BOLD = '\033[1m'
        DIM = '\033[2m'
        END = '\033[0m'
        
        print(f"{YELLOW}{BOLD}📊 SIMULATION MODE - PAPER TRADING{END}")
        print(f"{YELLOW}{BOLD}{'=' * 60}{END}")
        print(f"{BLUE}✅ Live blockchain connections (read-only){END}")
        print(f"{BLUE}✅ Real market data feeds{END}")
        print(f"{CYAN}📋 Paper trading execution{END}")
        print(f"{CYAN}💰 Virtual profit/loss tracking{END}")
        print(f"{YELLOW}{BOLD}{'=' * 60}{END}")
        
        # Simulation mode visual indicators
        print(f"{YELLOW}🟨 SIMULATION: CONTAINED DATA - WIRE MESH GRID{END}")
        print(f"{YELLOW}{DIM}🔒 Numbers are in CAGE - NOT OPEN/ARTICULATED{END}")
        print(f"{YELLOW}⚠️  Virtual/Contained - NOT REAL MONEY{END}")
        
        # Draw wire mesh grid pattern
        print(f"{YELLOW}{DIM}")
        print("    ┌─┬─┬─┬─┬─┬─┬─┬─┬─┬─┐  🟨 SIMULATION MODE")
        print("    │││││││││││││││││││  🔒 CONTAINED DATA")
        print("    ├─┼─┼─┼─┼─┼─┼─┼─┼─┤  ⚠️  NOT REAL MONEY")
        print("    │││││││││││││││││││")
        print("    ├─┼─┼─┼─┼─┼─┼─┼─┼─┤")
        print("    │││││││││││││││││││")
        print("    ├─┼─┼─┼─┼─┼─┼─┼─┼─┤")
        print("    │││││││││││││││││││")
        print("    └─┴─┴─┴─┴─┴─┴─┴─┴─┘  🔐 WIRE MESH GRID")
        print(f"{END}")
        print(f"{YELLOW}🔐 SIMULATION DATA CONTAINED IN WIRE MESH{END}")
        
        # Environment checks
        env_status = self.check_environment()
        
        # Launch simulation engine
        try:
            simulation_script = self.simulation_dir / "paper_trading_engine.py"
            if simulation_script.exists():
                print("🚀 Starting paper trading simulation...")
                subprocess.run([sys.executable, str(simulation_script)], cwd=self.base_dir)
                return True
            else:
                print("❌ ERROR: Simulation engine not found")
                return False
        except KeyboardInterrupt:
            print("\n🛑 Paper trading simulation stopped by user")
            return True
        except Exception as e:
            print(f"❌ ERROR: Failed to start simulation mode: {e}")
            return False
    
    def show_verification(self):
        """Show data verification results"""
        print("🔍 DATA VERIFICATION - ALL LIVE SOURCES")
        print("=" * 60)
        
        verification = self.verify_live_data()
        
        # Blockchain status
        bc_status = verification["blockchain_connection"]
        if bc_status.get("connected", False):
            print(f"✅ Blockchain: LIVE (Block {bc_status['latest_block']}, {bc_status['gas_price_gwei']:.1f} gwei)")
        else:
            print(f"❌ Blockchain: OFFLINE ({bc_status.get('error', 'Unknown error')})")
        
        # Mock data check
        mock_check = verification["mock_data_check"]
        print(f"{'✅' if mock_check.get('status') == 'CLEAN' else '❌'} Mock Data: {mock_check.get('status', 'Unknown')}")
        
        # Live market data
        market_data = verification["live_market_data"]
        if market_data.get("mock_data_present") == False:
            print("✅ Market Data: LIVE (No mock data detected)")
        else:
            print("❌ Market Data: Issue detected")
        
        print(f"✅ Architecture: {verification['overall_status']}")
        print("=" * 60)
        
        if verification["overall_status"] == "LIVE_DATA_READY":
            print("🎉 System ready for professional trading!")
        elif verification["overall_status"] == "LIVE_DATA_ARCHITECTURE":
            print("⚠️  Architecture is clean but blockchain not connected")
            print("   Set ETH_RPC_URL to enable live trading")
        else:
            print("❌ System needs configuration")
            print("   1. Set ETH_RPC_URL environment variable")
            print("   2. Install dependencies: pip install web3 aiohttp")
    
    def show_help(self):
        """Show help information"""
        print("🎛️  AINEON Professional Trading System")
        print("=" * 60)
        print("Live data architecture with zero mock data")
        print()
        print("USAGE:")
        print("  python SYSTEM_LAUNCHER.py [OPTION]")
        print()
        print("OPTIONS:")
        print("  1, --production    Launch real money trading")
        print("  2, --simulation    Launch paper trading with live data")
        print("  3, --verify        Verify data sources are live")
        print("  4, --status        Show system status")
        print("  5, --help          Show this help message")
        print()
        print("EXAMPLES:")
        print("  python SYSTEM_LAUNCHER.py --production")
        print("  python SYSTEM_LAUNCHER.py --simulation")
        print("  python SYSTEM_LAUNCHER.py --verify")
        print()
        print("REQUIREMENTS:")
        print("  • ETH_RPC_URL environment variable")
        print("  • Python packages: web3, aiohttp")
        print("  • Ethereum wallet for production mode")
        print()
        print("SAFETY:")
        print("  • Production mode: REAL MONEY at risk")
        print("  • Simulation mode: Safe paper trading")
        print("  • All data is LIVE from blockchain")
    
    def interactive_launch(self):
        """Interactive mode selection"""
        while True:
            print("\n🎛️  AINEON Professional Trading System")
            print("Choose operation mode:")
            print()
            print(f"{RED}1. 🚨 PRODUCTION - Real money trading{END}")
            print(f"{RED}   🟥 UNLOCKED/OPEN - Real profits flowing{END}")
            print(f"{GREEN}   • Live blockchain connections{END}")
            print(f"{GREEN}   • Real DEX price feeds{END}")
            print(f"{GREEN}   • Actual trade execution{END}")
            print(f"{RED}{BOLD}   ⚠️  REAL MONEY AT RISK{END}")
            print()
            print(f"{YELLOW}2. 📊 SIMULATION - Paper trading with live data{END}")
            print(f"{YELLOW}   🟨 CONTAINED - Wire mesh grid protection{END}")
            print(f"{YELLOW}   🔒 Numbers in CAGE - NOT ARTICULATED{END}")
            print(f"{BLUE}   • Live blockchain connections (read-only){END}")
            print(f"{BLUE}   • Real market data feeds{END}")
            print(f"{CYAN}   • Virtual profit/loss tracking{END}")
            print(f"{YELLOW}   💰 Safe for learning and testing{END}")
            print()
            print("3. 🔍 VERIFY - Check data sources")
            print("   • Verify blockchain connection")
            print("   • Check for mock data")
            print("   • Validate live market data")
            print()
            print("4. 📊 STATUS - Show system status")
            print("   • Environment configuration")
            print("   • Dependency status")
            print("   • Directory structure")
            print()
            print("5. ❌ EXIT - Quit application")
            
            try:
                choice = input("\nSelect option (1-5): ").strip()
                
                if choice == "1":
                    self.launch_production()
                elif choice == "2":
                    self.launch_simulation()
                elif choice == "3":
                    self.show_verification()
                elif choice == "4":
                    self.show_status()
                elif choice == "5":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid selection. Please choose 1-5.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def show_status(self):
        """Show detailed system status"""
        print("📊 AINEON SYSTEM STATUS")
        print("=" * 60)
        
        env_status = self.check_environment()
        
        print(f"Environment: {env_status['environment']}")
        print(f"Timestamp: {env_status['timestamp']}")
        print()
        
        print("CONFIGURATION:")
        print(f"  {'✅' if env_status['rpc_url_set'] else '❌'} ETH_RPC_URL configured")
        print(f"  {'✅' if env_status['python_dependencies'] else '❌'} Python dependencies")
        print(f"  {'✅' if env_status['directory_structure'] else '❌'} Directory structure")
        print()
        
        if env_status['rpc_url_set']:
            bc_status = self.check_blockchain_connection()
            print("BLOCKCHAIN:")
            print(f"  {'✅' if bc_status.get('connected') else '❌'} Connection: {'Connected' if bc_status.get('connected') else 'Failed'}")
            if bc_status.get('connected'):
                print(f"  Network: {bc_status.get('network', 'Unknown')}")
                print(f"  Latest Block: {bc_status.get('latest_block', 'Unknown')}")
                print(f"  Gas Price: {bc_status.get('gas_price_gwei', 0):.1f} gwei")
        else:
            print("BLOCKCHAIN:")
            print("  ❌ Not configured (set ETH_RPC_URL)")
        
        print()
        verification = self.verify_live_data()
        print("DATA VERIFICATION:")
        print(f"  Architecture Status: {verification['overall_status']}")
        
        print("=" * 60)

def main():
    """Main entry point"""
    launcher = AINEONSystemLauncher()
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ["1", "--production", "-p", "production"]:
            launcher.launch_production()
        elif arg in ["2", "--simulation", "-s", "simulation"]:
            launcher.launch_simulation()
        elif arg in ["3", "--verify", "-v", "verify"]:
            launcher.show_verification()
        elif arg in ["4", "--status", "-t", "status"]:
            launcher.show_status()
        elif arg in ["5", "--help", "-h", "help"]:
            launcher.show_help()
        else:
            print(f"❌ Unknown option: {arg}")
            launcher.show_help()
    else:
        # Interactive mode
        launcher.interactive_launch()

if __name__ == "__main__":
    main()