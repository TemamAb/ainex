export interface AdminConfig {
  profitTarget: {
    mode: 'adaptive' | 'manual';
    adaptiveSettings: AdaptiveTargetSettings;
    manualSettings: ManualTargetSettings;
  };
  reinvestment: {
    rate: number;
    compoundStrategy: 'aggressive' | 'moderate' | 'conservative';
    treasuryAllocation: number;
  };
  riskProfile: {
    level: number;
    maxDrawdown: number;
    positionSizing: 'dynamic' | 'fixed';
    securityLevel: 'high' | 'medium' | 'low';
  };
}

export interface AdaptiveTargetSettings {
  baseThreshold: number;
  marketConditionMultiplier: number;
  learningRate: number;
  performanceLookback: number;
}

export interface ManualTargetSettings {
  fixedThreshold: number;
  overrideAI: boolean;
}
