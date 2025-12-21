#!/usr/bin/env python3
"""
AINEON Ethereum Transfer Validator
Validates ETH transfers to user wallet on Ethereum blockchain using Etherscan API
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import os

class EthereumTransferValidator:
    def __init__(self, wallet_address: str, etherscan_api_key: str = None):
        self.wallet_address = wallet_address.lower()
        self.etherscan_api_key = etherscan_api_key or os.getenv('ETHERSCAN_API_KEY')
        self.base_url = "https://api.etherscan.io/api"
        
    def get_eth_balance(self) -> Dict:
        """Get current ETH balance of the wallet"""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': self.wallet_address,
            'tag': 'latest',
            'apikey': self.etherscan_api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
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
    
    def get_eth_transfers(self, start_block: int = 0, end_block: int = 99999999, 
                         page: int = 1, offset: int = 100) -> Dict:
        """Get ETH transfer transactions for the wallet"""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': self.wallet_address,
            'startblock': start_block,
            'endblock': end_block,
            'page': page,
            'offset': offset,
            'sort': 'desc',
            'apikey': self.etherscan_api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
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
    
    def analyze_transfer_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze transfer patterns to identify potential AINEON transfers"""
        eth_transfers = []
        total_received = 0
        total_sent = 0
        transfer_count = 0
        
        for tx in transactions:
            try:
                # Convert values from wei to eth
                value_wei = int(tx['value'])
                value_eth = value_wei / (10 ** 18)
                
                # Check if this is an incoming transfer (to our wallet)
                if tx['to'].lower() == self.wallet_address:
                    eth_transfers.append({
                        'hash': tx['hash'],
                        'from': tx['from'],
                        'to': tx['to'],
                        'value_eth': value_eth,
                        'value_formatted': f"{value_eth:.6f} ETH",
                        'block_number': int(tx['blockNumber']),
                        'timestamp': int(tx['timeStamp']),
                        'datetime': datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'),
                        'gas_used': int(tx['gasUsed']),
                        'gas_price_gwei': int(tx['gasPrice']) / (10 ** 9),
                        'status': 'Success' if tx['txreceipt_status'] == '1' else 'Failed'
                    })
                    total_received += value_eth
                    transfer_count += 1
                
                # Check if this is an outgoing transfer (from our wallet)
                elif tx['from'].lower() == self.wallet_address:
                    total_sent += value_eth
                    
            except (ValueError, KeyError) as e:
                continue
        
        # Sort by value (highest first)
        eth_transfers.sort(key=lambda x: x['value_eth'], reverse=True)
        
        return {
            'total_incoming_transfers': transfer_count,
            'total_eth_received': total_received,
            'total_eth_sent': total_sent,
            'net_balance_change': total_received - total_sent,
            'largest_incoming_transfer': eth_transfers[0] if eth_transfers else None,
            'recent_transfers': eth_transfers[:10],  # Top 10 recent
            'all_transfers': eth_transfers
        }
    
    def validate_aineon_transfers(self, expected_transfers: List[float]) -> Dict:
        """Validate expected AINEON transfers against blockchain data"""
        print("Fetching wallet balance and transaction history...")
        
        # Get current balance
        balance_info = self.get_eth_balance()
        if balance_info['status'] != 'success':
            return {
                'validation_status': 'error',
                'message': f"Failed to get balance: {balance_info['message']}"
            }
        
        print(f"Current Balance: {balance_info['balance_formatted']}")
        
        # Get all transactions
        print("Fetching transaction history...")
        tx_info = self.get_eth_transfers()
        
        if tx_info['status'] != 'success':
            return {
                'validation_status': 'error',
                'message': f"Failed to get transactions: {tx_info['message']}"
            }
        
        print(f"Found {tx_info['total']} total transactions")
        
        # Analyze transfer patterns
        analysis = self.analyze_transfer_patterns(tx_info['transactions'])
        
        # Check for transfers matching expected amounts (within 0.01 ETH tolerance)
        validated_transfers = []
        unmatched_expected = expected_transfers.copy()
        
        for tx in analysis['all_transfers']:
            tx_value = round(tx['value_eth'], 2)
            
            # Check if this transaction matches any expected transfer
            for i, expected in enumerate(unmatched_expected):
                if abs(tx_value - expected) <= 0.01:  # 0.01 ETH tolerance
                    validated_transfers.append({
                        'expected_amount': expected,
                        'actual_amount': tx_value,
                        'transaction_hash': tx['hash'],
                        'timestamp': tx['datetime'],
                        'block_number': tx['block_number'],
                        'status': tx['status'],
                        'matched': True
                    })
                    unmatched_expected.pop(i)
                    break
        
        # Summary
        validation_summary = {
            'wallet_address': self.wallet_address,
            'current_balance_eth': balance_info['balance_eth'],
            'validation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_blockchain_transfers': analysis['total_incoming_transfers'],
            'total_eth_received': analysis['total_eth_received'],
            'expected_transfers_count': len(expected_transfers),
            'validated_transfers_count': len(validated_transfers),
            'unmatched_expected_count': len(unmatched_expected),
            'validation_success_rate': len(validated_transfers) / len(expected_transfers) * 100 if expected_transfers else 0
        }
        
        return {
            'validation_status': 'completed',
            'summary': validation_summary,
            'validated_transfers': validated_transfers,
            'unmatched_expected': unmatched_expected,
            'recent_transfers': analysis['recent_transfers'],
            'largest_transfer': analysis['largest_incoming_transfer']
():
    # Your        }

def main wallet address
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
    
    # Initialize validator
    print("AINEON Ethereum Transfer Validator")
    print("=" * 50)
    print(f"Target Wallet: {wallet_address}")
    print(f"Expected Transfers: {expected_transfers}")
    print("=" * 50)
    
    validator = EthereumTransferValidator(wallet_address)
    
    # Run validation
    result = validator.validate_aineon_transfers(expected_transfers)
    
    if result['validation_status'] == 'error':
        print(f"Validation Error: {result['message']}")
        return
    
    # Display results
    summary = result['summary']
    print("\nVALIDATION SUMMARY")
    print("=" * 50)
    print(f"Current Balance: {summary['current_balance_eth']:.6f} ETH")
    print(f"Total Blockchain Transfers: {summary['total_blockchain_transfers']}")
    print(f"Total ETH Received: {summary['total_eth_received']:.6f} ETH")
    print(f"Expected Transfers: {summary['expected_transfers_count']}")
    print(f"Validated Transfers: {summary['validated_transfers_count']}")
    print(f"Success Rate: {summary['validation_success_rate']:.1f}%")
    
    if result['validated_transfers']:
        print("\nVALIDATED TRANSFERS")
        print("=" * 50)
        for transfer in result['validated_transfers']:
            print(f"Amount: {transfer['actual_amount']:.2f} ETH (expected {transfer['expected_amount']:.2f})")
            print(f"Hash: {transfer['transaction_hash']}")
            print(f"Time: {transfer['timestamp']}")
            print(f"Status: {transfer['status']}")
            print("-" * 30)
    
    if result['unmatched_expected']:
        print("\nUNMATCHED EXPECTED TRANSFERS")
        print("=" * 50)
        for amount in result['unmatched_expected']:
            print(f"Expected: {amount:.2f} ETH (not found on blockchain)")
    
    if result['recent_transfers']:
        print("\nRECENT LARGEST TRANSFERS")
        print("=" * 50)
        for tx in result['recent_transfers'][:5]:  # Top 5
            print(f"Amount: {tx['value_formatted']}")
            print(f"Hash: {tx['hash']}")
            print(f"Time: {tx['datetime']}")
            print(f"Status: {tx['status']}")
            print("-" * 30)
    
    print("\nEtherscan Links:")
    print(f"Wallet: https://etherscan.io/address/{wallet_address}")
    
    if result['validated_transfers']:
        for transfer in result['validated_transfers']:
            print(f"Tx: https://etherscan.io/tx/{transfer['transaction_hash']}")

if __name__ == "__main__":
    main()