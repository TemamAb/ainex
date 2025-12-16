#!/usr/bin/env python3
"""
Minimax Tool Call ID Diagnostic Script
Helps diagnose and fix "Minimax error: invalid params, tool call id is invalid (2013)"
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add core to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from debug_logger import (
    get_tool_call_tracker, 
    get_api_parameter_validator, 
    debug_log_api_call,
    generate_debug_report
)

def test_tool_call_id_generation():
    """Test tool call ID generation and validation"""
    print("=== Testing Tool Call ID Generation ===")
    
    tracker = get_tool_call_tracker()
    
    # Test multiple tool call generations
    test_operations = ["api_request", "debug_operation", "system_check", "parameter_validation"]
    
    generated_ids = []
    for i, operation in enumerate(test_operations):
        try:
            tool_call_id = tracker.generate_tool_call_id(operation, {"test_param": f"value_{i}"})
            generated_ids.append(tool_call_id)
            print(f"✓ Generated valid tool call ID for {operation}: {tool_call_id}")
        except Exception as e:
            print(f"✗ Failed to generate tool call ID for {operation}: {e}")
    
    # Test validation of generated IDs
    print(f"\n=== Validating {len(generated_ids)} Generated IDs ===")
    for tool_call_id in generated_ids:
        is_valid = tracker.validate_tool_call_id(tool_call_id)
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"{status}: {tool_call_id}")
    
    return generated_ids

def test_api_parameter_validation():
    """Test API parameter validation"""
    print("\n=== Testing API Parameter Validation ===")
    
    validator = get_api_parameter_validator()
    
    # Test valid parameters
    valid_params = {
        "tool_call_id": "tool_1234567890_abcdef12_api_request",
        "operation": "test_operation",
        "additional_param": "value"
    }
    
    is_valid = validator.validate_and_log_params("minimax", "test_operation", valid_params)
    print(f"✓ Valid parameters test: {'PASS' if is_valid else 'FAIL'}")
    
    # Test invalid parameters
    invalid_params = {
        "tool_call_id": "invalid_id",  # Too short, doesn't start with 'tool_'
        "operation": "",  # Empty operation
        "missing_required": "something"
    }
    
    is_valid = validator.validate_and_log_params("minimax", "test_operation", invalid_params)
    print(f"✓ Invalid parameters test: {'CORRECTLY_REJECTED' if not is_valid else 'INCORRECTLY_ACCEPTED'}")
    
    # Test missing tool_call_id
    missing_id_params = {
        "operation": "test_operation",
        "param": "value"
    }
    
    is_valid = validator.validate_and_log_params("minimax", "test_operation", missing_id_params)
    print(f"✓ Missing tool_call_id test: {'CORRECTLY_REJECTED' if not is_valid else 'INCORRECTLY_ACCEPTED'}")

def simulate_minimax_api_call():
    """Simulate a Minimax API call to test the debug system"""
    print("\n=== Simulating Minimax API Call ===")
    
    # Simulate a typical API call that might fail
    api_params = {
        "tool_call_id": "tool_1640995200000_a1b2c3d4_debug_operation",
        "operation": "debug_operation",
        "mode": "debug",
        "model": "minimax/minimax-m2:free"
    }
    
    # Log the API call
    debug_log_api_call("minimax", "debug_operation", api_params)
    print("✓ API call logged successfully")
    
    # Simulate a failed API call with invalid tool_call_id
    invalid_params = {
        "tool_call_id": "invalid_tool_call_id",
        "operation": "failed_operation",
        "error": "tool call id is invalid (2013)"
    }
    
    debug_log_api_call("minimax", "failed_operation", invalid_params)
    print("✓ Failed API call logged successfully")

def check_environment_configuration():
    """Check environment configuration for potential issues"""
    print("\n=== Checking Environment Configuration ===")
    
    # Check if .env file exists and is readable
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✓ {env_file} file exists")
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Check for common issues
            issues = []
            
            if "WALLET-ADDRESS" in content:
                issues.append("Found WALLET-ADDRESS (should be WALLET_ADDRESS)")
            
            if content.count("ETH_RPC_URL") > 1:
                issues.append("Multiple ETH_RPC_URL definitions found")
            
            if "https://api.pimlico.io" in content and "alchemy.com" in content:
                issues.append("Mixed RPC endpoint types (Pimlico + Alchemy)")
            
            if issues:
                print("⚠ Environment configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("✓ No obvious environment configuration issues found")
                
        except Exception as e:
            print(f"✗ Error reading {env_file}: {e}")
    else:
        print(f"✗ {env_file} file not found")

def generate_and_display_report():
    """Generate and display the debug report"""
    print("\n=== Generating Debug Report ===")
    
    report = generate_debug_report()
    print(report)
    
    # Save report to file
    report_file = "minimax_debug_report.txt"
    try:
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n✓ Debug report saved to {report_file}")
    except Exception as e:
        print(f"\n✗ Failed to save debug report: {e}")

def main():
    """Main diagnostic function"""
    print("Minimax Tool Call ID Diagnostic Tool")
    print("=" * 50)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print()
    
    try:
        # Run all diagnostic tests
        test_tool_call_id_generation()
        test_api_parameter_validation()
        simulate_minimax_api_call()
        check_environment_configuration()
        generate_and_display_report()
        
        print("\n" + "=" * 50)
        print("Diagnostic completed successfully!")
        print("Check 'debug_tool_calls.log' for detailed logging information")
        print("Check 'minimax_debug_report.txt' for the comprehensive report")
        
    except Exception as e:
        print(f"\n✗ Diagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)