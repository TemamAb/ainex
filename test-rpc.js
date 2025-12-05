const { ethers } = require('ethers');

const RPC_URLS = [
    'https://arb1.arbitrum.io/rpc',
    'https://1rpc.io/arb',
    'https://arbitrum-one.publicnode.com',
    'https://rpc.ankr.com/arbitrum'
];

async function testRpc() {
    for (const url of RPC_URLS) {
        console.log(`Testing connection to ${url}...`);
        try {
            const provider = new ethers.JsonRpcProvider(url);
            // Set timeout for faster failure
            const network = await Promise.race([
                provider.getNetwork(),
                new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
            ]);
            console.log(`SUCCESS: Connected to ${url} (Chain ID: ${network.chainId.toString()})`);
            return; // Exit on first success
        } catch (error) {
            console.error(`FAILED: ${url} - ${error.message}`);
        }
    }
    console.error('All RPCs failed.');
}

testRpc();
