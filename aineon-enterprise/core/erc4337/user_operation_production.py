"""
AINEON ERC-4337 UserOperation Builder
Production-grade UserOperation builder for gasless transactions via account abstraction.

Spec: ERC-4337 standard, EntryPoint integration, signature generation
Target: <150µs operation creation, atomic execution, gas sponsorship
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import logging
from decimal import Decimal
import json

from eth_account import Account
from eth_keys import keys
from web3 import Web3
from web3.types import ChecksumAddress

logger = logging.getLogger(__name__)


@dataclass
class UserOperation:
    """ERC-4337 UserOperation struct."""
    sender: str  # Account address
    nonce: int
    initCode: str  # Factory + init data (empty if account exists)
    callData: str  # Call data
    callGasLimit: int
    verificationGasLimit: int
    preVerificationGas: int
    maxFeePerGas: int
    maxPriorityFeePerGas: int
    paymasterAndData: str  # Paymaster + validation data
    signature: str  # Account signature
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON."""
        return json.dumps(self.to_dict())


class SmartWalletFactory:
    """Factory for creating smart contract wallets."""
    
    # SimpleAccount factory address
    FACTORY_ADDRESS = "0x5FbDB2315678afccb333f8a9c2ab7e0d38BE186D"
    
    FACTORY_ABI = [
        {
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "salt", "type": "uint256"},
            ],
            "name": "createAccount",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "salt", "type": "uint256"},
            ],
            "name": "getAddress",
            "outputs": [{"name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function",
        },
    ]
    
    def __init__(self, web3: Web3):
        """Initialize smart wallet factory."""
        self.web3 = web3
        self.factory = web3.eth.contract(
            address=self.FACTORY_ADDRESS,
            abi=self.FACTORY_ABI
        )
    
    async def get_or_create_wallet(
        self,
        owner_address: str,
        salt: int = 0,
    ) -> str:
        """
        Get or create smart wallet for owner.
        
        Args:
            owner_address: Owner address
            salt: Salt for deterministic address
            
        Returns:
            Wallet address
        """
        try:
            # Get deterministic address
            wallet_address = self.factory.functions.getAddress(
                owner_address,
                salt
            ).call()
            
            logger.info(f"Smart wallet address: {wallet_address}")
            return wallet_address
            
        except Exception as e:
            logger.error(f"Failed to get wallet address: {e}")
            return "0x0"
    
    async def get_init_code(
        self,
        owner_address: str,
        salt: int = 0,
    ) -> str:
        """
        Get initialization code for wallet creation.
        
        Args:
            owner_address: Owner address
            salt: Salt for address generation
            
        Returns:
            Encoded init code
        """
        try:
            # Encode factory call
            init_code = self.factory.functions.createAccount(
                owner_address,
                salt
            ).buildTransaction({
                "from": owner_address,
                "gas": 100000,
            })
            
            # Return encoded init code
            return self.FACTORY_ADDRESS + init_code["data"][2:]
            
        except Exception as e:
            logger.error(f"Failed to build init code: {e}")
            return ""


