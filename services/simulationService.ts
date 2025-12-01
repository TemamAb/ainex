import { TradeSignal, FlashLoanMetric } from '../types';

// SIM Mode Simulation Service
// Provides simulated data for testing arbitrage strategies without real trades

export interface SimulationMetrics {
    profitProjection: {
        hourly: number;
        daily: number;
        weekly: number;
        monthly: number;
    };
    latencyMetrics: {
        average: number;
        min: number;
        max: number;
        lastUpdate: number;
    };
    mevMetrics: {
        frontRunningAttempts: number;
        detectedAttacks: number;
        blockedAttacks: number;
        successRate: number;
    };
    flashLoanMetrics: FlashLoanMetric[];
    confidence: number;
    variance: number;
}

export interface SimulationResult {
    success: boolean;
    profit: number;
    gasUsed: number;
    latency: number;
    timestamp: number;
}

// Generate simulated profit projections based on market conditions
export const generateProfitProjection = (): SimulationMetrics['profitProjection'] => {
    // Base profit rates with some randomness
    const baseHourly = 25 + Math.random() * 50; // $25-75/hour

    return {
        hourly: baseHourly,
        daily: baseHourly * 24,
        weekly: baseHourly * 168,
        monthly: baseHourly * 720
    };
};

// Simulate latency metrics for different operations
export const generateLatencyMetrics = (): SimulationMetrics['latencyMetrics'] => {
    return {
        average: 35 + Math.random() * 30, // 35-65ms average
        min: 8 + Math.random() * 7, // 8-15ms min
        max: 100 + Math.random() * 100, // 100-200ms max
        lastUpdate: Date.now()
    };
};

// Simulate MEV protection metrics
export const generateMEVMetrics = (): SimulationMetrics['mevMetrics'] => {
    const attempts = Math.floor(Math.random() * 10);
    const detected = Math.floor(attempts * 0.8);
    const blocked = Math.floor(detected * 0.9);

    return {
        frontRunningAttempts: attempts,
        detectedAttacks: detected,
        blockedAttacks: blocked,
        successRate: blocked > 0 ? (blocked / detected) * 100 : 100
    };
};

// Get flash loan provider metrics
export const getFlashLoanMetrics = (): FlashLoanMetric[] => {
    return [
        {
            provider: 'Aave',
            utilization: 60 + Math.random() * 20,
            liquidityAvailable: '$8.2B'
        },
        {
            provider: 'Compound',
            utilization: 65 + Math.random() * 25,
            liquidityAvailable: '$3.1B'
        },
        {
            provider: 'Uniswap V3',
            utilization: 45 + Math.random() * 30,
            liquidityAvailable: '$2.8B'
        },
        {
            provider: 'Balancer',
            utilization: 50 + Math.random() * 20,
            liquidityAvailable: '$1.8B'
        }
    ];
};

// Calculate confidence score based on simulation performance
export const calculateConfidenceScore = (
    historicalResults: SimulationResult[],
    currentMetrics: SimulationMetrics
): number => {
    if (historicalResults.length === 0) return 50;

    // Calculate success rate
    const successRate = historicalResults.filter(r => r.success).length / historicalResults.length;

    // Calculate average profit
    const avgProfit = historicalResults.reduce((sum, r) => sum + r.profit, 0) / historicalResults.length;

    // Calculate latency consistency
    const avgLatency = historicalResults.reduce((sum, r) => sum + r.latency, 0) / historicalResults.length;

    // Weight the factors
    const confidence = (
        successRate * 0.4 + // 40% weight on success rate
        Math.min(avgProfit / 100, 1) * 0.3 + // 30% weight on profit (capped at $100)
        Math.max(0, 1 - avgLatency / 100) * 0.3 // 30% weight on latency (better when lower)
    ) * 100;

    return Math.min(95, Math.max(10, confidence));
};

