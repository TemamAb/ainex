"""
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║                    AINEON ENTERPRISE SECURITY MODULE                          ║
║                  Enhanced .env Encryption & Key Management                    ║
║                                                                                ║
║  Purpose: Secure handling of private keys and sensitive configuration         ║
║  Status: Production-ready encryption system                                   ║
║  Compliance: Enterprise-grade security standards                              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import hashlib
import hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as PBKDF2
from cryptography.hazmat.backends import default_backend
from typing import Dict, Any, Optional
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigEncryption:
    """Secure encryption/decryption for sensitive environment variables"""
    
    def __init__(self, encryption_password: Optional[str] = None):
        """
        Initialize encryption system
        
        Args:
            encryption_password: Master password for encryption (auto-generated if not provided)
        """
        self.encryption_password = encryption_password or os.getenv('ENCRYPTION_PASSWORD')
        if not self.encryption_password:
            self.encryption_password = self._generate_secure_password()
        
        self._cipher_suite = self._initialize_cipher()
        self.sensitive_keys = [
            'PRIVATE_KEY',
            'ENCRYPTION_PASSWORD',
            'ETHERSCAN_API_KEY',
            'ALCHEMY_API_KEY',
            'INFURA_PROJECT_ID',
        ]
        
        logger.info("✓ Encryption system initialized")
    
    def _generate_secure_password(self) -> str:
        """Generate secure random password"""
        import secrets
        password = secrets.token_urlsafe(32)
        logger.warning(f"⚠️  Generated encryption password: {password}")
        logger.warning("⚠️  SAVE THIS IN SECURE LOCATION (password manager, HSM, etc.)")
        return password
    
    def _initialize_cipher(self) -> Fernet:
        """Initialize Fernet cipher with derived key"""
        # Derive key from password using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'aineon_entropy_salt_v1',  # Fixed salt for consistency
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(
            kdf.derive(self.encryption_password.encode())
        )
        return Fernet(key)
    
    def encrypt_config(self, config_dict: Dict[str, Any]) -> Dict[str, str]:
        """Encrypt sensitive values in config dictionary"""
        encrypted = {}
        
        for key, value in config_dict.items():
            if key in self.sensitive_keys and value:
                try:
                    encrypted_value = self._cipher_suite.encrypt(
                        str(value).encode()
                    ).decode()
                    encrypted[key] = f"ENCRYPTED[{encrypted_value}]"
                    logger.info(f"✓ Encrypted {key}")
                except Exception as e:
                    logger.error(f"✗ Failed to encrypt {key}: {e}")
                    encrypted[key] = value
            else:
                encrypted[key] = value
        
        return encrypted
    
    def decrypt_config(self, config_dict: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt sensitive values in config dictionary"""
        decrypted = {}
        
        for key, value in config_dict.items():
            if isinstance(value, str) and value.startswith("ENCRYPTED["):
                try:
                    # Extract encrypted data
                    encrypted_data = value[len("ENCRYPTED["):-1]
                    decrypted_value = self._cipher_suite.decrypt(
                        encrypted_data.encode()
                    ).decode()
                    decrypted[key] = decrypted_value
                    logger.debug(f"✓ Decrypted {key}")
                except Exception as e:
                    logger.error(f"✗ Failed to decrypt {key}: {e}")
                    decrypted[key] = value
            else:
                decrypted[key] = value
        
        return decrypted
    
    def encrypt_private_key(self, private_key: str) -> str:
        """Encrypt private key specifically (highest security)"""
        # Add timestamp for key rotation tracking
        timestamped_key = f"{private_key}|{datetime.utcnow().isoformat()}"
        
        encrypted = self._cipher_suite.encrypt(
            timestamped_key.encode()
        ).decode()
        
        # Add checksum for integrity
        checksum = hashlib.sha256(private_key.encode()).hexdigest()[:8]
        return f"KEY[{encrypted}][{checksum}]"
    
    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt private key with integrity check"""
        try:
            # Extract encrypted data and checksum
            encrypted_data = encrypted_key[len("KEY["):-len("]" + encrypted_key.split("]")[-1])]
            checksum = encrypted_key.split("]")[-1]
            
            # Decrypt
            timestamped = self._cipher_suite.decrypt(
                encrypted_data.encode()
            ).decode()
            
            # Extract private key and timestamp
            private_key, timestamp_str = timestamped.rsplit("|", 1)
            
            # Verify integrity
            calculated_checksum = hashlib.sha256(private_key.encode()).hexdigest()[:8]
            if calculated_checksum != checksum:
                raise ValueError("Checksum mismatch - key may be corrupted")
            
            # Check key age (warn if >90 days)
            key_timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.utcnow() - key_timestamp
            if age > timedelta(days=90):
                logger.warning(f"⚠️  Private key is {age.days} days old - consider rotation")
            
            return private_key
            
        except Exception as e:
            logger.error(f"✗ Failed to decrypt private key: {e}")
            raise
    
    def create_encrypted_env_file(self, env_dict: Dict[str, str], 
                                 output_path: str = ".env.encrypted") -> bool:
        """Create encrypted .env file"""
        try:
            encrypted = self.encrypt_config(env_dict)
            
            with open(output_path, 'w') as f:
                for key, value in encrypted.items():
                    f.write(f"{key}={value}\n")
            
            logger.info(f"✓ Created encrypted config: {output_path}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create encrypted env: {e}")
            return False
    
    def load_encrypted_env_file(self, env_path: str = ".env.encrypted") -> Dict[str, Any]:
        """Load and decrypt .env file"""
        try:
            config = {}
            
            if not os.path.exists(env_path):
                logger.warning(f"⚠️  Config file not found: {env_path}")
                return config
            
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
            
            decrypted = self.decrypt_config(config)
            logger.info(f"✓ Loaded encrypted config from {env_path}")
            return decrypted
            
        except Exception as e:
            logger.error(f"✗ Failed to load encrypted env: {e}")
            return {}


class SecureKeyManager:
    """Manages private key lifecycle (generation, rotation, storage)"""
    
    def __init__(self, encryption: ConfigEncryption):
        self.encryption = encryption
        self.key_audit_log = []
    
    def validate_private_key(self, private_key: str) -> bool:
        """Validate private key format"""
        # Check format: should be 64 hex characters (256 bits)
        if not isinstance(private_key, str):
            return False
        
        # Remove 0x prefix if present
        key = private_key.replace('0x', '').replace('0X', '')
        
        # Check length (64 hex chars = 32 bytes)
        if len(key) != 64:
            return False
        
        # Check all hex characters
        try:
            int(key, 16)
            return True
        except ValueError:
            return False
    
    def get_account_from_key(self, private_key: str):
        """Derive account address from private key"""
        from web3 import Web3
        
        try:
            account = Web3.eth.account.from_key(private_key)
            return account
        except Exception as e:
            logger.error(f"✗ Failed to derive account: {e}")
            return None
    
    def audit_key_access(self, action: str, key_identifier: str, 
                        success: bool, notes: str = ""):
        """Log key access for audit trail"""
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,  # 'encrypt', 'decrypt', 'validate', etc.
            'key_id': key_identifier,
            'success': success,
            'notes': notes,
        }
        
        self.key_audit_log.append(audit_entry)
        
        log_level = logging.INFO if success else logging.WARNING
        logger.log(
            log_level,
            f"Key audit: {action} ({key_identifier}) - {'✓' if success else '✗'}"
        )
    
    def get_audit_log(self) -> list:
        """Get audit log entries"""
        return self.key_audit_log.copy()
    
    def export_audit_log(self, filepath: str = "key_audit_log.json") -> bool:
        """Export audit log to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.key_audit_log, f, indent=2)
            logger.info(f"✓ Exported audit log to {filepath}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to export audit log: {e}")
            return False


