#!/usr/bin/env python3
"""
IMMEDIATE BLOCKCHAIN CHECK
Shows real blockchain status right now
"""

import requests
import json
from datetime import datetime

def check_blockchain_now():
    wallet = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490"
    api_key = "YourApiKeyToken"
    base_url = "https://api.etherscan.io/api"
    
    print("REAL-TIME BLOCKCHAIN VERIFICATION")
    print("=" * 60)
    print(f"Wallet: {wallet}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Check balance
    print("CHECKING WALLET BALANCE...")
    try:
        params = {
            "module": "account",
            "action": "balance", 
            "address": wallet,
            "tag": "latest",
            "apikey": api_key
        }
        
        response = requests.get(base_url, params=params, timeout=5)
        data = response.json()
        
        if data.get("status") == "1":
            balance_wei = int(data.get("result", "0"), 16)
            balance_eth = balance_wei / (10**18)
            print(f"CURRENT BALANCE: {balance_eth:.6f} ETH")
            
            if balance_eth == 0.0:
                print("RESULT: WALLET IS COMPLETELY EMPTY")
                print("NO PROFITS DETECTED ON BLOCKCHAIN")
            else:
                print(f"RESULT: {balance_eth:.6f} ETH VERIFIED ON BLOCKCHAIN")
        else:
            print("ERROR: Could not fetch balance from blockchain")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    
    # Check transactions
    print("CHECKING TRANSACTION HISTORY...")
    try:
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 10,
            "sort": "desc",
            "apikey": api_key
        }
        
        response = requests.get(base_url, params=params, timeout=5)
        data = response.json()
        
        if data.get("status") == "1":
            txs = data.get("result", [])
            print(f"TOTAL TRANSACTIONS: {len(txs)}")
            
            if len(txs) == 0:
                print("RESULT: NO TRANSACTIONS EVER")
                print("NO PROFIT ACTIVITY ON BLOCKCHAIN")
            else:
                print("RESULT: TRANSACTION HISTORY EXISTS")
                
                # Analyze transactions
                total_incoming = 0.0
                total_outgoing = 0.0
                
                for tx in txs[:5]:  # Check last 5
                    value_eth = int(tx.get("value", "0"), 16) / (10**18)
                    from_addr = tx.get("from", "").lower()
                    to_addr = tx.get("to", "").lower()
                    wallet_lower = wallet.lower()
                    
                    timestamp = int(tx.get("timeStamp", "0"))
                    time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"  TX: {value_eth:.6f} ETH at {time_str}")
                    
                    if to_addr == wallet_lower:
                        total_incoming += value_eth
                    elif from_addr == wallet_lower:
                        total_outgoing += value_eth
                
                net_profit = total_incoming - total_outgoing
                print(f"\nFINAL ANALYSIS:")
                print(f"Total Incoming: {total_incoming:.6f} ETH")
                print(f"Total Outgoing: {total_outgoing:.6f} ETH")
                print(f"Net Profit: {net_profit:.6f} ETH")
                
                if net_profit <= 0.001:
                    print("VERDICT: NO SIGNIFICANT PROFITS")
                else:
                    print(f"VERDICT: {net_profit:.6f} ETH PROFIT VERIFIED")
        else:
            print("ERROR: Could not fetch transactions from blockchain")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()
    print("=" * 60)
    print("BLOCKCHAIN VERIFICATION COMPLETE")
    print("ALL DATA FROM ETHEREUM MAINNET")
    print("=" * 60)

if __name__ == "__main__":
    check_blockchain_now()