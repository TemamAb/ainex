"""
Pimlico Bundler Client - ERC-4337 UserOperation Submission
Handles sending UserOperations to Pimlico bundler with automatic failover
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
import aiohttp
from dataclasses import dataclass, asdict
from datetime import datetime
import time

logger = logging.getLogger(__name__)


@dataclass
class UserOperation:
    """ERC-4337 UserOperation structure"""
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
class BundlerConfig:
    """Bundler configuration"""
    pimlico_url: str = "https://api.pimlico.io/v2/ethereum/rpc"
    gelato_url: str = "https://relay.gelato.digital/rpc"
    candide_url: str = "https://api.candide.dev/rpc"
    max_retries: int = 5
    retry_backoff: List[int] = None  # [2, 4, 8, 16] seconds
    request_timeout: int = 30
    
    def __post_init__(self):
        if self.retry_backoff is None:
            self.retry_backoff = [2, 4, 8, 16]


class PimlicoBundlerClient:
    """
    Pimlico ERC-4337 Bundler Client
    
    Handles UserOperation submission with:
    - Multi-provider support (Pimlico, Gelato, Candide)
    - Automatic failover on rejection
    - Exponential backoff retry logic
    - Bundle inclusion monitoring
    - Transaction verification
    """
    
    def __init__(self, config: BundlerConfig = None):
        """Initialize bundler client"""
        self.config = config or BundlerConfig()
        self.providers = [
            {"name": "pimlico", "url": self.config.pimlico_url},
            {"name": "gelato", "url": self.config.gelato_url},
            {"name": "candide", "url": self.config.candide_url},
        ]
        self.current_provider_idx = 0
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = {
            "total_submissions": 0,
            "successful_submissions": 0,
            "failed_submissions": 0,
            "total_retries": 0,
            "provider_success_rates": {p["name"]: 0 for p in self.providers},
            "average_inclusion_time": 0,
            "inclusion_times": []
        }
    
    async def initialize(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
        logger.info("Pimlico bundler client initialized")
    
    async def shutdown(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
    
    async def send_user_operation(
        self,
        user_op: UserOperation,
        entry_point: str = "0x5FF137D4b0FDCD49DcA30c7B8b3D6C69D5EE1b23"
    ) -> tuple[bool, str]:
        """
        Send UserOperation to bundler
        
        Args:
            user_op: UserOperation to submit
            entry_point: EntryPoint contract address
        
        Returns:
            (success: bool, user_op_hash: str)
        """
        self.metrics["total_submissions"] += 1
        
        # Build request
        request_payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "eth_sendUserOperation",
            "params": [
                asdict(user_op),
                entry_point
            ]
        }
        
        # Try submission with failover
        for attempt in range(self.config.max_retries):
            provider = self.providers[self.current_provider_idx]
            
            try:
                logger.info(
                    f"Submitting UserOp to {provider['name']} "
                    f"(attempt {attempt + 1}/{self.config.max_retries})"
                )
                
                response = await self._post_request(
                    provider["url"],
                    request_payload
                )
                
                if response.get("result"):
                    user_op_hash = response["result"]
                    self.metrics["successful_submissions"] += 1
                    logger.info(f"✓ UserOp submitted: {user_op_hash}")
                    
                    # Update provider success rate
                    self._update_provider_metrics(provider["name"], success=True)
                    
                    return True, user_op_hash
                
                elif response.get("error"):
                    error = response["error"]
                    logger.warning(
                        f"Bundler rejected: {error.get('message', 'Unknown error')}"
                    )
                    
                    # Try fallback provider
                    self._switch_provider()
                    
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_backoff[min(attempt, len(self.config.retry_backoff) - 1)]
                        logger.info(f"Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        self.metrics["total_retries"] += 1
                    
                    self._update_provider_metrics(provider["name"], success=False)
                    continue
            
            except asyncio.TimeoutError:
                logger.error(f"Request timeout to {provider['name']}")
                self._switch_provider()
            
            except Exception as e:
                logger.error(f"Error submitting to {provider['name']}: {e}")
                self._update_provider_metrics(provider["name"], success=False)
                self._switch_provider()
        
        self.metrics["failed_submissions"] += 1
        logger.error("All bundler submission attempts failed")
        return False, ""
    
    async def get_user_operation_receipt(
        self,
        user_op_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get UserOperation receipt from bundler
        
        Args:
            user_op_hash: Hash returned from send_user_operation
        
        Returns:
            Receipt dict or None if not found
        """
        request_payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "eth_getUserOperationReceipt",
            "params": [user_op_hash]
        }
        
        try:
            provider = self.providers[self.current_provider_idx]
            response = await self._post_request(provider["url"], request_payload)
            
            if response.get("result"):
                receipt = response["result"]
                logger.info(f"Receipt found for {user_op_hash}")
                return receipt
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting receipt: {e}")
            return None
    
    async def wait_for_inclusion(
        self,
        user_op_hash: str,
        timeout: int = 120,
        poll_interval: int = 5
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Wait for UserOperation to be included in a bundle
        
        Args:
            user_op_hash: Hash to wait for
            timeout: Max seconds to wait
            poll_interval: Seconds between polls
        
        Returns:
            (success: bool, receipt: dict or None)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            receipt = await self.get_user_operation_receipt(user_op_hash)
            
            if receipt:
                elapsed = time.time() - start_time
                self.metrics["inclusion_times"].append(elapsed)
                self.metrics["average_inclusion_time"] = (
                    sum(self.metrics["inclusion_times"]) / 
                    len(self.metrics["inclusion_times"])
                )
                logger.info(f"✓ Included in {elapsed:.2f}s")
                return True, receipt
            
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"Timeout waiting for {user_op_hash}")
        return False, None
    
    async def estimate_user_operation_gas(
        self,
        user_op: UserOperation,
        entry_point: str = "0x5FF137D4b0FDCD49DcA30c7B8b3D6C69D5EE1b23"
    ) -> Optional[Dict[str, int]]:
        """
        Estimate gas for UserOperation
        
        Args:
            user_op: UserOperation to estimate
            entry_point: EntryPoint address
        
        Returns:
            {"callGasLimit": int, "verificationGasLimit": int, "preVerificationGas": int}
        """
        request_payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": "eth_estimateUserOperationGas",
            "params": [asdict(user_op), entry_point]
        }
        
        try:
            provider = self.providers[self.current_provider_idx]
            response = await self._post_request(provider["url"], request_payload)
            
            if response.get("result"):
                return response["result"]
            
            return None
        
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return None
    
    async def _post_request(
        self,
        url: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP POST request to bundler"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout)
            ) as response:
                return await response.json()
        
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"Request timeout to {url}")
        
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def _switch_provider(self):
        """Switch to next available provider"""
        self.current_provider_idx = (self.current_provider_idx + 1) % len(self.providers)
        logger.info(f"Switched to {self.providers[self.current_provider_idx]['name']}")
    
    def _update_provider_metrics(self, provider_name: str, success: bool):
        """Update provider success rate metrics"""
        # Simple success rate tracking
        if provider_name in self.metrics["provider_success_rates"]:
            current = self.metrics["provider_success_rates"][provider_name]
            # Weighted moving average
            self.metrics["provider_success_rates"][provider_name] = (
                current * 0.7 + (1.0 if success else 0.0) * 0.3
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bundler metrics"""
        return {
            "total_submissions": self.metrics["total_submissions"],
            "successful_submissions": self.metrics["successful_submissions"],
            "failed_submissions": self.metrics["failed_submissions"],
            "success_rate": (
                self.metrics["successful_submissions"] / 
                max(1, self.metrics["total_submissions"]) * 100
            ),
            "average_inclusion_time": self.metrics["average_inclusion_time"],
            "total_retries": self.metrics["total_retries"],
            "provider_success_rates": self.metrics["provider_success_rates"],
            "current_provider": self.providers[self.current_provider_idx]["name"]
        }


async def initialize_pimlico_bundler(config: BundlerConfig = None) -> PimlicoBundlerClient:
    """Factory function to initialize bundler client"""
    client = PimlicoBundlerClient(config)
    await client.initialize()
    return client
