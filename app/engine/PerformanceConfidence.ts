/**
 * PERFORMANCE CONFIDENCE SYSTEM
 * Calculates expected variance between SIM mode and LIVE mode
 * Based on real-time market conditions and historical accuracy
 */

export interface VarianceFactors {
    gasCost: number;        // ±2-3%
    slippage: number;       // ±1-2%
    mevRisk: number;        // ±1-2%
    networkLatency: number; // ±0.5-1%
    priceMovement: number;  // ±1-2%
    reversion: number;      // ±1-2%
}

export interface ConfidenceMetrics {
    expectedVariance: number;      // Total expected variance (%)
    confidenceScore: number;       // 0-100 confidence score
    varianceFactors: VarianceFactors;
    marketCondition: 'normal' | 'volatile' | 'extreme';
    lastUpdated: number;
}

export interface PerformanceHistory {
    simPredicted: number;
    liveActual: number;
    variance: number;
    timestamp: number;
}

class PerformanceConfidenceEngine {
    private history: PerformanceHistory[] = [];
    private readonly MAX_HISTORY = 100;

    // Baseline variance factors (%)
    private readonly BASELINE_VARIANCE = {
        gasCost: 2.5,
        slippage: 1.5,
        mevRisk: 1.5,
        networkLatency: 0.75,
        priceMovement: 1.5,
        reversion: 1.5
    };

    /**
     * Calculate current confidence metrics based on market conditions
     */
    calculateConfidence(
        gasPrice: number = 20,      // Current gas price in gwei
        volatility: number = 25,    // Market volatility (0-100)
        mevRiskScore: number = 0.3  // MEV risk (0-1)
    ): ConfidenceMetrics {
        const varianceFactors = this.calculateVarianceFactors(gasPrice, volatility, mevRiskScore);
        const expectedVariance = this.calculateTotalVariance(varianceFactors);
        const marketCondition = this.determineMarketCondition(gasPrice, volatility);
        const confidenceScore = this.calculateConfidenceScore(expectedVariance, marketCondition);

        return {
            expectedVariance,
            confidenceScore,
            varianceFactors,
            marketCondition,
            lastUpdated: Date.now()
        };
    }

    /**
     * Calculate individual variance factors based on current conditions
     */
    private calculateVarianceFactors(
        gasPrice: number,
        volatility: number,
        mevRiskScore: number
    ): VarianceFactors {
        // Gas cost variance increases with gas price volatility
        const gasCostVariance = this.BASELINE_VARIANCE.gasCost * (1 + (gasPrice - 20) / 100);

        // Slippage variance increases with market volatility
        const slippageVariance = this.BASELINE_VARIANCE.slippage * (1 + volatility / 100);

        // MEV risk variance based on MEV risk score
        const mevVariance = this.BASELINE_VARIANCE.mevRisk * (1 + mevRiskScore * 2);

        // Network latency - relatively stable
        const latencyVariance = this.BASELINE_VARIANCE.networkLatency;

        // Price movement variance increases with volatility
        const priceMovementVariance = this.BASELINE_VARIANCE.priceMovement * (1 + volatility / 50);

        // Reversion variance increases with volatility
        const reversionVariance = this.BASELINE_VARIANCE.reversion * (1 + volatility / 75);

        return {
            gasCost: Math.min(gasCostVariance, 5),           // Cap at 5%
            slippage: Math.min(slippageVariance, 3),         // Cap at 3%
            mevRisk: Math.min(mevVariance, 4),               // Cap at 4%
            networkLatency: latencyVariance,
            priceMovement: Math.min(priceMovementVariance, 3), // Cap at 3%
            reversion: Math.min(reversionVariance, 3)        // Cap at 3%
        };
    }

    /**
     * Calculate total expected variance
     */
    private calculateTotalVariance(factors: VarianceFactors): number {
        // Sum all variance factors
        const total = Object.values(factors).reduce((sum, val) => sum + val, 0);

        // Apply square root rule for independent factors (more realistic)
        const adjustedVariance = Math.sqrt(
            Object.values(factors).reduce((sum, val) => sum + val * val, 0)
        );

        return Math.round(adjustedVariance * 10) / 10; // Round to 1 decimal
    }

