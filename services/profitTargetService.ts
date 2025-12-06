import { ProfitTargetSettings, TradeSettings } from '../types';

// PROFIT TARGET SERVICE
// Calculates optimal profit targets based on market conditions, AI performance, and risk metrics
// Provides user override capability while maintaining AI-driven optimization

interface MarketConditions {
  volatility: number; // 0-1 (0 = stable, 1 = highly volatile)
  opportunityDensity: number; // 0-1 (number of arbitrage signals per minute)
  liquidityDepth: number; // 0-1 (available flash loan liquidity)
  gasEfficiency: number; // 0-1 (gas price relative to historical average)
}

interface AIPerformanceMetrics {
  confidence: number; // 0-1 (AI prediction accuracy)
  quantumAdvantage: number; // 0-1 (quantum optimization benefit)
  riskScore: number; // 0-1 (current risk assessment)
  successRate: number; // 0-1 (trade execution success rate)
}

class ProfitTargetService {
  private baseTargets = {
    hourly: 0.08, // Base optimal hourly target in ETH
    daily: 2.5,   // Base optimal daily target in ETH
    weekly: 15    // Base optimal weekly target in ETH
  };

  private adjustmentFactors = {
    volatilityMultiplier: {
      low: 1.2,    // 20% increase in stable markets
      medium: 1.0, // Baseline
      high: 0.7    // 30% reduction in volatile markets
    },
    opportunityMultiplier: {
      low: 0.8,    // 20% reduction with few opportunities
      medium: 1.0, // Baseline
      high: 1.4    // 40% increase with many opportunities
    },
    aiConfidenceMultiplier: {
      low: 0.85,   // 15% reduction with low AI confidence
      medium: 1.0, // Baseline
      high: 1.25   // 25% increase with high AI confidence
    },
    riskAdjustment: {
      low: 1.1,    // 10% increase with low risk
      medium: 1.0, // Baseline
      high: 0.75   // 25% reduction with high risk
    }
  };

  // Calculate optimal profit targets based on current market conditions and AI performance
  calculateOptimalTargets(
    marketConditions: MarketConditions,
    aiMetrics: AIPerformanceMetrics
  ): ProfitTargetSettings['optimal'] {
    // Determine adjustment categories
    const volatilityLevel = this.getVolatilityLevel(marketConditions.volatility);
    const opportunityLevel = this.getOpportunityLevel(marketConditions.opportunityDensity);
    const aiConfidenceLevel = this.getAIConfidenceLevel(aiMetrics.confidence);
    const riskLevel = this.getRiskLevel(aiMetrics.riskScore);

    // Calculate multipliers
    const volatilityMult = this.adjustmentFactors.volatilityMultiplier[volatilityLevel];
    const opportunityMult = this.adjustmentFactors.opportunityMultiplier[opportunityLevel];
    const aiConfidenceMult = this.adjustmentFactors.aiConfidenceMultiplier[aiConfidenceLevel];
    const riskMult = this.adjustmentFactors.riskAdjustment[riskLevel];

    // Apply quantum advantage and success rate adjustments
    const quantumBoost = 1 + (aiMetrics.quantumAdvantage * 0.2); // Up to 20% boost
    const successRateBoost = Math.max(0.8, aiMetrics.successRate); // Minimum 80% floor

    // Calculate final multipliers
    const totalMultiplier = volatilityMult * opportunityMult * aiConfidenceMult * riskMult * quantumBoost * successRateBoost;

    // Apply gas efficiency penalty (higher gas = lower targets)
    const gasPenalty = Math.max(0.7, marketConditions.gasEfficiency);

    // Calculate adjusted targets
    const adjustedHourly = this.baseTargets.hourly * totalMultiplier * gasPenalty;
    const adjustedDaily = this.baseTargets.daily * totalMultiplier * gasPenalty;
    const adjustedWeekly = this.baseTargets.weekly * totalMultiplier * gasPenalty;

    return {
      hourly: adjustedHourly.toFixed(4),
      daily: adjustedDaily.toFixed(4),
      weekly: adjustedWeekly.toFixed(2),
      unit: 'ETH'
    };
  }

  // Get the active target (optimal or user override)
  getActiveTarget(settings: ProfitTargetSettings): ProfitTargetSettings['active'] {
    if (settings.override.enabled) {
      return {
        hourly: settings.override.hourly,
        daily: settings.override.daily,
        weekly: settings.override.weekly,
        unit: settings.override.unit
      };
    }

    return {
      hourly: settings.optimal.hourly,
      daily: settings.optimal.daily,
      weekly: settings.optimal.weekly,
      unit: settings.optimal.unit
    };
  }

