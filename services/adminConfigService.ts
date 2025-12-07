import { AdminConfig } from '../types/admin';

export class AdminConfigService {
  private currentConfig: AdminConfig;

  constructor() {
    this.currentConfig = this.getDefaultConfig();
    this.loadSavedConfig();
  }

  getDefaultConfig(): AdminConfig {
    return {
      profitTarget: {
        mode: 'adaptive',
        adaptiveSettings: {
          baseThreshold: 0.2,
          marketConditionMultiplier: 1.2,
          learningRate: 0.8,
          performanceLookback: 30
        },
        manualSettings: {
          fixedThreshold: 0.5,
          overrideAI: false
        }
      },
      reinvestment: {
        rate: 70,
        compoundStrategy: 'moderate',
        treasuryAllocation: 30
      },
      riskProfile: {
        level: 6,
        maxDrawdown: 15,
        positionSizing: 'dynamic',
        securityLevel: 'high'
      }
    };
  }

  async loadSavedConfig(): Promise<void> {
    try {
      const response = await fetch('/api/admin/config');
      if (response.ok) {
        const savedConfig = await response.json();
        this.currentConfig = { ...this.getDefaultConfig(), ...savedConfig };
      }
    } catch (error) {
      console.warn('No saved config found, using defaults');
    }
  }

  async saveConfig(config: AdminConfig): Promise<boolean> {
    try {
      const response = await fetch('/api/admin/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        this.currentConfig = config;
        await this.updateAIEngine(config);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to save config:', error);
      return false;
    }
  }

  getCurrentConfig(): AdminConfig {
    return this.currentConfig;
  }

  private async updateAIEngine(config: AdminConfig): Promise<void> {
    const aiParams = {
      profitThreshold: config.profitTarget.mode === 'adaptive' 
        ? config.profitTarget.adaptiveSettings.baseThreshold
        : config.profitTarget.manualSettings.fixedThreshold,
      riskTolerance: config.riskProfile.level / 10,
      reinvestmentRate: config.reinvestment.rate / 100,
      securityLevel: config.riskProfile.securityLevel
    };

    await fetch('/api/ai/update-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(aiParams)
    });
  }
}