class SecureEnvironment:
    """Manages secure environment configuration"""
    
    def __init__(self, env_path: str = ".env.encrypted", 
                 encryption_password: Optional[str] = None):
        """Initialize secure environment"""
        self.encryption = ConfigEncryption(encryption_password)
        self.key_manager = SecureKeyManager(self.encryption)
        self.config = self.encryption.load_encrypted_env_file(env_path)
        
        # Validate critical keys on load
        if 'PRIVATE_KEY' in self.config:
            is_valid = self.key_manager.validate_private_key(
                self.config['PRIVATE_KEY']
            )
            self.key_manager.audit_key_access(
                'load_validate',
                'PRIVATE_KEY',
                is_valid,
                "Loaded private key validation"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        return self.config.get(key, default)
    
    def get_private_key(self) -> str:
        """Get decrypted private key with audit"""
        private_key = self.config.get('PRIVATE_KEY')
        
        if private_key:
            self.key_manager.audit_key_access(
                'retrieve',
                'PRIVATE_KEY',
                True,
                "Retrieved for use"
            )
        
        return private_key
    
    def get_account(self):
        """Get Web3 account from private key"""
        private_key = self.get_private_key()
        if private_key:
            account = self.key_manager.get_account_from_key(private_key)
            self.key_manager.audit_key_access(
                'derive_account',
                'PRIVATE_KEY',
                account is not None
            )
            return account
        return None
    
    def all_keys(self) -> Dict[str, Any]:
        """Get all non-sensitive config keys"""
        return {
            k: v for k, v in self.config.items()
            if k not in ['PRIVATE_KEY', 'ENCRYPTION_PASSWORD']
        }


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def initialize_secure_environment() -> SecureEnvironment:
    """Initialize secure environment from encrypted config"""
    encryption_password = os.getenv('ENCRYPTION_PASSWORD')
    
    if not encryption_password:
        logger.error("❌ ENCRYPTION_PASSWORD not set in environment")
        raise ValueError("ENCRYPTION_PASSWORD environment variable required")
    
    return SecureEnvironment(
        env_path=".env.encrypted",
        encryption_password=encryption_password
    )


def create_encrypted_env_from_plain(plain_env_path: str = ".env",
                                   encrypted_env_path: str = ".env.encrypted",
                                   encryption_password: Optional[str] = None) -> bool:
    """Convert plain .env to encrypted .env.encrypted"""
    
    if not os.path.exists(plain_env_path):
        logger.error(f"❌ Plain env file not found: {plain_env_path}")
        return False
    
    # Read plain env
    config = {}
    with open(plain_env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    # Encrypt and save
    encryption = ConfigEncryption(encryption_password)
    return encryption.create_encrypted_env_file(config, encrypted_env_path)


if __name__ == '__main__':
    # Test encryption system
    logging.basicConfig(level=logging.INFO)
    
    # Create encrypted env from plain text
    print("Converting .env to .env.encrypted...")
    create_encrypted_env_from_plain()