    /**
     * Determine market condition based on gas and volatility
     */
    private determineMarketCondition(
        gasPrice: number,
        volatility: number
    ): 'normal' | 'volatile' | 'extreme' {
        if (gasPrice > 100 || volatility > 70) {
            return 'extreme';
        } else if (gasPrice > 50 || volatility > 40) {
            return 'volatile';
        }
        return 'normal';
    }

    /**
     * Calculate confidence score (0-100)
     * Lower variance = higher confidence
     */
    private calculateConfidenceScore(
        expectedVariance: number,
        marketCondition: 'normal' | 'volatile' | 'extreme'
    ): number {
        // Base confidence from variance (5% variance = 90 confidence, 15% variance = 70 confidence)
        let confidence = 100 - (expectedVariance * 2);

        // Adjust for market conditions
        if (marketCondition === 'volatile') {
            confidence -= 5;
        } else if (marketCondition === 'extreme') {
            confidence -= 15;
        }

        // Apply historical accuracy if available
        if (this.history.length > 10) {
            const historicalAccuracy = this.calculateHistoricalAccuracy();
            confidence = confidence * 0.7 + historicalAccuracy * 0.3;
        }

        return Math.max(0, Math.min(100, Math.round(confidence)));
    }

    /**
     * Record actual performance for calibration
     */
    recordPerformance(simPredicted: number, liveActual: number): void {
        const variance = Math.abs((liveActual - simPredicted) / simPredicted) * 100;

        this.history.push({
            simPredicted,
            liveActual,
            variance,
            timestamp: Date.now()
        });

        // Keep only recent history
        if (this.history.length > this.MAX_HISTORY) {
            this.history.shift();
        }
    }

    /**
     * Calculate historical accuracy (0-100)
     */
    private calculateHistoricalAccuracy(): number {
        if (this.history.length === 0) return 85; // Default

        const avgVariance = this.history.reduce((sum, h) => sum + h.variance, 0) / this.history.length;

        // Convert variance to accuracy score
        // 5% avg variance = 90 accuracy, 15% avg variance = 70 accuracy
        return Math.max(0, Math.min(100, 100 - (avgVariance * 2)));
    }

    /**
     * Get performance statistics
     */
    getPerformanceStats(): {
        totalRecords: number;
        averageVariance: number;
        historicalAccuracy: number;
        recentTrend: 'improving' | 'stable' | 'degrading';
    } {
        if (this.history.length === 0) {
            return {
                totalRecords: 0,
                averageVariance: 0,
                historicalAccuracy: 85,
                recentTrend: 'stable'
            };
        }

        const avgVariance = this.history.reduce((sum, h) => sum + h.variance, 0) / this.history.length;
        const historicalAccuracy = this.calculateHistoricalAccuracy();

        // Calculate trend from recent vs older records
        const recentCount = Math.min(10, this.history.length);
        const recent = this.history.slice(-recentCount);
        const older = this.history.slice(0, -recentCount);

        let recentTrend: 'improving' | 'stable' | 'degrading' = 'stable';
        if (older.length > 0) {
            const recentAvg = recent.reduce((sum, h) => sum + h.variance, 0) / recent.length;
            const olderAvg = older.reduce((sum, h) => sum + h.variance, 0) / older.length;

            if (recentAvg < olderAvg - 1) {
                recentTrend = 'improving';
            } else if (recentAvg > olderAvg + 1) {
                recentTrend = 'degrading';
            }
        }

        return {
            totalRecords: this.history.length,
            averageVariance: Math.round(avgVariance * 10) / 10,
            historicalAccuracy,
            recentTrend
        };
    }

    /**
     * Get recent performance history
     */
    getRecentHistory(count: number = 20): PerformanceHistory[] {
        return this.history.slice(-count);
    }

    /**
     * Clear performance history
     */
    clearHistory(): void {
        this.history = [];
    }
}

// Singleton instance
export const performanceConfidence = new PerformanceConfidenceEngine();

// Export for testing
export { PerformanceConfidenceEngine };
