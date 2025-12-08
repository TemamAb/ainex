const { getAllModules, getModulesByType, activateModule, activateAllModules } = require('./services/moduleRegistry.ts');
const { runActivationSequence, getSimActivationSteps, getLiveActivationSteps } = require('./services/activationService.ts');

async function validateModuleActivation() {
    console.log('🔍 VALIDATING MODULE ACTIVATION FOR SIM AND LIVE MODES\n');

    // Get all modules
    const allModules = getAllModules();
    console.log(`📊 Total modules in registry: ${allModules.length}`);

    // Categorize modules
    const moduleTypes = ['STRATEGY', 'EXECUTION', 'INFRA', 'SECURITY', 'MONITORING', 'AI', 'BLOCKCHAIN', 'SERVICES'];
    moduleTypes.forEach(type => {
        const modules = getModulesByType(type);
        console.log(`  ${type}: ${modules.length} modules`);
    });

    console.log('\n🚀 TESTING SIM MODE ACTIVATION\n');

    // Test SIM mode activation
    const simSteps = getSimActivationSteps();
    console.log('SIM Activation Steps:');
    simSteps.forEach(step => console.log(`  - ${step.label}: ${step.details}`));

    // Run SIM activation sequence
    let simActivatedModules = [];
    const simResult = await runActivationSequence(
        simSteps,
        (steps) => {
            const currentStep = steps.find(s => s.status === 'IN_PROGRESS');
            if (currentStep) {
                console.log(`⏳ ${currentStep.label}...`);
            }
        },
        'SIM'
    );

    // Check which modules are active after SIM activation
    const activeAfterSim = allModules.filter(m => m.status === 'ACTIVE');
    console.log(`\n✅ SIM Mode: ${activeAfterSim.length} modules activated`);

    // Check that EXECUTION modules are NOT activated in SIM mode
    const executionModules = getModulesByType('EXECUTION');
    const activeExecutionInSim = executionModules.filter(m => m.status === 'ACTIVE');
    console.log(`  - Execution modules activated: ${activeExecutionInSim.length}/${executionModules.length}`);

    if (activeExecutionInSim.length > 0) {
        console.log('❌ ERROR: Execution modules should NOT be activated in SIM mode!');
        activeExecutionInSim.forEach(m => console.log(`    ${m.name}`));
    } else {
        console.log('✅ PASS: No execution modules activated in SIM mode');
    }

    // Reset all modules for LIVE test
    allModules.forEach(m => m.status = 'INACTIVE');

    console.log('\n🔴 TESTING LIVE MODE ACTIVATION\n');

    // Test LIVE mode activation
    const liveSteps = getLiveActivationSteps();
    console.log('LIVE Activation Steps:');
    liveSteps.forEach(step => console.log(`  - ${step.label}: ${step.details}`));

    // Run LIVE activation sequence
    const liveResult = await runActivationSequence(
        liveSteps,
        (steps) => {
            const currentStep = steps.find(s => s.status === 'IN_PROGRESS');
            if (currentStep) {
                console.log(`⏳ ${currentStep.label}...`);
            }
        },
        'LIVE'
    );

    // Check which modules are active after LIVE activation
    const activeAfterLive = allModules.filter(m => m.status === 'ACTIVE');
    console.log(`\n✅ LIVE Mode: ${activeAfterLive.length} modules activated`);

    // Check that ALL modules are activated in LIVE mode
    const inactiveAfterLive = allModules.filter(m => m.status !== 'ACTIVE');
    if (inactiveAfterLive.length > 0) {
        console.log('❌ ERROR: Some modules failed to activate in LIVE mode!');
        inactiveAfterLive.forEach(m => console.log(`    ${m.name} (${m.type})`));
    } else {
        console.log('✅ PASS: All modules activated in LIVE mode');
    }

    // Summary
    console.log('\n📋 VALIDATION SUMMARY');
    console.log('='.repeat(50));
    console.log(`Total Modules: ${allModules.length}`);
    console.log(`SIM Mode Activated: ${activeAfterSim.length}`);
    console.log(`LIVE Mode Activated: ${activeAfterLive.length}`);
    console.log(`Execution Modules Excluded from SIM: ${executionModules.length}`);

    const simExcludedTypes = ['EXECUTION'];
    const simExpectedActive = allModules.filter(m => !simExcludedTypes.includes(m.type)).length;
    const liveExpectedActive = allModules.length;

    console.log('\n🎯 EXPECTED VS ACTUAL:');
    console.log(`SIM Expected: ${simExpectedActive}, Actual: ${activeAfterSim.length} ${simExpectedActive === activeAfterSim.length ? '✅' : '❌'}`);
    console.log(`LIVE Expected: ${liveExpectedActive}, Actual: ${activeAfterLive.length} ${liveExpectedActive === activeAfterLive.length ? '✅' : '❌'}`);

    return {
        totalModules: allModules.length,
        simActivated: activeAfterSim.length,
        liveActivated: activeAfterLive.length,
        simSuccess: activeAfterSim.length === simExpectedActive,
        liveSuccess: activeAfterLive.length === liveExpectedActive
    };
}

// Run validation if this script is executed directly
if (require.main === module) {
    validateModuleActivation().then(result => {
        console.log('\n🏁 VALIDATION COMPLETE');
        process.exit(result.simSuccess && result.liveSuccess ? 0 : 1);
    }).catch(error => {
        console.error('❌ Validation failed:', error);
        process.exit(1);
    });
}

module.exports = { validateModuleActivation };
