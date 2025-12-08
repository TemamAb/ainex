import { AdminConfig } from '../types/admin';
import { logger } from '../utils/logger';

interface ConfigValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

interface ConfigBackup {
  config: AdminConfig;
  timestamp: number;
  version: string;
  userId?: string;
}

export class AdminConfigService {
  private currentConfig: AdminConfig;
  private configHistory: ConfigBackup[] = [];
  private lastSaveTime: number = 0;
  private readonly SAVE_COOLDOWN = 5000; // 5 seconds between saves
  private readonly MAX_HISTORY_SIZE = 10;
  private isInitialized: boolean = false;

  constructor() {
    this.currentConfig = this.getDefaultConfig();
    this.initializeService();
  }

  private async initializeService(): Promise<void> {
    try {
      await this.loadSavedConfig();
      await this.loadConfigHistory();
      this.isInitialized = true;
      logger.info('AdminConfigService initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize AdminConfigService:', error);
      // Continue with defaults if initialization fails
      this.isInitialized = true;
    }
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
        const validatedConfig = this.validateAndSanitizeConfig(savedConfig);
        this.currentConfig = { ...this.getDefaultConfig(), ...validatedConfig };
        logger.info('Configuration loaded successfully');
      } else {
        logger.warn(`Failed to load config: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      logger.warn('No saved config found, using defaults:', error);
    }
  }

  private async loadConfigHistory(): Promise<void> {
    try {
      const response = await fetch('/api/admin/config/history');
      if (response.ok) {
        const history = await response.json();
        this.configHistory = history.slice(0, this.MAX_HISTORY_SIZE);
      }
    } catch (error) {
      logger.warn('Failed to load config history:', error);
    }
  }

  validateConfig(config: Partial<AdminConfig>): ConfigValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Profit target validation
    if (config.profitTarget) {
      const { profitTarget } = config;

      if (profitTarget.mode === 'adaptive') {
        const { adaptiveSettings } = profitTarget;
        if (adaptiveSettings) {
          if (adaptiveSettings.baseThreshold < 0.01 || adaptiveSettings.baseThreshold > 5.0) {
            errors.push('Adaptive profit threshold must be between 0.01% and 5.0%');
          }
          if (adaptiveSettings.marketConditionMultiplier < 0.5 || adaptiveSettings.marketConditionMultiplier > 3.0) {
            errors.push('Market condition multiplier must be between 0.5 and 3.0');
          }
          if (adaptiveSettings.learningRate < 0.1 || adaptiveSettings.learningRate > 1.0) {
            errors.push('Learning rate must be between 0.1 and 1.0');
          }
        }
      } else if (profitTarget.mode === 'manual') {
        const { manualSettings } = profitTarget;
        if (manualSettings && (manualSettings.fixedThreshold < 0.01 || manualSettings.fixedThreshold > 10.0)) {
          errors.push('Manual profit threshold must be between 0.01% and 10.0%');
        }
      }
    }

    // Risk profile validation
    if (config.riskProfile) {
      const { riskProfile } = config;

      if (riskProfile.level < 1 || riskProfile.level > 10) {
        errors.push('Risk level must be between 1 and 10');
      }

      if (riskProfile.maxDrawdown < 1 || riskProfile.maxDrawdown > 50) {
        errors.push('Maximum drawdown must be between 1% and 50%');
      }

      if (riskProfile.maxDrawdown > 30) {
        warnings.push('High maximum drawdown (>30%) may expose significant risk');
      }
    }

    // Reinvestment validation
    if (config.reinvestment) {
      const { reinvestment } = config;

      if (reinvestment.rate < 0 || reinvestment.rate > 100) {
        errors.push('Reinvestment rate must be between 0% and 100%');
      }

      if (reinvestment.treasuryAllocation < 0 || reinvestment.treasuryAllocation > 100) {
        errors.push('Treasury allocation must be between 0% and 100%');
      }

      const totalAllocation = reinvestment.rate + reinvestment.treasuryAllocation;
      if (totalAllocation > 100) {
        errors.push('Total allocation (reinvestment + treasury) cannot exceed 100%');
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  private validateAndSanitizeConfig(config: any): AdminConfig {
    const validation = this.validateConfig(config);

    if (!validation.isValid) {
      throw new Error(`Invalid configuration: ${validation.errors.join(', ')}`);
    }

    // Sanitize and merge with defaults
    const sanitized = { ...this.getDefaultConfig() };

    if (config.profitTarget) {
      sanitized.profitTarget = { ...sanitized.profitTarget, ...config.profitTarget };
    }

    if (config.reinvestment) {
      sanitized.reinvestment = { ...sanitized.reinvestment, ...config.reinvestment };
    }

    if (config.riskProfile) {
      sanitized.riskProfile = { ...sanitized.riskProfile, ...config.riskProfile };
    }

    return sanitized;
  }

  async saveConfig(config: AdminConfig, userId?: string): Promise<{ success: boolean; errors?: string[]; warnings?: string[] }> {
    try {
      const response = await fetch('/api/admin/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config, userId })
      });

      if (response.ok) {
        this.currentConfig = config;
        await this.updateAIEngine(config);
        return { success: true };
      } else {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        return { success: false, errors: [errorData.message || `HTTP ${response.status}`] };
      }
    } catch (error) {
      logger.error('Failed to save config:', error);
      return { success: false, errors: [error instanceof Error ? error.message : 'Unknown error'] };
    }
  }

  getCurrentConfig(): AdminConfig {
    return { ...this.currentConfig }; // Return copy to prevent external mutation
  }

  isReady(): boolean {
    return this.isInitialized;
  }

  getConfigHistory(): ConfigBackup[] {
    return [...this.configHistory];
  }

  async rollbackToVersion(version: string): Promise<{ success: boolean; error?: string }> {
    const backup = this.configHistory.find(b => b.version === version);
    if (!backup) {
      return { success: false, error: 'Configuration version not found' };
    }

    try {
      const saveResult = await this.saveConfig(backup.config, 'system-rollback');
      if (saveResult.success) {
        logger.info(`Rolled back to configuration version ${version}`);
        return { success: true };
      } else {
        return { success: false, error: saveResult.errors?.join(', ') };
      }
    } catch (error) {
      return { success: false, error: `Rollback failed: ${error instanceof Error ? error.message : 'Unknown error'}` };
    }
  }

  async resetToDefaults(): Promise<{ success: boolean; error?: string }> {
    const defaultConfig = this.getDefaultConfig();
    try {
      const saveResult = await this.saveConfig(defaultConfig, 'system-reset');
      if (saveResult.success) {
        console.log('Configuration reset to defaults');
        return { success: true };
      } else {
        return { success: false, error: saveResult.errors?.join(', ') };
      }
    } catch (error) {
      return { success: false, error: `Reset failed: ${error instanceof Error ? error.message : 'Unknown error'}` };
    }
  }

  getConfigSummary(): {
    profitTarget: string;
    riskLevel: number;
    reinvestmentRate: number;
    lastModified: number;
    version: string;
  } {
    return {
      profitTarget: this.currentConfig.profitTarget.mode === 'adaptive'
        ? `${this.currentConfig.profitTarget.adaptiveSettings.baseThreshold}% (adaptive)`
        : `${this.currentConfig.profitTarget.manualSettings.fixedThreshold}% (manual)`,
      riskLevel: this.currentConfig.riskProfile.level,
      reinvestmentRate: this.currentConfig.reinvestment.rate,
      lastModified: this.lastSaveTime,
      version: this.configHistory[0]?.version || 'default'
    };
  }

  async exportConfig(): Promise<string> {
    const exportData = {
      config: this.currentConfig,
      metadata: {
        exportedAt: Date.now(),
        version: this.configHistory[0]?.version || 'default',
        history: this.configHistory.slice(0, 5) // Include last 5 changes
      }
    };

    return JSON.stringify(exportData, null, 2);
  }

  async importConfig(configJson: string): Promise<{ success: boolean; errors?: string[]; warnings?: string[] }> {
    try {
      const importData = JSON.parse(configJson);

      if (!importData.config) {
        return { success: false, errors: ['Invalid configuration format'] };
      }

      // Validate imported config
      const validation = this.validateConfig(importData.config);
      if (!validation.isValid) {
        return { success: false, errors: validation.errors, warnings: validation.warnings };
      }

      // Save imported config
      const saveResult = await this.saveConfig(importData.config, 'config-import');
      if (saveResult.success) {
        logger.info('Configuration imported successfully');
        return { success: true, warnings: saveResult.warnings };
      } else {
        return { success: false, errors: saveResult.errors };
      }
    } catch (error) {
      return {
        success: false,
        errors: [`Import failed: ${error instanceof Error ? error.message : 'Invalid JSON format'}`]
      };
    }
  }

  private async updateAIEngine(config: AdminConfig): Promise<void> {
    const aiParams = {
      profitThreshold: config.profitTarget.mode === 'adaptive'
        ? config.profitTarget.adaptiveSettings.baseThreshold
        : config.profitTarget.manualSettings.fixedThreshold,
      riskTolerance: config.riskProfile.level / 10,
      reinvestmentRate: config.reinvestment.rate / 100,
      securityLevel: config.riskProfile.securityLevel,
      maxDrawdown: config.riskProfile.maxDrawdown / 100,
      positionSizing: config.riskProfile.positionSizing
    };

    try {
      const response = await fetch('/api/ai/update-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(aiParams)
      });

      if (!response.ok) {
        logger.warn(`AI engine update failed: ${response.status} ${response.statusText}`);
      } else {
        logger.info('AI engine configuration updated successfully');
      }
    } catch (error) {
      logger.warn('Failed to update AI engine:', error);
      // Don't throw - AI update failure shouldn't break config save
    }
  }
}
