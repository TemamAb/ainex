"""
Week 4: Data Source Manager
Intelligently manages multiple data sources with fallback chains
"""

import asyncio
import logging
from typing import Optional, Dict, Tuple
from datetime import datetime
from decimal import Decimal
import aiohttp

from .models import (
    DataSource,
    VerificationStatus,
    VerifiedMetric,
    ProfitMetric,
    RiskMetric,
    HealthMetric,
    ValidationError,
)
from .validators import DashboardDataValidator
from .blockchain_verifier import BlockchainVerifier

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    Manages multiple data sources with intelligent fallback chains.
    
    Priority order:
    1. Backend API (primary, fastest)
    2. Blockchain read-only (fallback, verified)
    3. Cache (fallback, stale)
    4. Fail-loud (never silently return zeros)
    """
    
    def __init__(self, 
                 backend_api_url: str,
                 blockchain_rpc_url: str,
                 etherscan_api_key: str = "",
                 wallet_address: str = None):
        """
        Initialize data source manager.
        
        Args:
            backend_api_url: Backend API URL
            blockchain_rpc_url: Blockchain RPC URL
            etherscan_api_key: Etherscan API key
            wallet_address: Wallet to verify
        """
        self.backend_url = backend_api_url
        self.blockchain_rpc = blockchain_rpc_url
        self.wallet_address = wallet_address
        
        self.validator = DashboardDataValidator()
        self.blockchain = BlockchainVerifier(
            blockchain_rpc_url,
            etherscan_api_key,
            bool(etherscan_api_key)
        )
        
        self.cache = {}
        self.last_successful_source = {}
        self.fallback_counter = {}
    
    async def get_verified_profit(self) -> VerifiedMetric:
        """
        Get verified profit data from best available source.
        
        Tries in order:
        1. Backend API + blockchain verification
        2. Blockchain read-only
        3. Cache (if available)
        4. Fail with error
        """
        logger.info("Fetching verified profit data...")
        
        # Try backend first
        backend_data = await self._fetch_from_backend('/profit')
        if backend_data:
            try:
                # Validate data
                metric = self.validator.validate_profit_data(backend_data)
                
                # Try to verify against blockchain
                if self.wallet_address and metric.eth_amount > 0:
                    is_valid, msg, _ = await self.blockchain.verify_profit_against_balance(
                        self.wallet_address,
                        metric.eth_amount
                    )
                    
                    if is_valid:
                        metric.source = DataSource.BLOCKCHAIN
                        metric.verification_status = VerificationStatus.VERIFIED
                        metric.verified_by = "blockchain_verifier"
                        metric.confidence = 1.0
                        logger.info(f"✅ Profit verified via blockchain")
                        self.last_successful_source['profit'] = DataSource.BLOCKCHAIN
                        return metric
                    else:
                        logger.warning(f"⚠️ Blockchain verification failed: {msg}")
                        # Continue to fallback
                else:
                    # No blockchain verification available, trust backend validation
                    metric.source = DataSource.BACKEND
                    metric.verification_status = VerificationStatus.PENDING
                    metric.verified_by = "validator"
                    metric.confidence = 0.8
                    logger.info(f"✅ Profit validated via backend")
                    self.last_successful_source['profit'] = DataSource.BACKEND
                    return metric
            
            except ValidationError as e:
                logger.error(f"❌ Backend data validation failed: {e}")
                # Fall through to blockchain fallback
        
        # Fallback to blockchain read-only
        if self.wallet_address:
            try:
                balance = await self.blockchain.verify_eth_balance(self.wallet_address)
                logger.info(f"✅ Using blockchain balance as fallback: {balance} ETH")
                
                metric = ProfitMetric(
                    value=float(balance),
                    source=DataSource.BLOCKCHAIN,
                    verification_status=VerificationStatus.VERIFIED,
                    verified_at=datetime.now(),
                    verified_by="blockchain",
                    confidence=1.0,
                    is_stale=False,
                    age_seconds=0,
                    eth_amount=balance,
                    usd_amount=Decimal('0'),  # Would need price feed
                    blockchain_confirmed=True,
                )
                
                self.last_successful_source['profit'] = DataSource.BLOCKCHAIN
                return metric
            
            except Exception as e:
                logger.error(f"❌ Blockchain fallback failed: {e}")
        
        # Fallback to cache
        cached = self.cache.get('profit')
        if cached:
            logger.warning(f"⚠️ Using cached profit data")
            cached.is_stale = True
            self.last_successful_source['profit'] = DataSource.CACHE
            return cached
        
        # All sources failed - fail loudly
        logger.error("❌ ALL PROFIT DATA SOURCES FAILED")
        raise ValidationError("Cannot fetch profit data from any source (backend, blockchain, cache all failed)")
    
    async def get_verified_risk(self) -> VerifiedMetric:
        """
        Get verified risk data from best available source.
        
        Tries in order:
        1. Backend API
        2. Cache
        3. Fail with error
        """
        logger.info("Fetching verified risk data...")
        
        # Try backend
        backend_data = await self._fetch_from_backend('/risk')
        if backend_data:
            try:
                metric = self.validator.validate_risk_data(backend_data)
                metric.source = DataSource.BACKEND
                metric.verification_status = VerificationStatus.PENDING
                logger.info(f"✅ Risk data fetched from backend")
                self.last_successful_source['risk'] = DataSource.BACKEND
                return metric
            
            except ValidationError as e:
                logger.error(f"❌ Risk data validation failed: {e}")
        
        # Fallback to cache
        cached = self.cache.get('risk')
        if cached:
            logger.warning(f"⚠️ Using cached risk data")
            cached.is_stale = True
            self.last_successful_source['risk'] = DataSource.CACHE
            return cached
        
        # Fail loudly
        logger.error("❌ ALL RISK DATA SOURCES FAILED")
        raise ValidationError("Cannot fetch risk data from any source")
    
    async def get_verified_health(self) -> VerifiedMetric:
        """
        Get verified health data from best available source.
        """
        logger.info("Fetching verified health data...")
        
        # Try backend
        backend_data = await self._fetch_from_backend('/health')
        if backend_data:
            try:
                metric = self.validator.validate_health_data(backend_data)
                metric.source = DataSource.BACKEND
                logger.info(f"✅ Health data fetched from backend")
                self.last_successful_source['health'] = DataSource.BACKEND
                return metric
            
            except ValidationError as e:
                logger.error(f"❌ Health data validation failed: {e}")
        
        # Fallback to cache
        cached = self.cache.get('health')
        if cached:
            logger.warning(f"⚠️ Using cached health data")
            cached.is_stale = True
            return cached
        
        # Fail loudly
        logger.error("❌ ALL HEALTH DATA SOURCES FAILED")
        raise ValidationError("Cannot fetch health data from any source")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _fetch_from_backend(self, endpoint: str) -> Optional[Dict]:
        """
        Fetch data from backend API.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Data or None if failed
        """
        try:
            url = f"{self.backend_url}{endpoint}"
            logger.debug(f"Fetching from backend: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Cache successful response
                        self.cache[endpoint.strip('/')] = data
                        return data
                    else:
                        logger.warning(f"Backend API error {resp.status} on {endpoint}")
                        return None
        
        except asyncio.TimeoutError:
            logger.warning(f"Backend API timeout on {endpoint}")
            return None
        except Exception as e:
            logger.warning(f"Backend API error on {endpoint}: {e}")
            return None
    
    def get_data_source_status(self) -> Dict[str, Dict]:
        """Get status of all data sources"""
        return {
            'last_successful_sources': self.last_successful_source,
            'cached_metrics': list(self.cache.keys()),
            'blockchain_connected': self.blockchain.is_connected,
            'last_update': datetime.now().isoformat(),
        }


class FallbackChain:
    """Manages fallback chain for a single metric"""
    
    def __init__(self, metric_name: str, sources: list):
        """
        Initialize fallback chain.
        
        Args:
            metric_name: Name of metric
            sources: List of sources to try in order
        """
        self.metric_name = metric_name
        self.sources = sources
        self.current_source_index = 0
        self.last_successful_source = None
    
    async def get_value(self, fetchers: Dict) -> Tuple[Optional[any], DataSource]:
        """
        Get value from fallback chain.
        
        Args:
            fetchers: Dict of fetcher functions keyed by DataSource
            
        Returns:
            (value, source)
        """
        for source in self.sources:
            try:
                fetcher = fetchers.get(source)
                if not fetcher:
                    logger.debug(f"No fetcher for {source}")
                    continue
                
                value = await fetcher()
                self.last_successful_source = source
                logger.info(f"Got {self.metric_name} from {source.value}")
                return value, source
            
            except Exception as e:
                logger.warning(f"Failed to get {self.metric_name} from {source.value}: {e}")
                continue
        
        # All sources failed
        logger.error(f"All fallback sources failed for {self.metric_name}")
        return None, DataSource.UNKNOWN


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        manager = DataSourceManager(
            "http://localhost:8080",
            "http://localhost:8545",
            wallet_address="0x..."
        )
        
        try:
            profit = await manager.get_verified_profit()
            print(f"Profit: {profit.eth_amount} ETH (source: {profit.source.value})")
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(test())
