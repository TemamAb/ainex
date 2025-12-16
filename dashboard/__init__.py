"""
AINEON Enterprise Dashboard
Complete monitoring system with blockchain verification
"""

__version__ = "1.0.0"
__author__ = "Chief Architect - Enterprise Systems"

from .models import (
    DataSource,
    VerificationStatus,
    RiskLevel,
    VerifiedMetric,
    ProfitMetric,
    RiskMetric,
    HealthMetric,
    DashboardConfig,
)

from .validators import (
    DashboardDataValidator,
    DataConsistencyValidator,
)

from .config import (
    get_config,
    set_config,
)

__all__ = [
    'DataSource',
    'VerificationStatus',
    'RiskLevel',
    'VerifiedMetric',
    'ProfitMetric',
    'RiskMetric',
    'HealthMetric',
    'DashboardConfig',
    'DashboardDataValidator',
    'DataConsistencyValidator',
    'get_config',
    'set_config',
]
