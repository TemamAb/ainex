require('dotenv').config();

console.log('Environment Variables Check:');
console.log('NEXT_PUBLIC_GEMINI_API_KEY:', process.env.NEXT_PUBLIC_GEMINI_API_KEY ? 'SET' : 'NOT SET');
console.log('ETHERSCAN_API_KEY:', process.env.ETHERSCAN_API_KEY ? 'SET' : 'NOT SET');
console.log('ARBISCAN_API_KEY:', process.env.ARBISCAN_API_KEY ? 'SET' : 'NOT SET');
console.log('BASESCAN_API_KEY:', process.env.BASESCAN_API_KEY ? 'SET' : 'NOT SET');
console.log('ALCHEMY_MAINNET_URL:', process.env.ALCHEMY_MAINNET_URL ? 'SET' : 'NOT SET');
console.log('ETH_RPC_URL:', process.env.ETH_RPC_URL ? 'SET' : 'NOT SET');
