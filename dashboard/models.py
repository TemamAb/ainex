"""
Enterprise Dashboard Data Models
Defines all data structures with validation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, validator
import json


class DataSource(Enum):
    """Source of data"""
    BACKEND = "backend"
    BLOCKCHAIN = "blockchain"
    CACHE = "cache"
    ETHERSCAN = "etherscan"
    DEX_API = "dex_api"
    UNKNOWN = "unknown"


class VerificationStatus(Enum):
    """Verification status of data"""
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    NOT_CHECKED = "not_checked"
    SKIPPED = "skipped"


class RiskLevel(Enum):
    """Risk severity level"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ============================================================================
# BASE VERIFIED METRIC
# ============================================================================

@dataclass
class VerifiedMetric:
    """Base class for all verified metrics"""
    value: Any
    source: DataSource
    verification_status: VerificationStatus
    verified_at: datetime
    verified_by: str  # which service verified (e.g., "blockchain_verifier", "validator")
    confidence: float  # 0.0-1.0, how confident are we in this value
    is_stale: bool  # True if data is older than max_age
    age_seconds: int  # How old is this data
    error_message: Optional[str] = None  # If verification failed
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'value': str(self.value) if isinstance(self.value, Decimal) else self.value,
            'source': self.source.value,
            'verification_status': self.verification_status.value,
            'verified_at': self.verified_at.isoformat(),
            'verified_by': self.verified_by,
            'confidence': self.confidence,
            'is_stale': self.is_stale,
            'age_seconds': self.age_seconds,
            'error_message': self.error_message,
        }
    
    def is_trusted(self) -> bool:
        """Is this metric trusted enough to display?"""
        return (
            self.verification_status == VerificationStatus.VERIFIED and
            self.confidence >= 0.8 and
            not self.is_stale
        )


# ============================================================================
# PROFIT METRICS
# ============================================================================

@dataclass
class ProfitMetric(VerifiedMetric):
    """Verified profit metric"""
    eth_amount: Decimal = Decimal('0')
    usd_amount: Decimal = Decimal('0')
    etherscan_tx_hashes: List[str] = field(default_factory=list)  # Proof of profit
    blockchain_confirmed: bool = False
    transaction_count: int = 0
    verified_transaction_count: int = 0
    eth_price_usd: Decimal = Decimal('0')  # ETH price at time of verification
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        base = super().to_dict()
        base.update({
            'eth_amount': str(self.eth_amount),
            'usd_amount': str(self.usd_amount),
            'etherscan_tx_hashes': self.etherscan_tx_hashes,
            'blockchain_confirmed': self.blockchain_confirmed,
            'transaction_count': self.transaction_count,
            'verified_transaction_count': self.verified_transaction_count,
            'eth_price_usd': str(self.eth_price_usd),
        })
        return base


# Pydantic validation model for profit responses
class ProfitDataResponse(BaseModel):
    """Profit data from backend API with validation"""
    accumulated_eth: Decimal = Field(..., ge=0, description="Total ETH accumulated")
    accumulated_usd: Decimal = Field(..., ge=0, description="Total USD equivalent")
    accumulated_eth_verified: Decimal = Field(default=Decimal('0'), ge=0)
    accumulated_eth_pending: Decimal = Field(default=Decimal('0'), ge=0)
    transaction_count: int = Field(..., ge=0)
    verified_transactions: int = Field(default=0, ge=0)
    last_profit_time: Optional[datetime] = None
    auto_transfer_enabled: bool = False
    threshold_eth: Decimal = Field(default=Decimal('0.1'), gt=0)
    etherscan_enabled: bool = False
    verification_status: str = "UNKNOWN"
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    
    @validator('accumulated_eth')
    def validate_eth_amount(cls, v):
        if v < 0:
            raise ValueError('Profit cannot be negative')
        if v > 10000:  # Sanity check: max 10k ETH
            raise ValueError('Profit suspiciously high (>10,000 ETH)')
        return v
    
    @validator('transaction_count')
    def validate_tx_count(cls, v):
        if v < 0:
            raise ValueError('Transaction count cannot be negative')
        return v
    
    @validator('verified_transactions')
    def validate_verified_count(cls, v, values):
        if 'transaction_count' in values:
            if v > values['transaction_count']:
                raise ValueError('Verified transactions cannot exceed total transactions')
        return v
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


