#!/usr/bin/env python3
"""
AINEON Auto-Transfer Disabler
Chief Architect Command: Disable auto-transfer on all engines
"""

import os
import signal
import subprocess
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_transfer_disable.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoTransferDisabler:
    def __init__(self):
        self.wallet_address = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490"
        self.disable_file = "AUTO_TRANSFER_DISABLED.txt"
        
    def create_disable_confirmation(self):
        """Create confirmation file that auto-transfer is disabled"""
        with open(self.disable_file, 'w') as f:
            f.write(f"AUTO-TRANSFER DISABLED\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Command: Disable auto-transfer on all engines\n")
            f.write(f"Wallet: {self.wallet_address}\n")
            f.write(f"Status: DISABLED - Profits will accumulate in trading wallets\n")
        logger.info(f"Created disable confirmation file: {self.disable_file}")
        
    def stop_withdrawal_processes(self):
        """Stop all withdrawal monitoring processes"""
        logger.info("🛑 DISABLING AUTO-TRANSFER ON ALL ENGINES")
        
        # Processes that handle auto-withdrawal
        withdrawal_processes = [
            "direct_withdrawal_executor.py",
            "production_auto_withdrawal.py", 
            "accelerated_withdrawal_executor.py",
            "live_withdrawal_executor.py",
            "final_buffer_withdrawal.py"
        ]
        
        stopped_processes = []
        
        for process_name in withdrawal_processes:
            try:
                # Find and kill processes
                result = subprocess.run(
                    f'pgrep -f "{process_name}"',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            try:
                                os.kill(int(pid), signal.SIGTERM)
                                logger.info(f"✅ Stopped {process_name} (PID: {pid})")
                                stopped_processes.append(process_name)
                                time.sleep(1)  # Give process time to clean up
                            except ProcessLookupError:
                                logger.info(f"Process {pid} already terminated")
                            except Exception as e:
                                logger.error(f"Error stopping process {pid}: {e}")
                else:
                    logger.info(f"No running process found for {process_name}")
                    
            except Exception as e:
                logger.error(f"Error checking process {process_name}: {e}")
                
        return stopped_processes
        
    def update_engine_configs(self):
        """Update engine configurations to disable auto-transfer"""
        logger.info("📝 Updating engine configurations...")
        
        # List of engine files to update
        engine_files = [
            "flash_loan_live_deployment_enhanced.py",
            "flash_loan_live_deployment_fixed.py", 
            "flash_loan_live_deployment.py"
        ]
        
        updated_files = []
        
        for engine_file in engine_files:
            if os.path.exists(engine_file):
                try:
                    # Read the file
                    with open(engine_file, 'r') as f:
                        content = f.read()
                    
                    # Add auto-transfer disable flag
                    disable_flag = f'''
# AUTO-TRANSFER DISABLED - {datetime.now().isoformat()}
AUTO_TRANSFER_ENABLED = False
DISABLE_AUTO_TRANSFER = True
'''
                    
                    # Insert disable flag at the beginning of the file
                    new_content = disable_flag + content
                    
                    # Write back to file
                    with open(engine_file, 'w') as f:
                        f.write(new_content)
                    
                    updated_files.append(engine_file)
                    logger.info(f"✅ Updated {engine_file} - Auto-transfer disabled")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating {engine_file}: {e}")
            else:
                logger.info(f"File not found: {engine_file}")
                
        return updated_files
        
    def update_dashboard_configs(self):
        """Update dashboard configurations"""
        logger.info("📊 Updating dashboard configurations...")
        
        dashboard_files = [
            "aineon_live_profit_dashboard.py",
            "simple_live_dashboard.py",
            "aineon_chief_architect_dashboard_ascii.py"
        ]
        
        updated_dashboards = []
        
        for dashboard_file in dashboard_files:
            if os.path.exists(dashboard_file):
                try:
                    with open(dashboard_file, 'r') as f:
                        content = f.read()
                    
                    # Add auto-transfer disabled status
                    disable_status = f'''
# AUTO-TRANSFER STATUS: DISABLED - {datetime.now().isoformat()}
AUTO_TRANSFER_STATUS = "DISABLED - Profits accumulating in trading wallets"
TRANSFER_DISABLED = True
'''
                    
                    new_content = disable_status + content
                    
                    with open(dashboard_file, 'w') as f:
                        f.write(new_content)
                    
                    updated_dashboards.append(dashboard_file)
                    logger.info(f"✅ Updated dashboard {dashboard_file}")
                    
                except Exception as e:
                    logger.error(f"❌ Error updating dashboard {dashboard_file}: {e}")
                    
        return updated_dashboards
        
    def create_disabled_config_file(self):
        """Create a configuration file that indicates auto-transfer is disabled"""
        config_content = f"""# AINEON AUTO-TRANSFER CONFIGURATION
# Generated: {datetime.now().isoformat()}

[AUTO_TRANSFER]
ENABLED = False
DISABLED_TIMESTAMP = "{datetime.now().isoformat()}"
REASON = "Chief Architect Command - Disable auto-transfer on all engines"
WALLET_ADDRESS = "{self.wallet_address}"

[STATUS]
TRANSFERS_ACTIVE = False
PROFITS_ACCUMULATING = True
ENGINES_OPERATIONAL = True
MONITORING_ACTIVE = True

[ENGINES]
ENGINE_1_AUTO_TRANSFER = False
ENGINE_2_AUTO_TRANSFER = False
ALL_ENGINES_DISABLED = True

[NOTE]
Profits will now accumulate in the trading wallets instead of being auto-transferred.
Manual withdrawal can be initiated when desired.
"""
        
        with open("auto_transfer_config.ini", 'w') as f:
            f.write(config_content)
            
        logger.info("✅ Created auto-transfer configuration file")
        
    def display_status(self):
        """Display current status after disabling auto-transfer"""
        print("\n" + "="*80)
        print("🛑 AINEON AUTO-TRANSFER DISABLED")
        print("="*80)
        print(f"⏰  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🎯 Target Wallet: {self.wallet_address}")
        print(f"📁 Disable File: {self.disable_file}")
        print(f"⚙️  Config File: auto_transfer_config.ini")
        print()
        print("📊 CURRENT STATUS:")
        print("   • Auto-Transfer: DISABLED")
        print("   • Profit Accumulation: ACTIVE")
        print("   • Engine Operations: CONTINUING")
        print("   • Trading Wallets: ACCUMULATING PROFITS")
        print()
        print("💰 PROFIT FLOW NOW:")
        print("   Flash Loan Arbitrage → Profit Generation → Trading Wallet (ACCUMULATING)")
        print()
        print("🔧 TO RE-ENABLE AUTO-TRANSFER:")
        print("   Run: python enable_auto_transfer.py")
        print()
        print("📈 MONITORING:")
        print("   • Check aineon_live_dashboard.html for real-time profit accumulation")
        print("   • Profits will build up in trading wallets")
        print("   • Manual withdrawal available when needed")
        print("="*80)
        
    def run(self):
        """Main execution function"""
        logger.info("🚀 Starting AINEON Auto-Transfer Disable Process")
        
        # Step 1: Create disable confirmation
        self.create_disable_confirmation()
        
        # Step 2: Stop withdrawal processes
        stopped_processes = self.stop_withdrawal_processes()
        
        # Step 3: Update engine configurations
        updated_engines = self.update_engine_configs()
        
        # Step 4: Update dashboard configurations
        updated_dashboards = self.update_dashboard_configs()
        
        # Step 5: Create configuration file
        self.create_disabled_config_file()
        
        # Step 6: Display status
        self.display_status()
        
        # Summary
        logger.info("✅ AUTO-TRANSFER DISABLE PROCESS COMPLETED")
        logger.info(f"Stopped {len(stopped_processes)} withdrawal processes")
        logger.info(f"Updated {len(updated_engines)} engine configurations")
        logger.info(f"Updated {len(updated_dashboards)} dashboard configurations")
        
        return {
            'stopped_processes': stopped_processes,
            'updated_engines': updated_engines,
            'updated_dashboards': updated_dashboards,
            'status': 'DISABLED'
        }

if __name__ == "__main__":
    disabler = AutoTransferDisabler()
    result = disabler.run()
    
    print(f"\n🎯 RESULT: Auto-transfer disabled successfully")
    print(f"📋 Summary: {len(result['stopped_processes'])} processes stopped, "
          f"{len(result['updated_engines'])} engines updated")
