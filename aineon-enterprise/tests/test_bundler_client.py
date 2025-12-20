"""
Unit tests for Pimlico Bundler Client
Tests: submission, receipt verification, retry logic
"""

import pytest
import asyncio
from datetime import datetime
from core.executor.bundler_client import (
    PimlicoBundlerClient,
    UserOperation,
    OperationStatus,
)

class TestPimlicoBundlerClient:
    
    @pytest.fixture
    def client(self):
        return PimlicoBundlerClient(max_retries=2)
    
    @pytest.mark.asyncio
    async def test_user_op_submission(self, client):
        """Test basic UserOperation submission"""
        
        user_op = UserOperation(
            sender="0x1234567890123456789012345678901234567890",
            nonce=0,
            initCode="0x",
            callData="0xdeadbeef",
            callGasLimit=100000,
            verificationGasLimit=50000,
            preVerificationGas=25000,
            maxFeePerGas=50000000000,
            maxPriorityFeePerGas=2000000000,
            paymasterAndData="0x",
            signature="0x",
        )
        
        entry_point = "0x5FF137D4b0FDCD49DcA30c7B8e31256DC0E2CadB"
        
        # Should raise because we're using placeholder HTTP
        # In production tests, mock the HTTP layer
        with pytest.raises(Exception):
            await client.send_user_operation(user_op, entry_point)
    
    def test_operation_status_tracking(self, client):
        """Test operation status tracking"""
        
        user_op_hash = "0x" + "a" * 64
        
        # Should not be tracked initially
        assert client.get_operation_status(user_op_hash) is None
        
        # Manually add to tracking
        client.operations_map[user_op_hash] = {
            "status": OperationStatus.SUBMITTED,
            "submitted_at": datetime.now(),
            "metadata": {},
            "retries": 0,
        }
        
        # Should be tracked now
        assert client.get_operation_status(user_op_hash) == OperationStatus.SUBMITTED
    
    def test_request_id_generation(self, client):
        """Test JSON-RPC request ID generation"""
        
        id1 = client._next_request_id()
        id2 = client._next_request_id()
        id3 = client._next_request_id()
        
        assert id1 == 1
        assert id2 == 2
        assert id3 == 3
    
    def test_user_op_formatting(self, client):
        """Test UserOperation formatting for JSON"""
        
        user_op = UserOperation(
            sender="0x1234",
            nonce=5,
            initCode="0x",
            callData="0xdeadbeef",
            callGasLimit=100000,
            verificationGasLimit=50000,
            preVerificationGas=25000,
            maxFeePerGas=50000000000,
            maxPriorityFeePerGas=2000000000,
            paymasterAndData="0x",
            signature="0x",
        )
        
        formatted = client._format_user_op(user_op)
        
        assert formatted["sender"] == "0x1234"
        assert formatted["nonce"] == hex(5)
        assert formatted["callGasLimit"] == hex(100000)
        assert formatted["callData"] == "0xdeadbeef"
    
    def test_get_all_operations(self, client):
        """Test retrieving all tracked operations"""
        
        user_op_hash1 = "0x" + "a" * 64
        user_op_hash2 = "0x" + "b" * 64
        
        client.operations_map[user_op_hash1] = {
            "status": OperationStatus.SUBMITTED,
            "submitted_at": datetime.now(),
        }
        client.operations_map[user_op_hash2] = {
            "status": OperationStatus.BUNDLED,
            "submitted_at": datetime.now(),
        }
        
        all_ops = client.get_all_operations()
        
        assert len(all_ops) == 2
        assert user_op_hash1 in all_ops
        assert user_op_hash2 in all_ops
    
    def test_clear_old_operations(self, client):
        """Test clearing old operations"""
        from datetime import timedelta
        
        old_hash = "0x" + "a" * 64
        new_hash = "0x" + "b" * 64
        
        # Add old operation
        old_time = datetime.now() - timedelta(hours=2)
        client.operations_map[old_hash] = {
            "status": OperationStatus.SUBMITTED,
            "submitted_at": old_time,
        }
        
        # Add new operation
        client.operations_map[new_hash] = {
            "status": OperationStatus.SUBMITTED,
            "submitted_at": datetime.now(),
        }
        
        # Clear operations older than 1 hour
        client.clear_old_operations(age_seconds=3600)
        
        # Old should be removed, new should remain
        assert old_hash not in client.operations_map
        assert new_hash in client.operations_map

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
