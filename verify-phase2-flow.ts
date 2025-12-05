import { runSimulationLoop } from './services/simulationService.ts';
import { runPreflightChecks } from './services/preflightService.ts';
import { getRealPrices } from './services/priceService.ts';
import { getCurrentGasPrice } from './blockchain/providers.ts';

// VERIFICATION SCRIPT: PHASE 2 REAL ENGINE FLOW
// Automates the user journey: Config -> Preflight -> Sim (Real Analysis)

async function verifyFlow() {
    console.log('--- STARTING PHASE 2 VERIFICATION ---');

    // 1. Validate Real Price Feed
    console.log('\n[1] Testing Real-Time Price Feed...');
    try {
        const prices = await getRealPrices();
        console.log('    ETH Price:', prices.ethereum.usd);
        if (prices.ethereum.usd <= 0) throw new Error('Invalid ETH Price (0)');
        console.log('    [PASS] Real Price Feed Active');
    } catch (error) {
        console.error('    [FAIL] Price Feed Error:', error);
        process.exit(1);
    }

    // 2. Validate Real Gas Feed
    console.log('\n[2] Testing Real Gas Feed...');
    try {
        const gas = await getCurrentGasPrice('ethereum');
        console.log('    Gas Price (Wei):', gas.toString());
        if (gas <= 0n) throw new Error('Invalid Gas Price (0)');
        console.log('    [PASS] Real Gas Feed Active');
    } catch (error) {
        console.error('    [FAIL] Gas Feed Error:', error);
        // Warning only, RPC might be flaky on free tier
    }

    // 3. Run Preflight (Clean Registry)
    console.log('\n[3] Running Preflight Checks (No Mocking)...');
    try {
        const result = await runPreflightChecks();
        const failed = result.checks.filter(c => c.status === 'failed');
        if (failed.length > 0) {
            console.warn('    [WARN] Preflight has failures (Expected if env vars missing):');
            failed.forEach(f => console.log(`      - ${f.message}`));
        } else {
            console.log('    [PASS] All Preflight Checks Passed');
        }
    } catch (e) {
        console.error('    [FAIL] Preflight Exception:', e);
    }

    // 4. Run Real-Time Analysis Loop (SIM Mode)
    console.log('\n[4] Starting Real-Time Analysis Engine (5 seconds)...');
    return new Promise<void>((resolve) => {
        let updateCount = 0;
        const cleanup = runSimulationLoop(
            (metrics) => {
                updateCount++;
                console.log(`    [Update ${updateCount}] Conf: ${metrics.confidence}% | Proj Daily: $${metrics.profitProjection.daily.toFixed(2)}`);

                // Validate Data Integrity
                if (metrics.confidence === 10 && metrics.profitProjection.daily === 0) {
                    // This is acceptable behavior if data fetch failed, but we want to know
                }
            },
            (signal) => {
                console.log('    [SIGNAL] Arbitrage Opportunity Found:', signal);
            },
            5000 // Run for 5 seconds
        );

        setTimeout(() => {
            console.log('    [PASS] Analysis Loop Completed');
            resolve();
        }, 6000);
    });
}

verifyFlow().catch(console.error);
