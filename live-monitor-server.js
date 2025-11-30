// Live Profit Monitor Server
// Serves the HTML and provides RPC endpoint from .env

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { ethers } from 'ethers';

dotenv.config();

const app = express();
const PORT = 3002;

app.use(cors());
app.use(express.json());
app.use(express.static('.'));

// Provide RPC URL from .env
app.get('/api/rpc', (req, res) => {
    const rpcUrl = process.env.ETH_RPC_URL || "https://rpc.ankr.com/eth";
    res.json({ rpcUrl });
});

// Proxy blockchain requests to avoid CORS
app.post('/api/blockchain', async (req, res) => {
    try {
        const rpcUrl = process.env.ETH_RPC_URL || "https://rpc.ankr.com/eth";
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        
        const { method, params } = req.body;
        
        let result;
        switch (method) {
            case 'getBlockNumber':
                result = await provider.getBlockNumber();
                break;
            case 'getFeeData':
                result = await provider.getFeeData();
                break;
            case 'getEthPrice':
                const chainlinkABI = ["function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)"];
                const priceFeed = new ethers.Contract("0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419", chainlinkABI, provider);
                const roundData = await priceFeed.latestRoundData();
                result = Number(ethers.formatUnits(roundData.answer, 8));
                break;
            default:
                result = null;
        }
        
        res.json({ success: true, result });
    } catch (error) {
        res.json({ success: false, error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════╗
║     AINEX LIVE PROFIT MONITOR SERVER                     ║
╚═══════════════════════════════════════════════════════════╝

🚀 Server running on http://localhost:${PORT}
📊 Live Monitor: http://localhost:${PORT}/live-monitor.html
🔗 RPC: ${process.env.ETH_RPC_URL || 'Using fallback RPC'}

Press Ctrl+C to stop
    `);
});
