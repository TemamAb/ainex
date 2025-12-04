require('dotenv').config();
const https = require('https');

console.log('========================================');
console.log('INFURA API KEY VALIDATION');
console.log('========================================\n');

// Check for Infura-related environment variables
const infuraKeys = {
    'ALCHEMY_MAINNET_URL': process.env.ALCHEMY_MAINNET_URL,
    'ETH_RPC_URL': process.env.ETH_RPC_URL,
    'NEXT_PUBLIC_ETH_RPC_URL': process.env.NEXT_PUBLIC_ETH_RPC_URL
};

console.log('1. Checking Environment Variables:');
console.log('----------------------------------');
let infuraUrl = null;
let keySource = null;

for (const [key, value] of Object.entries(infuraKeys)) {
    if (value && value.includes('infura.io')) {
        console.log(`FOUND ${key}: ${value.substring(0, 50)}...`);
        infuraUrl = value;
        keySource = key;
    } else if (value) {
        console.log(`${key}: ${value.substring(0, 50)}... (not Infura)`);
    } else {
        console.log(`${key}: NOT SET`);
    }
}

console.log('\n2. Infura Key Detection:');
console.log('----------------------------------');
if (!infuraUrl) {
    console.log('WARNING: No Infura URL found in environment variables');
    console.log('Currently using alternative RPC providers');
    console.log('\nTo add Infura, set one of these variables:');
    console.log('  ETH_RPC_URL=https://mainnet.infura.io/v3/YOUR_API_KEY');
    console.log('  ALCHEMY_MAINNET_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY');
    process.exit(0);
}

console.log(`Detected Infura URL in: ${keySource}`);

// Extract the API key from the URL
let apiKey = null;
const match = infuraUrl.match(/infura\.io\/v3\/([a-zA-Z0-9]+)/);
if (match) {
    apiKey = match[1];
    console.log(`Extracted API Key: ${apiKey.substring(0, 8)}...${apiKey.substring(apiKey.length - 4)}`);
} else {
    console.log('ERROR: Could not extract API key from URL');
    process.exit(1);
}

console.log('\n3. Testing Infura Connection:');
console.log('----------------------------------');
console.log('Making test RPC call (eth_blockNumber)...\n');

// Make a test RPC call
const url = new URL(infuraUrl);
const postData = JSON.stringify({
    jsonrpc: '2.0',
    method: 'eth_blockNumber',
    params: [],
    id: 1
});

const options = {
    hostname: url.hostname,
    port: 443,
    path: url.pathname,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length
    }
};

const req = https.request(options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
        data += chunk;
    });

    res.on('end', () => {
        console.log('========================================');
        console.log('VALIDATION RESULT');
        console.log('========================================\n');

        try {
            const response = JSON.parse(data);

            if (response.error) {
                console.log('FAILED - Infura API Error:');
                console.log('Status:', res.statusCode);
                console.log('Error Code:', response.error.code);
                console.log('Error Message:', response.error.message);
                console.log('\nPossible Issues:');
                console.log('  1. Invalid or expired API key');
                console.log('  2. API key not activated');
                console.log('  3. Rate limit exceeded');
                console.log('  4. Network restrictions');
                console.log('\nGet a new API key at: https://infura.io/');
                process.exit(1);
            } else if (response.result) {
                const blockNumber = parseInt(response.result, 16);
                console.log('SUCCESS - Infura API Key is Valid!');
                console.log('----------------------------------');
                console.log('Current Block Number:', blockNumber.toLocaleString());
                console.log('Response Time:', res.headers['x-response-time'] || 'N/A');
                console.log('Status Code:', res.statusCode);
                console.log('\nYour Infura connection is working correctly.');
                process.exit(0);
            } else {
                console.log('UNEXPECTED - Unknown response format:');
                console.log(data);
                process.exit(1);
            }
        } catch (error) {
            console.log('FAILED - Could not parse response:');
            console.log('Raw Response:', data);
            console.log('Error:', error.message);
            process.exit(1);
        }
    });
});

req.on('error', (error) => {
    console.log('========================================');
    console.log('VALIDATION RESULT');
    console.log('========================================\n');
    console.log('FAILED - Network Error:');
    console.log('Error:', error.message);
    console.log('\nPossible Issues:');
    console.log('  1. No internet connection');
    console.log('  2. Firewall blocking HTTPS requests');
    console.log('  3. Invalid URL format');
    process.exit(1);
});

req.write(postData);
req.end();
