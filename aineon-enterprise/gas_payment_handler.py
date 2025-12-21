#!/usr/bin/env python3
"""
AINEON GAS PAYMENT HANDLER WITH PAYMASTER
ERC-4337 paymaster integration for gasless transactions
Enables gasless flash loan operations and arbitrage trades
"""

import asyncio
import json
import logging
import time
import secrets
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal
import aiohttp

from web3 import Web3
from eth_account import Account
from eth_typing import HexStr
from hexbytes import HexBytes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class GaslessTransactionRequest:
    """Gasless transaction request structure"""
    to: str
    value: int = 0
    data: bytes = b''
    gas_limit: int = 21000
    max_fee_per_gas: int = 0  # 0 for paymaster
    max_priority_fee_per_gas: int = 0  # 0 for paymaster
    chain_id: int = 1

@dataclass
class PaymasterResponse:
    """Response from paymaster service"""
    success: bool
    paymaster_and_data: Optional[HexBytes] = None
    pre_verification_gas: Optional[int] = None
    verification_gas_limit: Optional[int] = None
    call_gas_limit: Optional[int] = None
    error: Optional[str] = None

@dataclass
class GasOptimizationResult:
    """Gas optimization analysis result"""
    estimated_gas: int
    gas_price_wei: int
    total_cost_wei: int
    cost_usd: float
    optimization_level: str
    recommendations: List[str]

