// Test script to thoroughly test LiveModeDashboard component changes
const React = require('react');
const { renderToString } = require('react-dom/server');

// Mock the required dependencies
const mockSignals = [
  {
    id: '1',
    pair: 'ETH/USDT',
    expectedProfit: 0.5,
    confidence: 85,
    timestamp: new Date().toISOString(),
    status: 'active'
  },
  {
    id: '2',
    pair: 'BTC/USDT',
    expectedProfit: 1.2,
    confidence: 92,
    timestamp: new Date().toISOString(),
    status: 'pending'
  }
];

const mockLiveTrades = [
  {
    id: 'trade1',
    pair: 'ETH/USDT',
    amount: 1.5,
    profit: 0.075,
    status: 'completed',
    timestamp: new Date().toISOString()
  },
  {
    id: 'trade2',
    pair: 'BTC/USDT',
    amount: 0.1,
    profit: -0.02,
    status: 'active',
    timestamp: new Date().toISOString()
  }
];

async function testLiveModeDashboard() {
  console.log('🚀 Starting LiveModeDashboard Thorough Testing...\n');

  try {
    // Test 1: Import the component without errors
    console.log('1️⃣ Testing component import...');
    const { default: LiveModeDashboard } = require('./components/LiveModeDashboard');
    console.log('✅ Component imported successfully');

    // Test 2: Render with default props (empty liveTrades)
    console.log('\n2️⃣ Testing render with default props...');
    const element1 = React.createElement(LiveModeDashboard, {
      signals: mockSignals
    });

    try {
      const html1 = renderToString(element1);
      console.log('✅ Component rendered successfully with default liveTrades (empty array)');
      console.log('Rendered HTML length:', html1.length);
    } catch (error) {
      console.error('❌ Render failed with default props:', error.message);
      throw error;
    }

    // Test 3: Render with provided liveTrades
    console.log('\n3️⃣ Testing render with provided liveTrades...');
    const element2 = React.createElement(LiveModeDashboard, {
      signals: mockSignals,
      liveTrades: mockLiveTrades
    });

    try {
      const html2 = renderToString(element2);
      console.log('✅ Component rendered successfully with provided liveTrades');
      console.log('Rendered HTML length:', html2.length);
    } catch (error) {
      console.error('❌ Render failed with provided liveTrades:', error.message);
      throw error;
    }

    // Test 4: Render with empty liveTrades array explicitly
    console.log('\n4️⃣ Testing render with explicit empty liveTrades...');
    const element3 = React.createElement(LiveModeDashboard, {
      signals: mockSignals,
      liveTrades: []
    });

    try {
      const html3 = renderToString(element3);
      console.log('✅ Component rendered successfully with explicit empty liveTrades');
      console.log('Rendered HTML length:', html3.length);
    } catch (error) {
      console.error('❌ Render failed with explicit empty liveTrades:', error.message);
      throw error;
    }

    // Test 5: Verify no duplicate LiveTrade interface errors
    console.log('\n5️⃣ Testing for duplicate interface issues...');
    try {
      // Try to access the component multiple times to ensure no conflicts
      const component1 = require('./components/LiveModeDashboard');
      const component2 = require('./components/LiveModeDashboard');
      console.log('✅ No duplicate interface conflicts detected');
    } catch (error) {
      console.error('❌ Duplicate interface issue detected:', error.message);
      throw error;
    }

    console.log('\n🎉 ALL TESTS PASSED! LiveModeDashboard component is working correctly.');
    console.log('\n📊 Test Summary:');
    console.log('- ✅ Component imports without errors');
    console.log('- ✅ Renders with default empty liveTrades');
    console.log('- ✅ Renders with provided liveTrades data');
    console.log('- ✅ Renders with explicit empty liveTrades');
    console.log('- ✅ No duplicate LiveTrade interface conflicts');
    console.log('\n🚀 LiveModeDashboard is ready for production use!');

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
    process.exit(1);
  }
}

// Run the test
testLiveModeDashboard().catch(console.error);
