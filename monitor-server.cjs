// Ainex Live Monitor Server - Uses RPC from .env
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { ethers } = require('ethers');
const path = require('path');

dotenv.config();

const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

// Get RPC URL from .env (Alchemy or fallback)
const getRpcUrl = () => {
    return process.env.ALCHEMY_MAINNET_URL || 
           process.env.ETH_RPC_URL || 
           "https://rpc.ankr.com/eth";
};

// API endpoint to get blockchain data
app.get('/api/blockchain-data', async (req, res) => {
    try {
        const rpcUrl = getRpcUrl();
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        
        const blockNumber = await provider.getBlockNumber();
        const feeData = await provider.getFeeData();
        const gasPriceGwei = ethers.formatUnits(feeData.gasPrice, 'gwei');
        
        // Get ETH price from Chainlink
        const chainlinkABI = ["function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)"];
        const priceFeed = new ethers.Contract("0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419", chainlinkABI, provider);
        const roundData = await priceFeed.latestRoundData();
        const ethPrice = Number(ethers.formatUnits(roundData.answer, 8));
        
        res.json({
            success: true,
            blockNumber,
            gasPrice: parseFloat(gasPriceGwei),
            ethPrice,
            rpcUsed: rpcUrl.includes('alchemy') ? 'Alchemy' : 'Fallback'
        });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║     AINEX LIVE PROFIT MONITOR - RUNNING                  ║
╚═══════════════════════════════════════════════════════════╝

🚀 Server: http://localhost:${PORT}
📊 Monitor: http://localhost:${PORT}/live-monitor.html
🔗 RPC: ${getRpcUrl().includes('alchemy') ? 'Alchemy (from .env)' : 'Fallback RPC'}

Press Ctrl+C to stop
    `);
});
