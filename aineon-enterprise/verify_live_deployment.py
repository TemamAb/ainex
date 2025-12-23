#!/usr/bin/env python3
"""
AINEON LIVE DEPLOYMENT VERIFICATION
Verify the newly generated live deployment data on Etherscan
"""

import requests
import json
import time
from datetime import datetime

def verify_transaction(tx_hash):
    """Verify transaction on Etherscan"""
    try:
        print(f"Verifying transaction: {tx_hash}")
        
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
                print(f"  Block Number: {int(result.get('blockNumber', '0'), 16)}")
                return True
            else:
                print(f"Transaction not found or pending")
        else:
            print(f"API Error: {response.status_code}")
            
        return False
        
    except Exception as e:
        print(f"Error checking transaction: {e}")
        return False

def verify_wallet(wallet_address):
    """Check wallet balance"""
    try:
        print(f"\nChecking wallet balance for: {wallet_address}")
        
        url = f"https://api.etherscan.io/api?module=account&action=balance&address={wallet_address}&tag=latest"
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

def verify_contract(contract_address):
    """Check contract verification"""
    try:
        print(f"\nChecking contract: {contract_address}")
        
        url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('result'):
                result = data['result'][0]
                print(f"Contract Name: {result.get('ContractName', 'Unknown')}")
                print(f"Verified: {result.get('SourceCode', '') != ''}")
                print(f"Compiler: {result.get('CompilerVersion', 'Unknown')}")
                return True
            else:
                print(f"Contract not found or not verified")
        else:
            print(f"API Error: {response.status_code}")
            
        return False
        
    except Exception as e:
        print(f"Error checking contract: {e}")
        return False

def main():
    print("AINEON LIVE DEPLOYMENT VERIFICATION")
    print("=" * 50)
    
    # Live deployment data - Updated wallet from .env
    smart_wallet = "0x748Aa8ee067585F5bd02f0988eF6E71f2d662751"
    contract_address = "0x588c62217680b517091ad5ab01629f36a26d5593"
    transaction_hash = "0x00c69e2018f07abeb29a998b7370be1aa84ea9758d6ab479a072524e907b436c"
    
    print(f"Smart Wallet: {smart_wallet}")
    print(f"Contract: {contract_address}")
    print(f"Transaction: {transaction_hash}")
    print()
    
    # Verify transaction
    print("1. VERIFYING TRANSACTION:")
    tx_found = verify_transaction(transaction_hash)
    
    # Verify wallet
    print("\n2. VERIFYING WALLET:")
    balance = verify_wallet(smart_wallet)
    
    # Verify contract
    print("\n3. VERIFYING CONTRACT:")
    contract_verified = verify_contract(contract_address)
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY:")
    print(f"Transaction: {'FOUND' if tx_found else 'NOT FOUND'}")
    print(f"Wallet Balance: {balance if balance else 'Unknown'} ETH")
    print(f"Contract: {'VERIFIED' if contract_verified else 'NOT VERIFIED'}")
    
    if tx_found and balance is not None:
        print("\nRESULT: LIVE DEPLOYMENT VERIFIED ON BLOCKCHAIN")
        print("All data is authentic and verifiable on Etherscan")
    else:
        print("\nRESULT: VERIFICATION INCOMPLETE")
        print("Some data could not be verified")

if __name__ == "__main__":
    main()