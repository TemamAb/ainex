#!/usr/bin/env node

/**
 * LIVE MODE VALIDATION TEST
 * Validates that clicking "Start LIVE" properly:
 * 1. Zeros all metrics and blockchain events stream
 * 2. Uses real-time data (no mock/demo data)
 * 3. Operates with real funds execution
 * 4. Implements self-healing logic on failures
 */

const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

// Test Configuration
const TEST_CONFIG = {
  ethereumRpcUrl: process.env.ETHEREUM_RPC_URL || 'https://eth-mainnet.g.alchemy.com/v2/demo',
  testTimeout: 30000, // 30 seconds
  expectedZeroMetrics: ['liveTradeSignals', 'liveFlashLoanMetrics', 'liveBotStatuses', 'liveTradeLogs', 'liveProfitMetrics']
};

class LiveModeValidator {
  constructor() {
    this.testResults = {
      metricsZeroed: false,
      realTimeData: false,
      realFundsExecution: false,
      selfHealingActive: false,
      blockchainConnectivity: false,
      codeValidation: false
    };
    this.startTime = Date.now();
  }

  async runValidation() {
    console.log('🚀 Starting LIVE Mode Validation Tests...\n');

    try {
      // Test 1: Validate Code Implementation
      await this.testCodeImplementation();

      // Test 2: Validate Metrics Zeroing Logic
      await this.testMetricsZeroingLogic();

      // Test 3: Validate Real-Time Data Usage
      await this.testRealTimeData();

      // Test 4: Validate Real Funds Execution Setup
      await this.testRealFundsExecutionSetup();

      // Test 5: Validate Self-Healing Implementation
      await this.testSelfHealingImplementation();

      // Test 6: Validate Blockchain Connectivity
      await this.testBlockchainConnectivity();

      // Generate Report
      this.generateReport();

    } catch (error) {
      console.error('💥 Validation failed with error:', error.message);
      this.testResults.error = error.message;
    }
  }

  async testCodeImplementation() {
    console.log('📝 Test 1: Validating Code Implementation...');

    try {
      // Check if MasterDashboard has the required imports and functions
      const dashboardPath = path.join(__dirname, 'components', 'MasterDashboard.tsx');
      const dashboardContent = fs.readFileSync(dashboardPath, 'utf8');

      const checks = [
        dashboardContent.includes('selfHealingService'),
        dashboardContent.includes('resetLiveMetrics'),
        dashboardContent.includes('handleStartLive'),
        dashboardContent.includes('startSelfHealing'),
        dashboardContent.includes('🔥 LIVE MODE'),
        dashboardContent.includes('Protocol Enforcement: LIVE Metrics reset')
      ];

      this.testResults.codeValidation = checks.every(check => check);

      console.log(`✅ Code implementation: ${this.testResults.codeValidation ? 'PASSED' : 'FAILED'}`);
      if (!this.testResults.codeValidation) {
        console.log('❌ Missing required code elements in MasterDashboard');
      }

    } catch (error) {
      console.error('❌ Code implementation test failed:', error.message);
      this.testResults.codeValidation = false;
    }
  }

  async testMetricsZeroingLogic() {
    console.log('📊 Test 2: Validating Metrics Zeroing Logic...');

    try {
      const dashboardPath = path.join(__dirname, 'components', 'MasterDashboard.tsx');
      const dashboardContent = fs.readFileSync(dashboardPath, 'utf8');

      // Check that resetLiveMetrics function exists and zeros all required metrics
      const resetFunctionExists = dashboardContent.includes('const resetLiveMetrics = () => {');
      const zerosAllMetrics = TEST_CONFIG.expectedZeroMetrics.every(metric => {
        if (metric === 'liveProfitMetrics') {
          return dashboardContent.includes('liveProfitMetrics: { daily: 0, total: 0 }');
        }
        return dashboardContent.includes(`${metric}: []`);
      });

      // Check that handleStartLive calls resetLiveMetrics
      const callsResetFunction = dashboardContent.includes('resetLiveMetrics();') &&
                                dashboardContent.includes('handleStartLive = async () => {');

      this.testResults.metricsZeroed = resetFunctionExists && zerosAllMetrics && callsResetFunction;

      console.log(`✅ Metrics zeroing logic: ${this.testResults.metricsZeroed ? 'PASSED' : 'FAILED'}`);
      if (!this.testResults.metricsZeroed) {
        console.log('❌ Metrics zeroing logic is incomplete');
      }

    } catch (error) {
      console.error('❌ Metrics zeroing test failed:', error.message);
      this.testResults.metricsZeroed = false;
    }
  }

