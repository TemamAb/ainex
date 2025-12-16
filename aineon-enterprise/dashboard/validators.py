"""
Enterprise Dashboard Data Validator
Validates all dashboard data before display
"""

from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from jsonschema import validate, ValidationError as JsonSchemaError, Draft7Validator

from .models import (
    DashboardConfig,
    DataSource,
    VerificationStatus,
    VerifiedMetric,
    ProfitMetric,
    RiskMetric,
    HealthMetric,
    OpportunityMetric,
    ProfitDataResponse,
    RiskDataResponse,
    HealthCheckResponse,
    ValidationError,
    SchemaValidationError,
    RangeValidationError,
    FreshnessValidationError,
    ConsistencyValidationError,
    TypeValidationError,
)

logger = logging.getLogger(__name__)


class DashboardDataValidator:
    """
    Validates all dashboard data before display.
    Ensures data quality, consistency, and freshness.
    """
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load JSON schemas for validation"""
        return {
            'profit': {
                "type": "object",
                "required": ["accumulated_eth", "accumulated_usd", "transaction_count"],
                "properties": {
                    "accumulated_eth": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Total ETH accumulated"
                    },
                    "accumulated_usd": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Total USD equivalent"
                    },
                    "accumulated_eth_verified": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "accumulated_eth_pending": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "transaction_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "verified_transactions": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "auto_transfer_enabled": {
                        "type": "boolean",
                    },
                    "etherscan_enabled": {
                        "type": "boolean",
                    },
                    "verification_status": {
                        "type": "string",
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                    }
                },
                "additionalProperties": True
            },
            'risk': {
                "type": "object",
                "required": ["daily_loss_usd", "active_positions"],
                "properties": {
                    "daily_loss_usd": {
                        "type": "number",
                        "description": "Daily P&L loss"
                    },
                    "daily_loss_capacity": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "active_positions": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "position_size_max": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "circuit_breaker_status": {
                        "type": "string",
                    },
                    "circuit_breaker_triggered": {
                        "type": "boolean",
                    },
                    "risk_status": {
                        "type": "string",
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                    }
                },
                "additionalProperties": True
            },
            'health': {
                "type": "object",
                "required": ["status", "latency_ms"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["healthy", "degraded", "unhealthy"],
                    },
                    "rpc_connected": {
                        "type": "boolean",
                    },
                    "backend_alive": {
                        "type": "boolean",
                    },
                    "blockchain_accessible": {
                        "type": "boolean",
                    },
                    "latency_ms": {
                        "type": "number",
                        "minimum": 0,
                    },
                    "uptime_seconds": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                    }
                },
                "additionalProperties": True
            }
        }
    
    def validate_profit_data(self, data: Dict) -> ProfitMetric:
        """
        Validate profit data before display.
        
        Args:
            data: Raw profit data from backend
            
        Returns:
            ProfitMetric: Validated and annotated metric
            
        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating profit data: {data}")
        
        # 1. Schema validation
        try:
            validate(instance=data, schema=self.schemas['profit'])
            logger.debug("Schema validation passed")
        except JsonSchemaError as e:
            logger.error(f"Schema validation failed: {e}")
            raise SchemaValidationError(f"Schema validation failed: {e.message}")
        
        # 2. Type checking
        try:
            eth_amount = self._to_decimal(data.get('accumulated_eth', 0))
            usd_amount = self._to_decimal(data.get('accumulated_usd', 0))
            tx_count = self._to_int(data.get('transaction_count', 0))
            verified_count = self._to_int(data.get('verified_transactions', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Type conversion failed: {e}")
            raise TypeValidationError(f"Type conversion failed: {e}")
        
        # 3. Range validation
        self._validate_range('accumulated_eth', eth_amount, Decimal('0'), Decimal('10000'))
        self._validate_range('accumulated_usd', usd_amount, Decimal('0'), Decimal('100000000'))
        self._validate_range('transaction_count', tx_count, 0, 1000000)
        
        # 4. Consistency validation
        if verified_count > tx_count:
            raise ConsistencyValidationError(
                f"Verified transactions ({verified_count}) > total transactions ({tx_count})"
            )
        
        # 5. Freshness checking
        timestamp = self._parse_timestamp(data.get('timestamp'))
        age_seconds = (datetime.now() - timestamp).total_seconds()
        
        is_stale = age_seconds > self.config.max_data_age_seconds
        if is_stale:
            logger.warning(f"Data is {age_seconds}s old (max {self.config.max_data_age_seconds}s)")
        
        logger.info(f"Profit validation passed: {eth_amount} ETH, age: {age_seconds}s")
        
        # Return verified metric
        return ProfitMetric(
            value=float(eth_amount),
            source=DataSource.BACKEND,
            verification_status=VerificationStatus.NOT_CHECKED,
            verified_at=datetime.now(),
            verified_by="validator",
            confidence=0.9,
            is_stale=is_stale,
            age_seconds=int(age_seconds),
            eth_amount=eth_amount,
            usd_amount=usd_amount,
            transaction_count=tx_count,
            verified_transaction_count=verified_count,
        )
    
    def validate_risk_data(self, data: Dict) -> RiskMetric:
        """
        Validate risk data before display.
        
        Args:
            data: Raw risk data from backend
            
        Returns:
            RiskMetric: Validated and annotated metric
            
        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating risk data: {data}")
        
        # 1. Schema validation
        try:
            validate(instance=data, schema=self.schemas['risk'])
            logger.debug("Risk schema validation passed")
        except JsonSchemaError as e:
            logger.error(f"Risk schema validation failed: {e}")
            raise SchemaValidationError(f"Schema validation failed: {e.message}")
        
        # 2. Type checking
        try:
            daily_loss = self._to_decimal(data.get('daily_loss_usd', 0))
            capacity = self._to_decimal(data.get('daily_loss_capacity', self.config.daily_loss_limit_usd))
            positions = self._to_int(data.get('active_positions', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Type conversion failed: {e}")
            raise TypeValidationError(f"Type conversion failed: {e}")
        
        # 3. Range validation
        self._validate_range('daily_loss_usd', daily_loss, Decimal('-100000000'), Decimal('100000000'))
        self._validate_range('daily_loss_capacity', capacity, Decimal('0'), Decimal('100000000'))
        self._validate_range('active_positions', positions, 0, 1000000)
        
        # 4. Consistency validation
        if daily_loss > capacity:
            logger.warning(f"Daily loss {daily_loss} exceeds capacity {capacity}")
        
        # 5. Freshness checking
        timestamp = self._parse_timestamp(data.get('timestamp'))
        age_seconds = (datetime.now() - timestamp).total_seconds()
        is_stale = age_seconds > self.config.max_data_age_seconds
        
        logger.info(f"Risk validation passed: {daily_loss} USD loss, age: {age_seconds}s")
        
        return RiskMetric(
            value=float(daily_loss),
            source=DataSource.BACKEND,
            verification_status=VerificationStatus.NOT_CHECKED,
            verified_at=datetime.now(),
            verified_by="validator",
            confidence=0.9,
            is_stale=is_stale,
            age_seconds=int(age_seconds),
            daily_loss_usd=daily_loss,
            daily_loss_capacity=capacity,
            active_positions=positions,
            risk_status=data.get('risk_status', 'UNKNOWN'),
        )
    
    def validate_health_data(self, data: Dict) -> HealthMetric:
        """
        Validate health data before display.
        
        Args:
            data: Raw health data from backend
            
        Returns:
            HealthMetric: Validated and annotated metric
            
        Raises:
            ValidationError: If validation fails
        """
        logger.debug(f"Validating health data: {data}")
        
        # 1. Schema validation
        try:
            validate(instance=data, schema=self.schemas['health'])
            logger.debug("Health schema validation passed")
        except JsonSchemaError as e:
            logger.error(f"Health schema validation failed: {e}")
            raise SchemaValidationError(f"Schema validation failed: {e.message}")
        
        # 2. Type checking
        try:
            latency_ms = float(data.get('latency_ms', 0))
            uptime_seconds = self._to_int(data.get('uptime_seconds', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"Type conversion failed: {e}")
            raise TypeValidationError(f"Type conversion failed: {e}")
        
        # 3. Range validation
        self._validate_range('latency_ms', latency_ms, 0.0, 60000.0)
        self._validate_range('uptime_seconds', uptime_seconds, 0, 1000000000)
        
        # 4. Freshness checking
        timestamp = self._parse_timestamp(data.get('timestamp'))
        age_seconds = (datetime.now() - timestamp).total_seconds()
        is_stale = age_seconds > self.config.max_data_age_seconds
        
        logger.info(f"Health validation passed: {data.get('status')}, latency: {latency_ms}ms")
        
        return HealthMetric(
            value=data.get('status', 'UNKNOWN'),
            source=DataSource.BACKEND,
            verification_status=VerificationStatus.NOT_CHECKED,
            verified_at=datetime.now(),
            verified_by="validator",
            confidence=0.95,
            is_stale=is_stale,
            age_seconds=int(age_seconds),
            rpc_connected=data.get('rpc_connected', False),
            backend_alive=data.get('backend_alive', False),
            blockchain_accessible=data.get('blockchain_accessible', False),
            api_latency_ms=latency_ms,
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _to_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal"""
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        raise TypeError(f"Cannot convert {type(value)} to Decimal")
    
    def _to_int(self, value: Any) -> int:
        """Convert value to int"""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value)
        if isinstance(value, float):
            return int(value)
        raise TypeError(f"Cannot convert {type(value)} to int")
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """Parse timestamp from various formats"""
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except ValueError:
                pass
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp)
        # Default to now
        logger.warning(f"Could not parse timestamp: {timestamp}, using now()")
        return datetime.now()
    
    def _validate_range(self, field_name: str, value: Any, min_val: Any, max_val: Any) -> None:
        """Validate value is within range"""
        if value < min_val or value > max_val:
            raise RangeValidationError(
                f"{field_name} = {value} is outside allowed range [{min_val}, {max_val}]"
            )
    
    def validate_pydantic_model(self, model_class, data: Dict) -> any:
        """Validate data against Pydantic model"""
        try:
            return model_class(**data)
        except Exception as e:
            logger.error(f"Pydantic validation failed: {e}")
            raise ValidationError(f"Pydantic validation failed: {e}")