# ============================================================================
# RISK METRICS
# ============================================================================

@dataclass
class RiskMetric(VerifiedMetric):
    """Verified risk metric"""
    daily_loss_usd: Decimal = Decimal('0')
    daily_loss_capacity: Decimal = Decimal('1500000')  # $1.5M default
    active_positions: int = 0
    risk_status: str = "UNKNOWN"
    enforcement_verified: bool = False  # Is risk control actually enforced?
    enforcement_details: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        base = super().to_dict()
        base.update({
            'daily_loss_usd': str(self.daily_loss_usd),
            'daily_loss_capacity': str(self.daily_loss_capacity),
            'active_positions': self.active_positions,
            'risk_status': self.risk_status,
            'enforcement_verified': self.enforcement_verified,
            'enforcement_details': self.enforcement_details,
        })
        return base


class RiskDataResponse(BaseModel):
    """Risk data from backend API with validation"""
    daily_loss_usd: Decimal = Field(..., description="Daily P&L loss")
    daily_loss_capacity: Decimal = Field(
        default=Decimal('1500000'),
        description="Maximum daily loss allowed"
    )
    active_positions: int = Field(..., ge=0)
    position_size_max: Decimal = Field(
        default=Decimal('1000000'),
        description="Max position size in USD"
    )
    circuit_breaker_status: str = Field(default="UNKNOWN")
    circuit_breaker_triggered: bool = False
    risk_status: str = Field(default="UNKNOWN")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    
    @validator('daily_loss_usd')
    def validate_loss(cls, v):
        if v > 100000000:  # Sanity check: max $100M
            raise ValueError('Daily loss suspiciously high (>$100M)')
        return v
    
    @validator('daily_loss_capacity')
    def validate_capacity(cls, v):
        if v <= 0:
            raise ValueError('Daily loss capacity must be positive')
        return v
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat() if v else None,
        }


# ============================================================================
# HEALTH & SYSTEM METRICS
# ============================================================================

@dataclass
class HealthMetric(VerifiedMetric):
    """System health metric"""
    rpc_connected: bool = False
    backend_alive: bool = False
    blockchain_accessible: bool = False
    api_latency_ms: float = 0.0
    dependencies: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        base = super().to_dict()
        base.update({
            'rpc_connected': self.rpc_connected,
            'backend_alive': self.backend_alive,
            'blockchain_accessible': self.blockchain_accessible,
            'api_latency_ms': self.api_latency_ms,
            'dependencies': self.dependencies,
        })
        return base


class HealthCheckResponse(BaseModel):
    """Health check response from API"""
    status: str = Field(..., description="healthy|degraded|unhealthy")
    timestamp: datetime = Field(default_factory=datetime.now)
    rpc_connected: bool = True
    backend_alive: bool = True
    blockchain_accessible: bool = True
    latency_ms: float = Field(..., ge=0)
    uptime_seconds: int = Field(..., ge=0)
    
    @validator('status')
    def validate_status(cls, v):
        if v not in ['healthy', 'degraded', 'unhealthy']:
            raise ValueError("Status must be healthy|degraded|unhealthy")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# ============================================================================
# OPPORTUNITY METRICS
# ============================================================================

