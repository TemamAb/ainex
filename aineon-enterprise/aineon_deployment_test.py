#!/usr/bin/env python3
"""
AINEON DEPLOYMENT TEST & VALIDATION
Chief Architect - Test and validate the live profit dashboard deployment
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any

def test_dashboard_validation_system():
    """Test the dashboard validation system"""
    print("🧪 Testing Dashboard Validation System...")
    
    try:
        from dashboard_validation_system import DashboardFilter, DashboardType
        
        # Test validation
        filter_system = DashboardFilter()
        results = filter_system.scan_dashboard_directory(".")
        
        print(f"✅ Validation system working")
        print(f"   Found {len(results)} dashboard types")
        
        # Check for live dashboards
        live_dashboards = filter_system.get_live_dashboards()
        print(f"   Live dashboards found: {len(live_dashboards)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation system test failed: {e}")
        return False

def test_unified_dashboard():
    """Test the unified dashboard system"""
    print("🧪 Testing Unified Live Dashboard...")
    
    try:
        # Test if we can import the unified dashboard
        sys.path.append('.')
        from aineon_unified_live_dashboard import UnifiedLiveDashboard, LiveDashboardConnector
        
        # Test connector
        connector = LiveDashboardConnector()
        live_files = connector.live_dashboard_files
        
        print(f"✅ Unified dashboard system working")
        print(f"   Live dashboard files: {len(live_files)}")
        
        # Test validation
        test_file = "aineon_live_profit_dashboard.py"
        if os.path.exists(test_file):
            is_valid = connector.validate_live_dashboard(test_file)
            print(f"   {test_file} validation: {'LIVE' if is_valid else 'SIMULATED'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Unified dashboard test failed: {e}")
        return False

def test_advanced_monitor():
    """Test the advanced monitoring system"""
    print("🧪 Testing Advanced Monitor...")
    
    try:
        from aineon_advanced_monitor import AdvancedLiveMonitor, LiveProfitAutomation, LiveProfitAnalytics
        
        # Test monitor
        monitor = AdvancedLiveMonitor()
        automation = LiveProfitAutomation(monitor)
        analytics = LiveProfitAnalytics()
        
        print(f"✅ Advanced monitor system working")
        print(f"   Alert types supported: {len(monitor.alert_callbacks)}")
        print(f"   Automation active: {automation.automation_active}")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced monitor test failed: {e}")
        return False

def test_deployment_architect():
    """Test the master deployment architect"""
    print("🧪 Testing Master Deployment Architect...")
    
    try:
        from aineon_master_deployment_architect import AineonMasterDeploymentArchitect
        
        # Test architect
        architect = AineonMasterDeploymentArchitect()
        architecture = architect.system_architecture
        
        print(f"✅ Master deployment architect working")
        print(f"   System name: {architecture.name}")
        print(f"   Total components: {len(architecture.components)}")
        print(f"   Deployment order: {len(architecture.deployment_order)} components")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment architect test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive system test"""
    print("🚀 AINEON DEPLOYMENT COMPREHENSIVE TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)
    
    tests = [
        ("Dashboard Validation System", test_dashboard_validation_system),
        ("Unified Live Dashboard", test_unified_dashboard),
        ("Advanced Monitor", test_advanced_monitor),
        ("Master Deployment Architect", test_deployment_architect)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} Test...")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Test summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System ready for deployment.")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review before deployment.")
        return False

def analyze_dashboard_files():
    """Analyze dashboard files and generate report"""
    print("\n📊 ANALYZING DASHBOARD FILES...")
    
    dashboard_files = [
        "aineon_live_profit_dashboard.py",
        "aineon_chief_architect_live_dashboard.py", 
        "live_profit_dashboard.py",
        "production_aineon_dashboard.py",
        "aineon_master_dashboard.py",
        "elite_aineon_dashboard.py",
        "simple_live_dashboard.py",
        "production_dashboard.py"
    ]
    
    analysis_results = {}
    
    for file in dashboard_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                content = f.read()
            
            # Analyze indicators
            has_wallet = "0xA51E466e659Cf9DdD5a5CA9ECDd8392302102490" in content
            has_disabled = "DISABLED" in content and "AUTO_TRANSFER" in content
            has_withdrawals = "ETH" in content and "transfer" in content
            has_simulation = any(word in content.lower() for word in ["simulation", "mock", "demo", "random"])
            
            # Classification
            if has_wallet and has_withdrawals and not has_disabled and not has_simulation:
                classification = "LIVE_PROFIT"
                priority = "HIGH"
            elif "elite" in file.lower() or "master" in file.lower():
                classification = "SIMULATED_MASTER"
                priority = "LOW"
            else:
                classification = "SIMULATED"
                priority = "LOW"
            
            analysis_results[file] = {
                "classification": classification,
                "priority": priority,
                "has_wallet": has_wallet,
                "has_withdrawals": has_withdrawals,
                "has_disabled": has_disabled,
                "has_simulation": has_simulation
            }
            
            status_icon = "✅" if classification == "LIVE_PROFIT" else "🚫"
            print(f"{status_icon} {file:<40} | {classification:<15} | Priority: {priority}")
    
    # Save analysis
    with open("dashboard_classification_report.json", "w") as f:
        json.dump(analysis_results, f, indent=2)
    
    live_count = sum(1 for r in analysis_results.values() if r["classification"] == "LIVE_PROFIT")
    print(f"\n📈 SUMMARY: {live_count} live dashboards, {len(analysis_results) - live_count} simulated dashboards")
    
    return analysis_results

def main():
    """Main test function"""
    print("🏗️ AINEON CHIEF ARCHITECT - DEPLOYMENT VALIDATION")
    print("Testing live profit dashboard deployment system")
    print("=" * 80)
    
    # Analyze dashboard files
    analysis_results = analyze_dashboard_files()
    
    # Run comprehensive tests
    test_success = run_comprehensive_test()
    
    # Final recommendations
    print("\n" + "=" * 80)
    print("🎯 DEPLOYMENT RECOMMENDATIONS")
    print("=" * 80)
    
    if test_success:
        print("✅ System validation PASSED")
        print("\n🚀 DEPLOYMENT COMMANDS:")
        print("1. Start unified live dashboard:")
        print("   python aineon_unified_live_dashboard.py")
        print("\n2. Start master deployment architect:")
        print("   python aineon_master_deployment_architect.py")
        print("\n3. Run advanced monitoring:")
        print("   python aineon_advanced_monitor.py")
        
        print("\n📊 LIVE DASHBOARDS TO CONNECT:")
        live_dashboards = [file for file, analysis in analysis_results.items() 
                          if analysis["classification"] == "LIVE_PROFIT"]
        for dashboard in live_dashboards:
            print(f"   • {dashboard}")
        
        print("\n🚫 SIMULATED DASHBOARDS TO EXCLUDE:")
        simulated_dashboards = [file for file, analysis in analysis_results.items() 
                               if analysis["classification"] != "LIVE_PROFIT"]
        for dashboard in simulated_dashboards:
            print(f"   • {dashboard}")
            
    else:
        print("❌ System validation FAILED")
        print("\n⚠️ Please fix issues before deployment:")
        print("• Check import dependencies")
        print("• Verify dashboard file integrity")
        print("• Ensure all components are working")
    
    print("\n" + "=" * 80)
    print("🏁 DEPLOYMENT VALIDATION COMPLETE")
    print("=" * 80)
    
    return 0 if test_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)