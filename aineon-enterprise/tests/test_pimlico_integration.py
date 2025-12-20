"""
Test Pimlico Bundler Integration
Tests for UserOperation submission and bundler communication
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from datetime import datetime

from core.bundler.pimlico_bundler_client import (
    PimlicoBundlerClient,
    BundlerConfig,
    UserOperation,
    initialize_pimlico_bundler
)
from core.bundler.bundler_metrics import BundlerMetrics, initialize_metrics


# Fixtures

@pytest.fixture
async def bundler_client():
    """Create bundler client for testing"""
    config = BundlerConfig(request_timeout=10)
    client = PimlicoBundlerClient(config)
    await client.initialize()
    yield client
    await client.shutdown()


@pytest.fixture
def sample_user_op() -> UserOperation:
    """Sample UserOperation for testing"""
    return UserOperation(
        sender="0x1234567890123456789012345678901234567890",
        nonce=0,
        initCode="0x",
        callData="0xb61d27f6",
        callGasLimit=100000,
        verificationGasLimit=100000,
        preVerificationGas=25000,
        maxFeePerGas=100000000,
        maxPriorityFeePerGas=10000000,
        paymasterAndData="0x",
        signature="0x"
    )


@pytest.fixture
def metrics():
    """Create metrics tracker"""
    return initialize_metrics()


# Tests

class TestPimlicoBundlerClient:
    """Test PimlicoBundlerClient functionality"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, bundler_client):
        """Test bundler client initialization"""
        assert bundler_client is not None
        assert len(bundler_client.providers) == 3
        assert bundler_client.session is not None
    
    @pytest.mark.asyncio
    async def test_send_user_operation_success(self, bundler_client, sample_user_op):
        """Test successful UserOperation submission"""
        expected_hash = "0xabcd1234" * 16  # 64 hex chars
        
        # Mock the POST request
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": expected_hash
        }
        
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            success, user_op_hash = await bundler_client.send_user_operation(sample_user_op)
            
            assert success is True
            assert user_op_hash == expected_hash
            assert bundler_client.metrics["successful_submissions"] == 1
    
    @pytest.mark.asyncio
    async def test_send_user_operation_failure(self, bundler_client, sample_user_op):
        """Test failed UserOperation submission"""
        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32603,
                "message": "Internal error"
            }
        }
        
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            success, user_op_hash = await bundler_client.send_user_operation(sample_user_op)
            
            assert success is False
            assert user_op_hash == ""
            assert bundler_client.metrics["failed_submissions"] > 0
    
    @pytest.mark.asyncio
    async def test_send_user_operation_with_retries(self, bundler_client, sample_user_op):
        """Test UserOperation submission with exponential backoff"""
        expected_hash = "0xabcd1234" * 16
        
        # First two calls fail, third succeeds
        responses = [
            {"error": {"code": -32603, "message": "Temporarily unavailable"}},
            {"error": {"code": -32603, "message": "Temporarily unavailable"}},
            {"result": expected_hash}
        ]
        
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = responses
            
            # Mock sleep to speed up test
            with patch('asyncio.sleep', new_callable=AsyncMock):
                success, user_op_hash = await bundler_client.send_user_operation(sample_user_op)
            
            assert success is True
            assert user_op_hash == expected_hash
            assert bundler_client.metrics["total_retries"] >= 2
    
    @pytest.mark.asyncio
    async def test_get_user_operation_receipt(self, bundler_client):
        """Test getting UserOperation receipt"""
        user_op_hash = "0xabcd1234" * 16
        
        mock_receipt = {
            "userOpHash": user_op_hash,
            "entryPoint": "0x5FF137D4b0FDCD49DcA30c7B8b3D6C69D5EE1b23",
            "sender": "0x1234567890123456789012345678901234567890",
            "nonce": 0,
            "paymaster": "0x",
            "actualGasUsed": 75000,
            "actualGasCost": "7500000000000",
            "success": True,
            "logs": [],
            "receipt": {
                "transactionHash": "0xabc123",
                "blockNumber": 19000000,
                "blockHash": "0xdef456",
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x5FF137D4b0FDCD49DcA30c7B8b3D6C69D5EE1b23",
                "gasUsed": 100000,
                "status": 1
            }
        }
        
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"result": mock_receipt}
            
            receipt = await bundler_client.get_user_operation_receipt(user_op_hash)
            
            assert receipt is not None
            assert receipt["userOpHash"] == user_op_hash
            assert receipt["success"] is True
    
    @pytest.mark.asyncio
    async def test_wait_for_inclusion_success(self, bundler_client):
        """Test waiting for bundle inclusion"""
        user_op_hash = "0xabcd1234" * 16
        
        # Receipt appears after second poll
        receipts = [
            None,  # First poll: not included yet
            {
                "userOpHash": user_op_hash,
                "success": True,
                "receipt": {"transactionHash": "0xabc123"}
            }
        ]
        
        with patch.object(bundler_client, 'get_user_operation_receipt', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = receipts
            
            success, receipt = await bundler_client.wait_for_inclusion(
                user_op_hash,
                timeout=30,
                poll_interval=0.1
            )
            
            assert success is True
            assert receipt is not None
            assert receipt["userOpHash"] == user_op_hash
    
    @pytest.mark.asyncio
    async def test_wait_for_inclusion_timeout(self, bundler_client):
        """Test timeout waiting for bundle inclusion"""
        user_op_hash = "0xabcd1234" * 16
        
        with patch.object(bundler_client, 'get_user_operation_receipt', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            success, receipt = await bundler_client.wait_for_inclusion(
                user_op_hash,
                timeout=0.5,  # Very short timeout
                poll_interval=0.1
            )
            
            assert success is False
            assert receipt is None
    
    @pytest.mark.asyncio
    async def test_estimate_user_operation_gas(self, bundler_client, sample_user_op):
        """Test gas estimation"""
        gas_estimate = {
            "callGasLimit": "120000",
            "verificationGasLimit": "100000",
            "preVerificationGas": "30000"
        }
        
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"result": gas_estimate}
            
            result = await bundler_client.estimate_user_operation_gas(sample_user_op)
            
            assert result is not None
            assert result["callGasLimit"] == "120000"
            assert result["verificationGasLimit"] == "100000"
    
    @pytest.mark.asyncio
    async def test_provider_failover(self, bundler_client):
        """Test automatic provider failover"""
        initial_provider = bundler_client.providers[bundler_client.current_provider_idx]["name"]
        
        bundler_client._switch_provider()
        new_provider = bundler_client.providers[bundler_client.current_provider_idx]["name"]
        
        assert initial_provider != new_provider
    
    def test_provider_metrics_update(self, bundler_client):
        """Test provider metrics tracking"""
        bundler_client._update_provider_metrics("pimlico", success=True)
        bundler_client._update_provider_metrics("pimlico", success=True)
        bundler_client._update_provider_metrics("pimlico", success=False)
        
        assert bundler_client.metrics["provider_success_rates"]["pimlico"] > 0
    
    def test_get_stats(self, bundler_client):
        """Test metrics reporting"""
        bundler_client.metrics["total_submissions"] = 100
        bundler_client.metrics["successful_submissions"] = 95
        bundler_client.metrics["failed_submissions"] = 5
        
        stats = bundler_client.get_stats()
        
        assert stats["total_submissions"] == 100
        assert stats["successful_submissions"] == 95
        assert stats["success_rate"] == 95.0


class TestBundlerMetrics:
    """Test BundlerMetrics functionality"""
    
    def test_metrics_initialization(self, metrics):
        """Test metrics initialization"""
        assert metrics is not None
        assert len(metrics.metrics) == 0
    
    def test_record_submission(self, metrics):
        """Test recording a submission"""
        metrics.record_submission(
            provider="pimlico",
            user_op_hash="0xabcd1234",
            success=True,
            inclusion_time=1.5,
            profit=1.2
        )
        
        assert len(metrics.metrics) == 1
        assert metrics.metrics[0].success is True
        assert metrics.metrics[0].inclusion_time == 1.5
    
    def test_provider_stats(self, metrics):
        """Test provider statistics"""
        metrics.record_submission("pimlico", "0x1", True, 1.0)
        metrics.record_submission("pimlico", "0x2", True, 1.2)
        metrics.record_submission("pimlico", "0x3", False)
        
        stats = metrics.get_provider_stats("pimlico")
        
        assert stats["total_submissions"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert "66.67" in stats["success_rate"]  # ~66.67%
    
    def test_all_stats(self, metrics):
        """Test aggregated statistics"""
        metrics.record_submission("pimlico", "0x1", True, 1.0, profit=1.0)
        metrics.record_submission("gelato", "0x2", True, 1.5, profit=1.5)
        metrics.record_submission("pimlico", "0x3", False)
        
        stats = metrics.get_all_stats()
        
        assert stats["total_submissions"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
    
    def test_recent_submissions(self, metrics):
        """Test recent submission history"""
        for i in range(15):
            metrics.record_submission(
                "pimlico",
                f"0x{i:04x}",
                success=i % 2 == 0
            )
        
        recent = metrics.get_recent_submissions(limit=10)
        
        assert len(recent) == 10
        assert recent[0]["user_op_hash"] == "0x000e"  # Most recent
    
    def test_health_check(self, metrics):
        """Test health check"""
        # Add 100 submissions with 85% success rate
        for i in range(100):
            metrics.record_submission(
                "pimlico",
                f"0x{i:04x}",
                success=i % 100 < 85,
                inclusion_time=1.5
            )
        
        health = metrics.health_check()
        
        assert "healthy" in health["status"]
        assert "85" in health["recent_success_rate"]
    
    def test_trending_success_rate(self, metrics):
        """Test success rate trends"""
        # Add 50 submissions with improving success rate
        for i in range(50):
            success = i > 25  # 0% first 25, then 100%
            metrics.record_submission("pimlico", f"0x{i:04x}", success)
        
        trends = metrics.get_trending_success_rate(periods=5)
        
        assert len(trends) > 0
        # Later periods should have higher success rates
        assert trends[-1] > trends[0]


class TestInitialization:
    """Test initialization functions"""
    
    @pytest.mark.asyncio
    async def test_initialize_bundler(self):
        """Test bundler initialization"""
        client = await initialize_pimlico_bundler()
        
        assert client is not None
        assert client.session is not None
        
        await client.shutdown()
    
    def test_initialize_metrics(self):
        """Test metrics initialization"""
        metrics = initialize_metrics()
        
        assert metrics is not None
        assert len(metrics.metrics) == 0


# Integration tests

class TestIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_submission_flow(self, bundler_client, sample_user_op, metrics):
        """Test complete submission flow"""
        expected_hash = "0x" + "a" * 64
        
        # Mock submission
        with patch.object(bundler_client, '_post_request', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = [
                {"result": expected_hash},  # send_user_operation
                {"result": {"userOpHash": expected_hash, "success": True}}  # get receipt
            ]
            
            # Record metrics
            success, user_op_hash = await bundler_client.send_user_operation(sample_user_op)
            assert success
            
            # Record in metrics
            metrics.record_submission(
                provider="pimlico",
                user_op_hash=user_op_hash,
                success=True,
                inclusion_time=1.2,
                profit=1.5
            )
            
            # Verify metrics
            stats = metrics.get_all_stats()
            assert stats["total_submissions"] == 1
            assert "1.5 ETH" in stats["total_profit"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
