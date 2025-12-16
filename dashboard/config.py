"""
Enterprise Dashboard Configuration
Centralized configuration management for the dashboard system
"""

import os
from dataclasses import dataclass, asdict
from typing import Optional, List
from decimal import Decimal
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class BlockchainConfig:
    """Blockchain configuration"""
    rpc_url: str
    etherscan_api_key: str
    etherscan_enabled: bool = True
    chain_id: int = 1  # Mainnet by default
    confirmation_blocks: int = 12
    read_timeout_seconds: int = 10
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'BlockchainConfig':
        """Load from environment variables"""
        return cls(
            rpc_url=os.getenv('BLOCKCHAIN_RPC_URL', 'http://localhost:8545'),
            etherscan_api_key=os.getenv('ETHERSCAN_API_KEY', ''),
            etherscan_enabled=os.getenv('ETHERSCAN_ENABLED', 'true').lower() == 'true',
            chain_id=int(os.getenv('CHAIN_ID', '1')),
            confirmation_blocks=int(os.getenv('CONFIRMATION_BLOCKS', '12')),
            read_timeout_seconds=int(os.getenv('BLOCKCHAIN_TIMEOUT', '10')),
        )


@dataclass
class BackendConfig:
    """Backend API configuration"""
    api_url: str
    api_key: Optional[str] = None
    timeout_seconds: int = 5
    retry_count: int = 3
    retry_backoff_seconds: float = 1.0
    max_retry_backoff_seconds: float = 30.0
    enable_caching: bool = True
    cache_ttl_seconds: int = 60
    
    @classmethod
    def from_env(cls) -> 'BackendConfig':
        """Load from environment variables"""
        return cls(
            api_url=os.getenv('BACKEND_API_URL', 'http://localhost:8080'),
            api_key=os.getenv('BACKEND_API_KEY'),
            timeout_seconds=int(os.getenv('BACKEND_TIMEOUT', '5')),
            retry_count=int(os.getenv('BACKEND_RETRIES', '3')),
            retry_backoff_seconds=float(os.getenv('BACKEND_RETRY_BACKOFF', '1.0')),
            enable_caching=os.getenv('BACKEND_CACHING', 'true').lower() == 'true',
            cache_ttl_seconds=int(os.getenv('BACKEND_CACHE_TTL', '60')),
        )


@dataclass
class ValidationConfig:
    """Data validation configuration"""
    max_data_age_seconds: int = 300  # 5 minutes
    max_stale_data_age_seconds: int = 600  # 10 minutes
    precision_eth: int = 6
    precision_usd: int = 2
    enforce_validation: bool = True
    show_unverified_data: bool = False
    
    # Sanity check limits
    max_eth_amount: Decimal = Decimal('10000')
    max_usd_amount: Decimal = Decimal('100000000')
    max_daily_loss: Decimal = Decimal('100000000')
    
    @classmethod
    def from_env(cls) -> 'ValidationConfig':
        """Load from environment variables"""
        return cls(
            max_data_age_seconds=int(os.getenv('MAX_DATA_AGE', '300')),
            max_stale_data_age_seconds=int(os.getenv('MAX_STALE_AGE', '600')),
            precision_eth=int(os.getenv('PRECISION_ETH', '6')),
            precision_usd=int(os.getenv('PRECISION_USD', '2')),
            enforce_validation=os.getenv('ENFORCE_VALIDATION', 'true').lower() == 'true',
            show_unverified_data=os.getenv('SHOW_UNVERIFIED', 'false').lower() == 'true',
        )


@dataclass
class RiskConfig:
    """Risk management configuration"""
    daily_loss_limit_usd: Decimal = Decimal('1500000')
    max_position_size_usd: Decimal = Decimal('1000000')
    circuit_breaker_enabled: bool = True
    require_etherscan_verification: bool = True
    alert_on_enforcement_failure: bool = True
    
    @classmethod
    def from_env(cls) -> 'RiskConfig':
        """Load from environment variables"""
        return cls(
            daily_loss_limit_usd=Decimal(os.getenv('DAILY_LOSS_LIMIT', '1500000')),
            max_position_size_usd=Decimal(os.getenv('MAX_POSITION_SIZE', '1000000')),
            circuit_breaker_enabled=os.getenv('CIRCUIT_BREAKER_ENABLED', 'true').lower() == 'true',
            require_etherscan_verification=os.getenv('REQUIRE_ETHERSCAN', 'true').lower() == 'true',
            alert_on_enforcement_failure=os.getenv('ALERT_ENFORCEMENT', 'true').lower() == 'true',
        )


