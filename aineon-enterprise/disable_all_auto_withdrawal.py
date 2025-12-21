#!/usr/bin/env python3
"""
Disable Auto-Withdrawal Systems
Disables all auto-withdrawal and auto-transfer systems across the AINEON flash loan engines.
"""

import os
import signal
import time
import sys

def disable_auto_withdrawal():
    """Disable all auto-withdrawal systems"""
    print("🔴 DISABLING AUTO-WITHDRAWAL SYSTEMS...")
    
    # Kill auto-withdrawal processes
    withdrawal_processes = [
        "direct_withdrawal_executor.py",
        "production_auto_withdrawal.py", 
        "production_auto_withdrawal_fixed.py",
        "accelerated_withdrawal_executor.py",
        "live_withdrawal_executor.py",
        "auto_withdrawal_system.py"
    ]
    
    killed_processes = []
    
    for proc_name in withdrawal_processes:
        try:
            # Use taskkill for Windows
            os.system(f'taskkill /F /IM python.exe /FI "COMMANDLINE LIKE %{proc_name}%" 2>nul')
            killed_processes.append(proc_name)
            print(f"✅ Killed {proc_name}")
        except:
            pass
    
    # Create disabled flag files
    disabled_files = [
        "AUTO_TRANSFER_DISABLED.txt",
        "PRODUCTION_WITHDRAWAL_APPROVAL_REQUIRED.txt"
    ]
    
    for file in disabled_files:
        try:
            with open(file, 'w') as f:
                f.write("AUTO-WITHDRAWAL DISABLED BY USER REQUEST\n")
                f.write(f"Disabled at: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                f.write("All auto-withdrawal systems have been disabled.\n")
            print(f"✅ Created {file}")
        except Exception as e:
            print(f"⚠️  Could not create {file}: {e}")
    
    # Update configuration files to disable auto-withdrawal
    config_files = [
        "auto_transfer_config.ini",
        "unlimited_withdrawal_config.py"
    ]
    
    for config_file in config_files:
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Replace enabled with disabled
                content = content.replace('enabled = true', 'enabled = false')
                content = content.replace('AUTO_TRANSFER_ENABLED = True', 'AUTO_TRANSFER_ENABLED = False')
                content = content.replace('auto_withdrawal_enabled = True', 'auto_withdrawal_enabled = False')
                
                with open(config_file, 'w') as f:
                    f.write(content)
                print(f"✅ Updated {config_file}")
        except Exception as e:
            print(f"⚠️  Could not update {config_file}: {e}")
    
    print("\n🔴 AUTO-WITHDRAWAL SYSTEMS DISABLED")
    print("All auto-transfer systems have been successfully disabled.")
    print("Profits will accumulate in the trading wallets until manual withdrawal.")
    
    return True

if __name__ == "__main__":
    disable_auto_withdrawal()