#!/usr/bin/env python3
"""
AINEON Ethereum Transfer Validator - Simple Version
Validates ETH transfers to user wallet on Ethereum blockchain using Etherscan API
"""

import requests
import json
from datetime import datetime
import os

def get_eth_balance(wallet_address, etherscan_api_key=None):
    """Get current ETH balance of the wallet"""
    if not etherscan_api_key:
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
    
    base_url = "https://api.etherscan.io/api"
    params = {
        'module': 'account',
        'action': 'balance',
        'address': wallet_address,
        'tag': 'latest',
        'apikey': etherscan_api_key or 'YourApiKeyToken'
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == '1':
            balance_wei = int(data['result'])
            balance_eth = balance_wei / (10 ** 18)
            return {
                'status': 'success',
                'balance_wei': balance_wei,
                'balance_eth': balance_eth,
                'balance_formatted': f"{balance_eth:.6f} ETH"
            }
        else:
            return {
                'status': 'error',
                'message': data.get('message', 'Unknown error')
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def get_eth_transfers(wallet_address, etherscan_api_key=None, start_block=0, end_block=99999999):
    """Get ETH transfer transactions for the wallet"""
    if not etherscan_api_key:
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
    
    base_url = "https://api.etherscan.io/api"
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': wallet_address,
        'startblock': start_block,
        'endblock': end_block,
        'page': 1,
        'offset': 100,
        'sort': 'desc',
        'apikey': etherscan_api_key or 'YourApiKeyToken'
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == '1':
            transactions = data['result']
            return {
                'status': 'success',
                'transactions': transactions,
                'total': len(transactions)
            }
        else:
            return {
                'status': 'error',
                'message': data.get('message', 'Unknown error'),
                'result': data.get('result', [])
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

def analyze_transfers(wallet_address, transactions):
    """Analyze transfer patterns"""
    eth_transfers = []
    total_received = 0
    
    for tx in transactions:
        try:
            # Check if this is an incoming transfer (to our wallet)
            if tx['to'].lower() == wallet_address.lower():
                value_wei = int(tx['value'])
                value_eth = value_wei / (10 ** 18)
                
                eth_transfers.append({
                    'hash': tx['hash'],
                    'from': tx['from'],
                    'to': tx['to'],
                    'value_eth': value_eth,
                    'value_formatted': f"{value_eth:.6f} ETH",
                    'block_number': int(tx['blockNumber']),
                    'timestamp': int(tx['timeStamp']),
                    'datetime': datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'Success' if tx['txreceipt_status'] == '1' else 'Failed'
                })
                total_received += value_eth
                
        except (ValueError, KeyError) as e:
            continue
    
    # Sort by value (highest first)
    eth_transfers.sort(key=lambda x: x['value_eth'], reverse=True)
    
    return {
        'total_transfers': len(eth_transfers),
        'total_eth_received': total_received,
        'largest_transfer': eth_transfers[0] if eth_transfers else None,
        'recent_transfers': eth_transfers[:10],  # Top 10 recent
        'all_transfers': eth_transfers
    }

def main():
    # Configuration
    wallet_address = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490"
    
    # Expected transfers from dashboard (59.08 ETH total from various transfers)
    expected_transfers = [
        10.00,  # Multiple 10 ETH transfers
        10.00,
        10.00,
        10.00,
        5.00,   # 5 ETH transfer
        3.08,   # 3.08 ETH transfer
        1.00,   # 1 ETH transfer
    ]
    
    print("AINEON Ethereum Transfer Validator")
    print("=" * 50)
    print(f"Target Wallet: {wallet_address}")
    print(f"Expected Transfers: {expected_transfers}")
    print("=" * 50)
    
    # Get current balance
    print("\nFetching wallet balance...")
    balance_info = get_eth_balance(wallet_address)
    
    if balance_info['status'] != 'success':
        print(f"Failed to get balance: {balance_info['message']}")
        return
    
    print(f"Current Balance: {balance_info['balance_formatted']}")
    
    # Get transactions
    print("\nFetching transaction history...")
    tx_info = get_eth_transfers(wallet_address)
    
    if tx_info['status'] != 'success':
        print(f"Failed to get transactions: {tx_info['message']}")
        return
    
    print(f"Found {tx_info['total']} total transactions")
    
    # Analyze transfers
    print("\nAnalyzing transfers...")
    analysis = analyze_transfers(wallet_address, tx_info['transactions'])
    
    print(f"\nANALYSIS RESULTS")
    print("=" * 50)
    print(f"Total Incoming Transfers: {analysis['total_transfers']}")
    print(f"Total ETH Received: {analysis['total_eth_received']:.6f} ETH")
    
    if analysis['largest_transfer']:
        print(f"Largest Transfer: {analysis['largest_transfer']['value_formatted']}")
        print(f"Hash: {analysis['largest_transfer']['hash']}")
        print(f"Time: {analysis['largest_transfer']['datetime']}")
    
    print(f"\nRECENT LARGEST TRANSFERS")
    print("=" * 50)
    for tx in analysis['recent_transfers'][:5]:  # Top 5
        print(f"Amount: {tx['value_formatted']}")
        print(f"Hash: {tx['hash']}")
        print(f"Time: {tx['datetime']}")
        print(f"Status: {tx['status']}")
        print("-" * 30)
    
    # Check for expected transfers
    print(f"\nVALIDATING EXPECTED TRANSFERS")
    print("=" * 50)
    validated_count = 0
    unmatched_expected = expected_transfers.copy()
    
    for tx in analysis['all_transfers']:
        tx_value = round(tx['value_eth'], 2)
        
        # Check if this transaction matches any expected transfer
        for i, expected in enumerate(unmatched_expected):
            if abs(tx_value - expected) <= 0.01:  # 0.01 ETH tolerance
                print(f"MATCHED: {tx_value:.2f} ETH (expected {expected:.2f} ETH)")
                print(f"Hash: {tx['hash']}")
                print(f"Time: {tx['datetime']}")
                print("-" * 30)
                validated_count += 1
                unmatched_expected.pop(i)
                break
    
    print(f"\nVALIDATION SUMMARY")
    print("=" * 50)
    print(f"Expected Transfers: {len(expected_transfers)}")
    print(f"Matched Transfers: {validated_count}")
    print(f"Success Rate: {validated_count/len(expected_transfers)*100:.1f}%")
    
    if unmatched_expected:
        print(f"\nUNMATCHED EXPECTED TRANSFERS:")
        for amount in unmatched_expected:
            print(f"Expected: {amount:.2f} ETH (not found on blockchain)")
    
    print(f"\nEtherscan Links:")
    print(f"Wallet: https://etherscan.io/address/{wallet_address}")
    
    if analysis['recent_transfers']:
        for tx in analysis['recent_transfers'][:3]:
            print(f"Tx: https://etherscan.io/tx/{tx['hash']}")

if __name__ == "__main__":
    main()