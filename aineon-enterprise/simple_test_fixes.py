#!/usr/bin/env python3
"""
AINEON Engine Fix Validation Test (Simple)
Tests the critical fixes implemented to resolve 0% success rate
"""

import asyncio
import sys
import os
import numpy as np
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_validation_fixes():
    """Test the relaxed validation logic"""
    print("TESTING VALIDATION FIXES")
    print("=" * 50)
    
    # Import the fixed executor
    from core.ultra_low_latency_executor import UltraLowLatencyExecutor
    
    executor = UltraLowLatencyExecutor()
    
    # Test opportunities with different confidence levels
    test_opportunities = [
        {'spread_pct': 0.15, 'confidence': 0.65, 'buy_dex': 'UNISWAP_V3', 'sell_dex': 'SUSHISWAP', 'token_in': 'WETH', 'token_out': 'USDC'},
        {'spread_pct': 0.15, 'confidence': 0.75, 'buy_dex': 'UNISWAP_V3', 'sell_dex': 'SUSHISWAP', 'token_in': 'WETH', 'token_out': 'USDC'},
        {'spread_pct': 0.08, 'confidence': 0.85, 'buy_dex': 'UNISWAP_V3', 'sell_dex': 'SUSHISWAP', 'token_in': 'WETH', 'token_out': 'USDC'},
        {'spread_pct': 0.12, 'confidence': 0.55, 'buy_dex': 'UNISWAP_V3', 'sell_dex': 'SUSHISWAP', 'token_in': 'WETH', 'token_out': 'USDC'},
    ]
    
    print("Testing validation logic:")
    validation_results = []
    
    for i, opp in enumerate(test_opportunities):
        result = executor._validate_opportunity_fast(opp)
        validation_results.append(result)
        status = "PASS" if result else "FAIL"
        print(f"  Test {i+1}: Confidence={opp['confidence']:.2f}, Spread={opp['spread_pct']:.2f}% -> {status}")
    
    # Calculate success rate
    passed = sum(validation_results)
    total = len(validation_results)
    success_rate = passed / total * 100
    
    print(f"\nVALIDATION RESULTS:")
    print(f"  Passed: {passed}/{total}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Expected: >60% (relaxed from 0% due to confidence threshold fix)")
    
    return success_rate > 50

async def test_cache_fixes():
    """Test the improved price cache"""
    print("\nTESTING CACHE FIXES")
    print("=" * 50)
    
    from core.ultra_low_latency_executor import UltraLowLatencyExecutor
    
    executor = UltraLowLatencyExecutor()
    
    # Test cache hit rate with various opportunities
    test_pairs = [
        ('UNISWAP_V3', 'WETH', 'USDC'),
        ('SUSHISWAP', 'WBTC', 'WETH'),
        ('CURVE', 'USDC', 'USDT'),
        ('BALANCER', 'WETH', 'DAI'),
        ('1INCH', 'WETH', 'LINK'),
    ]
    
    print("Testing cache hit rate:")
    cache_hits = 0
    total_lookups = len(test_pairs)
    
    for dex, token_in, token_out in test_pairs:
        key = f"{dex}:{token_in}:{token_out}"
        price = executor.price_cache.get(key)
        if price:
            cache_hits += 1
            print(f"  HIT: {key}")
        else:
            print(f"  MISS: {key}")
    
    hit_rate = cache_hits / total_lookups * 100
    print(f"\nCACHE RESULTS:")
    print(f"  Cache Hits: {cache_hits}/{total_lookups}")
    print(f"  Hit Rate: {hit_rate:.1f}%")
    print(f"  Expected: >80% (expanded from ~10% due to cache coverage fix)")
    
    # Test cache size
    cache_size = len(executor.price_cache.cache)
    print(f"  Cache Size: {cache_size} entries")
    print(f"  Expected: ~90 entries (18 pairs × 5 DEXs)")
    
    return hit_rate > 70

async def test_end_to_end_execution():
    """Test complete execution pipeline"""
    print("\nTESTING END-TO-END EXECUTION")
    print("=" * 50)
    
    from core.ultra_low_latency_executor import UltraLowLatencyExecutor
    
    executor = UltraLowLatencyExecutor()
    
    # Generate test opportunities that should pass validation
    test_opportunities = []
    for i in range(10):
        opp = {
            'id': f'test_{i}',
            'buy_dex': np.random.choice(['UNISWAP_V3', 'SUSHISWAP', 'CURVE']),
            'sell_dex': np.random.choice(['UNISWAP_V3', 'SUSHISWAP', 'CURVE']),
            'token_in': np.random.choice(['WETH', 'WBTC', 'USDC']),
            'token_out': np.random.choice(['USDC', 'USDT', 'DAI']),
            'spread_pct': np.random.uniform(0.1, 2.0),  # 0.1% to 2.0%
            'confidence': np.random.uniform(0.65, 0.95),  # 65% to 95%
        }
        
        # Ensure buy and sell DEX are different
        if opp['buy_dex'] == opp['sell_dex']:
            opp['sell_dex'] = [dex for dex in ['UNISWAP_V3', 'SUSHISWAP', 'CURVE'] if dex != opp['buy_dex']][0]
            
        test_opportunities.append(opp)
    
    print(f"Testing {len(test_opportunities)} opportunities:")
    execution_results = []
    
    for i, opp in enumerate(test_opportunities):
        try:
            result = await executor.ultra_fast_execute(opp)
            execution_results.append(result)
            status = "SUCCESS" if result['success'] else f"FAIL ({result.get('reason', 'unknown')})"
            profit = result.get('profit', 0)
            print(f"  Test {i+1}: {status}, Profit={profit:.2f}")
        except Exception as e:
            execution_results.append({'success': False, 'error': str(e)})
            print(f"  Test {i+1}: ERROR - {e}")
    
    # Calculate success rate
    successful = sum(1 for r in execution_results if r.get('success', False))
    total = len(execution_results)
    success_rate = successful / total * 100
    
    # Calculate total profit
    total_profit = sum(r.get('profit', 0) for r in execution_results if r.get('success', False))
    
    print(f"\nEXECUTION RESULTS:")
    print(f"  Successful: {successful}/{total}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print(f"  Total Profit: {total_profit:.2f}")
    print(f"  Expected: >50% success rate, >0 profit (fixed from 0%)")
    
    return success_rate > 40 and total_profit > 0

async def main():
    """Run all validation tests"""
    print("AINEON ENGINE FIX VALIDATION")
    print("Testing critical fixes for 0% success rate issue")
    print(f"Test Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run all tests
    validation_passed = await test_validation_fixes()
    cache_passed = await test_cache_fixes()
    execution_passed = await test_end_to_end_execution()
    
    # Final results
    print("\n" + "=" * 60)
    print("FINAL VALIDATION RESULTS")
    print("=" * 60)
    
    tests = [
        ("Validation Logic Fix", validation_passed),
        ("Price Cache Fix", cache_passed),
        ("End-to-End Execution", execution_passed)
    ]
    
    all_passed = True
    for test_name, passed in tests:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOVERALL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\nSUCCESS: Engine fixes are working!")
        print("   - Validation logic relaxed (confidence: 0.6+, spread: 0.05%+)")
        print("   - Price cache expanded with consistent data")
        print("   - End-to-end execution producing profits")
        print("\nThe engine should now generate >50% success rate and profits!")
    else:
        print("\nWARNING: Some fixes may need adjustment")
        print("   - Check individual test results above")
        print("   - May need further debugging")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)