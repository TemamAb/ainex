require('dotenv').config();

const REQUIRED_VARS = {
    // Frontend (Next.js) - NEXT_PUBLIC_ prefix
    frontend: [
        'NEXT_PUBLIC_ETH_RPC_URL',
        'NEXT_PUBLIC_ARBITRUM_RPC_URL',
        'NEXT_PUBLIC_BASE_RPC_URL',
        'NEXT_PUBLIC_ETH_WS_URL',
        'NEXT_PUBLIC_ARBITRUM_WS_URL',
        'NEXT_PUBLIC_BASE_WS_URL'
    ],

    // API Keys for blockchain explorers
    apiKeys: [
        'ETHERSCAN_API_KEY',
        'ARBISCAN_API_KEY'
    ],

    // Backend/Hardhat RPC URLs
    backend: [
        'ETH_RPC_URL',
        'ALCHEMY_MAINNET_URL'
    ]
};

const OPTIONAL_VARS = [
    'NEXT_PUBLIC_GEMINI_API_KEY',  // Optional - has fallback logic
    'BASESCAN_API_KEY',             // Optional - placeholder OK
    'ARBITRUM_RPC_URL',
    'POLYGON_RPC_URL',
    'BSC_RPC_URL',
    'BASE_RPC_URL',
    'OPTIMISM_RPC_URL',
    'PRIVATE_KEY',
    'REDIS_HOST',
    'REDIS_PORT',
    'REDIS_PASSWORD',
    'PG_HOST',
    'PG_PORT',
    'PG_DATABASE',
    'PG_USER',
    'PG_PASSWORD',
    'JWT_SECRET',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
    'GITHUB_CLIENT_ID',
    'GITHUB_CLIENT_SECRET'
];

console.log('=============================================');
console.log('AINEX ENVIRONMENT VALIDATION REPORT');
console.log('=============================================\n');

let hasErrors = false;
let hasWarnings = false;

// Check required frontend variables
console.log('FRONTEND VARIABLES (NEXT_PUBLIC_*)');
console.log('---------------------------------------------');
REQUIRED_VARS.frontend.forEach(varName => {
    const value = process.env[varName];
    if (!value || value.trim() === '') {
        console.log(`FAIL ${varName}: MISSING (REQUIRED)`);
        hasErrors = true;
    } else {
        console.log(`PASS ${varName}: SET (${value.length} chars)`);
    }
});
console.log('');

// Check required API keys
console.log('API KEYS (Blockchain Explorers)');
console.log('---------------------------------------------');
REQUIRED_VARS.apiKeys.forEach(varName => {
    const value = process.env[varName];
    if (!value || value.trim() === '') {
        console.log(`FAIL ${varName}: MISSING (REQUIRED)`);
        hasErrors = true;
    } else {
        console.log(`PASS ${varName}: SET (${value.length} chars)`);
    }
});
console.log('');

// Check required backend variables
console.log('BACKEND VARIABLES (Core Engine)');
console.log('---------------------------------------------');
REQUIRED_VARS.backend.forEach(varName => {
    const value = process.env[varName];
    if (!value || value.trim() === '') {
        console.log(`FAIL ${varName}: MISSING (REQUIRED)`);
        hasErrors = true;
    } else {
        console.log(`PASS ${varName}: SET (${value.length} chars)`);
    }
});
console.log('');

// Check optional variables
console.log('OPTIONAL VARIABLES');
console.log('---------------------------------------------');
const setOptional = [];
const missingOptional = [];
OPTIONAL_VARS.forEach(varName => {
    const value = process.env[varName];
    if (value && value.trim() !== '' && value !== 'YourApiKeyToken') {
        setOptional.push(varName);
    } else {
        missingOptional.push(varName);
    }
});
console.log(`Set: ${setOptional.length}/${OPTIONAL_VARS.length}`);
if (setOptional.length > 0) {
    setOptional.forEach(v => console.log(`  + ${v}`));
}
console.log(`Not Set: ${missingOptional.length}/${OPTIONAL_VARS.length}`);
if (missingOptional.length > 0 && missingOptional.length <= 10) {
    missingOptional.forEach(v => console.log(`  - ${v}`));
}
console.log('');

// Final summary
console.log('=============================================');
console.log('VALIDATION SUMMARY');
console.log('=============================================');

if (hasErrors) {
    console.log('STATUS: FAILED - Missing required variables');
    console.log('ACTION: Add missing variables to .env file');
    process.exit(1);
} else {
    console.log('STATUS: PASSED - All required variables present');
    console.log('DEPLOYMENT: READY');

    if (missingOptional.length > 0) {
        console.log('\nNOTE: Some optional features disabled due to missing variables');
        console.log('      Dashboard will work with full core functionality');
    }

    process.exit(0);
}
