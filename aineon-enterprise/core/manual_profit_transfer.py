#!/usr/bin/env python3
"""
AINEON Manual Profit Transfer CLI
Enables manual control over profit withdrawals (MANUAL MODE)
"""

import os
import asyncio
import json
from decimal import Decimal
from dotenv import load_dotenv
from web3 import Web3
from profit_manager import ProfitManager

load_dotenv()


class ManualTransferCLI:
    """Manual profit transfer interface"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ETH_RPC_URL")))
        self.wallet_address = os.getenv("WALLET_ADDRESS")
        self.profit_manager = ProfitManager(
            self.w3,
            self.wallet_address,
            os.getenv("PRIVATE_KEY", "")
        )
    
    async def get_current_balance(self) -> Decimal:
        """Get current verified profit balance"""
        return self.profit_manager.verified_profits_eth
    
    async def get_transfer_info(self) -> Dict:
        """Get transfer mode information"""
        return await self.profit_manager.get_transfer_status()
    
    async def initiate_transfer(self, amount_eth: Decimal) -> bool:
        """Initiate manual profit transfer"""
        return await self.profit_manager.manual_transfer_profits(amount_eth)
    
    async def transfer_all(self) -> bool:
        """Transfer all accumulated profits"""
        return await self.profit_manager.manual_transfer_profits()
    
    async def show_menu(self):
        """Display interactive menu"""
        while True:
            print("\n" + "="*70)
            print("AINEON MANUAL PROFIT TRANSFER - MANUAL MODE")
            print("="*70)
            
            # Get current status
            balance = await self.get_current_balance()
            info = await self.get_transfer_info()
            
            print(f"\nCurrent Status:")
            print(f"  Mode:                {info['mode']}")
            print(f"  Accumulated Profits: {balance:.6f} ETH")
            print(f"  Threshold:           {info['threshold_for_transfer']:.6f} ETH")
            print(f"  Destination:         {info['destination_address']}")
            
            print(f"\nOptions:")
            print(f"  1. Transfer All Profits ({balance:.6f} ETH)")
            print(f"  2. Transfer Custom Amount")
            print(f"  3. View Transfer History")
            print(f"  4. Check Wallet Balance")
            print(f"  5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                if await self.transfer_all():
                    print("\n✅ Manual transfer initiated")
                else:
                    print("\n❌ Transfer failed - no profits to transfer")
            
            elif choice == "2":
                try:
                    amount = float(input("Enter amount in ETH: "))
                    if await self.initiate_transfer(Decimal(str(amount))):
                        print(f"\n✅ Transfer of {amount} ETH initiated")
                    else:
                        print("\n❌ Transfer failed")
                except ValueError:
                    print("\n❌ Invalid amount")
            
            elif choice == "3":
                print("\nTransfer History:")
                for tx in self.profit_manager.transaction_history:
                    if tx.get('mode') == 'MANUAL':
                        print(f"  {tx['timestamp']}: {tx['amount_eth']} ETH -> {tx['status']}")
            
            elif choice == "4":
                balance_wei = self.w3.eth.get_balance(self.wallet_address)
                balance_eth = self.w3.from_wei(balance_wei, 'ether')
                print(f"\nWallet Balance: {balance_eth} ETH")
            
            elif choice == "5":
                print("\nExiting...")
                break
            
            else:
                print("\n❌ Invalid option")


async def main():
    """Main CLI entry point"""
    print("\n" + "="*70)
    print("AINEON MANUAL PROFIT TRANSFER TOOL")
    print("Transfer Control Mode - No Automatic Transfers")
    print("="*70)
    
    cli = ManualTransferCLI()
    
    # Show initial status
    info = await cli.get_transfer_info()
    print(f"\n✅ Transfer Mode: {info['mode']}")
    print(f"✅ Auto-Transfer: Disabled")
    print(f"✅ Control: Manual (user-initiated)")
    
    # Show interactive menu
    await cli.show_menu()


if __name__ == "__main__":
    asyncio.run(main())
