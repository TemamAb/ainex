import { ethers } from 'ethers';
import { detectArbitrageOpportunities, executeFlashLoanArbitrage } from './arbitrageService';
import { validateExecutionReadiness, executeTrade } from './executionService';
import type { TradeSignal, BotStatus } from '../types';

// TRI-TIER BOT SYSTEM
// Detection -> Decision -> Execution with AI Optimization

interface BotTier {
    name: string;
    status: 'ACTIVE' | 'IDLE' | 'ERROR';
    lastActivity: number;
    performance: number;
}

interface AiOptimization {
    strategyWeights: { [key: string]: number };
    riskAdjustment: number;
    profitMultiplier: number;
    confidenceThreshold: number;
}

class TriTierBotSystem {
    private detectionBot: BotTier;
    private decisionBot: BotTier;
    private executionBot: BotTier;
    private aiOptimizer: AiOptimization;
    private isRunning: boolean = false;
    private onNewSignal?: (signal: TradeSignal) => void;
    private onBotStatusUpdate?: (statuses: BotStatus[]) => void;

    constructor() {
        this.detectionBot = {
            name: 'Detection Bot',
            status: 'IDLE',
            lastActivity: Date.now(),
            performance: 100
        };

        this.decisionBot = {
            name: 'Decision Bot',
            status: 'IDLE',
            lastActivity: Date.now(),
            performance: 100
        };

        this.executionBot = {
            name: 'Execution Bot',
            status: 'IDLE',
            lastActivity: Date.now(),
            performance: 100
        };

        this.aiOptimizer = {
            strategyWeights: {
                'dex_arbitrage': 0.6,
                'cross_chain': 0.3,
                'flash_loan': 0.1
            },
            riskAdjustment: 1.0,
            profitMultiplier: 1.0,
            confidenceThreshold: 85
        };
    }

    async start(
        onNewSignal: (signal: TradeSignal) => void,
        onBotStatusUpdate: (statuses: BotStatus[]) => void
    ): Promise<() => void> {
        this.isRunning = true;
        this.onNewSignal = onNewSignal;
        this.onBotStatusUpdate = onBotStatusUpdate;

        console.log('[TRI-TIER BOT] Starting Detection -> Decision -> Execution pipeline...');

        // Start detection loop
        const detectionInterval = setInterval(() => this.runDetectionCycle(), 3000);

        // Start decision loop
        const decisionInterval = setInterval(() => this.runDecisionCycle(), 5000);

        // Start execution loop
        const executionInterval = setInterval(() => this.runExecutionCycle(), 10000);

        // Start AI optimization loop
        const aiInterval = setInterval(() => this.runAiOptimization(), 30000);

        return () => {
            this.isRunning = false;
            clearInterval(detectionInterval);
            clearInterval(decisionInterval);
            clearInterval(executionInterval);
            clearInterval(aiInterval);
        };
    }