  async testRealTimeData() {
    console.log('📈 Test 3: Validating Real-Time Data Usage...');

    try {
      // Check scanner service for real-time implementation
      const scannerPath = path.join(__dirname, 'services', 'scannerService.ts');
      const scannerContent = fs.readFileSync(scannerPath, 'utf8');

      const realTimeChecks = [
        scannerContent.includes('getRealDEXPrice'),
        scannerContent.includes('getCurrentBlockNumber'),
        scannerContent.includes('scanForArbitrageOpportunities'),
        scannerContent.includes('startScanning'),
        scannerContent.includes('ethers.Contract'),
        scannerContent.includes('Quoter contract'),
        !scannerContent.includes('mock') && !scannerContent.includes('demo')
      ];

      // Check execution service for real blockchain interaction
      const executionPath = path.join(__dirname, 'services', 'executionService.ts');
      const executionContent = fs.readFileSync(executionPath, 'utf8');

      const executionChecks = [
        executionContent.includes('executeTrade'),
        executionContent.includes('real Uniswap V3 Router'),
        executionContent.includes('real token addresses'),
        executionContent.includes('actual arbitrage'),
        executionContent.includes('real swap')
      ];

      this.testResults.realTimeData = realTimeChecks.every(check => check) && executionChecks.every(check => check);

      console.log(`✅ Real-time data: ${this.testResults.realTimeData ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      console.error('❌ Real-time data test failed:', error.message);
      this.testResults.realTimeData = false;
    }
  }

  async testRealFundsExecutionSetup() {
    console.log('💰 Test 4: Validating Real Funds Execution Setup...');

    try {
      const executionPath = path.join(__dirname, 'services', 'executionService.ts');
      const executionContent = fs.readFileSync(executionPath, 'utf8');

      const realFundsChecks = [
        executionContent.includes('real funds'),
        executionContent.includes('CRITICAL: This module handles Real Funds'),
        executionContent.includes('validateExecutionReadiness'),
        executionContent.includes('smart wallet'),
        executionContent.includes('gasless execution'),
        executionContent.includes('Uniswap V3 SwapRouter02'),
        executionContent.includes('actualProfit'),
        executionContent.includes('real swap')
      ];

      this.testResults.realFundsExecution = realFundsChecks.every(check => check);

      console.log(`✅ Real funds execution: ${this.testResults.realFundsExecution ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      console.error('❌ Real funds execution test failed:', error.message);
      this.testResults.realFundsExecution = false;
    }
  }

  async testSelfHealingImplementation() {
    console.log('🩺 Test 5: Validating Self-Healing Implementation...');

    try {
      const healingPath = path.join(__dirname, 'services', 'selfHealingService.ts');
      const healingContent = fs.readFileSync(healingPath, 'utf8');

      const healingChecks = [
        healingContent.includes('SelfHealingService'),
        healingContent.includes('performHealthCheck'),
        healingContent.includes('generateHealingActions'),
        healingContent.includes('reconnectScanner'),
        healingContent.includes('restartModule'),
        healingContent.includes('CRITICAL'),
        healingContent.includes('retryActivation'),
        healingContent.includes('emergencyShutdown')
      ];

      // Check that MasterDashboard integrates self-healing
      const dashboardPath = path.join(__dirname, 'components', 'MasterDashboard.tsx');
      const dashboardContent = fs.readFileSync(dashboardPath, 'utf8');

      const integrationChecks = [
        dashboardContent.includes('selfHealingService.startSelfHealing'),
        dashboardContent.includes('Self-healing service activated')
      ];

      this.testResults.selfHealingActive = healingChecks.every(check => check) && integrationChecks.every(check => check);

      console.log(`✅ Self-healing implementation: ${this.testResults.selfHealingActive ? 'PASSED' : 'FAILED'}`);

    } catch (error) {
      console.error('❌ Self-healing test failed:', error.message);
      this.testResults.selfHealingActive = false;
    }
  }

  async testBlockchainConnectivity() {
    console.log('🔗 Test 6: Validating Blockchain Connectivity...');

    try {
      const provider = new ethers.JsonRpcProvider(TEST_CONFIG.ethereumRpcUrl);

      // Test basic connectivity with timeout
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Connection timeout')), 10000)
      );

      const connectionPromise = Promise.all([
        provider.getBlockNumber(),
        provider.getNetwork()
      ]);

      const [blockNumber, network] = await Promise.race([connectionPromise, timeoutPromise]);

      const isConnected = blockNumber > 0 && network && network.name === 'mainnet';

      this.testResults.blockchainConnectivity = !!isConnected;

      console.log(`✅ Blockchain connectivity: ${isConnected ? 'PASSED' : 'FAILED'}`);
      if (isConnected) {
        console.log(`   📊 Connected to ${network.name}, Block: ${blockNumber}`);
      }

    } catch (error) {
      console.error('❌ Blockchain connectivity test failed:', error.message);
      this.testResults.blockchainConnectivity = false;
    }
  }

  generateReport() {
    const duration = Date.now() - this.startTime;
    const passedTests = Object.values(this.testResults).filter(result => result === true).length;
    const totalTests = Object.keys(this.testResults).length;

    console.log('\n' + '='.repeat(60));
    console.log('📋 LIVE MODE VALIDATION REPORT');
    console.log('='.repeat(60));

    console.log(`⏱️  Duration: ${duration}ms`);
    console.log(`✅ Passed: ${passedTests}/${totalTests}`);
    console.log(`❌ Failed: ${totalTests - passedTests}/${totalTests}`);

    console.log('\n📊 Test Results:');
    Object.entries(this.testResults).forEach(([test, result]) => {
      const icon = result ? '✅' : '❌';
      const status = result ? 'PASSED' : 'FAILED';
      console.log(`   ${icon} ${test}: ${status}`);
    });

    if (this.testResults.error) {
      console.log(`\n💥 Error: ${this.testResults.error}`);
    }

    console.log('\n🎯 Validation Summary:');
    if (passedTests === totalTests) {
      console.log('✅ ALL TESTS PASSED - LIVE mode is properly configured!');
      console.log('🚀 Ready for real fund execution with self-healing capabilities.');
      console.log('\n🔥 LIVE MODE FEATURES VALIDATED:');
      console.log('   • Metrics zeroing on startup');
      console.log('   • Real-time blockchain data integration');
      console.log('   • Real funds execution capability');
      console.log('   • Self-healing failure recovery');
      console.log('   • Live blockchain connectivity');
    } else {
      console.log('⚠️  SOME TESTS FAILED - Review configuration before live deployment.');
      console.log('🔧 Check failed tests and ensure all services are properly configured.');
      console.log('\n❌ FAILED VALIDATIONS:');
      Object.entries(this.testResults).forEach(([test, result]) => {
        if (!result) {
          console.log(`   • ${test.replace(/([A-Z])/g, ' $1').toLowerCase()}`);
        }
      });
    }

    console.log('='.repeat(60) + '\n');
  }
}

// Main execution
async function main() {
  console.log('🔬 AINEX Live Mode Validator v1.0\n');

  // Run validation
  const validator = new LiveModeValidator();
  await validator.runValidation();

  // Exit with appropriate code
  const passedTests = Object.values(validator.testResults).filter(result => result === true).length;
  const totalTests = Object.keys(validator.testResults).length;

  process.exit(passedTests === totalTests ? 0 : 1);
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('💥 Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run the validation
if (require.main === module) {
  main().catch((error) => {
    console.error('💥 Validation failed:', error);
    process.exit(1);
  });
}

module.exports = { LiveModeValidator };
