"""
AINEON Enterprise Configuration Management
Centralized, validated configuration with environment-specific settings
"""

import os
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environments"""
    TESTNET = "testnet"
    MAINNET = "mainnet"


class RiskTier(Enum):
    """Risk management tiers"""
    CONSERVATIVE = "conservative"      # Small position sizes, tight limits
    BALANCED = "balanced"              # Medium position sizes
    AGGRESSIVE = "aggressive"          # Large position sizes (advanced only)


@dataclass
class RiskLimits:
    """Risk management limits"""
    max_per_trade_usd: int              # Maximum per single trade
    max_daily_loss_usd: int             # Maximum daily loss
    max_concurrent_positions: int       # Maximum open positions
    max_slippage_pct: float             # Maximum acceptable slippage
    max_position_age_seconds: int       # Max time to keep position open
    min_confidence_threshold: float     # Minimum confidence to execute
    circuit_breaker_consecutive_failures: int  # Failures before halt


class AineonConfig:
    """Enterprise configuration management"""
    
    # Default risk limits by tier
    RISK_PROFILES = {
        RiskTier.CONSERVATIVE: RiskLimits(
            max_per_trade_usd=10_000,
            max_daily_loss_usd=100_000,
            max_concurrent_positions=2,
            max_slippage_pct=0.05,
            max_position_age_seconds=60,
            min_confidence_threshold=0.80,
            circuit_breaker_consecutive_failures=2,
        ),
        RiskTier.BALANCED: RiskLimits(
            max_per_trade_usd=100_000,
            max_daily_loss_usd=1_500_000,
            max_concurrent_positions=5,
            max_slippage_pct=0.10,
            max_position_age_seconds=120,
            min_confidence_threshold=0.75,
            circuit_breaker_consecutive_failures=3,
        ),
        RiskTier.AGGRESSIVE: RiskLimits(
            max_per_trade_usd=1_000_000,
            max_daily_loss_usd=15_000_000,
            max_concurrent_positions=10,
            max_slippage_pct=0.15,
            max_position_age_seconds=180,
            min_confidence_threshold=0.70,
            circuit_breaker_consecutive_failures=5,
        ),
    }
    
    def __init__(self, 
                 environment: Environment = Environment.TESTNET,
                 risk_tier: RiskTier = RiskTier.BALANCED):
        """
        Initialize configuration
        
        Args:
            environment: TESTNET or MAINNET
            risk_tier: CONSERVATIVE, BALANCED, or AGGRESSIVE
        """
        self.environment = environment
        self.risk_tier = risk_tier
        self.risk_limits = self.RISK_PROFILES[risk_tier]
        
        # Load from environment
        self._load_from_env()
        
        # Validate required settings
        self._validate()
        
        logger.info(f"✓ Config initialized ({environment.value}, {risk_tier.value})")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        self.rpc_url = os.getenv('ETH_RPC_URL')
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY', '')
        self.paymaster_url = os.getenv('PAYMASTER_URL', '')
        self.bundler_url = os.getenv('BUNDLER_URL', '')
        self.profit_wallet = os.getenv('PROFIT_WALLET', self.wallet_address)
        self.port = int(os.getenv('PORT', '8081'))
        
        # DEX configurations
        self.uniswap_v3_router = '0xE592427A0AEce92De3Edee1F18E0157C05861564'
        self.uniswap_v2_router = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
        self.sushiswap_router = '0xd9e1cE17f2641f24aE9FEd266bf554A05A98eFDB'
        self.balancer_vault = '0xBA12222222228d8Ba445958a75a0704d566BF2C8'
        self.curve_address_provider = '0x0000000022D53366457F9d5E68Ec105046FC4383'
        self.aave_pool = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9'
        
        # Token addresses
        self.weth = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
        self.usdc = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
        self.usdt = '0xdAC17F958D2ee523a2206206994597C13D831ec7'
        self.dai = '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        
        # API rate limits (requests per second)
        self.api_rate_limits = {
            'uniswap': 10,
            'sushiswap': 10,
            'balancer': 5,
            'curve': 5,
            'aave': 10,
            'etherscan': 5,
        }
        
        # Monitoring (always enabled in monitoring-only mode)
        self.enable_monitoring = True
        self.monitoring_port = int(os.getenv('MONITORING_PORT', '9090'))
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    def _validate(self):
        """Validate required configuration"""
        required = [
            ('rpc_url', 'ETH_RPC_URL'),
            ('contract_address', 'CONTRACT_ADDRESS'),
            ('wallet_address', 'WALLET_ADDRESS'),
        ]
        
        missing = [env_var for attr, env_var in required if not getattr(self, attr)]
        
        if missing:
            raise RuntimeError(f"❌ FATAL: Missing required env vars: {', '.join(missing)}")
        
        optional = [
            ('etherscan_api_key', 'ETHERSCAN_API_KEY'),
            ('paymaster_url', 'PAYMASTER_URL'),
        ]
        
        warnings = [env_var for attr, env_var in optional 
                   if not getattr(self, attr, None)]
        
        if warnings:
            logger.warning(f"⚠️  Some features may be limited: {', '.join(warnings)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self, key, default)
    
    def get_risk_limit(self, limit_name: str) -> Any:
        """Get specific risk limit"""
        return getattr(self.risk_limits, limit_name)
    
    def __repr__(self) -> str:
        """String representation"""
        return (f"AineonConfig("
                f"env={self.environment.value}, "
                f"risk={self.risk_tier.value}, "
                f"rpc={self.rpc_url[:30]}..., "
                f"wallet={self.wallet_address[:10]}...)")


def get_config(environment: Optional[Environment] = None,
              risk_tier: Optional[RiskTier] = None) -> AineonConfig:
    """Get or create singleton config instance"""
    
    if environment is None:
        env_str = os.getenv('ENVIRONMENT', 'testnet').lower()
        environment = Environment.TESTNET if env_str == 'testnet' else Environment.MAINNET
    
    if risk_tier is None:
        tier_str = os.getenv('RISK_TIER', 'balanced').lower()
        if tier_str == 'conservative':
            risk_tier = RiskTier.CONSERVATIVE
        elif tier_str == 'aggressive':
            risk_tier = RiskTier.AGGRESSIVE
        else:
            risk_tier = RiskTier.BALANCED
    
    return AineonConfig(environment, risk_tier)