// Calculate variance between SIM and expected LIVE results
export const calculateVariance = (confidence: number): number => {
    // Higher confidence = lower variance
    // 95% confidence = ~5% variance
    // 50% confidence = ~25% variance
    return Math.max(5, 50 - confidence / 2);
};

// Simulate a single arbitrage opportunity
export const simulateArbitrageOpportunity = (): SimulationResult => {
    const success = Math.random() > 0.15; // 85% success rate
    const baseProfit = 10 + Math.random() * 90; // $10-100 profit
    const gasCost = 5 + Math.random() * 15; // $5-20 gas
    const latency = 20 + Math.random() * 80; // 20-100ms

    return {
        success,
        profit: success ? baseProfit - gasCost : -gasCost,
        gasUsed: gasCost,
        latency,
        timestamp: Date.now()
    };
};

// Run continuous simulation for SIM mode
export const runSimulationLoop = (
    onMetricsUpdate: (metrics: SimulationMetrics) => void,
    onNewSignal: (signal: TradeSignal) => void,
    duration: number = 30000 // 30 seconds default
): () => void => {
    let isRunning = true;
    const results: SimulationResult[] = [];
    let confidence = 50;

    const updateMetrics = () => {
        const metrics: SimulationMetrics = {
            profitProjection: generateProfitProjection(),
            latencyMetrics: generateLatencyMetrics(),
            mevMetrics: generateMEVMetrics(),
            flashLoanMetrics: getFlashLoanMetrics(),
            confidence,
            variance: calculateVariance(confidence)
        };

        onMetricsUpdate(metrics);
    };

    // Initial update
    updateMetrics();

    // Simulation loop
    const interval = setInterval(() => {
        if (!isRunning) return;

        // Simulate new arbitrage opportunity
        const result = simulateArbitrageOpportunity();
        results.push(result);

        // Update confidence based on results
        confidence = calculateConfidenceScore(results.slice(-20), {
            profitProjection: generateProfitProjection(),
            latencyMetrics: generateLatencyMetrics(),
            mevMetrics: generateMEVMetrics(),
            flashLoanMetrics: getFlashLoanMetrics(),
            confidence,
            variance: calculateVariance(confidence)
        });

        // Generate trade signal if successful
        if (result.success && Math.random() > 0.7) { // 30% chance of generating signal
            const signal: TradeSignal = {
                id: `sim-${Date.now()}`,
                blockNumber: Math.floor(Date.now() / 1000),
                pair: ['ETH/USDC', 'BTC/USDT', 'ARB/ETH'][Math.floor(Math.random() * 3)],
                chain: ['Ethereum', 'Arbitrum', 'Base'][Math.floor(Math.random() * 3)] as any,
                action: ['FLASH_LOAN', 'MEV_BUNDLE', 'LONG'][Math.floor(Math.random() * 3)] as any,
                confidence: confidence,
                expectedProfit: result.profit.toString(),
                route: ['Uniswap', 'Sushiswap', 'PancakeSwap'].slice(0, Math.floor(Math.random() * 3) + 1),
                timestamp: Date.now(),
                status: 'DETECTED'
            };

            onNewSignal(signal);
        }

        updateMetrics();
    }, 2000); // Update every 2 seconds

    // Stop after duration
    setTimeout(() => {
        isRunning = false;
        clearInterval(interval);
    }, duration);

    // Return cleanup function
    return () => {
        isRunning = false;
        clearInterval(interval);
    };
};

// Get profit attribution by strategy, chain, and pair
export const getProfitAttribution = () => {
    return {
        byStrategy: {
            'Arbitrage': 0.45,
            'Liquidation': 0.30,
            'MEV': 0.25
        },
        byChain: {
            'Ethereum': 0.50,
            'Arbitrum': 0.35,
            'Base': 0.15
        },
        byPair: {
            'ETH/USDC': 0.25,
            'BTC/USDT': 0.20,
            'ARB/ETH': 0.15,
            'LINK/USDC': 0.12,
            'UNI/ETH': 0.10,
            'Others': 0.18
        }
    };
};