class DataConsistencyValidator:
    """Validates consistency between multiple data sources"""
    
    def __init__(self, config: DashboardConfig = None):
        self.config = config or DashboardConfig()
    
    def validate_profit_consistency(self,
                                   backend_profit: ProfitMetric,
                                   blockchain_balance: Optional[Decimal] = None) -> Tuple[bool, str]:
        """
        Validate profit data is consistent.
        
        Args:
            backend_profit: Profit from backend
            blockchain_balance: Actual balance from blockchain (optional)
            
        Returns:
            (is_consistent, message)
        """
        logger.debug("Validating profit consistency")
        
        # If no blockchain data, we can't validate
        if blockchain_balance is None:
            return True, "Cannot validate (no blockchain data)"
        
        # Check if claimed profit is less than or equal to blockchain balance
        discrepancy = blockchain_balance - backend_profit.eth_amount
        
        if discrepancy < 0:
            # Blockchain balance is less than claimed profit
            logger.error(f"Profit mismatch: claimed {backend_profit.eth_amount} but balance is {blockchain_balance}")
            return False, f"Claimed profit exceeds blockchain balance (missing {abs(discrepancy)} ETH)"
        
        if discrepancy > 0:
            # Blockchain has more than claimed
            logger.warning(f"Balance mismatch: blockchain has {blockchain_balance} but claimed {backend_profit.eth_amount}")
            return True, f"Balance inconsistency: {discrepancy} ETH unaccounted for"
        
        # Perfect match
        return True, "Profit verified on blockchain"
    
    def validate_risk_consistency(self, backend_risk: RiskMetric) -> Tuple[bool, str]:
        """
        Validate risk data is internally consistent.
        
        Args:
            backend_risk: Risk data from backend
            
        Returns:
            (is_consistent, message)
        """
        logger.debug("Validating risk consistency")
        
        # Check: current loss < capacity
        if backend_risk.daily_loss_usd > backend_risk.daily_loss_capacity:
            logger.error(f"Risk inconsistency: loss {backend_risk.daily_loss_usd} exceeds capacity {backend_risk.daily_loss_capacity}")
            return False, f"Daily loss exceeds capacity (must stop trading)"
        
        # Check: active positions is non-negative
        if backend_risk.active_positions < 0:
            logger.error(f"Risk inconsistency: negative positions {backend_risk.active_positions}")
            return False, "Negative active positions (invalid state)"
        
        return True, "Risk data is consistent"


if __name__ == "__main__":
    # Test validators
    logging.basicConfig(level=logging.DEBUG)
    
    validator = DashboardDataValidator()
    
    # Test profit validation
    profit_data = {
        'accumulated_eth': 0.5,
        'accumulated_usd': 1000.0,
        'transaction_count': 10,
        'verified_transactions': 9,
        'timestamp': datetime.now().isoformat(),
    }
    
    profit_metric = validator.validate_profit_data(profit_data)
    print(f"✅ Profit validation passed: {profit_metric.eth_amount} ETH")
    
    # Test risk validation
    risk_data = {
        'daily_loss_usd': 50000.0,
        'daily_loss_capacity': 1500000.0,
        'active_positions': 5,
        'risk_status': 'HEALTHY',
        'timestamp': datetime.now().isoformat(),
    }
    
    risk_metric = validator.validate_risk_data(risk_data)
    print(f"✅ Risk validation passed: {risk_metric.daily_loss_usd} USD loss")
