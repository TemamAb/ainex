"""
Validation Script - Verify all critical components are implemented
Run this to validate the AINEON system is functional
"""

import sys
import os
from decimal import Decimal

def validate_imports():
    """Validate all required modules can be imported"""
    print("\n" + "="*80)
    print("VALIDATING IMPORTS")
    print("="*80)
    
    try:
        print("✓ Importing risk_manager...", end=" ")
        from risk_manager import RiskManager
        print("SUCCESS")
        
        print("✓ Importing profit_manager...", end=" ")
        from profit_manager import ProfitManager
        print("SUCCESS")
        
        print("✓ Importing tier_scanner...", end=" ")
        from tier_scanner import MarketScanner
        print("SUCCESS")
        
        print("✓ Importing tier_orchestrator...", end=" ")
        from tier_orchestrator import Orchestrator
        print("SUCCESS")
        
        print("✓ Importing tier_executor...", end=" ")
        from tier_executor import MultiStrategyExecutionEngine
        print("SUCCESS")
        
        return True
    except ImportError as e:
        print(f"FAILED: {e}")
        return False


def validate_risk_manager():
    """Validate RiskManager implementation"""
    print("\n" + "="*80)
    print("VALIDATING RISK MANAGER")
    print("="*80)
    
    try:
        from risk_manager import RiskManager
        
        rm = RiskManager(max_daily_loss_usd=1_500_000)
        
        # Test 1: Can execute under limits
        print("✓ Test 1: Can execute under limits...", end=" ")
        can_execute, reason = rm.can_execute_trade("WETH/USDC", Decimal("1_000_000"), 0.9)
        assert can_execute is True
        print("PASS")
        
        # Test 2: Reject oversized position
        print("✓ Test 2: Reject oversized position...", end=" ")
        can_execute, reason = rm.can_execute_trade("WETH/USDC", Decimal("20_000_000"), 0.9)
        assert can_execute is False
        print("PASS")
        
        # Test 3: Position tracking
        print("✓ Test 3: Position tracking...", end=" ")
        rm.add_position("pos_1", "WETH/USDC", Decimal("1_000_000"), 2000.0)
        assert len(rm.active_positions) == 1
        print("PASS")
        
        # Test 4: P&L calculation
        print("✓ Test 4: P&L calculation...", end=" ")
        rm.close_position("pos_1", 2100.0, Decimal("50_000"))
        assert rm.daily_pnl == Decimal("50_000")
        print("PASS")
        
        # Test 5: Daily loss cap
        print("✓ Test 5: Daily loss cap enforcement...", end=" ")
        rm.daily_pnl = Decimal("-1_500_001")
        can_execute, reason = rm.can_execute_trade("WETH/USDC", Decimal("1_000_000"), 0.9)
        assert can_execute is False
        assert rm.circuit_breaker_triggered
        print("PASS")
        
        # Test 6: Risk metrics reporting
        print("✓ Test 6: Risk metrics reporting...", end=" ")
        metrics = rm.get_risk_metrics()
        assert "active_positions" in metrics
        assert "daily_pnl_usd" in metrics
        assert "circuit_breaker_triggered" in metrics
        print("PASS")
        
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_profit_manager():
    """Validate ProfitManager implementation"""
    print("\n" + "="*80)
    print("VALIDATING PROFIT MANAGER")
    print("="*80)
    
    try:
        from profit_manager import ProfitManager
        from unittest.mock import Mock
        
        # Create mock Web3
        mock_w3 = Mock()
        mock_w3.eth.get_balance.return_value = int(10e18)
        mock_w3.from_wei.return_value = 10.0
        mock_w3.eth.chain_id = 1
        mock_w3.to_checksum_address.side_effect = lambda x: x
        
        # Test initialization (skip wallet verification for mock)
        print("✓ Test 1: Initialization...", end=" ")
        pm = ProfitManager(mock_w3, "0x1234", "0x5678")
        print("PASS")
        
        # Test 2: Record trade
        print("✓ Test 2: Record trade...", end=" ")
        pm.record_trade("sig_1", Decimal("0.5"), "0xhash1", "CONFIRMED")
        assert pm.accumulated_eth == Decimal("0.5")
        print("PASS")
        
        # Test 3: Multiple trades
        print("✓ Test 3: Multiple trades...", end=" ")
        pm.record_trade("sig_2", Decimal("0.25"), "0xhash2", "CONFIRMED")
        assert pm.accumulated_eth == Decimal("0.75")
        assert len(pm.transaction_history) == 2
        print("PASS")
        
        # Test 4: Get stats
        print("✓ Test 4: Get stats...", end=" ")
        stats = pm.get_stats()
        assert stats["accumulated_eth"] == 0.75
        assert stats["transaction_count"] == 2
        print("PASS")
        
        # Test 5: Transaction history
        print("✓ Test 5: Transaction history...", end=" ")
        history = pm.get_transaction_history(limit=10)
        assert len(history) == 2
        print("PASS")
        
        # Test 6: Auto-transfer setup
        print("✓ Test 6: Auto-transfer setup...", end=" ")
        pm.set_auto_transfer("0xrecipient", 10.0)
        assert pm.auto_transfer_enabled is True
        print("PASS")
        
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_system_integration():
    """Validate unified system integration"""
    print("\n" + "="*80)
    print("VALIDATING SYSTEM INTEGRATION")
    print("="*80)
    
    try:
        print("✓ Test 1: RiskManager in unified_system...", end=" ")
        # Check that unified_system imports RiskManager
        with open("unified_system.py", "r") as f:
            content = f.read()
            assert "from risk_manager import RiskManager" in content
            assert "self.risk_manager = RiskManager" in content
        print("PASS")
        
        print("✓ Test 2: Risk checking in executor...", end=" ")
        # Check that executor checks risk limits
        with open("unified_system.py", "r") as f:
            content = f.read()
            assert "can_execute, reason = self.risk_manager.can_execute_trade" in content
            assert "if not can_execute" in content
        print("PASS")
        
        print("✓ Test 3: Profit tracking in executor...", end=" ")
        # Check that executor tracks profits
        with open("unified_system.py", "r") as f:
            content = f.read()
            assert "self.profit_manager.record_trade" in content
        print("PASS")
        
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validations"""
    print("\n" + "="*80)
    print("AINEON IMPLEMENTATION VALIDATION")
    print("="*80)
    print(f"Working directory: {os.getcwd()}")
    
    results = []
    
    results.append(("Imports", validate_imports()))
    results.append(("Risk Manager", validate_risk_manager()))
    results.append(("Profit Manager", validate_profit_manager()))
    results.append(("System Integration", validate_system_integration()))
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("✓ ALL VALIDATIONS PASSED")
        print("\nSystem is ready for:")
        print("  • Risk management with daily loss caps")
        print("  • Profit tracking and verification")
        print("  • Tier integration and execution")
        print("\nNext steps:")
        print("  1. Deploy to testnet")
        print("  2. Run 24-hour validation")
        print("  3. Execute canary with $100K")
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("\nPlease fix issues above before deployment")
        return 1
    
    print("="*80 + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