class GasPaymentHandler:
    """
    GAS PAYMENT HANDLER WITH PAYMASTER
    ERC-4337 paymaster integration for gasless transactions
    Supports multiple paymaster providers and gas optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Web3 connection
        self.rpc_url = config.get('rpc_url', 'https://eth-mainnet.g.alchemy.com/v2/')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Paymaster configuration
        self.paymaster_configs = {
            'erc4337': {
                'address': config.get('paymaster_address'),
                'url': config.get('paymaster_url'),
                'api_key': config.get('paymaster_api_key'),
                'enabled': config.get('paymaster_enabled', False)
            },
            'alchemy': {
                'url': 'https://alchemy.com',
                'api_key': config.get('alchemy_api_key'),
                'enabled': False
            },
            'pillar': {
                'url': 'https://pillarxyz.xyz',
                'api_key': config.get('pillar_api_key'),
                'enabled': False
            },
            'biconomy': {
                'url': 'https://api.biconomy.io',
                'api_key': config.get('biconomy_api_key'),
                'enabled': False
            }
        }
        
        # Gas optimization settings
        self.gas_optimization = {
            'max_gas_price': config.get('max_gas_price', 100_000_000_000),  # 100 gwei
            'min_gas_price': config.get('min_gas_price', 1_000_000_000),    # 1 gwei
            'gas_price_multiplier': config.get('gas_price_multiplier', 1.2),
            'target_confirmation_time': config.get('target_confirmation_time', 30),  # seconds
            'mev_protection': config.get('mev_protection', True)
        }
        
        # Tracking
        self.gas_statistics = {
            'total_transactions': 0,
            'gasless_transactions': 0,
            'total_gas_saved_wei': 0,
            'average_gas_price': 0,
            'successful_paymaster_calls': 0,
            'failed_paymaster_calls': 0
        }
        
        # ERC-4337 constants
        self.ERC4337_VALIDATION_MAGIC = 0x21  # Magic number for ERC-4337 validation
        self.ERC4337_VALIDATION_FAILED = 0
        
        logger.info("GasPaymentHandler initialized with ERC-4337 paymaster support")
    
    async def create_gasless_user_operation(self, tx_request: GaslessTransactionRequest) -> Dict[str, Any]:
        """
        Create ERC-4337 user operation with paymaster integration
        Returns user operation that can be submitted to paymaster
        """
        try:
            # Generate random values for user operation
            nonce = self._generate_nonce()
            
            # Estimate gas limits
            gas_limits = await self._estimate_gas_limits(tx_request)
            
            # Create base user operation
            user_op = {
                'sender': tx_request.to,  # Will be updated with actual sender
                'nonce': nonce,
                'initCode': b'',
                'callData': tx_request.data.hex() if tx_request.data else '0x',
                'callGasLimit': gas_limits['call_gas_limit'],
                'verificationGasLimit': gas_limits['verification_gas_limit'],
                'preVerificationGas': gas_limits['pre_verification_gas'],
                'maxFeePerGas': tx_request.max_fee_per_gas or self._get_optimal_gas_price(),
                'maxPriorityFeePerGas': tx_request.max_priority_fee_per_gas or self._get_optimal_gas_price() // 2,
                'paymasterAndData': b'',
                'signature': b''
            }
            
            # Get paymaster sponsorship if enabled
            if self.paymaster_configs['erc4337']['enabled']:
                paymaster_response = await self._get_paymaster_sponsorship(user_op)
                
                if paymaster_response.success and paymaster_response.paymaster_and_data:
                    user_op['paymasterAndData'] = paymaster_response.paymaster_and_data
                    user_op['preVerificationGas'] = paymaster_response.pre_verification_gas
                    user_op['verificationGasLimit'] = paymaster_response.verification_gas_limit
                    user_op['callGasLimit'] = paymaster_response.call_gas_limit
                    
                    logger.info("Paymaster sponsorship obtained - transaction will be gasless")
                else:
                    logger.warning(f"Paymaster sponsorship failed: {paymaster_response.error}")
            
            # Calculate estimated costs
            cost_analysis = await self._analyze_gas_costs(user_op)
            
            return {
                'user_operation': user_op,
                'cost_analysis': cost_analysis,
                'is_gasless': bool(user_op.get('paymasterAndData')),
                'estimated_cost_usd': cost_analysis['total_cost_usd']
            }
            
        except Exception as e:
            logger.error(f"Failed to create gasless user operation: {e}")
            raise
    
    def _generate_nonce(self) -> int:
        """Generate random nonce for user operation"""
        return secrets.randbelow(2**64)
    
    async def _estimate_gas_limits(self, tx_request: GaslessTransactionRequest) -> Dict[str, int]:
        """Estimate gas limits for user operation"""
        # Base gas costs for different operations
        base_costs = {
            'transfer': 21000,
            'erc20_transfer': 65000,
            'contract_interaction': 100000,
            'flash_loan': 300000,
            'arbitrage': 500000
        }
        
        # Determine operation type from data
        if not tx_request.data:
            operation_type = 'transfer'
        elif len(tx_request.data) < 100:
            operation_type = 'erc20_transfer'
        elif len(tx_request.data) < 500:
            operation_type = 'contract_interaction'
        elif 'flash' in tx_request.data.hex().lower():
            operation_type = 'flash_loan'
        else:
            operation_type = 'arbitrage'
        
        base_gas = base_costs.get(operation_type, tx_request.gas_limit)
        
        # Add overhead for ERC-4337
        verification_overhead = 50000  # Account creation and validation
        pre_verification_overhead = 21000  # Pre-verification gas
        
        return {
            'call_gas_limit': int(base_gas * 1.1),  # 10% buffer
            'verification_gas_limit': verification_overhead,
            'pre_verification_gas': pre_verification_overhead
        }
    
    def _get_optimal_gas_price(self) -> int:
        """Get optimal gas price based on network conditions"""
        try:
            # Get current gas price
            current_gas_price = self.w3.eth.gas_price
            
            # Apply optimization multiplier
            optimal_price = int(current_gas_price * self.gas_optimization['gas_price_multiplier'])
            
            # Apply bounds
            optimal_price = max(
                optimal_price,
                self.gas_optimization['min_gas_price']
            )
            optimal_price = min(
                optimal_price,
                self.gas_optimization['max_gas_price']
            )
            
            return optimal_price
            
        except Exception as e:
            logger.warning(f"Failed to get optimal gas price: {e}")
            return 25_000_000_000  # Default 25 gwei
    
    async def _get_paymaster_sponsorship(self, user_op: Dict[str, Any]) -> PaymasterResponse:
        """Get paymaster sponsorship for user operation"""
        try:
            if not self.paymaster_configs['erc4337']['enabled']:
                return PaymasterResponse(success=False, error="Paymaster not enabled")
            
            # Prepare paymaster request
            paymaster_request = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'pm_sponsorUserOperation',
                'params': [
                    user_op,
                    {
                        'entryPoint': '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789'  # Standard entry point
                    }
                ]
            }
            
            # Add API key if available
            if self.paymaster_configs['erc4337']['api_key']:
                paymaster_request['params'].append({
                    'apiKey': self.paymaster_configs['erc4337']['api_key']
                })
            
            # Make request to paymaster
            async with aiohttp.ClientSession() as session:
                url = self.paymaster_configs['erc4337']['url']
                if not url:
                    return PaymasterResponse(success=False, error="No paymaster URL configured")
                
                async with session.post(url, json=paymaster_request) as response:
                    result = await response.json()
                    
                    if result.get('result'):
                        paymaster_data = result['result']
                        return PaymasterResponse(
                            success=True,
                            paymaster_and_data=HexBytes(paymaster_data['paymasterAndData']),
                            pre_verification_gas=paymaster_data.get('preVerificationGas', 21000),
                            verification_gas_limit=paymaster_data.get('verificationGasLimit', 500000),
                            call_gas_limit=paymaster_data.get('callGasLimit', 300000)
                        )
                    else:
                        error = result.get('error', {}).get('message', 'Unknown paymaster error')
                        self.gas_statistics['failed_paymaster_calls'] += 1
                        return PaymasterResponse(success=False, error=error)
                        
        except Exception as e:
            logger.error(f"Paymaster sponsorship failed: {e}")
            self.gas_statistics['failed_paymaster_calls'] += 1
            return PaymasterResponse(success=False, error=str(e))
    
    async def _analyze_gas_costs(self, user_op: Dict[str, Any]) -> GasOptimizationResult:
        """Analyze gas costs and provide optimization recommendations"""
        try:
            # Calculate gas costs
            total_gas = (
                user_op.get('preVerificationGas', 21000) +
                user_op.get('verificationGasLimit', 500000) +
                user_op.get('callGasLimit', 300000)
            )
            
            gas_price = user_op.get('maxFeePerGas', self._get_optimal_gas_price())
            total_cost_wei = total_gas * gas_price
            
            # Convert to USD (approximate ETH price)
            eth_price_usd = 2000.0  # This should be fetched from price oracle
            total_cost_usd = (total_cost_wei / 1e18) * eth_price_usd
            
            # Determine optimization level
            if total_cost_usd < 1:
                optimization_level = 'excellent'
            elif total_cost_usd < 5:
                optimization_level = 'good'
            elif total_cost_usd < 20:
                optimization_level = 'fair'
            else:
                optimization_level = 'poor'
            
            # Generate recommendations
            recommendations = []
            
            if total_cost_usd > 10:
                recommendations.append("Consider using paymaster for gasless transaction")
            
            if gas_price > 50_000_000_000:  # 50 gwei
                recommendations.append("Gas price is high, consider waiting for lower network congestion")
            
            if user_op.get('paymasterAndData'):
                recommendations.append("✅ Using paymaster - transaction will be gasless")
            
            if total_gas > 500000:
                recommendations.append("High gas usage detected, consider optimizing contract calls")
            
            return GasOptimizationResult(
                estimated_gas=total_gas,
                gas_price_wei=gas_price,
                total_cost_wei=total_cost_wei,
                cost_usd=total_cost_usd,
                optimization_level=optimization_level,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Gas cost analysis failed: {e}")
            return GasOptimizationResult(
                estimated_gas=0,
                gas_price_wei=0,
                total_cost_wei=0,
                cost_usd=0,
                optimization_level='unknown',
                recommendations=[f"Analysis failed: {str(e)}"]
            )
    
    async def execute_gasless_transaction(self, user_op: Dict[str, Any], private_key: str) -> Dict[str, Any]:
        """
        Execute gasless transaction using ERC-4337 flow
        Signs and submits user operation via bundler
        """
        try:
            # Create account from private key
            account = Account.from_key(private_key)
            user_op['sender'] = account.address
            
            # Sign user operation
            signed_user_op = self._sign_user_operation(user_op, account)
            
            # Submit to bundler
            submission_result = await self._submit_to_bundler(signed_user_op)
            
            if submission_result['success']:
                self.gas_statistics['gasless_transactions'] += 1
                logger.info(f"Gasless transaction submitted: {submission_result['user_operation_hash']}")
            else:
                logger.error(f"Gasless transaction failed: {submission_result['error']}")
            
            return submission_result
            
        except Exception as e:
            logger.error(f"Gasless transaction execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sign_user_operation(self, user_op: Dict[str, Any], account: Account) -> Dict[str, Any]:
        """Sign user operation for ERC-4337"""
        try:
            # Create signing data (simplified)
            # In production, would follow ERC-4337 signing specification
            signing_data = {
                'sender': user_op['sender'],
                'nonce': user_op['nonce'],
                'initCode': user_op['initCode'],
                'callData': user_op['callData'],
                'callGasLimit': user_op['callGasLimit'],
                'verificationGasLimit': user_op['verificationGasLimit'],
                'preVerificationGas': user_op['preVerificationGas'],
                'maxFeePerGas': user_op['maxFeePerGas'],
                'maxPriorityFeePerGas': user_op['maxPriorityFeePerGas'],
                'paymasterAndData': user_op['paymasterAndData']
            }
            
            # Convert to bytes for signing
            import rlp
            from eth_utils import encode_hex
            
            # Simplified signing - in production use proper ERC-4337 signing
            sign_data = json.dumps(signing_data, sort_keys=True).encode()
            signature = account.sign_message(sign_data)
            
            user_op['signature'] = signature.signature.hex()
            
            return user_op
            
        except Exception as e:
            logger.error(f"User operation signing failed: {e}")
            raise
    
    async def _submit_to_bundler(self, signed_user_op: Dict[str, Any]) -> Dict[str, Any]:
        """Submit signed user operation to bundler"""
        try:
            # Prepare bundler request
            bundler_request = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'eth_sendUserOperation',
                'params': [
                    signed_user_op,
                    '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789'  # Entry point
                ]
            }
            
            # Submit to bundler (using same RPC for now)
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_url, json=bundler_request) as response:
                    result = await response.json()
                    
                    if result.get('result'):
                        return {
                            'success': True,
                            'user_operation_hash': result['result'],
                            'is_gasless': bool(signed_user_op.get('paymasterAndData'))
                        }
                    else:
                        error = result.get('error', {}).get('message', 'Bundler submission failed')
                        return {
                            'success': False,
                            'error': error
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_gasless_transaction_status(self, user_operation_hash: str) -> Dict[str, Any]:
        """Check status of gasless transaction"""
        try:
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(user_operation_hash)
            
            if receipt:
                return {
                    'confirmed': True,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'status': 'success' if receipt['status'] == 1 else 'failed',
                    'transaction_hash': user_operation_hash
                }
            else:
                # Check if in mempool
                transaction = self.w3.eth.get_transaction(user_operation_hash)
                if transaction:
                    return {
                        'confirmed': False,
                        'in_mempool': True,
                        'status': 'pending'
                    }
                else:
                    return {
                        'confirmed': False,
                        'in_mempool': False,
                        'status': 'not_found'
                    }
                    
        except Exception as e:
            return {
                'confirmed': False,
                'error': str(e)
            }
    
    async def optimize_gas_for_arbitrage(self, strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize gas usage for arbitrage strategies"""
        try:
            # Analyze strategy gas requirements
            estimated_gas = strategy_data.get('estimated_gas', 500000)
            expected_profit_usd = strategy_data.get('expected_profit_usd', 0)
            
            # Calculate gas cost percentage
            current_gas_price = self._get_optimal_gas_price()
            gas_cost_wei = estimated_gas * current_gas_price
            gas_cost_usd = (gas_cost_wei / 1e18) * 2000.0  # Approximate ETH price
            
            gas_cost_percentage = (gas_cost_usd / expected_profit_usd * 100) if expected_profit_usd > 0 else 0
            
            # Determine if gasless is beneficial
            gasless_recommended = gas_cost_percentage > 5  # More than 5% of profit
            
            # Optimization recommendations
            recommendations = []
            
            if gas_cost_percentage > 10:
                recommendations.append("HIGH gas cost - strongly recommend gasless transaction")
            elif gas_cost_percentage > 5:
                recommendations.append("Moderate gas cost - gasless recommended")
            elif gas_cost_percentage < 2:
                recommendations.append("Low gas cost - regular transaction acceptable")
            
            if estimated_gas > 800000:
                recommendations.append("Consider optimizing contract calls to reduce gas usage")
            
            if self.paymaster_configs['erc4337']['enabled']:
                recommendations.append("✅ Paymaster available for gasless execution")
            
            return {
                'estimated_gas': estimated_gas,
                'gas_cost_usd': gas_cost_usd,
                'gas_cost_percentage': gas_cost_percentage,
                'gasless_recommended': gasless_recommended,
                'optimization_level': 'excellent' if gas_cost_percentage < 2 else 'good' if gas_cost_percentage < 5 else 'poor',
                'recommendations': recommendations,
                'paymaster_enabled': self.paymaster_configs['erc4337']['enabled']
            }
            
        except Exception as e:
            logger.error(f"Gas optimization analysis failed: {e}")
            return {
                'error': str(e),
                'gasless_recommended': True  # Default to gasless on error
            }
    
    def get_gas_statistics(self) -> Dict[str, Any]:
        """Get comprehensive gas usage statistics"""
        try:
            total_txs = self.gas_statistics['total_transactions']
            gasless_txs = self.gas_statistics['gasless_transactions']
            gasless_percentage = (gasless_txs / total_txs * 100) if total_txs > 0 else 0
            
            return {
                'total_transactions': total_txs,
                'gasless_transactions': gasless_txs,
                'gasless_percentage': gasless_percentage,
                'total_gas_saved_wei': self.gas_statistics['total_gas_saved_wei'],
                'total_gas_saved_usd': (self.gas_statistics['total_gas_saved_wei'] / 1e18) * 2000.0,
                'paymaster_success_rate': (
                    self.gas_statistics['successful_paymaster_calls'] / 
                    (self.gas_statistics['successful_paymaster_calls'] + self.gas_statistics['failed_paymaster_calls']) * 100
                    if (self.gas_statistics['successful_paymaster_calls'] + self.gas_statistics['failed_paymaster_calls']) > 0 else 0
                ),
                'average_gas_price_gwei': self.gas_statistics['average_gas_price'] / 1e9 if self.gas_statistics['average_gas_price'] > 0 else 0,
                'paymaster_configured': self.paymaster_configs['erc4337']['enabled']
            }
            
        except Exception as e:
            logger.error(f"Failed to get gas statistics: {e}")
            return {'error': str(e)}
    
    async def estimate_regular_vs_gasless_cost(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare costs between regular and gasless transactions"""
        try:
            # Estimate regular transaction cost
            gas_limit = tx_data.get('gas_limit', 300000)
            gas_price = self._get_optimal_gas_price()
            regular_cost_wei = gas_limit * gas_price
            regular_cost_usd = (regular_cost_wei / 1e18) * 2000.0
            
            # Estimate gasless transaction cost (only pre-verification gas)
            gasless_cost_wei = 21000 * gas_price  # Only pre-verification gas
            gasless_cost_usd = (gasless_cost_wei / 1e18) * 2000.0
            
            # Calculate savings
            savings_wei = regular_cost_wei - gasless_cost_wei
            savings_percentage = (savings_wei / regular_cost_wei * 100) if regular_cost_wei > 0 else 0
            
            return {
                'regular_transaction': {
                    'cost_wei': regular_cost_wei,
                    'cost_usd': regular_cost_usd,
                    'gas_limit': gas_limit,
                    'gas_price_wei': gas_price
                },
                'gasless_transaction': {
                    'cost_wei': gasless_cost_wei,
                    'cost_usd': gasless_cost_usd,
                    'gas_limit': 21000,  # Only pre-verification
                    'gas_price_wei': gas_price
                },
                'savings': {
                    'wei': savings_wei,
                    'usd': (savings_wei / 1e18) * 2000.0,
                    'percentage': savings_percentage
                },
                'recommendation': 'gasless' if savings_percentage > 20 else 'regular'
            }
            
        except Exception as e:
            logger.error(f"Cost comparison failed: {e}")
            return {'error': str(e)}

# Configuration for gas payment handler
GAS_HANDLER_CONFIG = {
    'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/',
    'paymaster_enabled': True,
    'paymaster_address': '0x1234567890123456789012345678901234567890',  # Example address
    'paymaster_url': 'https://api.pimlico.io/v1/rpc/your-api-key',  # Example Pimlico
    'paymaster_api_key': 'your_paymaster_api_key',
    'max_gas_price': 100_000_000_000,
    'min_gas_price': 1_000_000_000,
    'gas_price_multiplier': 1.2,
    'target_confirmation_time': 30,
    'mev_protection': True
}

async def main():
    """Test gas payment handler with paymaster"""
    print("⛽ AINEON GAS PAYMENT HANDLER WITH PAYMASTER - GASLESS TRANSACTIONS")
    print("=" * 80)
    
    # Initialize gas handler
    gas_handler = GasPaymentHandler(GAS_HANDLER_CONFIG)
    
    # Test gas optimization
    print("\n🔧 GAS OPTIMIZATION ANALYSIS")
    test_strategy = {
        'estimated_gas': 400000,
        'expected_profit_usd': 150.0,
        'operation_type': 'flash_loan_arbitrage'
    }
    
    optimization = await gas_handler.optimize_gas_for_arbitrage(test_strategy)
    
    print(f"Estimated Gas: {optimization['estimated_gas']:,}")
    print(f"Gas Cost: ${optimization['gas_cost_usd']:.2f}")
    print(f"Gas Cost % of Profit: {optimization['gas_cost_percentage']:.1f}%")
    print(f"Gasless Recommended: {optimization['gasless_recommended']}")
    print(f"Optimization Level: {optimization['optimization_level']}")
    
    print("\nRecommendations:")
    for rec in optimization['recommendations']:
        print(f"  • {rec}")
    
    # Test cost comparison
    print("\n💰 REGULAR VS GASLESS COST COMPARISON")
    tx_data = {
        'gas_limit': 400000,
        'to': '0x742d35Cc6434C0532925a3b8D4c9c96BfD2d8c5f',
        'data': '0x1234567890abcdef'
    }
    
    cost_comparison = await gas_handler.estimate_regular_vs_gasless_cost(tx_data)
    
    print(f"Regular Transaction: ${cost_comparison['regular_transaction']['cost_usd']:.2f}")
    print(f"Gasless Transaction: ${cost_comparison['gasless_transaction']['cost_usd']:.2f}")
    print(f"Savings: ${cost_comparison['savings']['usd']:.2f} ({cost_comparison['savings']['percentage']:.1f}%)")
    print(f"Recommendation: {cost_comparison['recommendation']}")
    
    # Test user operation creation
    print("\n📝 CREATING GASLESS USER OPERATION")
    gasless_request = GaslessTransactionRequest(
        to='0x742d35Cc6434C0532925a3b8D4c9c96BfD2d8c5f',
        value=0,
        data=b'\x12\x34\x56\x78\x90\xab\xcd\xef',
        gas_limit=300000
    )
    
    user_op_result = await gas_handler.create_gasless_user_operation(gasless_request)
    
    print(f"Is Gasless: {user_op_result['is_gasless']}")
    print(f"Estimated Cost: ${user_op_result['estimated_cost_usd']:.2f}")
    
    # Show gas statistics
    print("\n📊 GAS STATISTICS")
    stats = gas_handler.get_gas_statistics()
    
    print(f"Total Transactions: {stats.get('total_transactions', 0)}")
    print(f"Gasless Transactions: {stats.get('gasless_transactions', 0)}")
    print(f"Gasless Percentage: {stats.get('gasless_percentage', 0):.1f}%")
    print(f"Paymaster Configured: {stats.get('paymaster_configured', False)}")
    
    print("\n✅ GAS PAYMENT HANDLER TEST COMPLETE")
    print("🚀 Ready for gasless flash loan arbitrage operations!")

if __name__ == "__main__":
    asyncio.run(main())