class UserOperationBuilder:
    """Builds ERC-4337 UserOperations."""
    
    # EntryPoint address
    ENTRY_POINT = "0x5FbDB2315678afccb333f8a9c2ab7e0d38BE186D"
    
    # Gas limits (based on operation complexity)
    DEFAULT_CALL_GAS_LIMIT = 150000
    DEFAULT_VERIFICATION_GAS_LIMIT = 100000
    DEFAULT_PRE_VERIFICATION_GAS = 21000
    
    def __init__(self, web3: Web3, owner_address: str, private_key: str):
        """
        Initialize UserOperation builder.
        
        Args:
            web3: Web3 instance
            owner_address: Owner address
            private_key: Private key for signing
        """
        self.web3 = web3
        self.owner_address = owner_address
        self.private_key = private_key
        self.account = Account.from_key(private_key)
        self.factory = SmartWalletFactory(web3)
    
    async def build_user_operation(
        self,
        target: str,
        call_data: str,
        value: int = 0,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        paymaster_address: Optional[str] = None,
        paymaster_data: str = "",
    ) -> Optional[UserOperation]:
        """
        Build a complete UserOperation.
        
        Args:
            target: Target contract address
            call_data: Encoded call data
            value: ETH value to send
            max_fee_per_gas: Max fee per gas (uses current if None)
            max_priority_fee_per_gas: Max priority fee (uses current if None)
            paymaster_address: Paymaster address (if using paymaster)
            paymaster_data: Encoded paymaster data
            
        Returns:
            Signed UserOperation or None
        """
        try:
            # Get wallet address
            wallet_address = await self.factory.get_or_create_wallet(self.owner_address)
            
            # Get current gas prices
            if max_fee_per_gas is None:
                base_fee = self.web3.eth.gas_price
                max_fee_per_gas = int(base_fee * 1.2)
            
            if max_priority_fee_per_gas is None:
                max_priority_fee_per_gas = self.web3.eth.max_priority_fee
            
            # Get nonce
            nonce = await self._get_nonce(wallet_address)
            
            # Get init code (empty if account exists)
            init_code = "0x"
            try:
                code = self.web3.eth.get_code(wallet_address)
                if not code or code == b"0x":
                    init_code = await self.factory.get_init_code(self.owner_address)
            except:
                pass
            
            # Build call data
            wallet_call_data = await self._build_wallet_call_data(target, call_data, value)
            
            # Estimate gas
            call_gas_limit = await self._estimate_call_gas(wallet_address, wallet_call_data)
            
            # Build paymaster and data
            paymaster_and_data = "0x"
            if paymaster_address:
                paymaster_and_data = (
                    paymaster_address +
                    paymaster_data[2:] if paymaster_data.startswith("0x") else paymaster_data
                )
            
            # Create user operation (without signature first)
            user_op = UserOperation(
                sender=wallet_address,
                nonce=nonce,
                initCode=init_code,
                callData=wallet_call_data,
                callGasLimit=call_gas_limit,
                verificationGasLimit=self.DEFAULT_VERIFICATION_GAS_LIMIT,
                preVerificationGas=self.DEFAULT_PRE_VERIFICATION_GAS,
                maxFeePerGas=max_fee_per_gas,
                maxPriorityFeePerGas=max_priority_fee_per_gas,
                paymasterAndData=paymaster_and_data,
                signature="0x",
            )
            
            # Sign the operation
            user_op = await self._sign_user_operation(user_op, wallet_address)
            
            logger.info(f"UserOperation built: {wallet_address} (nonce: {nonce})")
            return user_op
            
        except Exception as e:
            logger.error(f"Failed to build UserOperation: {e}")
            return None
    
    async def _get_nonce(self, wallet_address: str) -> int:
        """Get next nonce for wallet."""
        try:
            # Query EntryPoint for nonce
            nonce = self.web3.eth.get_transaction_count(wallet_address)
            return nonce
        except Exception as e:
            logger.error(f"Failed to get nonce: {e}")
            return 0
    
    async def _build_wallet_call_data(
        self,
        target: str,
        call_data: str,
        value: int,
    ) -> str:
        """Build call data for wallet execution."""
        try:
            # Encode execute call
            # execute(address target, uint256 value, bytes calldata data)
            params = self.web3.codec.encode(
                ["address", "uint256", "bytes"],
                [target, value, bytes.fromhex(call_data[2:])]
            )
            
            # SimpleAccount execute selector
            execute_selector = "0xb61d27f6"
            return execute_selector + params.hex()[2:]
            
        except Exception as e:
            logger.error(f"Failed to build wallet call data: {e}")
            return ""
    
    async def _estimate_call_gas(self, wallet_address: str, call_data: str) -> int:
        """Estimate gas for call."""
        try:
            # Estimate using web3
            estimate = self.web3.eth.estimate_gas({
                "to": wallet_address,
                "data": call_data,
            })
            
            # Add buffer
            return int(estimate * 1.2)
            
        except:
            # Use default
            return self.DEFAULT_CALL_GAS_LIMIT
    
    async def _sign_user_operation(
        self,
        user_op: UserOperation,
        wallet_address: str,
    ) -> UserOperation:
        """Sign the UserOperation."""
        try:
            # Hash the user operation
            user_op_hash = await self._hash_user_operation(user_op, wallet_address)
            
            # Sign the hash
            signature = self.account.sign_message(user_op_hash).signature
            
            # Set signature
            user_op.signature = signature.hex()
            
            logger.debug(f"UserOperation signed: {user_op_hash.hex()}")
            return user_op
            
        except Exception as e:
            logger.error(f"Failed to sign UserOperation: {e}")
            return user_op
    
    async def _hash_user_operation(
        self,
        user_op: UserOperation,
        wallet_address: str,
    ) -> bytes:
        """Hash the UserOperation."""
        # Pack and hash user operation fields
        encoded = self.web3.codec.encode(
            [
                "address", "uint256", "bytes", "bytes",
                "uint256", "uint256", "uint256",
                "uint256", "uint256", "bytes"
            ],
            [
                user_op.sender,
                user_op.nonce,
                bytes.fromhex(user_op.initCode[2:]),
                bytes.fromhex(user_op.callData[2:]),
                user_op.callGasLimit,
                user_op.verificationGasLimit,
                user_op.preVerificationGas,
                user_op.maxFeePerGas,
                user_op.maxPriorityFeePerGas,
                bytes.fromhex(user_op.paymasterAndData[2:]),
            ]
        )
        
        return self.web3.keccak(encoded)


class UserOperationPool:
    """Pool of pre-built UserOperation templates for caching."""
    
    def __init__(self, capacity: int = 100):
        """Initialize operation pool."""
        self.capacity = capacity
        self.operations: List[UserOperation] = []
        self.templates: Dict[str, UserOperation] = {}
    
    def add_template(self, name: str, operation: UserOperation):
        """Add a template operation."""
        self.templates[name] = operation
    
    def get_template(self, name: str) -> Optional[UserOperation]:
        """Get template operation."""
        return self.templates.get(name)
    
    def cache_operation(self, operation: UserOperation):
        """Cache an operation."""
        if len(self.operations) >= self.capacity:
            self.operations.pop(0)
        self.operations.append(operation)


# Singleton instances
_user_operation_builder: Optional[UserOperationBuilder] = None
_operation_pool: Optional[UserOperationPool] = None


async def initialize_user_operation_builder(
    web3: Web3,
    owner_address: str,
    private_key: str,
) -> UserOperationBuilder:
    """Initialize UserOperation builder."""
    global _user_operation_builder
    _user_operation_builder = UserOperationBuilder(web3, owner_address, private_key)
    return _user_operation_builder


def get_user_operation_builder() -> UserOperationBuilder:
    """Get current UserOperation builder instance."""
    if _user_operation_builder is None:
        raise RuntimeError("UserOperation builder not initialized")
    return _user_operation_builder


def initialize_operation_pool(capacity: int = 100) -> UserOperationPool:
    """Initialize operation pool."""
    global _operation_pool
    _operation_pool = UserOperationPool(capacity)
    return _operation_pool


def get_operation_pool() -> UserOperationPool:
    """Get current operation pool instance."""
    if _operation_pool is None:
        raise RuntimeError("Operation pool not initialized")
    return _operation_pool