@dataclass
class CacheConfig:
    """Cache configuration"""
    enabled: bool = True
    backend: str = 'redis'  # redis or memory
    redis_url: str = 'redis://localhost:6379'
    memory_max_items: int = 1000
    default_ttl_seconds: int = 60
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Load from environment variables"""
        return cls(
            enabled=os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
            backend=os.getenv('CACHE_BACKEND', 'memory').lower(),
            redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
            memory_max_items=int(os.getenv('CACHE_MAX_ITEMS', '1000')),
            default_ttl_seconds=int(os.getenv('CACHE_TTL', '60')),
        )


@dataclass
class AlertConfig:
    """Alert and notification configuration"""
    alert_on_validation_failure: bool = True
    alert_on_verification_failure: bool = True
    alert_on_data_mismatch: bool = True
    alert_on_stale_data: bool = True
    alert_on_api_timeout: bool = True
    alert_on_circuit_breaker: bool = True
    
    # Alert channels
    enable_email_alerts: bool = False
    email_recipients: List[str] = None
    enable_slack_alerts: bool = False
    slack_webhook_url: Optional[str] = None
    enable_pagerduty_alerts: bool = False
    pagerduty_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'AlertConfig':
        """Load from environment variables"""
        email_recipients = os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
        email_recipients = [e.strip() for e in email_recipients if e.strip()]
        
        return cls(
            alert_on_validation_failure=os.getenv('ALERT_VALIDATION', 'true').lower() == 'true',
            alert_on_verification_failure=os.getenv('ALERT_VERIFICATION', 'true').lower() == 'true',
            alert_on_data_mismatch=os.getenv('ALERT_MISMATCH', 'true').lower() == 'true',
            alert_on_stale_data=os.getenv('ALERT_STALE', 'true').lower() == 'true',
            alert_on_api_timeout=os.getenv('ALERT_TIMEOUT', 'true').lower() == 'true',
            alert_on_circuit_breaker=os.getenv('ALERT_CIRCUIT_BREAKER', 'true').lower() == 'true',
            enable_email_alerts=os.getenv('EMAIL_ALERTS', 'false').lower() == 'true',
            email_recipients=email_recipients,
            enable_slack_alerts=os.getenv('SLACK_ALERTS', 'false').lower() == 'true',
            slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            enable_pagerduty_alerts=os.getenv('PAGERDUTY_ALERTS', 'false').lower() == 'true',
            pagerduty_key=os.getenv('PAGERDUTY_KEY'),
        )


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: Optional[str] = None
    enable_json_logging: bool = False
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load from environment variables"""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            format=os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_path=os.getenv('LOG_FILE'),
            enable_json_logging=os.getenv('JSON_LOGGING', 'false').lower() == 'true',
        )


