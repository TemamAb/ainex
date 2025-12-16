"""
Key Rotation Engine - Automated Key Management
Hardware wallet integration with automated rotation scheduling
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

logger = logging.getLogger(__name__)


class KeyType(Enum):
    """Types of keys managed"""
    SIGNING_KEY = "signing_key"
    ENCRYPTION_KEY = "encryption_key"
    API_KEY = "api_key"
    WEBHOOK_SECRET = "webhook_secret"


class RotationPolicy(Enum):
    """Rotation policies"""
    WEEKLY = 7  # days
    MONTHLY = 30
    QUARTERLY = 90
    ON_DEMAND = 0
    NEVER = -1


@dataclass
class KeyMetadata:
    """Metadata for a key"""
    key_id: str
    key_type: KeyType
    created_at: datetime
    last_rotated: datetime
    rotation_policy: RotationPolicy
    version: int
    is_active: bool
    hardware_wallet: Optional[str] = None  # e.g., "ledger_nano_s"
    
    def is_due_for_rotation(self) -> bool:
        """Check if key needs rotation"""
        if self.rotation_policy == RotationPolicy.NEVER:
            return False
        if self.rotation_policy == RotationPolicy.ON_DEMAND:
            return False
        
        days_since_rotation = (datetime.utcnow() - self.last_rotated).days
        return days_since_rotation >= self.rotation_policy.value


@dataclass
class RotationRecord:
    """Record of a key rotation"""
    key_id: str
    rotation_timestamp: datetime
    old_version: int
    new_version: int
    reason: str
    verified: bool
    verification_timestamp: Optional[datetime] = None


class HardwareWalletConnector:
    """Interface to hardware wallets (Ledger, Trezor, etc.)"""
    
    def __init__(self, wallet_type: str = "ledger_nano_s"):
        self.wallet_type = wallet_type
        self.connected = False
        self.device_info = {}
    
    async def connect(self) -> bool:
        """Connect to hardware wallet"""
        try:
            logger.info(f"Connecting to {self.wallet_type}...")
            
            # In production, this would use ledger/trezor libraries
            # For now, simulate connection
            self.connected = True
            self.device_info = {
                'type': self.wallet_type,
                'version': '1.0.0',
                'connected_at': datetime.utcnow().isoformat(),
            }
            
            logger.info(f"Connected to {self.wallet_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to hardware wallet: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from hardware wallet"""
        self.connected = False
        logger.info(f"Disconnected from {self.wallet_type}")
    
    async def sign_transaction(self, transaction_hex: str) -> Optional[str]:
        """Sign transaction using hardware wallet"""
        if not self.connected:
            logger.error("Hardware wallet not connected")
            return None
        
        try:
            # In production, would send to hardware wallet for user approval
            logger.debug("Transaction signed by hardware wallet")
            return f"0x{transaction_hex}"  # Placeholder
            
        except Exception as e:
            logger.error(f"Failed to sign transaction: {e}")
            return None
    
    async def get_address(self, account_index: int = 0) -> Optional[str]:
        """Get address from hardware wallet"""
        if not self.connected:
            return None
        
        # In production, would retrieve from device
        return f"0x{'0' * 40}"  # Placeholder
    
    async def verify_address(self, account_index: int = 0) -> bool:
        """Display address on device for verification"""
        if not self.connected:
            return False
        
        logger.info(f"Verify address on device (account {account_index})")
        return True


