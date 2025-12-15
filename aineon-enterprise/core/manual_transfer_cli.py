"""
Manual Profit Transfer CLI - Control and execute manual transfers
For use with MANUAL transfer mode
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
from profit_manager import ProfitManager

load_dotenv()


class ManualTransferCLI:
    """CLI for manual profit transfers"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        self.private_key = os.getenv("PRIVATE_KEY")
        
        self.profit_manager = ProfitManager(
            self.w3,
            self.wallet_address,
            self.private_key
        )
        
        # Set to MANUAL mode
        self.profit_manager.set_transfer_mode("MANUAL")
    
    async def check_balance(self):
        """Check current balance"""
        print("\n" + "="*80)
        print("BALANCE CHECK".center(80))
        print("="*80)
        
        try:
            balance = await self.profit_manager.get_balance_from_blockchain()
            print(f"Wallet: {self.wallet_address}")
            print(f"Current Balance: {balance:.6f} ETH")
            
            # Calculate USD value
            eth_price = await self._get_eth_price()
            if eth_price:
                usd_value = float(balance) * eth_price
                print(f"USD Value: ${usd_value:,.2f}")
            
            print(f"Transfer Mode: {self.profit_manager.transfer_mode}")
            
        except Exception as e:
            print(f"❌ Error checking balance: {e}")
    
    async def transfer_profits(self, amount_eth: float, recipient: str):
        """Execute manual profit transfer"""
        print("\n" + "="*80)
        print("MANUAL PROFIT TRANSFER".center(80))
        print("="*80)
        
        print(f"Amount: {amount_eth} ETH")
        print(f"Recipient: {recipient}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Confirmation
        confirm = input("\nProceed with transfer? (yes/no): ").lower()
        if confirm != "yes":
            print("❌ Transfer cancelled")
            return
        
        try:
            print("\n⏳ Processing transfer...")
            tx_hash = await self.profit_manager.manual_transfer_profits(amount_eth, recipient)
            
            if tx_hash:
                print(f"\n✅ Transfer successful!")
                print(f"Transaction Hash: {tx_hash}")
                print(f"Status: Pending")
                print(f"\nView on Etherscan: https://etherscan.io/tx/{tx_hash}")
            else:
                print(f"\n❌ Transfer failed")
        
        except Exception as e:
            print(f"❌ Error during transfer: {e}")
    
    async def view_history(self):
        """View transfer history"""
        print("\n" + "="*80)
        print("TRANSFER HISTORY".center(80))
        print("="*80)
        
        history = self.profit_manager.get_transaction_history(limit=20)
        
        if not history:
            print("No transactions recorded")
            return
        
        print(f"\nTotal Transactions: {len(history)}")
        print("\nRecent Transfers:")
        print("-" * 80)
        
        for i, tx in enumerate(history, 1):
            if tx.get("type") == "MANUAL_TRANSFER":
                amount = tx.get("profit_eth", 0)
                recipient = tx.get("recipient", "N/A")
                tx_hash = tx.get("tx_hash", "N/A")
                timestamp = tx.get("timestamp", "N/A")
                
                print(f"\n{i}. {timestamp}")
                print(f"   Amount: {amount:.6f} ETH")
                print(f"   Recipient: {recipient}")
                print(f"   Hash: {tx_hash[:20]}...")
    
    async def configure_auto_transfer(self):
        """Configure auto-transfer settings"""
        print("\n" + "="*80)
        print("CONFIGURE AUTO-TRANSFER".center(80))
        print("="*80)
        
        recipient = input("Recipient address (0x...): ").strip()
        if not recipient.startswith("0x"):
            print("❌ Invalid address format")
            return
        
        try:
            threshold = float(input("Threshold (ETH): "))
        except ValueError:
            print("❌ Invalid threshold amount")
            return
        
        self.profit_manager.set_auto_transfer(recipient, threshold)
        
        print(f"\n✅ Auto-transfer configured:")
        print(f"   Recipient: {recipient}")
        print(f"   Threshold: {threshold} ETH")
        print(f"\nTo enable AUTO mode, set TRANSFER_MODE=AUTO in .env")
    
    async def change_transfer_mode(self, mode: str):
        """Change transfer mode"""
        print("\n" + "="*80)
        print("CHANGE TRANSFER MODE".center(80))
        print("="*80)
        
        self.profit_manager.set_transfer_mode(mode)
        print(f"✅ Transfer mode set to: {mode}")
        
        if mode == "MANUAL":
            print("   Profits accumulate in wallet")
            print("   Transfer requires manual action")
        elif mode == "AUTO":
            print("   Profits transfer automatically at threshold")
            print("   Must configure recipient first")
        elif mode == "DISABLED":
            print("   Profits accumulate indefinitely")
            print("   No automatic transfers")
    
    async def _get_eth_price(self) -> float:
        """Get current ETH price"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
                ) as response:
                    data = await response.json()
                    return data['ethereum']['usd']
        except:
            return None
    
    async def show_menu(self):
        """Show interactive menu"""
        while True:
            print("\n" + "="*80)
            print("MANUAL PROFIT TRANSFER CONTROL".center(80))
            print("="*80)
            print("\nOptions:")
            print("  1. Check Balance")
            print("  2. Transfer Profits (MANUAL)")
            print("  3. View Transfer History")
            print("  4. Configure Auto-Transfer")
            print("  5. Change Transfer Mode")
            print("  6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                await self.check_balance()
            
            elif choice == "2":
                amount = input("Amount (ETH): ").strip()
                recipient = input("Recipient (0x...): ").strip()
                try:
                    amount = float(amount)
                    await self.transfer_profits(amount, recipient)
                except ValueError:
                    print("❌ Invalid amount")
            
            elif choice == "3":
                await self.view_history()
            
            elif choice == "4":
                await self.configure_auto_transfer()
            
            elif choice == "5":
                print("\nTransfer Modes:")
                print("  1. MANUAL (default)")
                print("  2. AUTO")
                print("  3. DISABLED")
                mode_choice = input("Select mode (1-3): ").strip()
                
                modes = {"1": "MANUAL", "2": "AUTO", "3": "DISABLED"}
                if mode_choice in modes:
                    await self.change_transfer_mode(modes[mode_choice])
                else:
                    print("❌ Invalid choice")
            
            elif choice == "6":
                print("\n✅ Goodbye!")
                break
            
            else:
                print("❌ Invalid option")


async def main():
    """Main entry point"""
    cli = ManualTransferCLI()
    
    if len(sys.argv) > 1:
        # Command line arguments
        command = sys.argv[1]
        
        if command == "balance":
            await cli.check_balance()
        
        elif command == "transfer":
            if len(sys.argv) < 4:
                print("Usage: python manual_transfer_cli.py transfer <amount> <recipient>")
                return
            amount = float(sys.argv[2])
            recipient = sys.argv[3]
            await cli.transfer_profits(amount, recipient)
        
        elif command == "history":
            await cli.view_history()
        
        elif command == "mode":
            if len(sys.argv) < 3:
                print("Usage: python manual_transfer_cli.py mode <MANUAL|AUTO|DISABLED>")
                return
            mode = sys.argv[2].upper()
            await cli.change_transfer_mode(mode)
        
        else:
            print(f"Unknown command: {command}")
    else:
        # Interactive menu
        await cli.show_menu()


if __name__ == "__main__":
    asyncio.run(main())