    private async runDetectionCycle(): Promise<void> {
        if (!this.isRunning) return;

        try {
            this.detectionBot.status = 'ACTIVE';
            this.detectionBot.lastActivity = Date.now();

            // Detect arbitrage opportunities
            const opportunities = await detectArbitrageOpportunities();

            if (opportunities.length > 0) {
                console.log(`[DETECTION BOT] Found ${opportunities.length} arbitrage opportunities`);

                // Convert to TradeSignals and pass to decision bot
                for (const opp of opportunities) {
                    const signal: TradeSignal = {
                        id: `arb_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                        blockNumber: await this.getCurrentBlockNumber(),
                        pair: this.getTokenPairName(opp.tokenIn, opp.tokenOut),
                        chain: 'Ethereum',
                        action: 'FLASH_LOAN',
                        confidence: opp.confidence,
                        expectedProfit: opp.expectedProfit.toString(),
                        route: opp.route,
                        timestamp: Date.now(),
                        txHash: '',
                        status: 'DETECTED'
                    };

                    if (this.onNewSignal) {
                        this.onNewSignal(signal);
                    }
                }

                this.detectionBot.performance = Math.min(100, this.detectionBot.performance + 1);
            }

            this.updateBotStatuses();
        } catch (error) {
            console.error('[DETECTION BOT] Error:', error);
            this.detectionBot.status = 'ERROR';
            this.detectionBot.performance = Math.max(0, this.detectionBot.performance - 5);
        } finally {
            if (this.detectionBot.status === 'ACTIVE') {
                this.detectionBot.status = 'IDLE';
            }
        }
    }

    private async runDecisionCycle(): Promise<void> {
        if (!this.isRunning) return;

        try {
            this.decisionBot.status = 'ACTIVE';
            this.decisionBot.lastActivity = Date.now();

            // Decision logic would analyze signals and apply AI optimization
            // For now, signals are passed through with AI-adjusted confidence

            this.decisionBot.performance = Math.min(100, this.decisionBot.performance + 0.5);
            this.updateBotStatuses();
        } catch (error) {
            console.error('[DECISION BOT] Error:', error);
            this.decisionBot.status = 'ERROR';
            this.decisionBot.performance = Math.max(0, this.decisionBot.performance - 5);
        } finally {
            if (this.decisionBot.status === 'ACTIVE') {
                this.decisionBot.status = 'IDLE';
            }
        }
    }

    private async runExecutionCycle(): Promise<void> {
        if (!this.isRunning) return;

        try {
            this.executionBot.status = 'ACTIVE';
            this.executionBot.lastActivity = Date.now();

            // Check for pending signals that meet execution criteria
            // This would be integrated with the signal queue from MasterDashboard

            // Validate execution readiness (gasless mode, Pimlico health, etc.)
            const ready = await validateExecutionReadiness();
            if (!ready) {
                console.warn('[EXECUTION BOT] System not ready for execution');
                return;
            }

            this.executionBot.performance = Math.min(100, this.executionBot.performance + 2);
            this.updateBotStatuses();
        } catch (error) {
            console.error('[EXECUTION BOT] Error:', error);
            this.executionBot.status = 'ERROR';
            this.executionBot.performance = Math.max(0, this.executionBot.performance - 10);
        } finally {
            if (this.executionBot.status === 'ACTIVE') {
                this.executionBot.status = 'IDLE';
            }
        }
    }

    private async runAiOptimization(): Promise<void> {
        if (!this.isRunning) return;

        try {
            // AI optimization logic - adjust strategy weights based on performance
            const totalPerformance = this.detectionBot.performance + this.decisionBot.performance + this.executionBot.performance;
            const avgPerformance = totalPerformance / 3;

            // Adjust risk and profit multipliers based on performance
            if (avgPerformance > 90) {
                this.aiOptimizer.riskAdjustment = Math.min(1.2, this.aiOptimizer.riskAdjustment + 0.01);
                this.aiOptimizer.profitMultiplier = Math.min(1.15, this.aiOptimizer.profitMultiplier + 0.005);
            } else if (avgPerformance < 70) {
                this.aiOptimizer.riskAdjustment = Math.max(0.8, this.aiOptimizer.riskAdjustment - 0.01);
                this.aiOptimizer.profitMultiplier = Math.max(0.85, this.aiOptimizer.profitMultiplier - 0.005);
            }

            console.log(`[AI OPTIMIZER] Performance: ${avgPerformance.toFixed(1)}%, Risk: ${this.aiOptimizer.riskAdjustment.toFixed(2)}x, Profit: ${this.aiOptimizer.profitMultiplier.toFixed(2)}x`);
        } catch (error) {
            console.error('[AI OPTIMIZER] Error:', error);
        }
    }

    private updateBotStatuses(): void {
        if (this.onBotStatusUpdate) {
            const statuses: BotStatus[] = [
                {
                    id: 'detection-bot',
                    name: this.detectionBot.name,
                    type: 'Detection',
                    tier: 'TIER_1_ARBITRAGE',
                    status: this.detectionBot.status === 'ACTIVE' ? 'ACTIVE' : 'STANDBY',
                    uptime: '99.8%',
                    efficiency: this.detectionBot.performance
                },
                {
                    id: 'decision-bot',
                    name: this.decisionBot.name,
                    type: 'Decision',
                    tier: 'TIER_2_LIQUIDATION',
                    status: this.decisionBot.status === 'ACTIVE' ? 'ACTIVE' : 'STANDBY',
                    uptime: '99.5%',
                    efficiency: this.decisionBot.performance
                },
                {
                    id: 'execution-bot',
                    name: this.executionBot.name,
                    type: 'Execution',
                    tier: 'TIER_3_MEV',
                    status: this.executionBot.status === 'ACTIVE' ? 'ACTIVE' : 'STANDBY',
                    uptime: '99.2%',
                    efficiency: this.executionBot.performance
                }
            ];
            this.onBotStatusUpdate(statuses);
        }
    }

    private async getCurrentBlockNumber(): Promise<number> {
        try {
            const { getEthereumProvider } = await import('../blockchain/providers');
            const provider = await getEthereumProvider();
            return await provider.getBlockNumber();
        } catch (error) {
            console.error('Error getting block number:', error);
            return 0;
        }
    }

    private getTokenPairName(tokenIn: string, tokenOut: string): string {
        // Simplified token name mapping
        const tokenNames: { [key: string]: string } = {
            '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': 'WETH',
            '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 'USDC',
            '0x6B175474E89094C44Da98b954EedeAC495271d0F': 'DAI'
        };

        const inName = tokenNames[tokenIn] || 'ETH';
        const outName = tokenNames[tokenOut] || 'USDC';

        return `${inName}/${outName}`;
    }
}

export { TriTierBotSystem };