  // Update dynamic adjustment factors based on real-time data
  updateDynamicFactors(
    settings: ProfitTargetSettings,
    marketConditions: MarketConditions,
    aiMetrics: AIPerformanceMetrics
  ): ProfitTargetSettings {
    return {
      ...settings,
      dynamicAdjustment: {
        marketVolatility: marketConditions.volatility,
        opportunityDensity: marketConditions.opportunityDensity,
        aiConfidence: aiMetrics.confidence,
        riskScore: aiMetrics.riskScore
      }
    };
  }

  // Validate user override targets (ensure they're reasonable)
  validateOverrideTargets(override: ProfitTargetSettings['override']): {
    isValid: boolean;
    warnings: string[];
    suggestions: string[];
  } {
    const warnings: string[] = [];
    const suggestions: string[] = [];

    const hourlyTarget = parseFloat(override.hourly);
    const dailyTarget = parseFloat(override.daily);
    const weeklyTarget = parseFloat(override.weekly);

    // Check for unrealistic targets
    if (hourlyTarget > 1.0) {
      warnings.push('Hourly target exceeds realistic maximum (1.0 ETH)');
      suggestions.push('Consider hourly target ≤ 0.5 ETH for sustainable operation');
    }

    if (dailyTarget > 10.0) {
      warnings.push('Daily target exceeds realistic maximum (10.0 ETH)');
      suggestions.push('Consider daily target ≤ 5.0 ETH for risk management');
    }

    if (weeklyTarget > 50.0) {
      warnings.push('Weekly target exceeds realistic maximum (50.0 ETH)');
      suggestions.push('Consider weekly target ≤ 25.0 ETH for market volatility');
    }

    // Check for inconsistent targets
    const expectedWeeklyFromDaily = dailyTarget * 7;
    const weeklyVariance = Math.abs(weeklyTarget - expectedWeeklyFromDaily) / expectedWeeklyFromDaily;

    if (weeklyVariance > 0.3) { // 30% variance
      warnings.push('Weekly target inconsistent with daily target');
      suggestions.push(`Expected weekly target: ${(dailyTarget * 7).toFixed(2)} ETH based on daily target`);
    }

    return {
      isValid: warnings.length === 0,
      warnings,
      suggestions
    };
  }

  // Get target achievement status
  getTargetStatus(
    currentProfit: { hourly: number; daily: number; weekly: number },
    activeTargets: ProfitTargetSettings['active']
  ): {
    hourly: { achieved: boolean; percentage: number; remaining: number };
    daily: { achieved: boolean; percentage: number; remaining: number };
    weekly: { achieved: boolean; percentage: number; remaining: number };
  } {
    const hourlyTarget = parseFloat(activeTargets.hourly);
    const dailyTarget = parseFloat(activeTargets.daily);
    const weeklyTarget = parseFloat(activeTargets.weekly);

    return {
      hourly: {
        achieved: currentProfit.hourly >= hourlyTarget,
        percentage: (currentProfit.hourly / hourlyTarget) * 100,
        remaining: Math.max(0, hourlyTarget - currentProfit.hourly)
      },
      daily: {
        achieved: currentProfit.daily >= dailyTarget,
        percentage: (currentProfit.daily / dailyTarget) * 100,
        remaining: Math.max(0, dailyTarget - currentProfit.daily)
      },
      weekly: {
        achieved: currentProfit.weekly >= weeklyTarget,
        percentage: (currentProfit.weekly / weeklyTarget) * 100,
        remaining: Math.max(0, weeklyTarget - currentProfit.weekly)
      }
    };
  }

  // Helper methods for categorization
  private getVolatilityLevel(volatility: number): 'low' | 'medium' | 'high' {
    if (volatility < 0.3) return 'low';
    if (volatility < 0.7) return 'medium';
    return 'high';
  }

  private getOpportunityLevel(density: number): 'low' | 'medium' | 'high' {
    if (density < 0.3) return 'low';
    if (density < 0.7) return 'medium';
    return 'high';
  }

  private getAIConfidenceLevel(confidence: number): 'low' | 'medium' | 'high' {
    if (confidence < 0.6) return 'low';
    if (confidence < 0.85) return 'medium';
    return 'high';
  }

  private getRiskLevel(riskScore: number): 'low' | 'medium' | 'high' {
    if (riskScore < 0.3) return 'low';
    if (riskScore < 0.7) return 'medium';
    return 'high';
  }
}

// Singleton instance
export const profitTargetService = new ProfitTargetService();
export default profitTargetService;