@dataclass
class DashboardConfig:
    """Complete dashboard configuration"""
    # Sub-configurations
    blockchain: BlockchainConfig
    backend: BackendConfig
    validation: ValidationConfig
    risk: RiskConfig
    cache: CacheConfig
    alerts: AlertConfig
    logging: LoggingConfig
    
    # General settings
    environment: str = 'development'  # development, staging, production
    debug: bool = False
    wallet_address: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'DashboardConfig':
        """Load all configuration from environment variables"""
        logger.info("Loading dashboard configuration from environment")
        
        return cls(
            blockchain=BlockchainConfig.from_env(),
            backend=BackendConfig.from_env(),
            validation=ValidationConfig.from_env(),
            risk=RiskConfig.from_env(),
            cache=CacheConfig.from_env(),
            alerts=AlertConfig.from_env(),
            logging=LoggingConfig.from_env(),
            environment=os.getenv('ENVIRONMENT', 'development').lower(),
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            wallet_address=os.getenv('WALLET_ADDRESS'),
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'DashboardConfig':
        """Load configuration from JSON file"""
        logger.info(f"Loading dashboard configuration from {file_path}")
        
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # Build nested configurations
        return cls(
            blockchain=BlockchainConfig(**config_dict.get('blockchain', {})),
            backend=BackendConfig(**config_dict.get('backend', {})),
            validation=ValidationConfig(**config_dict.get('validation', {})),
            risk=RiskConfig(**config_dict.get('risk', {})),
            cache=CacheConfig(**config_dict.get('cache', {})),
            alerts=AlertConfig(**config_dict.get('alerts', {})),
            logging=LoggingConfig(**config_dict.get('logging', {})),
            environment=config_dict.get('environment', 'development'),
            debug=config_dict.get('debug', False),
            wallet_address=config_dict.get('wallet_address'),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'blockchain': asdict(self.blockchain),
            'backend': asdict(self.backend),
            'validation': asdict(self.validation),
            'risk': asdict(self.risk),
            'cache': asdict(self.cache),
            'alerts': asdict(self.alerts),
            'logging': asdict(self.logging),
            'environment': self.environment,
            'debug': self.debug,
            'wallet_address': self.wallet_address,
        }
    
    def to_json(self, file_path: str = None) -> str:
        """Convert to JSON"""
        config_dict = self.to_dict()
        
        # Convert Decimal objects to strings
        def decimal_encoder(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        json_str = json.dumps(config_dict, indent=2, default=decimal_encoder)
        
        if file_path:
            logger.info(f"Saving configuration to {file_path}")
            with open(file_path, 'w') as f:
                f.write(json_str)
        
        return json_str
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration"""
        errors = []
        
        # Validate blockchain config
        if not self.blockchain.rpc_url:
            errors.append("blockchain.rpc_url is required")
        
        # Validate backend config
        if not self.backend.api_url:
            errors.append("backend.api_url is required")
        
        # Validate risk config
        if self.risk.daily_loss_limit_usd <= 0:
            errors.append("risk.daily_loss_limit_usd must be positive")
        
        if self.risk.max_position_size_usd <= 0:
            errors.append("risk.max_position_size_usd must be positive")
        
        # Validate cache config
        if self.cache.enabled and self.cache.backend not in ['redis', 'memory']:
            errors.append(f"Invalid cache backend: {self.cache.backend}")
        
        if self.environment not in ['development', 'staging', 'production']:
            errors.append(f"Invalid environment: {self.environment}")
        
        return len(errors) == 0, errors
    
    def log_summary(self) -> None:
        """Log configuration summary"""
        logger.info("=" * 60)
        logger.info("DASHBOARD CONFIGURATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Debug: {self.debug}")
        logger.info(f"Wallet: {self.wallet_address or 'NOT SET'}")
        logger.info("")
        logger.info(f"Blockchain RPC: {self.blockchain.rpc_url}")
        logger.info(f"Etherscan Enabled: {self.blockchain.etherscan_enabled}")
        logger.info(f"Backend API: {self.backend.api_url}")
        logger.info(f"Cache: {self.cache.backend} (TTL: {self.cache.default_ttl_seconds}s)")
        logger.info(f"Max Data Age: {self.validation.max_data_age_seconds}s")
        logger.info(f"Daily Loss Limit: ${self.risk.daily_loss_limit_usd}")
        logger.info("=" * 60)


# Global configuration instance
_global_config: Optional[DashboardConfig] = None


def get_config() -> DashboardConfig:
    """Get global configuration instance"""
    global _global_config
    
    if _global_config is None:
        # Try loading from file first
        config_file = os.getenv('CONFIG_FILE')
        if config_file and os.path.exists(config_file):
            _global_config = DashboardConfig.from_file(config_file)
        else:
            # Fall back to environment variables
            _global_config = DashboardConfig.from_env()
        
        # Validate
        is_valid, errors = _global_config.validate()
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            raise ValueError("Invalid configuration")
        
        _global_config.log_summary()
    
    return _global_config


def set_config(config: DashboardConfig) -> None:
    """Set global configuration instance"""
    global _global_config
    _global_config = config


if __name__ == "__main__":
    # Test configuration loading
    logging.basicConfig(level=logging.DEBUG)
    
    config = DashboardConfig.from_env()
    print(config.to_json())
