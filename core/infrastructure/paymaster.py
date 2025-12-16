import os
import requests
from web3 import Web3

class PimlicoPaymaster:
    def __init__(self):
        self.chain_id = 1 # Mainnet
        self.entry_point = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
        self.pimlico_url = os.getenv("PAYMASTER_URL")
        self.bundler_url = os.getenv("BUNDLER_URL")

    def build_user_op(self, sender, call_data, nonce):
        """
        Constructs an ERC-4337 UserOperation to be sponsored.
        """
        # 1. Standard UserOp Structure
        user_op = {
            "sender": sender,
            "nonce": hex(nonce),
            "initCode": "0x",
            "callData": call_data,
            "callGasLimit": hex(500000),
            "verificationGasLimit": hex(100000),
            "preVerificationGas": hex(50000),
            "maxFeePerGas": hex(30000000000), # 30 Gwei
            "maxPriorityFeePerGas": hex(1000000000), # 1 Gwei
            "paymasterAndData": "0x", # Filled by Pimlico
            "signature": "0x" # Dummy for estimation
        }
        return user_op

    def sponsor_transaction(self, user_op):
        """
        Requests Pimlico to sign and pay for the gas.
        """
        # 1. Ask Pimlico for Paymaster Data
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "pm_sponsorUserOperation",
            "params": [user_op, {"entryPoint": self.entry_point}]
        }
        
        response = requests.post(self.pimlico_url, json=payload).json()
        
        if 'error' in response:
            print(f"[PAYMASTER] Sponsorship Failed: {response['error']}")
            return None
            
        # 2. Inject Paymaster Data into UserOp
        user_op['paymasterAndData'] = response['result']['paymasterAndData']
        print(f"[PAYMASTER] Gas Sponsored! Paymaster: {user_op['paymasterAndData'][:10]}...")
        return user_op

    def send_bundle(self, user_op, signature):
        """
        Sends the signed UserOp to the Bundler (Flashbots/Pimlico).
        """
        user_op['signature'] = signature
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_sendUserOperation",
            "params": [user_op, self.entry_point]
        }
        res = requests.post(self.bundler_url, json=payload).json()
        return res
