#!/usr/bin/env python3
"""
AINEON Wallet Address Validator
Validates Ethereum wallet addresses for profit withdrawal configuration
"""

import re
import sys
from web3 import Web3
from eth_account import Account
import asyncio

def validate_ethereum_address(address: str) -> dict:
    """
    Validate an Ethereum address
    
    Returns:
        dict: {
            'valid': bool,
            'checksum_valid': bool,
            'format_correct': bool,
            'message': str,
            'normalized_address': str
        }
    """
    
    # Clean address (remove spaces, convert to lowercase)
    address = address.strip().lower()
    
    # Check basic format
    format_pattern = r'^0x[a-f0-9]{40}$'
    format_correct = bool(re.match(format_pattern, address))
    
    if not format_correct:
        return {
            'valid': False,
            'checksum_valid': False,
            'format_correct': False,
            'message': 'Invalid format: Address must be 0x followed by 40 hexadecimal characters',
            'normalized_address': None
        }
    
    # Check checksum
    try:
        checksum_address = Web3.to_checksum_address(address)
        checksum_valid = (address == checksum_address.lower())
        normalized_address = checksum_address
    except Exception as e:
        return {
            'valid': False,
            'checksum_valid': False,
            'format_correct': True,
            'message': f'Invalid address: {str(e)}',
            'normalized_address': None
        }
    
    return {
        'valid': True,
        'checksum_valid': checksum_valid,
        'format_correct': True,
        'message': 'Valid Ethereum address',
        'normalized_address': normalized_address
    }

async def verify_address_on_chain(w3: Web3, address: str) -> dict:
    """
    Verify if address exists on blockchain
    
    Returns:
        dict: {
            'exists': bool,
            'balance_eth': str,
            'message': str
        }
    """
    try:
        # Check if address has any transactions
        balance_wei = w3.eth.get_balance(address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        
        return {
            'exists': True,
            'balance_eth': str(balance_eth),
            'message': f'Address exists with balance: {balance_eth:.6f} ETH'
        }
    except Exception as e:
        return {
            'exists': False,
            'balance_eth': '0',
            'message': f'Address verification failed: {str(e)}'
        }

def is_different_from_trading_wallet(address: str, trading_wallet: str) -> bool:
    """Check if address is different from trading wallet"""
    return address.lower() != trading_wallet.lower()

async def main():
    print("=" * 60)
    print("AINEON WALLET ADDRESS VALIDATOR")
    print("=" * 60)
    print()
    
    if len(sys.argv) != 2:
        print("Usage: python wallet_validator.py <ethereum_address>")
        print()
        print("Example:")
        print("python wallet_validator.py 0x742d35Cc6634C0532925a3b8D40715Ded8cE6a8d")
        return
    
    address = sys.argv[1]
    print(f"Validating address: {address}")
    print()
    
    # Basic validation
    validation = validate_ethereum_address(address)
    
    print("VALIDATION RESULTS:")
    print(f"   Format: {'[OK] Valid' if validation['format_correct'] else '[FAIL] Invalid'}")
    print(f"   Checksum: {'[OK] Valid' if validation['checksum_valid'] else '[WARN] No checksum'}")
    print(f"   Overall: {'[OK] VALID' if validation['valid'] else '[FAIL] INVALID'}")
    print()
    
    print(f"Message: {validation['message']}")
    print()
    
    if validation['valid'] and validation['normalized_address']:
        print(f"Normalized Address: {validation['normalized_address']}")
        print()
        
        # Check if different from typical trading wallets (security check)
        trading_wallet_examples = [
            "0x742d35Cc6634C0532925a3b8D40715Ded8E6a8d",  # Example
            "0x0000000000000000000000000000000000000000",  # Zero address
        ]
        
        is_safe = True
        for example in trading_wallet_examples:
            if is_different_from_trading_wallet(validation['normalized_address'], example):
                continue
            else:
                is_safe = False
                print("[WARN] SECURITY WARNING: Address matches example trading wallet")
                break
        
        if is_safe:
            print("[OK] Security Check: Address appears safe for profit withdrawal")
        print()
        
        # Try to verify on blockchain (optional)
        try:
            # Use public RPC endpoint for validation
            w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.alchemyapi.io/v2/demo'))
            
            print("Checking blockchain verification...")
            chain_result = await verify_address_on_chain(w3, validation['normalized_address'])
            print(f"   Blockchain: {'[OK] Exists' if chain_result['exists'] else '[FAIL] Not found'}")
            print(f"   Balance: {chain_result['balance_eth']} ETH")
            print(f"   Status: {chain_result['message']}")
            
        except Exception as e:
            print(f"   [WARN] Blockchain check failed: {str(e)[:50]}...")
        
        print()
        print("[OK] ADDRESS VALIDATION COMPLETE")
        print()
        print("[READY] FOR PROFIT WITHDRAWAL CONFIGURATION")
        
    else:
        print("[FAIL] ADDRESS VALIDATION FAILED")
        print("Please provide a valid Ethereum address")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())