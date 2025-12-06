// Simple test script to run preflight checks
const { runPreflightChecks } = require('./services/preflightService.ts');

async function testPreflight() {
    console.log('🧪 Testing Preflight Checks...');

    try {
        const results = await runPreflightChecks('sim', (checks) => {
            console.log(`📊 Progress: ${checks.filter(c => c.status === 'passed').length}/${checks.length} checks passed`);
        });

        console.log(`\n✅ Preflight Results:`);
        console.log(`All Passed: ${results.allPassed}`);
        console.log(`Total Checks: ${results.checks.length}`);

        const passed = results.checks.filter(c => c.status === 'passed').length;
        const failed = results.checks.filter(c => c.status === 'failed').length;

        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${failed}`);

        if (!results.allPassed) {
            console.log('\n❌ Failed Checks:');
            results.checks.filter(c => c.status === 'failed').forEach(check => {
                console.log(`- ${check.name}: ${check.message}`);
            });
        }

    } catch (error) {
        console.error('❌ Preflight test failed:', error.message);
        console.error(error.stack);
    }
}

testPreflight();
