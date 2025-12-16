"""
Curve Gauge Handler - Curve Finance & Gauge Integration
Stable swap AMM support with gauge farming and metapool routing
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class CurvePoolType(Enum):
    """Curve pool types"""
    STABLESWAP = "stableswap"
    CRYPTOSWAP = "cryptoswap"
    TRICRYPTO = "tricrypto"
    METAPOOL = "metapool"


@dataclass
class CurvePool:
    """Curve liquidity pool"""
    pool_address: str
    pool_name: str
    pool_type: CurvePoolType
    coins: List[str]
    balances: List[float]
    amplification: float
    fee_bps: int
    admin_fee_bps: int
    virtual_price: float
    tvl_usd: float
    volume_24h: float


@dataclass
class CurveGauge:
    """Curve gauge for farming"""
    gauge_address: str
    gauge_name: str
    pool_address: str
    token: str  # Reward token (usually CRV)
    crv_apy: float  # CRV APY
    bonus_apy: float  # Additional token APY (if any)
    total_apy: float
    tvl_usd: float
    weight: float  # Gauge weight


@dataclass
class CurveSwapQuote:
    """Quote for a Curve swap"""
    pool_address: str
    token_in: str
    token_out: str
    amount_in: float
    amount_out: float
    price: float
    slippage_percent: float
    execution_fee: float


class CurveGaugeHandler:
    """Handles Curve Finance pools and gauge integration"""
    
    def __init__(self):
        self.pools: Dict[str, CurvePool] = {}
        self.gauges: Dict[str, CurveGauge] = {}
        self.metapools: Dict[str, str] = {}  # metapool_address -> base_pool_address
        self.connected = False
        self.registry_address = os.getenv('CURVE_REGISTRY', '0x90E00ACe148ca3b23Ac1bC8c240C2a7Dd9c2d7f5')
        self.gauge_controller_address = os.getenv('CURVE_GAUGE_CONTROLLER', '0x2F50D538606Fa9EDD2B68Bf0C4f3eab3da1C5746')
    
    async def connect(self) -> bool:
        """Connect to Curve"""
        try:
            logger.info("Connecting to Curve")
            
            # Load initial pools
            await self._load_pools()
            
            # Load gauges
            await self._load_gauges()
            
            self.connected = True
            logger.info(f"Connected to Curve: {len(self.pools)} pools, {len(self.gauges)} gauges")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def _load_pools(self):
        """Load Curve pools from registry"""
        try:
            # Simplified: load well-known pools
            well_known_pools = [
                {
                    'address': '0xA2B47E3D5c44877cca798eae935d2b6Eeae0e777',
                    'name': '3Pool',
                    'type': CurvePoolType.STABLESWAP,
                    'coins': ['USDC', 'USDT', 'DAI'],
                    'balances': [1000000, 1000000, 1000000],
                },
                {
                    'address': '0x7fC77B5d8585917865723385EF430D7f1C7dAd5B',
                    'name': 'crvBTC/BTC',
                    'type': CurvePoolType.CRYPTOSWAP,
                    'coins': ['crvBTC', 'WBTC'],
                    'balances': [100, 100],
                },
            ]
            
            for pool_data in well_known_pools:
                pool = CurvePool(
                    pool_address=pool_data['address'],
                    pool_name=pool_data['name'],
                    pool_type=pool_data['type'],
                    coins=pool_data['coins'],
                    balances=pool_data['balances'],
                    amplification=1000.0 if pool_data['type'] == CurvePoolType.STABLESWAP else 0.0,
                    fee_bps=1,  # 0.01%
                    admin_fee_bps=5000,  # 50% of fees
                    virtual_price=1.0,
                    tvl_usd=sum(pool_data['balances']) * 1000,  # Rough estimate
                    volume_24h=1000000.0,
                )
                
                self.pools[pool_data['address']] = pool
            
            logger.info(f"Loaded {len(self.pools)} Curve pools")
            
        except Exception as e:
            logger.error(f"Pool loading error: {e}")
    
    async def _load_gauges(self):
        """Load Curve gauges"""
        try:
            # Simplified: create gauges for loaded pools
            for pool_address, pool in self.pools.items():
                gauge = CurveGauge(
                    gauge_address=f"0x{pool_address[2:].lower()}",
                    gauge_name=f"{pool.pool_name} Gauge",
                    pool_address=pool_address,
                    token='CRV',
                    crv_apy=0.25,  # 25% APY
                    bonus_apy=0.05,  # 5% bonus
                    total_apy=0.30,  # 30% total
                    tvl_usd=pool.tvl_usd,
                    weight=1.0,
                )
                
                self.gauges[gauge.gauge_address] = gauge
            
            logger.info(f"Loaded {len(self.gauges)} Curve gauges")
            
        except Exception as e:
            logger.error(f"Gauge loading error: {e}")
    
    async def get_swap_quote(self, pool_address: str, token_in: str,
                            token_out: str, amount_in: float) -> Optional[CurveSwapQuote]:
        """Get swap quote from Curve pool"""
        try:
            if pool_address not in self.pools:
                logger.warning(f"Pool not found: {pool_address}")
                return None
            
            pool = self.pools[pool_address]
            
            # Find token indices
            try:
                i = pool.coins.index(token_in)
                j = pool.coins.index(token_out)
            except ValueError:
                logger.warning(f"Tokens not in pool: {token_in}, {token_out}")
                return None
            
            # Calculate output (simplified stableswap formula)
            amount_out = await self._calculate_dy(pool, i, j, amount_in)
            
            # Calculate fee
            fee_percent = (pool.fee_bps / 10000) * 100
            
            # Calculate actual output after fee
            actual_output = amount_out * (1 - pool.fee_bps / 10000)
            
            quote = CurveSwapQuote(
                pool_address=pool_address,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                amount_out=actual_output,
                price=actual_output / amount_in,
                slippage_percent=fee_percent,
                execution_fee=amount_in * (pool.fee_bps / 10000),
            )
            
            return quote
            
        except Exception as e:
            logger.error(f"Quote error: {e}")
            return None
    
    async def _calculate_dy(self, pool: CurvePool, i: int, j: int, dx: float) -> float:
        """Calculate dy for stableswap formula"""
        try:
            # Simplified stableswap constant product formula
            # For actual implementation, use the proper stableswap math
            
            if pool.pool_type == CurvePoolType.STABLESWAP:
                # Stableswap: maintains close to 1:1 price
                return dx * 0.9999  # Nearly 1:1 with tiny slippage
            else:
                # Cryptoswap: normal AMM formula
                x = pool.balances[i]
                y = pool.balances[j]
                return (y * dx) / (x + dx)
            
        except Exception:
            return dx
    
    async def get_best_pool(self, token_in: str, token_out: str) -> Optional[CurvePool]:
        """Find best pool for swap"""
        try:
            candidates = []
            
            for pool in self.pools.values():
                if token_in in pool.coins and token_out in pool.coins:
                    candidates.append(pool)
            
            if not candidates:
                return None
            
            # Return pool with highest liquidity
            return max(candidates, key=lambda p: p.tvl_usd)
            
        except Exception as e:
            logger.error(f"Pool search error: {e}")
            return None
    
    async def register_metapool(self, metapool_address: str, base_pool_address: str) -> bool:
        """Register a metapool (pool that uses another pool as base)"""
        try:
            self.metapools[metapool_address] = base_pool_address
            logger.info(f"Registered metapool: {metapool_address}")
            return True
        except Exception as e:
            logger.error(f"Metapool registration error: {e}")
            return False
    
    async def get_gauge_apy(self, gauge_address: str) -> Optional[Dict[str, float]]:
        """Get current APY for a gauge"""
        try:
            if gauge_address not in self.gauges:
                return None
            
            gauge = self.gauges[gauge_address]
            
            return {
                'crv_apy': gauge.crv_apy,
                'bonus_apy': gauge.bonus_apy,
                'total_apy': gauge.total_apy,
                'tvl_usd': gauge.tvl_usd,
            }
            
        except Exception as e:
            logger.error(f"Gauge APY error: {e}")
            return None
    
    async def estimate_farming_rewards(self, gauge_address: str, liquidity_usd: float,
                                      days: int = 30) -> Optional[Dict]:
        """Estimate farming rewards"""
        try:
            if gauge_address not in self.gauges:
                return None
            
            gauge = self.gauges[gauge_address]
            
            # Estimate daily return
            daily_return = (gauge.total_apy / 365) * liquidity_usd
            
            # Project for period
            total_rewards = daily_return * days
            
            return {
                'gauge_address': gauge_address,
                'liquidity_usd': liquidity_usd,
                'period_days': days,
                'daily_reward_usd': daily_return,
                'total_reward_usd': total_rewards,
                'crv_reward': (daily_return * (gauge.crv_apy / gauge.total_apy)) * days,
                'bonus_reward': (daily_return * (gauge.bonus_apy / gauge.total_apy)) * days,
            }
            
        except Exception as e:
            logger.error(f"Reward estimation error: {e}")
            return None
    
    async def find_arbitrage_opportunities(self, max_opportunities: int = 10) -> List[Dict]:
        """Find potential arbitrage between Curve and other DEXes"""
        opportunities = []
        
        try:
            # Compare Curve prices with external data
            # This would integrate with WebSocket feeder for real-time comparison
            
            for pool in list(self.pools.values())[:5]:  # Check first 5 pools
                if len(pool.coins) >= 2:
                    token_in = pool.coins[0]
                    token_out = pool.coins[1]
                    
                    # Dummy opportunity
                    opportunity = {
                        'pool_address': pool.pool_address,
                        'token_in': token_in,
                        'token_out': token_out,
                        'curve_price': 1.0,
                        'market_price': 1.001,
                        'price_diff_percent': 0.1,
                        'estimated_profit': 100,
                    }
                    
                    opportunities.append(opportunity)
                
                if len(opportunities) >= max_opportunities:
                    break
            
            logger.info(f"Found {len(opportunities)} potential arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Arbitrage detection error: {e}")
            return []
    
    def get_handler_status(self) -> Dict[str, Any]:
        """Get handler status"""
        return {
            'connected': self.connected,
            'pools_loaded': len(self.pools),
            'gauges_loaded': len(self.gauges),
            'metapools_registered': len(self.metapools),
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    async def disconnect(self):
        """Disconnect from Curve"""
        self.connected = False
        logger.info("Disconnected from Curve")


# Global instance
_handler: Optional[CurveGaugeHandler] = None


async def init_curve_handler() -> CurveGaugeHandler:
    """Initialize global Curve handler"""
    global _handler
    _handler = CurveGaugeHandler()
    await _handler.connect()
    return _handler


async def get_curve_handler() -> CurveGaugeHandler:
    """Get global Curve handler"""
    global _handler
    if not _handler:
        _handler = await init_curve_handler()
    return _handler
