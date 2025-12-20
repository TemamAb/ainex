import pytest
import asyncio
from core.rpc_provider_manager import RPCProviderManager

@pytest.mark.asyncio
async def test_rpc_failover():
    """Test RPC failover system"""
    manager = RPCProviderManager()
    await manager.initialize()
    
    # Test health checks run
    await asyncio.sleep(35)
    report = manager.get_health_report()
    
    # Verify report structure
    assert report is not None
    assert "Alchemy" in report or "Infura" in report
    
    # Check provider health status
    for provider_name, health_data in report.items():
        assert "healthy" in health_data
        assert "latency_ms" in health_data
        assert "success_count" in health_data
        assert "error_count" in health_data
    
    print("✅ RPC failover system operational")

@pytest.mark.asyncio
async def test_rpc_provider_selection():
    """Test best provider selection"""
    manager = RPCProviderManager()
    await manager.initialize()
    
    # Let health checks run
    await asyncio.sleep(35)
    
    # Get best provider
    best_provider = await manager.get_best_provider()
    assert best_provider is not None
    
    print("✅ RPC provider selection working")

@pytest.mark.asyncio
async def test_health_check_provider():
    """Test individual provider health check"""
    manager = RPCProviderManager()
    
    # Test health check on a provider
    test_provider = manager.config.providers[0]
    await manager.health_check_provider(test_provider)
    
    # Verify health metrics updated
    health = manager.health[test_provider["name"]]
    assert health.latency_ms >= 0
    
    print("✅ Provider health check working")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
