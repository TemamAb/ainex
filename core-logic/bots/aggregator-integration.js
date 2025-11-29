const { ethers } = require("ethers");
const { FlashLoanAggregator } = require("../execution/flash-aggregator");

// Deployed Contract Address (from deploy.cjs output)
const AGGREGATOR_ADDRESS = "0x82BBAA3B0982D88741B275aE1752DB85CAfe3c65";

// ABI for ApexFlashAggregator
const AGGREGATOR_ABI = [
    "function executeArbitrage(address token, uint256 amount, bytes calldata data) external",
    "function owner() view returns (address)"
];

class AggregatorIntegration {
    constructor(provider, signer) {
        this.provider = provider;
        this.signer = signer;
        this.contract = new ethers.Contract(AGGREGATOR_ADDRESS, AGGREGATOR_ABI, signer);
        this.aiAggregator = new FlashLoanAggregator();
    }

    /**
     * Execute arbitrage using the best flash loan provider
     * @param {string} token - Token address to borrow
     * @param {string} amount - Amount to borrow (in wei)
     * @param {Object} arbDetails - Router and trade details
     */
    async executeTrade(token, amount, arbDetails) {
        console.log(`🤖 Analyzing Flash Loan Providers for ${amount} of ${token}...`);

        // 1. AI Selection of Best Provider
        // Convert amount to number for AI logic (simplified)
        const amountNum = Number(ethers.formatUnits(amount, 6)); // Assuming USDC/USDT
        const bestProviderName = await this.aiAggregator.selectOptimalProvider("USDC", amountNum);

        console.log(`✅ AI Selected Provider: ${bestProviderName}`);

        // Map Provider Name to Enum ID
        // AAVE_V3=0, BALANCER_V2=1, UNISWAP_V3=2, DYDX=3, MAKER=4
        const providerMap = {
            'AAVE_V3': 0,
            'BALANCER_V2': 1,
            'UNISWAP_V3': 2,
            'DYDX': 3,
            'MAKER': 4
        };
        const providerId = providerMap[bestProviderName] || 0;

        // 2. Encode Arbitrage Data
        // struct ArbitrageData { router1, router2, tokenIn, tokenMid, amountIn, minAmountMid, minAmountFinal, provider }
        const abiCoder = new ethers.AbiCoder();
        const data = abiCoder.encode(
            ['address', 'address', 'address', 'address', 'uint256', 'uint256', 'uint256', 'uint8'],
            [
                arbDetails.router1,
                arbDetails.router2,
                token,
                arbDetails.tokenMid,
                amount,
                arbDetails.minAmountMid,
                arbDetails.minAmountFinal,
                providerId // NEW: Provider Enum
            ]
        );

        // 3. Execute Transaction
        console.log(`🚀 Submitting Transaction to ApexFlashAggregator...`);
        try {
            const tx = await this.contract.executeArbitrage(token, amount, data);
            console.log(`✅ Transaction Sent: ${tx.hash}`);
            return tx;
        } catch (error) {
            console.error(`❌ Execution Failed: ${error.message}`);
            throw error;
        }
    }
}

module.exports = { AggregatorIntegration, AGGREGATOR_ADDRESS };
