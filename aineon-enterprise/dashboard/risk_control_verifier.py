"""
Week 3: Risk Control Verification Layer
Verifies that all risk controls are actually enforced in the backend
"""

import asyncio
import logging
from typing import Tuple, Dict, Optional
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class RiskControlVerificationError(Exception):
    """Risk control verification failed"""
    pass


class RiskControlVerifier:
    """Verifies that risk controls are actually enforced"""
    
    def __init__(self, backend_api_url: str):
        self.backend_url = backend_api_url
        self.verification_results = {}
        self.last_verification = None
    
    async def verify_circuit_breaker(self) -> Tuple[bool, str, Dict]:
        """
        Verify circuit breaker is implemented and active.
        
        Returns:
            (is_verified, message, details)
        """
        try:
            logger.info("Verifying circuit breaker...")
            
            # 1. Check if circuit breaker exists
            response = await self._get_from_backend('/risk/circuit-breaker')
            
            if not response.get('exists'):
                msg = "Circuit breaker not implemented in backend"
                logger.error(f"❌ {msg}")
                return False, msg, {'exists': False}
            
            # 2. Check if it's active
            if not response.get('is_active'):
                msg = "Circuit breaker exists but is not active"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # 3. Check if it's being monitored
            if not response.get('is_monitored'):
                msg = "Circuit breaker not being monitored"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            msg = "Circuit breaker verified and active"
            logger.info(f"✅ {msg}")
            return True, msg, response
        
        except Exception as e:
            logger.error(f"Circuit breaker verification error: {e}")
            return False, f"Verification error: {e}", {}
    
    async def verify_daily_loss_limit(self) -> Tuple[bool, str, Dict]:
        """
        Verify daily loss limit is enforced.
        
        Returns:
            (is_verified, message, details)
        """
        try:
            logger.info("Verifying daily loss limit...")
            
            response = await self._get_from_backend('/risk/daily-loss-limit')
            
            # Check if enforced
            if not response.get('enforced'):
                msg = "Daily loss limit not enforced"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check if limit is configured
            limit = response.get('limit_usd')
            if limit is None or limit <= 0:
                msg = "Daily loss limit not configured"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check if current loss is tracked
            current_loss = response.get('current_loss_usd')
            if current_loss is None:
                msg = "Current daily loss not tracked"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check if we have enforcement evidence
            if not response.get('enforcement_evidence'):
                msg = "No evidence of loss limit enforcement"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            msg = f"Daily loss limit enforced (${limit}, current: ${current_loss})"
            logger.info(f"✅ {msg}")
            return True, msg, response
        
        except Exception as e:
            logger.error(f"Daily loss limit verification error: {e}")
            return False, f"Verification error: {e}", {}
    
    async def verify_position_size_limit(self) -> Tuple[bool, str, Dict]:
        """
        Verify max position size is enforced.
        
        Returns:
            (is_verified, message, details)
        """
        try:
            logger.info("Verifying position size limit...")
            
            response = await self._get_from_backend('/risk/position-size-limit')
            
            # Check if enforced
            if not response.get('enforced'):
                msg = "Position size limit not enforced"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check if limit is configured
            max_size = response.get('max_position_usd')
            if max_size is None or max_size <= 0:
                msg = "Position size limit not configured"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check current position size
            current_size = response.get('current_position_usd', 0)
            if current_size > max_size:
                msg = f"Current position (${current_size}) exceeds limit (${max_size})"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            msg = f"Position size limit enforced (max: ${max_size}, current: ${current_size})"
            logger.info(f"✅ {msg}")
            return True, msg, response
        
        except Exception as e:
            logger.error(f"Position size limit verification error: {e}")
            return False, f"Verification error: {e}", {}
    
    async def verify_etherscan_requirement(self) -> Tuple[bool, str, Dict]:
        """
        Verify profits are verified on Etherscan.
        
        Returns:
            (is_verified, message, details)
        """
        try:
            logger.info("Verifying Etherscan requirement...")
            
            response = await self._get_from_backend('/profit/etherscan-verification')
            
            # Check if enabled
            if not response.get('enabled'):
                msg = "Etherscan verification not enabled"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check if API key is configured
            if not response.get('api_key_configured'):
                msg = "Etherscan API key not configured"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            # Check verification stats
            verified_count = response.get('verified_count', 0)
            total_count = response.get('total_count', 0)
            
            if total_count > 0 and verified_count == 0:
                msg = f"0/{total_count} profits verified on Etherscan"
                logger.error(f"❌ {msg}")
                return False, msg, response
            
            verification_rate = (verified_count / total_count * 100) if total_count > 0 else 100
            msg = f"Etherscan verification enabled ({verified_count}/{total_count} verified, {verification_rate:.1f}%)"
            logger.info(f"✅ {msg}")
            return True, msg, response
        
        except Exception as e:
            logger.error(f"Etherscan verification error: {e}")
            return False, f"Verification error: {e}", {}
    
    async def verify_all_controls(self) -> Dict[str, Tuple[bool, str, Dict]]:
        """
        Verify all risk controls.
        
        Returns:
            Dictionary of all verification results
        """
        logger.info("Verifying all risk controls...")
        
        results = {
            'circuit_breaker': await self.verify_circuit_breaker(),
            'daily_loss_limit': await self.verify_daily_loss_limit(),
            'position_size_limit': await self.verify_position_size_limit(),
            'etherscan_requirement': await self.verify_etherscan_requirement(),
        }
        
        # Count verified controls
        verified = sum(1 for v in results.values() if v[0])
        total = len(results)
        
        logger.info(f"Risk controls verification: {verified}/{total} verified")
        self.last_verification = datetime.now()
        
        return results
    
    def get_enforcement_status(self, results: Dict[str, Tuple[bool, str, Dict]]) -> str:
        """
        Get overall enforcement status.
        
        Args:
            results: Results from verify_all_controls()
            
        Returns:
            Status string
        """
        verified = sum(1 for v in results.values() if v[0])
        total = len(results)
        
        if verified == total:
            return "✅ ALL CONTROLS ENFORCED"
        elif verified >= total * 0.75:
            return "⚠️ PARTIAL ENFORCEMENT"
        else:
            return "❌ CONTROLS NOT ENFORCED"
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _get_from_backend(self, endpoint: str) -> Dict:
        """
        Fetch from backend API.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response JSON
        """
        try:
            url = f"{self.backend_url}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        logger.error(f"Backend API error: {resp.status}")
                        return {}
        
        except asyncio.TimeoutError:
            logger.error(f"Backend API timeout on {endpoint}")
            return {}
        except Exception as e:
            logger.error(f"Backend API error: {e}")
            return {}
    
    async def test_circuit_breaker(self) -> bool:
        """
        Test if circuit breaker actually halts trading.
        
        Returns:
            True if circuit breaker halts trading
        """
        try:
            # Send a large loss scenario and see if trading halts
            response = await self._get_from_backend('/risk/test-circuit-breaker')
            return response.get('halted', False)
        except Exception as e:
            logger.error(f"Circuit breaker test failed: {e}")
            return False


