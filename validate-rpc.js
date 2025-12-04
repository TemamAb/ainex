require('dotenv').config();
const https = require('https');

console.log('========================================');
console.log('ALCHEMY/RPC API KEY VALIDATION');
console.log('========================================\n');

// Get the RPC URL
const rpcUrl = process.env.ETH_RPC_URL || process.env.ALCHEMY_MAINNET_URL || process.env.NEXT_PUBLIC_ETH_RPC_URL;

if (!rpcUrl) {
    console.log('ERROR: No RPC URL found in environment variables');
    console.log('Please set one of: ETH_RPC_URL, ALCHEMY_MAINNET_URL, NEXT_PUBLIC_ETH_RPC_URL');
    process.exit(1);
}

console.log('1. RPC Configuration:');
console.log('----------------------------------');
console.log('URL:', rpcUrl.substring(0, 60) + '...');

// Detect provider type
let provider = 'Unknown';
let apiKey = null;

if (rpcUrl.includes('alchemy.com')) {
    provider = 'Alchemy';
    const match = rpcUrl.match(/alchemy\.com\/v2\/([a-zA-Z0-9_-]+)/);
    if (match) apiKey = match[1];
} else if (rpcUrl.includes('infura.io')) {
    provider = 'Infura';
    const match = rpcUrl.match(/infura\.io\/v3\/([a-zA-Z0-9]+)/);
    if (match) apiKey = match[1];
} else if (rpcUrl.includes('llamarpc.com')) {
    provider = 'LlamaRPC (Public)';
} else if (rpcUrl.includes('ankr.com')) {
    provider = 'Ankr';
} else {
    provider = 'Custom RPC';
}

console.log('Provider:', provider);
if (apiKey) {
    console.log('API Key:', apiKey.substring(0, 10) + '...' + apiKey.substring(apiKey.length - 4));
} else {
    console.log('API Key: Not applicable (public endpoint)');
}

console.log('\n2. Testing Connection:');
console.log('----------------------------------');
console.log('Making test RPC call (eth_blockNumber)...\n');

const url = new URL(rpcUrl);
const postData = JSON.stringify({
    jsonrpc: '2.0',
    method: 'eth_blockNumber',
    params: [],
    id: 1
});

const options = {
    hostname: url.hostname,
    port: 443,
    path: url.pathname + url.search,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
    },
    timeout: 10000
};

const startTime = Date.now();

const req = https.request(options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
        data += chunk;
    });

    res.on('end', () => {
        const elapsed = Date.now() - startTime;

        console.log('========================================');
        console.log('VALIDATION RESULT');
        console.log('========================================\n');

        try {
            const response = JSON.parse(data);

            if (response.error) {
                console.log('FAILED - API Error:');
                console.log('----------------------------------');
                console.log('HTTP Status:', res.statusCode);
                console.log('Error Code:', response.error.code);
                console.log('Error Message:', response.error.message);
                console.log('Response Time:', elapsed + 'ms');
                console.log('\nPossible Issues:');
                if (provider === 'Alchemy' || provider === 'Infura') {
                    console.log('  1. Invalid or expired API key');
                    console.log('  2. API key not activated');
                    console.log('  3. Rate limit exceeded');
                    console.log('  4. Insufficient credits/plan limits');
                }
                console.log('  5. Network/firewall restrictions');
                process.exit(1);
            } else if (response.result) {
                const blockNumber = parseInt(response.result, 16);
                console.log('SUCCESS - RPC Connection Valid!');
                console.log('----------------------------------');
                console.log('Provider:', provider);
                console.log('Current Block:', blockNumber.toLocaleString());
                console.log('Response Time:', elapsed + 'ms');
                console.log('HTTP Status:', res.statusCode);

                // Performance assessment
                console.log('\nPerformance Assessment:');
                if (elapsed < 100) {
                    console.log('  Excellent (<100ms)');
                } else if (elapsed < 300) {
                    console.log('  Good (100-300ms)');
                } else if (elapsed < 1000) {
                    console.log('  Fair (300-1000ms)');
                } else {
                    console.log('  Slow (>1000ms) - Consider switching provider');
                }

                console.log('\nYour RPC connection is working correctly!');
                process.exit(0);
            } else {
                console.log('UNEXPECTED - Unknown response format:');
                console.log('----------------------------------');
                console.log('HTTP Status:', res.statusCode);
                console.log('Raw Response:', data.substring(0, 200));
                process.exit(1);
            }
        } catch (error) {
            console.log('FAILED - Could not parse response:');
            console.log('----------------------------------');
            console.log('HTTP Status:', res.statusCode);
            console.log('Raw Response:', data.substring(0, 200));
            console.log('Parse Error:', error.message);
            process.exit(1);
        }
    });
});

req.on('error', (error) => {
    console.log('========================================');
    console.log('VALIDATION RESULT');
    console.log('========================================\n');
    console.log('FAILED - Network Error:');
    console.log('----------------------------------');
    console.log('Error:', error.message);
    console.log('Code:', error.code || 'N/A');
    console.log('\nPossible Issues:');
    console.log('  1. No internet connection');
    console.log('  2. Firewall blocking HTTPS requests');
    console.log('  3. Invalid URL format');
    console.log('  4. DNS resolution failure');
    process.exit(1);
});

req.on('timeout', () => {
    req.destroy();
    console.log('========================================');
    console.log('VALIDATION RESULT');
    console.log('========================================\n');
    console.log('FAILED - Request Timeout');
    console.log('----------------------------------');
    console.log('The request took longer than 10 seconds');
    console.log('Your RPC provider may be experiencing issues');
    process.exit(1);
});

req.write(postData);
req.end();
