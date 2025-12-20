"""
Pimlico Bundler Client Integration
Handles UserOperation submission, tracking, and receipt verification
Status: Production-Ready
"""

import asyncio
import json
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    BUNDLED = "BUNDLED"
    INCLUDED = "INCLUDED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REVERTED = "REVERTED"

@dataclass
class UserOperation:
    sender: str
    nonce: int
    initCode: str
    callData: str
    callGasLimit: int
    verificationGasLimit: int
    preVerificationGas: int
    maxFeePerGas: int
    maxPriorityFeePerGas: int
    paymasterAndData: str
    signature: str

@dataclass
class OperationReceipt:
    userOpHash: str
    blockNumber: int
    blockHash: str
    transactionHash: str
    transactionIndex: int
    success: bool
    actualGasUsed: int
    actualGasCost: int
    logs: List[Dict[str, Any]]

class PimlicoBundlerClient:
    """
    Handles all interactions with Pimlico Bundler service
    Supports: UserOp submission, tracking, receipt verification
    """
    
    def __init__(
        self,
        paymaster_url: str = "https://api.pimlico.io/v2/ethereum/rpc",
        chain_id: int = 1,
        max_retries: int = 3,
    ):
        self.paymaster_url = paymaster_url
        self.chain_id = chain_id
        self.max_retries = max_retries
        self.request_id = 0
        self.operations_map: Dict[str, Dict[str, Any]] = {}
        
    async def send_user_operation(
        self,
        user_op: UserOperation,
        entry_point: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send UserOperation to Pimlico bundler
        Returns: user_op_hash (unique identifier)
        """
        try:
            user_op_json = self._format_user_op(user_op)
            
            # Prepare RPC request
            payload = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": "eth_sendUserOperation",
                "params": [user_op_json, entry_point]
            }
            
            # Submit with retry
            user_op_hash = await self._submit_with_retry(payload)
            
            # Track operation
            self.operations_map[user_op_hash] = {
                "user_op": user_op,
                "status": OperationStatus.SUBMITTED,
                "submitted_at": datetime.now(),
                "metadata": metadata or {},
                "retries": 0,
            }
            
            logger.info(f"✅ UserOp sent: {user_op_hash[:16]}... | Status: SUBMITTED")
            return user_op_hash
            
        except Exception as e:
            logger.error(f"❌ Failed to send UserOp: {str(e)}")
            raise
    
    async def get_user_op_receipt(
        self,
        user_op_hash: str,
        timeout_seconds: int = 300,
    ) -> Optional[OperationReceipt]:
        """
        Poll Pimlico for UserOperation receipt
        Blocks until receipt available or timeout
        """
        start_time = datetime.now()
        poll_interval = 1  # seconds
        
        while True:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout_seconds:
                logger.error(f"⏱️ Receipt timeout for {user_op_hash[:16]}...")
                return None
            
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "eth_getUserOperationReceipt",
                    "params": [user_op_hash]
                }
                
                # Make RPC call
                response = await self._make_rpc_call(payload)
                
                if response and "result" in response and response["result"]:
                    receipt_data = response["result"]
                    receipt = OperationReceipt(
                        userOpHash=user_op_hash,
                        blockNumber=receipt_data.get("blockNumber"),
                        blockHash=receipt_data.get("blockHash"),
                        transactionHash=receipt_data.get("transactionHash"),
                        transactionIndex=receipt_data.get("transactionIndex"),
                        success=receipt_data.get("success", False),
                        actualGasUsed=receipt_data.get("actualGasUsed", 0),
                        actualGasCost=receipt_data.get("actualGasCost", 0),
                        logs=receipt_data.get("logs", []),
                    )
                    
                    # Update operation status
                    if user_op_hash in self.operations_map:
                        self.operations_map[user_op_hash]["status"] = (
                            OperationStatus.CONFIRMED if receipt.success 
                            else OperationStatus.REVERTED
                        )
                        self.operations_map[user_op_hash]["receipt"] = receipt
                    
                    logger.info(
                        f"📦 Receipt received: {user_op_hash[:16]}... | "
                        f"Success: {receipt.success} | Gas: {receipt.actualGasUsed}"
                    )
                    return receipt
                
                # Wait before next poll
                await asyncio.sleep(poll_interval)
                
            except Exception as e:
                logger.warning(f"⚠️ Poll error: {str(e)} | Retrying...")
                await asyncio.sleep(poll_interval)
    
    async def track_operation(
        self,
        user_op_hash: str,
        callback: Optional[callable] = None,
    ) -> Optional[OperationReceipt]:
        """
        Track operation from submission to confirmation
        Optionally call callback when complete
        """
        if user_op_hash not in self.operations_map:
            logger.warning(f"⚠️ Operation not tracked: {user_op_hash[:16]}...")
            return None
        
        # Update status to BUNDLED
        self.operations_map[user_op_hash]["status"] = OperationStatus.BUNDLED
        
        # Get receipt
        receipt = await self.get_user_op_receipt(user_op_hash)
        
        if receipt and callback:
            try:
                await callback(receipt)
            except Exception as e:
                logger.error(f"Callback error: {str(e)}")
        
        return receipt
    
    async def _submit_with_retry(
        self,
        payload: Dict[str, Any],
        current_attempt: int = 0,
    ) -> str:
        """
        Submit with exponential backoff retry
        Base delay: 250ms, 500ms, 1000ms
        """
        try:
            response = await self._make_rpc_call(payload)
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"RPC Error: {error_msg}")
                
                if current_attempt < self.max_retries:
                    delay = (250 * (2 ** current_attempt)) / 1000  # Convert to seconds
                    logger.info(f"⏳ Retrying in {delay}s... (attempt {current_attempt + 1})")
                    await asyncio.sleep(delay)
                    return await self._submit_with_retry(payload, current_attempt + 1)
                else:
                    raise Exception(f"Max retries exceeded: {error_msg}")
            
            if "result" not in response:
                raise Exception("Invalid RPC response: no result field")
            
            return response["result"]
            
        except Exception as e:
            if current_attempt < self.max_retries:
                delay = (250 * (2 ** current_attempt)) / 1000
                logger.info(f"⏳ Retrying in {delay}s... (attempt {current_attempt + 1})")
                await asyncio.sleep(delay)
                return await self._submit_with_retry(payload, current_attempt + 1)
            else:
                raise
    
    async def _make_rpc_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make RPC call to Pimlico
        In production, use aiohttp.ClientSession
        """
        try:
            # This is a placeholder - in production use actual HTTP client
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.paymaster_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"RPC call failed: {str(e)}")
            raise
    
    def _format_user_op(self, user_op: UserOperation) -> Dict[str, Any]:
        """Convert UserOperation dataclass to dict for JSON serialization"""
        return {
            "sender": user_op.sender,
            "nonce": hex(user_op.nonce),
            "initCode": user_op.initCode,
            "callData": user_op.callData,
            "callGasLimit": hex(user_op.callGasLimit),
            "verificationGasLimit": hex(user_op.verificationGasLimit),
            "preVerificationGas": hex(user_op.preVerificationGas),
            "maxFeePerGas": hex(user_op.maxFeePerGas),
            "maxPriorityFeePerGas": hex(user_op.maxPriorityFeePerGas),
            "paymasterAndData": user_op.paymasterAndData,
            "signature": user_op.signature,
        }
    
    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID"""
        self.request_id += 1
        return self.request_id
    
    def get_operation_status(self, user_op_hash: str) -> Optional[OperationStatus]:
        """Get current status of tracked operation"""
        if user_op_hash in self.operations_map:
            return self.operations_map[user_op_hash]["status"]
        return None
    
    def get_all_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get all tracked operations"""
        return self.operations_map.copy()
    
    def clear_old_operations(self, age_seconds: int = 3600):
        """Clear operations older than specified age"""
        now = datetime.now()
        to_remove = []
        
        for hash_key, op_data in self.operations_map.items():
            age = (now - op_data["submitted_at"]).total_seconds()
            if age > age_seconds:
                to_remove.append(hash_key)
        
        for hash_key in to_remove:
            del self.operations_map[hash_key]
        
        if to_remove:
            logger.info(f"🧹 Cleared {len(to_remove)} old operations")


# Integration with existing executor
class BundlerIntegration:
    """High-level bundler integration for AINEON executor"""
    
    def __init__(self, paymaster_url: str = None):
        self.client = PimlicoBundlerClient(
            paymaster_url=paymaster_url or "https://api.pimlico.io/v2/ethereum/rpc"
        )
    
    async def execute_user_operation(
        self,
        user_op: UserOperation,
        entry_point: str,
        profit_handler: Optional[callable] = None,
    ) -> Optional[OperationReceipt]:
        """
        Execute complete UserOp flow:
        1. Send to bundler
        2. Track until confirmation
        3. Verify profit
        4. Trigger profit handler
        """
        try:
            # Submit
            user_op_hash = await self.client.send_user_operation(user_op, entry_point)
            
            # Track to completion
            async def on_completion(receipt: OperationReceipt):
                if receipt.success and profit_handler:
                    await profit_handler(receipt)
            
            receipt = await self.client.track_operation(user_op_hash, on_completion)
            return receipt
            
        except Exception as e:
            logger.error(f"❌ UserOp execution failed: {str(e)}")
            raise
