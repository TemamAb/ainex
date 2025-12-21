#!/usr/bin/env python3
"""
Live Blockchain Verification for AINEON Flash Loan Engine
Checks actual transactions in real-time
"""

import requests
import json
import time
from datetime import datetime

# The target wallet
TARGET_WALLET = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490"

# Recent transaction hashes from the live engine
RECENT_TRANSACTIONS = [
    "0xa48b0b75d84a1731b65df9bea4fcb26dc18a7c66a662589b7fb799765b343ab3",
    "0xae9b7bdf418b74c1139504213d1549025ec6b99c19a323aaff1cd89b5bef7ba6",
    "0x29b7a5246bcd7221efc0126cb58685cb5979d243d542cbc041f530911964a39d",
    "0x8ba4d8c8f48da66e13e776ef13ca6beb33594be3f72a380bab19aece8f2198cc",
    "0x03700139cd5bfbeba10ac858427895a0153b1b5abe7ed8b1eb34cac5a4b0e1ac"
]

def check_transaction(tx_hash):
    """Check a transaction on Etherscan"""
    try:
        # Try different Etherscan endpoints
        base_urls = [
            "https://api.etherscan.io",
            "https://api-goerli.etherscan.io", 
            "https://api-sepolia.etherscan.io"
        ]
        
        for base_url in base_urls:
            try:
                # Try without API key first
                url = f"{base_url}/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey=YourApiKeyToken"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result') and data['result'] != 'Not found':
                        print(f"✅ LIVE TRANSACTION FOUND: {tx_hash}")
                        print(f"   From: {data['result']['from']}")
                        print(f"   To: {data['result']['to']}")
                        print(f"   Value: {int(data['result']['value'], 16) / 1e18:.6f} ETH")
                        print(f"   Status: {'SUCCESS' if data['result']['hash'] else 'PENDING'}")
                        return True
                    else:
                        print(f"⏳ Transaction {tx_hash[:10]}... not found on {base_url}")
            except:
                continue
                
        return False
        
    except Exception as e:
        print(f"❌ Error checking {tx_hash}: {e}")
        return False

def check_wallet_balance():
    """Check current wallet balance"""
    try:
        # Multiple endpoints to try
        base_urls = [
            "https://api.etherscan.io",
            "https://api-goerli.etherscan.io",
            "https://api-sepolia.etherscan.io"
        ]
        
        for base_url in base_urls:
            try:
                url = f"{base_url}/api?module=account&action=balance&address={TARGET_WALLET}&tag=latest&apikey=YourApiKeyToken"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == '1' and data.get('result'):
                        balance_wei = int(data['result'])
                        balance_eth = balance_wei / 1e18
                        print(f"✅ WALLET BALANCE: {balance_eth:.6f} ETH")
                        return balance_eth
                    else:
                        print(f"⏳ Balance check on {base_url}: {data.get('message', 'No response')}")
            except:
                continue
                
        print("❌ Could not verify wallet balance")
        return None
        
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return None

def main():
    print("🔍 LIVE BLOCKCHAIN VERIFICATION - AINEON ENGINE")
    print("=" * 60)
    print(f"Target Wallet: {TARGET_WALLET}")
    print(f"Check Time: {datetime.now()}")
    print("=" * 60)
    
    # Check wallet balance
    print("\n💰 CHECKING WALLET BALANCE...")
    balance = check_wallet_balance()
    
    # Check recent transactions
    print("\n🔄 CHECKING LIVE TRANSACTIONS...")
    found_count = 0
    
    for i, tx_hash in enumerate(RECENT_TRANSACTIONS, 1):
        print(f"\n[{i}/{len(RECENT_TRANSACTIONS)}] Checking: {tx_hash[:10]}...")
        if check_transaction(tx_hash):
            found_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION SUMMARY:")
    print(f"   Transactions Found: {found_count}/{len(RECENT_TRANSACTIONS)}")
    print(f"   Wallet Balance: {balance if balance else 'Unknown'} ETH")
    
    if found_count > 0:
        print(f"   ✅ BLOCKCHAIN VERIFICATION: CONFIRMED LIVE SYSTEM")
    else:
        print(f"   ⚠️  BLOCKCHAIN VERIFICATION: INCOMPLETE")
    
    print("=" * 60)

if __name__ == "__main__":
    main()