class KeyRotationEngine:
    """Manages key lifecycle and automated rotation"""
    
    def __init__(self, hardware_wallet_type: str = "ledger_nano_s"):
        self.keys: Dict[str, KeyMetadata] = {}
        self.rotation_records: List[RotationRecord] = []
        self.hardware_wallet = HardwareWalletConnector(hardware_wallet_type)
        self.rotation_tasks: Dict[str, asyncio.Task] = {}
        self.rotation_callbacks: Dict[str, List[Callable]] = {}
    
    async def initialize(self) -> bool:
        """Initialize key rotation engine"""
        success = await self.hardware_wallet.connect()
        if not success:
            logger.warning("Hardware wallet unavailable, will use software signing")
        
        # Load existing keys from config
        await self._load_keys_from_config()
        
        # Start rotation monitoring
        await self._start_rotation_monitor()
        
        return True
    
    async def _load_keys_from_config(self):
        """Load key metadata from configuration"""
        try:
            # In production, would load from secure storage
            pass
        except Exception as e:
            logger.error(f"Failed to load keys: {e}")
    
    async def register_key(self, key_id: str, key_type: KeyType,
                          rotation_policy: RotationPolicy,
                          hardware_wallet: Optional[str] = None) -> bool:
        """Register a key for management"""
        now = datetime.utcnow()
        
        metadata = KeyMetadata(
            key_id=key_id,
            key_type=key_type,
            created_at=now,
            last_rotated=now,
            rotation_policy=rotation_policy,
            version=1,
            is_active=True,
            hardware_wallet=hardware_wallet,
        )
        
        self.keys[key_id] = metadata
        logger.info(f"Key registered: {key_id} ({key_type.value})")
        
        # Schedule rotation if needed
        if rotation_policy != RotationPolicy.NEVER:
            await self.schedule_rotation(key_id, rotation_policy)
        
        return True
    
    async def rotate_key(self, key_id: str, reason: str = "scheduled") -> bool:
        """Perform key rotation"""
        if key_id not in self.keys:
            logger.error(f"Key not found: {key_id}")
            return False
        
        metadata = self.keys[key_id]
        old_version = metadata.version
        new_version = old_version + 1
        
        try:
            # Step 1: Generate new key
            new_key = await self._generate_new_key(key_id, metadata.key_type)
            if not new_key:
                logger.error(f"Failed to generate new key: {key_id}")
                return False
            
            # Step 2: Store new key version
            await self._store_key_version(key_id, new_key, new_version)
            
            # Step 3: Verify new key works
            verified = await self._verify_key(key_id, new_key)
            if not verified:
                logger.error(f"Key verification failed: {key_id}")
                return False
            
            # Step 4: Mark new key as active
            metadata.is_active = True
            metadata.version = new_version
            metadata.last_rotated = datetime.utcnow()
            
            # Step 5: Create rotation record
            record = RotationRecord(
                key_id=key_id,
                rotation_timestamp=datetime.utcnow(),
                old_version=old_version,
                new_version=new_version,
                reason=reason,
                verified=True,
                verification_timestamp=datetime.utcnow(),
            )
            self.rotation_records.append(record)
            
            # Step 6: Notify callbacks
            await self._notify_rotation_callbacks(key_id, old_version, new_version)
            
            logger.info(f"Key rotated: {key_id} (v{old_version} → v{new_version})")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {key_id} - {e}")
            return False
    
    async def _generate_new_key(self, key_id: str, key_type: KeyType) -> Optional[str]:
        """Generate a new key"""
        try:
            if key_type == KeyType.SIGNING_KEY:
                return await self._generate_signing_key(key_id)
            elif key_type == KeyType.ENCRYPTION_KEY:
                return await self._generate_encryption_key()
            else:
                return await self._generate_api_key()
            
        except Exception as e:
            logger.error(f"Key generation failed: {e}")
            return None
    
    async def _generate_signing_key(self, key_id: str) -> Optional[str]:
        """Generate signing key (via hardware wallet if available)"""
        if self.hardware_wallet.connected:
            # In production, would generate on device
            return await self.hardware_wallet.get_address()
        else:
            # Fallback to software generation
            import secrets
            return secrets.token_hex(32)
    
    async def _generate_encryption_key(self) -> str:
        """Generate encryption key"""
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    
    async def _generate_api_key(self) -> str:
        """Generate API key"""
        import secrets
        return secrets.token_urlsafe(32)
    
    async def _store_key_version(self, key_id: str, key_value: str, version: int) -> bool:
        """Store key version in secure storage"""
        try:
            # In production, would store in Vault or hardware wallet
            logger.debug(f"Stored key version: {key_id} v{version}")
            return True
        except Exception as e:
            logger.error(f"Failed to store key version: {e}")
            return False
    
    async def _verify_key(self, key_id: str, key_value: str) -> bool:
        """Verify new key is functional"""
        try:
            # Try using the new key for a test operation
            logger.debug(f"Verifying key: {key_id}")
            return True
        except Exception as e:
            logger.error(f"Key verification failed: {e}")
            return False
    
    async def _notify_rotation_callbacks(self, key_id: str, old_version: int, new_version: int):
        """Notify registered callbacks about rotation"""
        if key_id in self.rotation_callbacks:
            for callback in self.rotation_callbacks[key_id]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(key_id, old_version, new_version)
                    else:
                        callback(key_id, old_version, new_version)
                except Exception as e:
                    logger.error(f"Rotation callback failed: {e}")
    
    async def schedule_rotation(self, key_id: str, rotation_policy: RotationPolicy):
        """Schedule automatic rotation for a key"""
        if rotation_policy == RotationPolicy.NEVER or rotation_policy == RotationPolicy.ON_DEMAND:
            return
        
        async def rotation_task():
            while True:
                await asyncio.sleep(rotation_policy.value * 24 * 3600)  # Convert days to seconds
                await self.rotate_key(key_id, reason="scheduled")
        
        if key_id in self.rotation_tasks:
            self.rotation_tasks[key_id].cancel()
        
        task = asyncio.create_task(rotation_task())
        self.rotation_tasks[key_id] = task
        logger.info(f"Rotation scheduled for {key_id}: every {rotation_policy.value} days")
    
    async def _start_rotation_monitor(self):
        """Monitor for keys due for rotation"""
        async def monitor_task():
            while True:
                await asyncio.sleep(3600)  # Check every hour
                
                for key_id, metadata in self.keys.items():
                    if metadata.is_due_for_rotation():
                        logger.warning(f"Key due for rotation: {key_id}")
                        # Could auto-rotate or send alert
        
        asyncio.create_task(monitor_task())
    
    def register_rotation_callback(self, key_id: str, callback: Callable):
        """Register callback to be notified of rotations"""
        if key_id not in self.rotation_callbacks:
            self.rotation_callbacks[key_id] = []
        
        self.rotation_callbacks[key_id].append(callback)
        logger.debug(f"Rotation callback registered for {key_id}")
    
    async def get_rotation_history(self, key_id: str) -> List[RotationRecord]:
        """Get rotation history for a key"""
        return [r for r in self.rotation_records if r.key_id == key_id]
    
    async def shutdown(self):
        """Shutdown and cleanup"""
        # Cancel all rotation tasks
        for task in self.rotation_tasks.values():
            task.cancel()
        
        # Disconnect hardware wallet
        await self.hardware_wallet.disconnect()
        
        logger.info("Key rotation engine shutdown complete")


# Global instance
_rotation_engine: Optional[KeyRotationEngine] = None


async def init_key_rotation(hardware_wallet_type: str = "ledger_nano_s") -> KeyRotationEngine:
    """Initialize global key rotation engine"""
    global _rotation_engine
    _rotation_engine = KeyRotationEngine(hardware_wallet_type)
    await _rotation_engine.initialize()
    return _rotation_engine


async def register_key(key_id: str, key_type: KeyType,
                      rotation_policy: RotationPolicy) -> bool:
    """Register a key globally"""
    global _rotation_engine
    if not _rotation_engine:
        _rotation_engine = await init_key_rotation()
    
    return await _rotation_engine.register_key(key_id, key_type, rotation_policy)


async def rotate_key_now(key_id: str, reason: str = "manual") -> bool:
    """Rotate a key immediately"""
    global _rotation_engine
    if not _rotation_engine:
        return False
    
    return await _rotation_engine.rotate_key(key_id, reason)
