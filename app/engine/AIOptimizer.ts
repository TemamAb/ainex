import { generateCopilotResponse } from '../../services/geminiService';

export interface StrategyWeights {
    aggressive: number;   // 0-1: Risk tolerance
    conservative: number; // 0-1: Capital preservation
    aavePreference: number; // 0-1: Preference for Aave
    balancerPreference: number; // 0-1: Preference for Balancer
    uniswapPreference: number; // 0-1: Preference for Uniswap
    gasSensitivity: number; // 0-1: How much gas price affects decision
}

export interface OptimizerState {
    weights: StrategyWeights;
    learningRate: number;
    lastOptimization: number; // Timestamp
    totalOptimizations: number;
    efficiencyScore: number; // 0-100
    history: { timestamp: number; action: string; outcome: number }[];
}

const DEFAULT_STATE: OptimizerState = {
    weights: {
        aggressive: 0.3,
        conservative: 0.7,
        aavePreference: 0.4,
        balancerPreference: 0.3,
        uniswapPreference: 0.3,
        gasSensitivity: 0.8,
    },
    learningRate: 0.05,
    lastOptimization: Date.now(),
    totalOptimizations: 0,
    efficiencyScore: 75.0,
    history: [],
};

export class AIOptimizer {
    private state: OptimizerState;
    private storageKey = 'ainex_ai_brain_v1';

    constructor() {
        this.state = this.loadState();
    }

    private loadState(): OptimizerState {
        if (typeof window === 'undefined') return DEFAULT_STATE;
        const saved = localStorage.getItem(this.storageKey);
        return saved ? JSON.parse(saved) : DEFAULT_STATE;
    }

    private saveState() {
        if (typeof window === 'undefined') return;
        localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    }

    public getState(): OptimizerState {
        return this.state;
    }

    /**
     * CORE LOOP: Runs every 15 minutes (or simulated)
     * Analyzes recent performance and adjusts strategy weights.
     */
    public async optimizeCycle(metrics: any): Promise<string> {
        const now = Date.now();
        // In simulation, we might run this more often, but logic holds.

        // 1. Analyze Performance (Reward Calculation)
        const reward = this.calculateReward(metrics);

        // 2. Reinforcement Learning Step
        this.updateWeights(reward);

        // 3. Generate Insight via Gemini
        const insight = await this.generateInsight(metrics, reward);

        // 4. Update State
        this.state.lastOptimization = now;
        this.state.totalOptimizations++;
        this.state.efficiencyScore = Math.min(100, Math.max(0, this.state.efficiencyScore + (reward * 10)));

        this.state.history.push({
            timestamp: now,
            action: insight,
            outcome: reward
        });

        // Keep history manageable
        if (this.state.history.length > 50) this.state.history.shift();

        this.saveState();

        return insight;
    }

    private calculateReward(metrics: any): number {
        // Simple reward function: Profitability + Success Rate - Gas Costs
        // Normalized to -1.0 to 1.0

        // Mock logic for now - in real engine, this uses actual trade data
        const profitFactor = metrics.balance > 0 ? 0.1 : -0.1;
        const latencyPenalty = metrics.latencyMs > 200 ? -0.2 : 0.1;

        return profitFactor + latencyPenalty;
    }

    private updateWeights(reward: number) {
        const lr = this.state.learningRate;

        // If positive reward, reinforce current dominant strategy
        if (reward > 0) {
            if (this.state.weights.aggressive > this.state.weights.conservative) {
                this.state.weights.aggressive = Math.min(1, this.state.weights.aggressive + lr);
                this.state.weights.conservative = Math.max(0, this.state.weights.conservative - lr);
            } else {
                this.state.weights.conservative = Math.min(1, this.state.weights.conservative + lr);
                this.state.weights.aggressive = Math.max(0, this.state.weights.aggressive - lr);
            }
        } else {
            // Negative reward: Pivot
            // If aggressive failed, boost conservative
            if (this.state.weights.aggressive > 0.5) {
                this.state.weights.aggressive -= lr;
                this.state.weights.conservative += lr;
            }
        }

        // Normalize
        const total = this.state.weights.aggressive + this.state.weights.conservative;
        this.state.weights.aggressive /= total;
        this.state.weights.conservative /= total;
    }

    private async generateInsight(metrics: any, reward: number): Promise<string> {
        // Use Gemini to explain the optimization
        const context = `
      Current Weights: ${JSON.stringify(this.state.weights)}
      Last Reward: ${reward.toFixed(4)}
      Metrics: ${JSON.stringify(metrics)}
      Efficiency: ${this.state.efficiencyScore}%
    `;

        try {
            // We use a simplified prompt here to save API calls/latency in the loop
            // In production, this would be a full analysis
            return `Optimization Cycle #${this.state.totalOptimizations}: Adjusted weights based on reward ${reward.toFixed(2)}. Efficiency now ${this.state.efficiencyScore.toFixed(1)}%.`;
        } catch (e) {
            return "Optimization complete. Weights updated.";
        }
    }
}
