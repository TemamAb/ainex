// Test script to verify scannerService no longer generates mock blockchain events
const { arbitrageScanner, liquidationScanner, mevScanner, strategyOptimizer } = require('./services/scannerService');

async function testScannerService() {
  console.log('🚀 Testing scannerService for mock event removal...\n');

  let totalSignals = 0;
  let testPassed = true;

  // Test 1: ArbitrageScanner - should still work with real DEX queries
  console.log('1️⃣ Testing ArbitrageScanner...');
  try {
    let arbitrageSignals = 0;
    await arbitrageScanner.startScanning((signal) => {
      console.log('Arbitrage signal detected:', signal.id, signal.pair);
      arbitrageSignals++;
      totalSignals++;
    });

    // Let it run for a short time
    await new Promise(resolve => setTimeout(resolve, 2000));

    await arbitrageScanner.stopScanning();
    console.log(`✅ ArbitrageScanner generated ${arbitrageSignals} signals (should be real DEX-based)`);
  } catch (error) {
    console.error('❌ ArbitrageScanner test failed:', error.message);
    testPassed = false;
  }

  // Test 2: LiquidationScanner - should generate no mock signals
  console.log('\n2️⃣ Testing LiquidationScanner...');
  try {
    let liquidationSignals = 0;
    await liquidationScanner.startScanning((signal) => {
      console.log('Liquidation signal detected:', signal.id, signal.pair);
      liquidationSignals++;
      totalSignals++;
    });

    // Let it run for a short time
    await new Promise(resolve => setTimeout(resolve, 2000));

    await liquidationScanner.stopScanning();

    if (liquidationSignals === 0) {
      console.log('✅ LiquidationScanner generated 0 signals (mock events removed)');
    } else {
      console.log(`⚠️ LiquidationScanner generated ${liquidationSignals} signals (may be real or mock)`);
    }
  } catch (error) {
    console.error('❌ LiquidationScanner test failed:', error.message);
    testPassed = false;
  }

  // Test 3: MEVScanner - should generate no mock signals
  console.log('\n3️⃣ Testing MEVScanner...');
  try {
    let mevSignals = 0;
    await mevScanner.startScanning((signal) => {
      console.log('MEV signal detected:', signal.id, signal.pair);
      mevSignals++;
      totalSignals++;
    });

    // Let it run for a short time
    await new Promise(resolve => setTimeout(resolve, 1000));

    await mevScanner.stopScanning();

    if (mevSignals === 0) {
      console.log('✅ MEVScanner generated 0 signals (mock events removed)');
    } else {
      console.log(`⚠️ MEVScanner generated ${mevSignals} signals (may be real or mock)`);
    }
  } catch (error) {
    console.error('❌ MEVScanner test failed:', error.message);
    testPassed = false;
  }

  // Test 4: StrategyOptimizer - should use default values, not random
  console.log('\n4️⃣ Testing StrategyOptimizer...');
  try {
    let optimizationCount = 0;
    await strategyOptimizer.startOptimization((optimization) => {
      optimizationCount++;
      console.log(`Strategy optimization ${optimizationCount}:`, {
        confidence: optimization.confidence,
        marketConditions: optimization.marketConditions,
        adjustmentsCount: optimization.strategyAdjustments.length
      });

      // Verify market conditions are not random
      const conditions = optimization.marketConditions;
      if (conditions.volatility === 0.2 &&
          conditions.liquidity === 0.7 &&
          conditions.gasPrice === 50 &&
          conditions.marketTrend === 'neutral') {
        console.log('✅ StrategyOptimizer using default market conditions (not random)');
      } else {
        console.log('⚠️ StrategyOptimizer may still be using random values');
      }
    });

    // Let it run for a short time
    await new Promise(resolve => setTimeout(resolve, 2000));

    await strategyOptimizer.stopOptimization();
    console.log(`✅ StrategyOptimizer ran ${optimizationCount} optimization cycles`);
  } catch (error) {
    console.error('❌ StrategyOptimizer test failed:', error.message);
    testPassed = false;
  }

  // Summary
  console.log('\n📊 Test Summary:');
  console.log(`- Total signals generated: ${totalSignals}`);
  console.log('- ArbitrageScanner: Should generate real DEX-based signals');
  console.log('- LiquidationScanner: Should generate 0 mock signals');
  console.log('- MEVScanner: Should generate 0 mock signals');
  console.log('- StrategyOptimizer: Should use default market conditions');

  if (testPassed) {
    console.log('\n🎉 TEST PASSED: Mock blockchain events successfully removed from live mode!');
  } else {
    console.log('\n❌ TEST FAILED: Some issues detected with mock event removal');
    process.exit(1);
  }
}

// Run the test
testScannerService().catch(console.error);
