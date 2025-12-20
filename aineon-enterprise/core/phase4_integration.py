import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta

from core.phase4_orchestrator import Phase4Orchestrator

logger = logging.getLogger(__name__)


class Phase4IntegrationManager:
    """Integrates Phase 4 intelligence into main AINEON system"""
    
    def __init__(self, main_orchestrator=None, config: Dict = None):
        self.main_orchestrator = main_orchestrator
        self.config = config or {}
        
        # Initialize Phase 4
        self.phase4 = Phase4Orchestrator(self.config)
        self.phase4_enabled = False
        
        # Integration metrics
        self.integration_stats = {
            'opportunities_processed': 0,
            'trades_executed': 0,
            'phase4_decisions': 0,
            'fallback_decisions': 0
        }
        
        self.integration_history = []
    
    async def initialize_phase4(self) -> Dict:
        """Initialize Phase 4 integration"""
        logger.info("Initializing Phase 4 integration")
        
        result = await self.phase4.enable_phase4()
        self.phase4_enabled = True
        
        return {
            'status': 'phase4_initialized',
            'timestamp': datetime.now().isoformat(),
            'phase4_result': result
        }
    
    async def process_with_phase4(self, opportunity: Dict, 
                                 use_fallback: bool = False) -> Dict:
        """Process opportunity through Phase 4 intelligence"""
        
        if not self.phase4_enabled or use_fallback:
            # Use Phase 1-3 logic
            return await self._phase1_3_processing(opportunity)
        
        try:
            # Process through Phase 4
            decision = await self.phase4.process_opportunity(opportunity)
            
            self.integration_stats['phase4_decisions'] += 1
            
            return {
                'source': 'phase4',
                'decision': decision,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Phase 4 processing failed: {e}, falling back to Phase 1-3")
            self.integration_stats['fallback_decisions'] += 1
            return await self._phase1_3_processing(opportunity)
    
    async def _phase1_3_processing(self, opportunity: Dict) -> Dict:
        """Fallback to Phase 1-3 processing"""
        if self.main_orchestrator and hasattr(self.main_orchestrator, 'process_opportunity'):
            return await self.main_orchestrator.process_opportunity(opportunity)
        
        # Minimal fallback decision
        return {
            'source': 'phase1_3_fallback',
            'strategy_id': 0,
            'confidence': 0.7,
            'timestamp': datetime.now().isoformat()
        }
    
    async def execute_with_phase4(self, decision: Dict, 
                                 execution_fn: Callable) -> Dict:
        """Execute decision and track Phase 4 learning"""
        
        # Execute trade
        result = await execution_fn(decision)
        
        self.integration_stats['trades_executed'] += 1
        
        # If Phase 4 was used, record experience
        if decision.get('source') == 'phase4' and self.phase4_enabled:
            # The Phase 4 orchestrator handles learning internally
            # Just ensure result is tracked
            logger.info(f"Phase 4 trade executed: profit={result.get('profit', 0)}")
        
        return result
    
    async def hourly_optimization(self) -> Dict:
        """Run hourly optimization for Phase 4"""
        
        if not self.phase4_enabled:
            return {"status": "phase4_disabled"}
        
        logger.info("Running Phase 4 hourly optimization")
        
        hourly_result = await self.phase4.hourly_cycle()
        
        self.integration_history.append(hourly_result)
        
        return {
            'status': 'hourly_optimization_complete',
            'timestamp': datetime.now().isoformat(),
            'phase4_result': hourly_result
        }
    
    async def health_check(self) -> Dict:
        """Check Phase 4 health"""
        
        if not self.phase4_enabled:
            return {
                'phase4_enabled': False,
                'status': 'disabled',
                'recommendation': 'enable_phase4'
            }
        
        status = self.phase4.get_system_status()
        
        health = {
            'phase4_enabled': True,
            'status': status['status'],
            'timestamp': datetime.now().isoformat(),
            'components_healthy': self._check_component_health(status),
            'integration_stats': self.integration_stats
        }
        
        return health
    
    def _check_component_health(self, status: Dict) -> Dict:
        """Check health of Phase 4 components"""
        
        components = status.get('components', {})
        
        health = {
            'rl_model': bool(components.get('rl_model')),
            'learning_engine': bool(components.get('learning_engine')),
            'transformer': bool(components.get('transformer')),
            'gpu_acceleration': bool(components.get('acceleration')),
            'all_healthy': True
        }
        
        # Check critical metrics
        if components.get('acceleration', {}).get('avg_gpu_inference_ms', 1000) > 1:
            health['all_healthy'] = False
        
        return health
    
    async def adaptive_enable_disable(self) -> Dict:
        """Adaptively enable/disable Phase 4 based on performance"""
        
        health = await self.health_check()
        
        # Decision logic
        decision = {
            'timestamp': datetime.now().isoformat(),
            'previous_state': 'enabled' if self.phase4_enabled else 'disabled',
            'action': 'no_change'
        }
        
        # Check if should disable
        if self.phase4_enabled:
            components = health.get('components_healthy', {})
            if not components.get('all_healthy', False):
                decision['action'] = 'disable_phase4'
                decision['reason'] = 'Components not healthy'
                await self.phase4.disable_phase4()
                self.phase4_enabled = False
        
        # Check if should enable
        else:
            if health.get('components_healthy', {}).get('all_healthy', False):
                decision['action'] = 'enable_phase4'
                decision['reason'] = 'All components healthy'
                await self.phase4.enable_phase4()
                self.phase4_enabled = True
        
        decision['new_state'] = 'enabled' if self.phase4_enabled else 'disabled'
        
        return decision
    
    def get_integration_stats(self) -> Dict:
        """Get Phase 4 integration statistics"""
        
        return {
            'timestamp': datetime.now().isoformat(),
            'phase4_enabled': self.phase4_enabled,
            'integration_stats': self.integration_stats,
            'phase4_status': self.phase4.get_system_status() if self.phase4_enabled else None,
            'integration_history_size': len(self.integration_history)
        }
    
    async def shutdown(self):
        """Shutdown Phase 4"""
        logger.info("Shutting down Phase 4 integration")
        await self.phase4.shutdown()
        self.phase4_enabled = False


# Utility functions for main system integration

async def enhance_with_phase4(orchestrator, opportunity: Dict, 
                             execution_fn: Callable) -> Dict:
    """Convenience function to enhance opportunity with Phase 4"""
    
    # Create integration manager if not exists
    if not hasattr(orchestrator, '_phase4_manager'):
        orchestrator._phase4_manager = Phase4IntegrationManager(orchestrator)
        await orchestrator._phase4_manager.initialize_phase4()
    
    manager = orchestrator._phase4_manager
    
    # Process opportunity
    decision = await manager.process_with_phase4(opportunity)
    
    # Execute
    result = await manager.execute_with_phase4(decision, execution_fn)
    
    return {
        'decision': decision,
        'execution_result': result
    }


async def get_phase4_metrics(orchestrator) -> Dict:
    """Get Phase 4 metrics from orchestrator"""
    
    if not hasattr(orchestrator, '_phase4_manager'):
        return {"status": "phase4_not_initialized"}
    
    manager = orchestrator._phase4_manager
    return manager.get_integration_stats()


async def trigger_phase4_optimization(orchestrator) -> Dict:
    """Trigger hourly Phase 4 optimization"""
    
    if not hasattr(orchestrator, '_phase4_manager'):
        return {"status": "phase4_not_initialized"}
    
    manager = orchestrator._phase4_manager
    return await manager.hourly_optimization()