@dataclass
class OpportunityMetric(VerifiedMetric):
    """Verified arbitrage opportunity"""
    pair: str = ""
    dex: str = ""
    profit_usd: Decimal = Decimal('0')
    profit_percentage: Decimal = Decimal('0')
    confidence: float = 0.0
    buy_price: Decimal = Decimal('0')
    sell_price: Decimal = Decimal('0')
    slippage_estimated: Decimal = Decimal('0')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        base = super().to_dict()
        base.update({
            'pair': self.pair,
            'dex': self.dex,
            'profit_usd': str(self.profit_usd),
            'profit_percentage': str(self.profit_percentage),
            'confidence': self.confidence,
            'buy_price': str(self.buy_price),
            'sell_price': str(self.sell_price),
            'slippage_estimated': str(self.slippage_estimated),
        })
        return base


# ============================================================================
# ALERT & NOTIFICATION
# ============================================================================

@dataclass
class Alert:
    """System alert"""
    alert_id: str
    title: str
    description: str
    level: RiskLevel
    source: str  # which component triggered this
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'alert_id': self.alert_id,
            'title': self.title,
            'description': self.description,
            'level': self.level.value,
            'source': self.source,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None,
            'acknowledged_by': self.acknowledged_by,
        }


# ============================================================================
# VALIDATION ERROR TYPES
# ============================================================================

class ValidationError(Exception):
    """Base validation error"""
    pass


class SchemaValidationError(ValidationError):
    """Schema validation failed"""
    pass


class RangeValidationError(ValidationError):
    """Value out of range"""
    pass


class FreshnessValidationError(ValidationError):
    """Data too old"""
    pass


class ConsistencyValidationError(ValidationError):
    """Data inconsistent"""
    pass


class TypeValidationError(ValidationError):
    """Type mismatch"""
    pass


# ============================================================================
# VERIFICATION ERROR TYPES
# ============================================================================

class VerificationError(Exception):
    """Base verification error"""
    pass


class BlockchainVerificationError(VerificationError):
    """Blockchain verification failed"""
    pass


class RiskControlVerificationError(VerificationError):
    """Risk control verification failed"""
    pass


class DataMismatchError(VerificationError):
    """Data mismatch between sources"""
    pass


# ============================================================================
# API ERROR TYPES
# ============================================================================

class APIError(Exception):
    """Base API error"""
    pass


class BackendUnavailableError(APIError):
    """Backend API is unavailable"""
    pass


class BlockchainUnavailableError(APIError):
    """Blockchain RPC is unavailable"""
    pass


class EtherscanUnavailableError(APIError):
    """Etherscan API is unavailable"""
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    # Data validation
    max_data_age_seconds: int = 300  # 5 minutes
    max_stale_data_age_seconds: int = 600  # 10 minutes before completely stale
    
    # Blockchain verification
    blockchain_rpc_url: str = "http://localhost:8545"
    etherscan_api_key: str = ""
    etherscan_enabled: bool = False
    
    # Risk management
    daily_loss_limit_usd: Decimal = Decimal('1500000')
    max_position_size_usd: Decimal = Decimal('1000000')
    require_etherscan_verification: bool = True
    
    # Performance
    cache_ttl_seconds: int = 60
    verification_timeout_seconds: int = 10
    api_timeout_seconds: int = 5
    
    # Display
    precision_eth: int = 6
    precision_usd: int = 2
    show_unverified_data: bool = False
    
    # Alerts
    alert_on_verification_failure: bool = True
    alert_on_data_mismatch: bool = True
    alert_on_stale_data: bool = True
    alert_on_api_timeout: bool = True


@dataclass
class DataSourceConfig:
    """Configuration for data sources"""
    backend_api_url: str = "http://localhost:8080"
    backend_api_timeout: int = 5
    
    blockchain_rpc_url: str = "http://localhost:8545"
    blockchain_timeout: int = 10
    
    etherscan_api_url: str = "https://api.etherscan.io/api"
    etherscan_timeout: int = 5
    
    dex_price_urls: List[str] = field(default_factory=list)
    
    cache_backend: str = "redis"  # redis or memory
    cache_redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 60
