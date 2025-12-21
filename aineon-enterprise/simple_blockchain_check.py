#!/usr/bin/env python3
"""
Simple blockchain verification for AINEON live transactions
"""

import requests
import json
import time

# Live transaction hash from the engine
LATEST_TX = "0x1404f0a079ac0904d4e245fb3a3cf1b24548f73179fabc850f53d87e0c5ce30a"
TARGET_WALLET = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490"

def check_transaction(tx_hash):
    """Check transaction on Etherscan"""
    try:
        print(f"Checking transaction: {tx_hash}")
        
        # Try mainnet
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('result') and data['result'] != 'Not found':
                print(f"SUCCESS: Found transaction {tx_hash}")
                result = data['result']
                print(f"  From: {result.get('from', 'N/A')}")
                print(f"  To: {result.get('to', 'N/A')}")
                value_wei = int(result.get('value', '0'), 16)
                value_eth = value_wei / 1e18
                print(f"  Value: {value_eth:.6f} ETH")
                print(f"  Gas Used: {int(result.get('gas', '0'), 16)}")
                return True
            else:
                print(f"Transaction not found or pending")
        else:
            print(f"API Error: {response.status_code}")
            
        return False
        
    except Exception as e:
        print(f"Error checking transaction: {e}")
        return False

def check_wallet_balance():
    """Check wallet balance"""
    try:
        print(f"\nChecking wallet balance for: {TARGET_WALLET}")
        
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={TARGET_WALLET}&tag=latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('result'):
                balance_wei = int(data['result'])
                balance_eth = balance_wei / 1e18
                print(f"Wallet Balance: {balance_eth:.6f} ETH")
                return balance_eth
            else:
                print(f"Could not get balance: {data.get('message', 'Unknown error')}")
        else:
            print(f"API Error: {response.status_code}")
            
        return None
        
    except Exception as e:
        print(f"Error checking balance: {e}")
        return None

def main():
    print("AINEON LIVE BLOCKCHAIN VERIFICATION")
    print("=" * 50)
    
    # Check latest transaction
    print("\n1. CHECKING LATEST TRANSACTION:")
    tx_found = check_transaction(LATEST_TX)
    
    # Check wallet balance
    print("\n2. CHECKING WALLET BALANCE:")
    balance = check_wallet_balance()
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY:")
    print(f"Latest Transaction: {'FOUND' if tx_found else 'NOT FOUND'}")
    print(f"Wallet Balance: {balance if balance else 'Unknown'} ETH")
    
    if tx_found:
        print("\nRESULT: LIVE TRANSACTIONS CONFIRMED ON BLOCKCHAIN")
    else:
        print("\nRESULT: TRANSACTION VERIFICATION INCOMPLETE")

if __name__ == "__main__":
    main()