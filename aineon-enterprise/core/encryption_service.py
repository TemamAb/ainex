"""
Encryption Service - AES-256 & TLS 1.3 Support
Field-level encryption for sensitive data at rest and in transit
"""

import os
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import json
from base64 import b64encode, b64decode

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import ssl

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    FERNET = "fernet"  # Symmetric, high-level
    RSA_OAEP = "rsa_oaep"  # Asymmetric


@dataclass
class EncryptedData:
    """Encrypted data container"""
    ciphertext: bytes
    algorithm: str
    iv: Optional[bytes] = None  # Initialization vector
    tag: Optional[bytes] = None  # Authentication tag for GCM
    salt: Optional[bytes] = None
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'ciphertext': b64encode(self.ciphertext).decode(),
            'algorithm': self.algorithm,
            'iv': b64encode(self.iv).decode() if self.iv else None,
            'tag': b64encode(self.tag).decode() if self.tag else None,
            'salt': b64encode(self.salt).decode() if self.salt else None,
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'EncryptedData':
        """Deserialize from dictionary"""
        return EncryptedData(
            ciphertext=b64decode(data['ciphertext']),
            algorithm=data['algorithm'],
            iv=b64decode(data['iv']) if data.get('iv') else None,
            tag=b64decode(data['tag']) if data.get('tag') else None,
            salt=b64decode(data['salt']) if data.get('salt') else None,
        )


class EncryptionService:
    """Provides AES-256 encryption for sensitive data"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.backend = default_backend()
        
        # Get or generate master key
        if master_key:
            self.master_key = master_key
        else:
            key_env = os.getenv('ENCRYPTION_MASTER_KEY')
            if key_env:
                self.master_key = b64decode(key_env)
            else:
                self.master_key = Fernet.generate_key()
                logger.warning("Generated random master key - use ENCRYPTION_MASTER_KEY env var in production")
        
        self.fernet = Fernet(self.master_key)
    
    def encrypt_aes_gcm(self, plaintext: bytes, associated_data: Optional[bytes] = None) -> EncryptedData:
        """
        Encrypt using AES-256-GCM (authenticated encryption)
        
        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (not encrypted)
        
        Returns:
            EncryptedData with ciphertext, IV, and authentication tag
        """
        # Generate random 96-bit IV (12 bytes)
        iv = os.urandom(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.GCM(iv),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        # Encrypt and get authentication tag
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=EncryptionAlgorithm.AES_256_GCM.value,
            iv=iv,
            tag=encryptor.tag
        )
    
    def decrypt_aes_gcm(self, encrypted: EncryptedData, 
                       associated_data: Optional[bytes] = None) -> bytes:
        """Decrypt AES-256-GCM encrypted data"""
        if encrypted.algorithm != EncryptionAlgorithm.AES_256_GCM.value:
            raise ValueError(f"Invalid algorithm: {encrypted.algorithm}")
        
        cipher = Cipher(
            algorithms.AES(self.master_key),
            modes.GCM(encrypted.iv, encrypted.tag),
            backend=self.backend
        )
        
        decryptor = cipher.decryptor()
        
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)
        
        try:
            plaintext = decryptor.update(encrypted.ciphertext) + decryptor.finalize()
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed (authentication tag mismatch): {e}")
            raise
    
    def encrypt_fernet(self, plaintext: bytes) -> EncryptedData:
        """Encrypt using Fernet (simplified, suitable for keys)"""
        ciphertext = self.fernet.encrypt(plaintext)
        return EncryptedData(
            ciphertext=ciphertext,
            algorithm=EncryptionAlgorithm.FERNET.value
        )
    
    def decrypt_fernet(self, encrypted: EncryptedData) -> bytes:
        """Decrypt Fernet encrypted data"""
        if encrypted.algorithm != EncryptionAlgorithm.FERNET.value:
            raise ValueError(f"Invalid algorithm: {encrypted.algorithm}")
        
        try:
            plaintext = self.fernet.decrypt(encrypted.ciphertext)
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_json(self, data: Dict, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM) -> str:
        """Encrypt JSON data"""
        json_bytes = json.dumps(data).encode('utf-8')
        
        if algorithm == EncryptionAlgorithm.AES_256_GCM:
            encrypted = self.encrypt_aes_gcm(json_bytes)
        elif algorithm == EncryptionAlgorithm.FERNET:
            encrypted = self.encrypt_fernet(json_bytes)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return json.dumps(encrypted.to_dict())
    
    def decrypt_json(self, encrypted_str: str) -> Dict:
        """Decrypt JSON data"""
        encrypted_dict = json.loads(encrypted_str)
        encrypted = EncryptedData.from_dict(encrypted_dict)
        
        if encrypted.algorithm == EncryptionAlgorithm.AES_256_GCM.value:
            json_bytes = self.decrypt_aes_gcm(encrypted)
        elif encrypted.algorithm == EncryptionAlgorithm.FERNET.value:
            json_bytes = self.decrypt_fernet(encrypted)
        else:
            raise ValueError(f"Unknown algorithm: {encrypted.algorithm}")
        
        return json.loads(json_bytes.decode('utf-8'))


class TLSConfig:
    """TLS 1.3 configuration"""
    
    def __init__(self, cert_path: str, key_path: str):
        self.cert_path = cert_path
        self.key_path = key_path
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create TLS 1.3 SSL context"""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Load certificate and key
        context.load_cert_chain(self.cert_path, self.key_path)
        
        # Set strong ciphers
        context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256')
        
        # Enable additional security options
        context.options |= ssl.OP_NO_COMPRESSION
        
        logger.info("TLS 1.3 context created")
        return context