class EnforcementValidator:
    """Validates that enforcement actually works"""
    
    def __init__(self):
        self.enforcement_tests = {}
    
    async def validate_loss_limit_enforcement(self, 
                                             backend_url: str,
                                             test_loss_amount: float) -> Tuple[bool, str]:
        """
        Validate that loss limit actually stops trading.
        
        Args:
            backend_url: Backend API URL
            test_loss_amount: Amount to test with
            
        Returns:
            (is_enforced, message)
        """
        try:
            # Try to execute trade that would exceed loss limit
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/risk/test-loss-limit",
                    json={'test_loss': test_loss_amount},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('trade_blocked'):
                            return True, "Loss limit enforcement verified"
                        else:
                            return False, "Trade was not blocked by loss limit"
                    else:
                        return False, f"Backend error: {resp.status}"
        
        except Exception as e:
            logger.error(f"Loss limit enforcement test error: {e}")
            return False, f"Test error: {e}"
    
    async def validate_position_limit_enforcement(self,
                                                 backend_url: str,
                                                 test_position_size: float) -> Tuple[bool, str]:
        """
        Validate that position size limit actually stops trades.
        
        Returns:
            (is_enforced, message)
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/risk/test-position-limit",
                    json={'test_position': test_position_size},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('trade_blocked'):
                            return True, "Position limit enforcement verified"
                        else:
                            return False, "Trade was not blocked by position limit"
                    else:
                        return False, f"Backend error: {resp.status}"
        
        except Exception as e:
            logger.error(f"Position limit enforcement test error: {e}")
            return False, f"Test error: {e}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        verifier = RiskControlVerifier("http://localhost:8080")
        results = await verifier.verify_all_controls()
        status = verifier.get_enforcement_status(results)
        print(f"\n{status}")
        for control, (verified, msg, _) in results.items():
            symbol = "✅" if verified else "❌"
            print(f"  {symbol} {control}: {msg}")
    
    asyncio.run(test())
