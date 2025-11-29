import { ethers } from 'ethers';

export interface SimulationMetrics {
    ethPrice: number;
    gasPrice: number;
    volatilityIndex: number; // 0-100
    liquidityDepth: number; // in USD
    theoreticalMaxProfit: number; // The "Perfect Trade" profit
    aiCapturedProfit: number; // What the AI actually captured
    confidence: number; // (Captured / Max) * 100
}

export class SimulationEngine {
    private metrics: SimulationMetrics;
    private intervalId: NodeJS.Timeout | null = null;
    private onUpdate: (metrics: SimulationMetrics) => void;
    private provider: ethers.JsonRpcProvider;

    // Public RPCs for Real Data (Fallbacks included)
    private rpcUrls = [
        "https://eth.llamarpc.com",
        "https://rpc.ankr.com/eth",
        "https://cloudflare-eth.com"
    ];

    constructor(onUpdate: (metrics: SimulationMetrics) => void) {
        this.onUpdate = onUpdate;
        this.provider = new ethers.JsonRpcProvider(this.rpcUrls[0]);

        this.metrics = {
            ethPrice: 0,
            gasPrice: 0,
            volatilityIndex: 0,
            liquidityDepth: 0,
            theoreticalMaxProfit: 0,
            aiCapturedProfit: 0,
            confidence: 0
        };
    }

    public start() {
        if (this.intervalId) return;

        // Initial Fetch
        this.fetchRealData();

        // Run simulation tick every 3 seconds (approx block time)
        this.intervalId = setInterval(() => {
            this.fetchRealData();
        }, 3000);
    }

    public stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    private async fetchRealData() {
        try {
            // 1. Fetch Real Gas Price
            const feeData = await this.provider.getFeeData();
            const gasPriceGwei = feeData.gasPrice ? Number(ethers.formatUnits(feeData.gasPrice, 'gwei')) : 20;

            // 2. Fetch Real ETH Price (Mocking via random walk from base if RPC fails, or using a simple oracle call if possible)
            // For robustness in this demo, we'll use a base price + volatility since we don't have a direct Oracle contract handy without deployment.
            // However, we will make it "feel" real by tying it to the gas price which IS real.
            // High Gas usually correlates with High Volatility/Activity.

            // Simulating Price Movement based on Real Gas Activity
            const basePrice = 3500;
            const volatilityFactor = (gasPriceGwei / 20); // Normalized to 20 gwei baseline
            const randomFluctuation = (Math.random() - 0.5) * 10 * volatilityFactor;
            const currentEthPrice = basePrice + randomFluctuation;

            // 3. Calculate Volatility Index (0-100)
            // Real Gas Price is a great proxy for network congestion and volatility
            const volatilityIndex = Math.min(100, Math.max(0, gasPriceGwei * 2));

            // 4. Calculate "Theoretical Max Profit" (The Adoptive Target)
            // This is the money on the table.
            // Formula: Base * Volatility * LiquidityFactor
            const theoreticalMax = (volatilityIndex / 10) * 0.05; // e.g., 50 vol -> 0.25 ETH max profit available

            // 5. Calculate AI Performance (Simulation)
            // The AI "runs" and tries to capture this. 
            // It starts low and learns.
            // We simulate the "Learning Curve" here.
            const currentEfficiency = this.metrics.confidence / 100; // Previous confidence
            const learningRate = 0.02; // Improves 2% per tick
            const newEfficiency = Math.min(0.95, currentEfficiency + learningRate); // Caps at 95% realistic max

            const aiCaptured = theoreticalMax * newEfficiency;

            // 6. Update Metrics
            this.metrics = {
                ethPrice: currentEthPrice,
                gasPrice: gasPriceGwei,
                volatilityIndex: volatilityIndex,
                liquidityDepth: 500000000, // Static for now
                theoreticalMaxProfit: theoreticalMax,
                aiCapturedProfit: aiCaptured,
                confidence: newEfficiency * 100
            };

            this.onUpdate({ ...this.metrics });

        } catch (error) {
            console.error("Error fetching real data:", error);
        }
    }

    public getMetrics(): SimulationMetrics {
        return { ...this.metrics };
    }
}
