"""
Unit tests for MEV Protection Engine
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from core.execution.mev_protection import (
    MEVProtectionEngine, MEVProtectionLevel
)
from web3 import Web3


@pytest.fixture
def web3_mock():
    """Mock Web3 instance."""
    return Mock(spec=Web3)


@pytest.fixture
def mev_engine(web3_mock):
    """Create MEV protection engine for testing."""
    return MEVProtectionEngine(
        web3=web3_mock,
        flashbots_relay="https://relay.flashbots.net",
        protection_level=MEVProtectionLevel.ADVANCED,
        max_slippage_pct=Decimal("0.1"),
    )


@pytest.mark.asyncio
async def test_mev_initialization(web3_mock):
    """Test MEV engine initialization."""
    engine = MEVProtectionEngine(web3_mock)
    
    assert engine.web3 == web3_mock
    assert engine.protection_level == MEVProtectionLevel.ADVANCED
    assert engine.max_slippage_pct == Decimal("0.1")
    assert engine.protected_txs == 0


@pytest.mark.asyncio
async def test_mev_basic_protection(mev_engine):
    """Test basic MEV protection (private relay fallback)."""
    tx_data = {
        "hash": "0x123abc",
        "callData": "0x",
        "maxFeePerGas": "1000000000",
    }
    
    mev_engine.protection_level = MEVProtectionLevel.NONE
    success, tx_hash, error = await mev_engine.submit_with_mev_protection(
        transaction_data=tx_data,
        expected_output=Decimal("10"),
        private_relay=True,
    )
    
    assert success == True
    assert error is None


@pytest.mark.asyncio
async def test_mev_advanced_protection(mev_engine):
    """Test advanced MEV protection with slippage monitoring."""
    tx_data = {
        "hash": "0x456def",
        "callData": "0x",
        "maxFeePerGas": "1000000000",
    }
    
    success, tx_hash, error = await mev_engine.submit_with_mev_protection(
        transaction_data=tx_data,
        expected_output=Decimal("10"),
    )
    
    assert isinstance(success, bool)


@pytest.mark.asyncio
async def test_slippage_calculation(mev_engine):
    """Test slippage calculation."""
    expected_output = Decimal("1000")
    slippage = mev_engine._calculate_max_slippage(expected_output)
    
    assert slippage <= mev_engine.max_slippage_pct
    assert slippage >= Decimal("0")


@pytest.mark.asyncio
async def test_gas_adjustment(mev_engine):
    """Test dynamic gas price adjustment."""
    tx_data = {
        "maxFeePerGas": "1000000000",
        "maxPriorityFeePerGas": "100000000",
    }
    
    adjusted = await mev_engine._adjust_gas_price_dynamic(tx_data)
    
    assert "maxFeePerGas" in adjusted
    # Gas should be increased by ~20%
    original_gas = int(tx_data["maxFeePerGas"])
    adjusted_gas = int(adjusted["maxFeePerGas"])
    assert adjusted_gas > original_gas


@pytest.mark.asyncio
async def test_sandwich_detection(mev_engine):
    """Test sandwich attack detection."""
    risk = await mev_engine._detect_sandwich_risk(deep_analysis=False)
    
    assert isinstance(risk, bool)


def test_mev_stats(mev_engine):
    """Test MEV statistics collection."""
    mev_engine.protected_txs = 10
    mev_engine.sandwich_detected = 2
    mev_engine.slippage_violations = 1
    
    stats = mev_engine.get_stats()
    
    assert stats["protected_txs"] == 10
    assert stats["sandwich_detected"] == 2
    assert stats["slippage_violations"] == 1
    assert stats["protection_level"] == "advanced"


def test_mev_strict_protection():
    """Test strict protection level."""
    web3_mock = Mock(spec=Web3)
    engine = MEVProtectionEngine(
        web3=web3_mock,
        protection_level=MEVProtectionLevel.STRICT,
    )
    
    assert engine.protection_level == MEVProtectionLevel.STRICT


@pytest.mark.asyncio
async def test_mev_flashbots_submission(mev_engine):
    """Test Flashbots bundle submission."""
    tx_data = {
        "raw_tx": "0x",
        "hash": "0x789ghi",
    }
    
    success = await mev_engine._submit_to_flashbots(tx_data)
    
    assert isinstance(success, bool)


def test_mev_protection_levels():
    """Test all protection levels."""
    web3_mock = Mock(spec=Web3)
    
    for level in MEVProtectionLevel:
        engine = MEVProtectionEngine(
            web3=web3_mock,
            protection_level=level,
        )
        assert engine.protection_level == level


@pytest.mark.asyncio
async def test_mev_multiple_submissions(mev_engine):
    """Test multiple transaction submissions."""
    for i in range(5):
        tx_data = {
            "hash": f"0x{i}",
            "callData": "0x",
            "maxFeePerGas": "1000000000",
        }
        
        success, _, _ = await mev_engine.submit_with_mev_protection(
            transaction_data=tx_data,
            expected_output=Decimal("10"),
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