class FieldEncryption:
    """Field-level encryption for specific JSON fields"""
    
    def __init__(self, encryption_service: EncryptionService):
        self.encryption_service = encryption_service
        self.encrypted_fields = {
            'private_key', 'api_key', 'password', 'mnemonic',
            'secret', 'token', 'credential'
        }
    
    def encrypt_fields(self, data: Dict, fields: Optional[set] = None) -> Dict:
        """Encrypt specified fields in dictionary"""
        fields_to_encrypt = fields or self.encrypted_fields
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                value = encrypted_data[field]
                if isinstance(value, str):
                    value_bytes = value.encode('utf-8')
                else:
                    value_bytes = json.dumps(value).encode('utf-8')
                
                encrypted = self.encryption_service.encrypt_aes_gcm(value_bytes)
                encrypted_data[f"_{field}_encrypted"] = encrypted.to_dict()
                encrypted_data.pop(field, None)
        
        return encrypted_data
    
    def decrypt_fields(self, data: Dict, fields: Optional[set] = None) -> Dict:
        """Decrypt specified fields in dictionary"""
        decrypted_data = data.copy()
        fields_to_decrypt = fields or self.encrypted_fields
        
        for field in fields_to_decrypt:
            encrypted_key = f"_{field}_encrypted"
            
            if encrypted_key in decrypted_data:
                encrypted_dict = decrypted_data[encrypted_key]
                encrypted = EncryptedData.from_dict(encrypted_dict)
                
                value_bytes = self.encryption_service.decrypt_aes_gcm(encrypted)
                
                try:
                    decrypted_data[field] = json.loads(value_bytes.decode('utf-8'))
                except json.JSONDecodeError:
                    decrypted_data[field] = value_bytes.decode('utf-8')
                
                decrypted_data.pop(encrypted_key, None)
        
        return decrypted_data


# Global instance
_encryption_service: Optional[EncryptionService] = None


def init_encryption(master_key: Optional[bytes] = None) -> EncryptionService:
    """Initialize global encryption service"""
    global _encryption_service
    _encryption_service = EncryptionService(master_key)
    return _encryption_service


def get_encryption_service() -> EncryptionService:
    """Get global encryption service"""
    global _encryption_service
    if not _encryption_service:
        _encryption_service = EncryptionService()
    return _encryption_service
