import { ethers } from 'ethers';
import * as dotenv from 'dotenv';

dotenv.config();

const MAINNET_RPC = process.env.ETH_RPC_URL || "https://rpc.ankr.com/eth";
const CHAINLINK_ETH_USD = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419";

// Uniswap V2 Router
const UNISWAP_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
const SUSHISWAP_ROUTER = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F";

// WETH and USDC addresses
const WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2";
const USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48";

const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
    white: '\x1b[37m',
    reset: '\x1b[0m',
    bold: '\x1b[1m'
};

async function monitorLiveBlockchain() {
    console.log(`${colors.bold}${colors.cyan}
╔═══════════════════════════════════════════════════════════╗
║     AINEX LIVE BLOCKCHAIN WAR GAME - PROFIT MONITOR      ║
║                  REAL-TIME EVENTS ONLY                    ║
╚═══════════════════════════════════════════════════════════╝
${colors.reset}\n`);

    const provider = new ethers.JsonRpcProvider(MAINNET_RPC);
    
    // Get initial state
    const blockNumber = await provider.getBlockNumber();
    const feeData = await provider.getFeeData();
    const gasPriceGwei = ethers.formatUnits(feeData.gasPrice!, 'gwei');
    
    // Get ETH price from Chainlink
    const chainlinkABI = ["function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)"];
    const priceFeed = new ethers.Contract(CHAINLINK_ETH_USD, chainlinkABI, provider);
    const roundData = await priceFeed.latestRoundData();
    const ethPrice = Number(ethers.formatUnits(roundData.answer, 8));

    console.log(`${colors.yellow}📊 LIVE MARKET STATUS${colors.reset}`);
    console.log(`   Block: ${colors.bold}#${blockNumber}${colors.reset}`);
    console.log(`   Gas: ${colors.bold}${parseFloat(gasPriceGwei).toFixed(2)} Gwei${colors.reset}`);
    console.log(`   ETH: ${colors.bold}$${ethPrice.toFixed(2)}${colors.reset}\n`);

    let totalProfit = 0;
    let tradeCount = 0;

    console.log(`${colors.bold}${colors.green}⚡ LIVE ARBITRAGE SCANNER ACTIVE${colors.reset}\n`);

    // Listen to new blocks
    provider.on('block', async (newBlockNumber) => {
        const timestamp = new Date().toLocaleTimeString();
        
        // Fetch real prices from DEXs (this is actual on-chain data)
        try {
            const routerABI = [
                "function getAmountsOut(uint amountIn, address[] memory path) public view returns (uint[] memory amounts)"
            ];
            
            const uniswapRouter = new ethers.Contract(UNISWAP_ROUTER, routerABI, provider);
            const sushiswapRouter = new ethers.Contract(SUSHISWAP_ROUTER, routerABI, provider);
            
            const amountIn = ethers.parseEther("1"); // 1 ETH
            const path = [WETH, USDC];
            
            // Get REAL prices from both DEXs
            const uniswapAmounts = await uniswapRouter.getAmountsOut(amountIn, path);
            const sushiswapAmounts = await sushiswapRouter.getAmountsOut(amountIn, path);
            
            const uniswapPrice = Number(ethers.formatUnits(uniswapAmounts[1], 6));
            const sushiswapPrice = Number(ethers.formatUnits(sushiswapAmounts[1], 6));
            
            const priceDiff = Math.abs(uniswapPrice - sushiswapPrice);
            const profitPct = (priceDiff / Math.max(uniswapPrice, sushiswapPrice)) * 100;
            
            // Calculate potential profit
            const flashLoanAmount = 1000000; // 1M USDC
            const potentialProfit = (priceDiff / Math.max(uniswapPrice, sushiswapPrice)) * flashLoanAmount;
            
            if (potentialProfit > 100) { // Only show if profit > $100
                tradeCount++;
                totalProfit += potentialProfit;
                
                const buyDex = uniswapPrice < sushiswapPrice ? "Uniswap" : "Sushiswap";
                const sellDex = uniswapPrice < sushiswapPrice ? "Sushiswap" : "Uniswap";
                
                console.log(`${colors.bold}${colors.green}🎯 OPPORTUNITY #${tradeCount}${colors.reset} [Block ${newBlockNumber}] ${colors.cyan}${timestamp}${colors.reset}`);
                console.log(`   ${colors.yellow}Buy:${colors.reset}  ${buyDex} @ $${Math.min(uniswapPrice, sushiswapPrice).toFixed(2)}`);
                console.log(`   ${colors.yellow}Sell:${colors.reset} ${sellDex} @ $${Math.max(uniswapPrice, sushiswapPrice).toFixed(2)}`);
                console.log(`   ${colors.bold}${colors.green}💰 Profit: $${potentialProfit.toFixed(2)} (${profitPct.toFixed(3)}%)${colors.reset}`);
                console.log(`   ${colors.magenta}📈 Total Profit: $${totalProfit.toFixed(2)}${colors.reset}\n`);
            } else {
                // Show heartbeat every 5 blocks
                if (newBlockNumber % 5 === 0) {
                    console.log(`${colors.blue}⏱️  Block ${newBlockNumber} | Scanning... | Gas: ${parseFloat(gasPriceGwei).toFixed(2)} Gwei${colors.reset}`);
                }
            }
            
        } catch (error) {
            console.log(`${colors.red}⚠️  Error fetching prices: ${error.message}${colors.reset}`);
        }
    });

    // Keep alive
    console.log(`${colors.cyan}🔄 Monitoring live blockchain events... Press Ctrl+C to stop${colors.reset}\n`);
}

monitorLiveBlockchain().catch(console.error);
