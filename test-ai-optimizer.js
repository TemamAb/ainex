const { AIOptimizerService } = require('./services/aiOptimizerService');

async function testAIOptimizer() {
  console.log('🧪 Testing AI Optimizer Service...\n');

  const aiOptimizer = new AIOptimizerService();

  try {
    // Test 1: AI Strategy Suggestions
    console.log('1️⃣ Testing getAIStrategySuggestions...');
    const suggestions = await aiOptimizer.getAIStrategySuggestions();
    console.log('✅ AI Strategy Suggestions:', suggestions);

    // Validate structure
    if (!suggestions.profitTarget || !suggestions.riskProfile || !suggestions.reinvestmentRate) {
      throw new Error('Invalid suggestions structure');
    }
    console.log('✅ Suggestions structure validated\n');

    // Test 2: Strategy Optimization
    console.log('2️⃣ Testing optimizeStrategy...');
    const currentSettings = {
      profitTarget: { daily: '1.25' },
      riskProfile: 'MEDIUM',
      reinvestmentRate: 70,
      aiOptimizationCycle: 30
    };

    const optimizedSettings = await aiOptimizer.optimizeStrategy(currentSettings);
    console.log('✅ Optimized Settings:', optimizedSettings);

    // Validate optimization
    if (!optimizedSettings.profitTarget || !optimizedSettings.riskProfile) {
      throw new Error('Invalid optimized settings structure');
    }
    console.log('✅ Optimization structure validated\n');

    // Test 3: Strategy Audit
    console.log('3️⃣ Testing auditStrategy...');
    const auditSettings = {
      profitTarget: { daily: '1.50' },
      riskProfile: 'HIGH',
      reinvestmentRate: 85
    };

    const auditResults = await aiOptimizer.auditStrategy(auditSettings);
    console.log('✅ Audit Results:', auditResults);

    // Validate audit structure
    if (!auditResults.profitTarget || !auditResults.riskProfile || !auditResults.recommendations) {
      throw new Error('Invalid audit results structure');
    }
    console.log('✅ Audit structure validated\n');

    // Test 4: Strategy Enhancement
    console.log('4️⃣ Testing enhanceStrategy...');
    const enhancedSettings = await aiOptimizer.enhanceStrategy(currentSettings);
    console.log('✅ Enhanced Settings:', enhancedSettings);

    // Validate enhancement
    if (!enhancedSettings.isAIConfigured) {
      throw new Error('AI configuration flag not set');
    }
    console.log('✅ Enhancement structure validated\n');

    // Test 5: Performance Statistics
    console.log('5️⃣ Testing getPerformanceStatistics...');
    const performanceStats = await aiOptimizer.getPerformanceStatistics('today');
    console.log('✅ Performance Statistics:', performanceStats);

    // Validate performance stats
    if (!performanceStats.totalTrades || performanceStats.successRate === undefined) {
      throw new Error('Invalid performance statistics structure');
    }
    console.log('✅ Performance statistics validated\n');

    // Test 6: Arbitrage Opportunities
    console.log('6️⃣ Testing findArbitrageOpportunities...');
    const opportunities = await aiOptimizer.findArbitrageOpportunities();
    console.log('✅ Found', opportunities.length, 'arbitrage opportunities');

    // Validate opportunities structure
    if (!Array.isArray(opportunities)) {
      throw new Error('Opportunities should be an array');
    }
    console.log('✅ Opportunities structure validated\n');

    // Test 7: Optimization Status
    console.log('7️⃣ Testing getOptimizationStatus...');
    const status = await aiOptimizer.getOptimizationStatus();
    console.log('✅ Optimization Status:', status);

    // Validate status structure
    if (!status.status || status.currentOpportunities === undefined) {
      throw new Error('Invalid optimization status structure');
    }
    console.log('✅ Status structure validated\n');

    console.log('🎉 All AI Optimizer tests passed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run the tests
testAIOptimizer().catch(console.error);
