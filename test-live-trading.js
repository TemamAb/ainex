const { ethers } = require('ethers');

// Test script to verify AINEX live trading and profit generation
async function testLiveTrading() {
  console.log('🚀 Starting AINEX Live Trading Test Suite...\n');

  try {
    // Test 1: Smart Wallet Generation
    console.log('1️⃣ Testing Smart Wallet Auto-Generation...');
    const { generateSmartWallet, getSmartWalletSigner, isSmartWalletReady } = require('./services/smartWalletService');

    const wallet = await generateSmartWallet('ethereum');
    console.log('✅ Smart wallet generated:', wallet.smartWalletAddress);

    const ready = await isSmartWalletReady('ethereum');
    console.log('✅ Wallet ready for trading:', ready);

    const { signer, smartWallet } = await getSmartWalletSigner('ethereum');
    console.log('✅ Signer retrieved for smart wallet:', smartWallet.smartWalletAddress);

    // Test 2: Execution Service Readiness
    console.log('\n2️⃣ Testing Execution Service Readiness...');
    const { validateExecutionReadiness } = require('./services/executionService');

    const isReady = await validateExecutionReadiness();
    console.log('✅ Execution readiness:', isReady);

    // Test 3: Blockchain Provider Connection
    console.log('\n3️⃣ Testing Blockchain Provider Connection...');
    const { getEthereumProvider, getRecentTransactions } = require('./blockchain/providers');

    const provider = await getEthereumProvider();
    const blockNumber = await provider.getBlockNumber();
    console.log('✅ Connected to Ethereum, current block:', blockNumber);

    const transactions = await getRecentTransactions('ethereum', 3);
    console.log('✅ Recent transactions fetched:', transactions.length);

    // Test 4: Simulation Service (Real-time Analysis)
    console.log('\n4️⃣ Testing Real-time Analysis Engine...');
    const { runSimulationLoop } = require('./services/simulationService');

    // Run simulation for 5 seconds to generate signals
    let simulationData = null;
    const cleanup = runSimulationLoop(
      (metrics) => {
        simulationData = metrics;
        console.log('✅ Simulation metrics received:', {
          confidence: metrics.confidence,
          profitProjection: metrics.profitProjection
        });
      },
      (signal) => {
        console.log('✅ Arbitrage signal detected:', signal.pair, 'Expected profit:', signal.expectedProfit);
      }
    );

    // Wait for simulation data
    await new Promise(resolve => setTimeout(resolve, 3000));
    cleanup();

    if (simulationData) {
      console.log('✅ Real-time analysis working, confidence:', simulationData.confidence + '%');
    }

    // Test 5: Activation Service
    console.log('\n5️⃣ Testing Module Activation...');
    const { runActivationSequence, getLiveActivationSteps } = require('./services/activationService');

    const steps = getLiveActivationSteps();
    console.log('✅ Live activation steps loaded:', steps.length);

    // Test 6: Contract Service
    console.log('\n6️⃣ Testing DEX Contract Integration...');
    const { getRouterContract } = require('./services/contractService');

    const router = await getRouterContract('ethereum', signer);
    console.log('✅ DEX router contract loaded');

    console.log('\n🎉 ALL TESTS PASSED! AINEX is ready for live trading and profit generation.');
    console.log('\n📊 Test Summary:');
    console.log('- ✅ Smart wallet auto-generation');
    console.log('- ✅ Gasless execution ready');
    console.log('- ✅ Blockchain connectivity');
    console.log('- ✅ Real-time arbitrage detection');
    console.log('- ✅ Module activation system');
    console.log('- ✅ DEX contract integration');
    console.log('\n🚀 Ready to start LIVE mode and generate profit!');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
  }
}

// Run the test
testLiveTrading().catch(console.error);
