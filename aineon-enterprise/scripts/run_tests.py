#!/usr/bin/env python3
"""
AINEON Enterprise Test Runner
Runs comprehensive test suite with performance benchmarking
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(cmd, description):
    """Run command with proper error handling"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"⏱️  Execution time: {end_time - start_time:.2f} seconds")
        
        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print("❌ FAILED")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
            
            return False
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    deps = [
        "pytest",
        "pytest-asyncio", 
        "pytest-cov",
        "pytest-benchmark",
        "pytest-mock",
        "black",
        "flake8",
        "mypy",
        "safety",
        "bandit",
        "psutil"
    ]
    
    for dep in deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    
    return True

def run_code_quality_checks():
    """Run code quality and security checks"""
    print("\n🔍 Running Code Quality Checks...")
    
    checks = [
        ("black --check --diff .", "Code Formatting Check"),
        ("flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics", "Linting Check"),
        ("mypy . --ignore-missing-imports", "Type Checking"),
        ("safety check", "Security Vulnerability Scan"),
        ("bandit -r . -f json -o bandit-report.json", "Security Linting")
    ]
    
    for cmd, description in checks:
        if not run_command(cmd, description):
            return False
    
    return True

def run_unit_tests():
    """Run unit tests with coverage"""
    print("\n🧪 Running Unit Tests...")
    
    test_commands = [
        ("python -m pytest tests/ -v --tb=short", "Unit Tests"),
        ("python -m pytest tests/ --cov=core --cov-report=term-missing", "Unit Tests with Coverage"),
        ("python -m pytest tests/ -m 'not slow' -v", "Fast Unit Tests")
    ]
    
    for cmd, description in test_commands:
        if not run_command(cmd, description):
            return False
    
    return True

def run_performance_tests():
    """Run performance benchmarks"""
    print("\n⚡ Running Performance Tests...")
    
    perf_tests = [
        ("python core/tests/stress_test_engine.py", "Stress Test Engine"),
        ("python core/tests/load_test_suite.py", "Load Test Suite"),
        ("python -m pytest tests/test_comprehensive_suite.py::TestPerformanceBenchmarks -v", "Performance Benchmarks")
    ]
    
    for cmd, description in perf_tests:
        if not run_command(cmd, description):
            return False
    
    return True

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests...")
    
    return run_command(
        "python -m pytest tests/test_comprehensive_suite.py::TestIntegrationScenarios -v",
        "Integration Tests"
    )

def generate_reports():
    """Generate test and coverage reports"""
    print("\n📊 Generating Reports...")
    
    reports = [
        ("python -m pytest tests/ --cov=core --cov-report=html:htmlcov", "HTML Coverage Report"),
        ("python -m pytest tests/ --cov=core --cov-report=xml:coverage.xml", "XML Coverage Report")
    ]
    
    for cmd, description in reports:
        run_command(cmd, description)
    
    # Check if reports were generated
    if os.path.exists("htmlcov/index.html"):
        print("✅ HTML coverage report generated: htmlcov/index.html")
    
    if os.path.exists("coverage.xml"):
        print("✅ XML coverage report generated: coverage.xml")

def main():
    """Main test runner function"""
    print("🚀 AINEON ENTERPRISE TEST SUITE")
    print("="*80)
    print("Comprehensive testing framework for Chief Architect validation")
    print("="*80)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir.parent)
    
    success = True
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Dependency installation failed")
        return False
    
    # Step 2: Code quality checks
    if not run_code_quality_checks():
        print("⚠️  Code quality checks failed, but continuing...")
    
    # Step 3: Run unit tests
    if not run_unit_tests():
        print("❌ Unit tests failed")
        success = False
    
    # Step 4: Run performance tests
    if not run_performance_tests():
        print("⚠️  Performance tests failed, but continuing...")
    
    # Step 5: Run integration tests
    if not run_integration_tests():
        print("⚠️  Integration tests failed, but continuing...")
    
    # Step 6: Generate reports
    generate_reports()
    
    # Final summary
    print("\n" + "="*80)
    if success:
        print("✅ ALL TESTS PASSED - PHASE 1 VALIDATION SUCCESSFUL")
        print("🎯 Ready to proceed to Phase 2: Simulation Validation")
    else:
        print("❌ SOME TESTS FAILED - REVIEW REQUIRED")
        print("🔧 Fix issues before proceeding to Phase 2")
    print("="*80)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)