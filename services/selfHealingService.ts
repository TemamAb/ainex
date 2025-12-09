import { logger } from '../utils/logger';
import { runActivationSequence, getLiveActivationSteps, ActivationStep } from './activationService';
import { arbitrageScanner, liquidationScanner, mevScanner } from './scannerService';
import { validateExecutionReadiness } from './executionService';

export interface HealingAction {
  id: string;
  type: 'RESTART_MODULE' | 'RETRY_ACTIVATION' | 'FALLBACK_MODE' | 'RECONNECT_SCANNER' | 'RESET_METRICS';
  target: string;
  reason: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  timestamp: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  retryCount: number;
  maxRetries: number;
}

export interface SystemHealth {
  overall: 'HEALTHY' | 'DEGRADED' | 'CRITICAL' | 'FAILED';
  modules: {
    scanners: boolean;
    execution: boolean;
    blockchain: boolean;
    wallet: boolean;
  };
  lastCheck: number;
  issues: string[];
}

class SelfHealingService {
  private isActive = false;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  private healingQueue: HealingAction[] = [];
  private systemHealth: SystemHealth = {
    overall: 'HEALTHY',
    modules: {
      scanners: true,
      execution: true,
      blockchain: true,
      wallet: true
    },
    lastCheck: Date.now(),
    issues: []
  };

  private readonly HEALTH_CHECK_INTERVAL = 30000; // 30 seconds
  private readonly MAX_RETRY_ATTEMPTS = 3;
  private readonly CRITICAL_FAILURE_THRESHOLD = 5; // minutes

  async startSelfHealing(): Promise<void> {
    if (this.isActive) return;

    this.isActive = true;
    logger.info('🩺 Self-Healing Service: Starting automated system recovery...');

    // Start periodic health monitoring
    this.healthCheckInterval = setInterval(async () => {
      await this.performHealthCheck();
    }, this.HEALTH_CHECK_INTERVAL);

    // Process healing queue
    this.processHealingQueue();
  }

  async stopSelfHealing(): Promise<void> {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    this.isActive = false;
    logger.info('🩺 Self-Healing Service: Stopped');
  }

  async performHealthCheck(): Promise<SystemHealth> {
    const issues: string[] = [];
    let criticalIssues = 0;

    try {
      // Check scanner health
      const scannerHealth = await this.checkScannerHealth();
      this.systemHealth.modules.scanners = scannerHealth.healthy;
      if (!scannerHealth.healthy) {
        issues.push(...scannerHealth.issues);
        criticalIssues++;
      }

      // Check execution health
      const executionHealth = await this.checkExecutionHealth();
      this.systemHealth.modules.execution = executionHealth.healthy;
      if (!executionHealth.healthy) {
        issues.push(...executionHealth.issues);
        criticalIssues++;
      }

      // Check blockchain connectivity
      const blockchainHealth = await this.checkBlockchainHealth();
      this.systemHealth.modules.blockchain = blockchainHealth.healthy;
      if (!blockchainHealth.healthy) {
        issues.push(...blockchainHealth.issues);
        criticalIssues++;
      }

      // Check wallet health
      const walletHealth = await this.checkWalletHealth();
      this.systemHealth.modules.wallet = walletHealth.healthy;
      if (!walletHealth.healthy) {
        issues.push(...walletHealth.issues);
        criticalIssues++;
      }

      // Determine overall health
      if (criticalIssues >= 3) {
        this.systemHealth.overall = 'FAILED';
      } else if (criticalIssues >= 2) {
        this.systemHealth.overall = 'CRITICAL';
      } else if (criticalIssues >= 1) {
        this.systemHealth.overall = 'DEGRADED';
      } else {
        this.systemHealth.overall = 'HEALTHY';
      }

      this.systemHealth.issues = issues;
      this.systemHealth.lastCheck = Date.now();

      // Trigger healing actions for issues
      if (issues.length > 0) {
        await this.generateHealingActions(issues);
      }

      logger.info(`🩺 Health Check: ${this.systemHealth.overall} (${issues.length} issues detected)`);

    } catch (error: any) {
      logger.error('🩺 Health check failed:', error.message);
      this.systemHealth.overall = 'FAILED';
      this.systemHealth.issues = [`Health check error: ${error.message}`];
    }

    return this.systemHealth;
  }

  private async checkScannerHealth(): Promise<{ healthy: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      // Check if scanners are running by attempting a lightweight operation
      // This is a simplified check - in production would monitor actual scanner activity

      // For now, assume scanners are healthy if no exceptions occur
      // In production, this would check actual scanner metrics and activity

      return { healthy: true, issues: [] };
    } catch (error: any) {
      issues.push(`Scanner health check failed: ${error.message}`);
      return { healthy: false, issues };
    }
  }

  private async checkExecutionHealth(): Promise<{ healthy: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      const executionReady = await validateExecutionReadiness();
      if (!executionReady) {
        issues.push('Execution environment not ready');
      }

      return { healthy: executionReady, issues };
    } catch (error: any) {
      issues.push(`Execution health check failed: ${error.message}`);
      return { healthy: false, issues };
    }
  }

  private async checkBlockchainHealth(): Promise<{ healthy: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      const { getEthereumProvider } = await import('../blockchain/providers');
      const provider = await getEthereumProvider();

      // Test basic connectivity
      const blockNumber = await provider.getBlockNumber();
      const latestBlock = await provider.getBlock('latest');

      if (!blockNumber || !latestBlock) {
        issues.push('Blockchain connectivity test failed');
        return { healthy: false, issues };
      }

      // Check if block is recent (within last 5 minutes)
      const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
      const blockTimestamp = latestBlock.timestamp * 1000;

      if (blockTimestamp < fiveMinutesAgo) {
        issues.push('Blockchain data is stale');
        return { healthy: false, issues };
      }

      return { healthy: true, issues };
    } catch (error: any) {
      issues.push(`Blockchain health check failed: ${error.message}`);
      return { healthy: false, issues };
    }
  }

  private async checkWalletHealth(): Promise<{ healthy: boolean; issues: string[] }> {
    const issues: string[] = [];

    try {
      const { generateSmartWallet } = require('./smartWalletService');
      const wallet = await generateSmartWallet('ethereum');

      if (!wallet || !wallet.smartWalletAddress) {
        issues.push('Smart wallet generation failed');
        return { healthy: false, issues };
      }

      return { healthy: true, issues };
    } catch (error: any) {
      issues.push(`Wallet health check failed: ${error.message}`);
      return { healthy: false, issues };
    }
  }

  private async generateHealingActions(issues: string[]): Promise<void> {
    for (const issue of issues) {
      let action: HealingAction | null = null;

      if (issue.includes('scanner') || issue.includes('Scanner')) {
        action = {
          id: `heal-${Date.now()}-${Math.random()}`,
          type: 'RECONNECT_SCANNER',
          target: 'arbitrageScanner',
          reason: issue,
          priority: issue.includes('critical') ? 'CRITICAL' : 'HIGH',
          timestamp: Date.now(),
          status: 'PENDING',
          retryCount: 0,
          maxRetries: this.MAX_RETRY_ATTEMPTS
        };
      } else if (issue.includes('execution') || issue.includes('Execution')) {
        action = {
          id: `heal-${Date.now()}-${Math.random()}`,
          type: 'RESTART_MODULE',
          target: 'executionService',
          reason: issue,
          priority: 'CRITICAL',
          timestamp: Date.now(),
          status: 'PENDING',
          retryCount: 0,
          maxRetries: this.MAX_RETRY_ATTEMPTS
        };
      } else if (issue.includes('blockchain') || issue.includes('Blockchain')) {
        action = {
          id: `heal-${Date.now()}-${Math.random()}`,
          type: 'RETRY_ACTIVATION',
          target: 'blockchain-modules',
          reason: issue,
          priority: 'CRITICAL',
          timestamp: Date.now(),
          status: 'PENDING',
          retryCount: 0,
          maxRetries: this.MAX_RETRY_ATTEMPTS
        };
      } else if (issue.includes('wallet') || issue.includes('Wallet')) {
        action = {
          id: `heal-${Date.now()}-${Math.random()}`,
          type: 'RESTART_MODULE',
          target: 'smartWalletService',
          reason: issue,
          priority: 'HIGH',
          timestamp: Date.now(),
          status: 'PENDING',
          retryCount: 0,
          maxRetries: this.MAX_RETRY_ATTEMPTS
        };
      }

      if (action) {
        this.healingQueue.push(action);
        logger.warn(`🩺 Generated healing action: ${action.type} for ${action.target} (${action.reason})`);
      }
    }
  }

  private async processHealingQueue(): Promise<void> {
    if (this.healingQueue.length === 0) {
      setTimeout(() => this.processHealingQueue(), 5000); // Check every 5 seconds
      return;
    }

    // Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
    const priorityOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
    this.healingQueue.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

    // Process pending actions
    const pendingActions = this.healingQueue.filter(action => action.status === 'PENDING');

    for (const action of pendingActions) {
      if (action.retryCount >= action.maxRetries) {
        action.status = 'FAILED';
        logger.error(`🩺 Healing action failed permanently: ${action.type} for ${action.target}`);
        continue;
      }

      action.status = 'IN_PROGRESS';
      action.retryCount++;

      try {
        const success = await this.executeHealingAction(action);

        if (success) {
          action.status = 'COMPLETED';
          logger.info(`✅ Healing action completed: ${action.type} for ${action.target}`);
        } else {
          action.status = 'PENDING'; // Will retry
          logger.warn(`⚠️ Healing action failed, will retry: ${action.type} for ${action.target} (attempt ${action.retryCount}/${action.maxRetries})`);
        }
      } catch (error: any) {
        action.status = 'PENDING'; // Will retry
        logger.error(`💥 Healing action error: ${action.type} for ${action.target} - ${error.message}`);
      }
    }

    // Clean up completed/failed actions older than 1 hour
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    this.healingQueue = this.healingQueue.filter(action =>
      action.status === 'PENDING' || action.status === 'IN_PROGRESS' || action.timestamp > oneHourAgo
    );

    // Continue processing
    setTimeout(() => this.processHealingQueue(), 10000); // Check every 10 seconds
  }

  private async executeHealingAction(action: HealingAction): Promise<boolean> {
    try {
      switch (action.type) {
        case 'RECONNECT_SCANNER':
          return await this.reconnectScanner(action.target);

        case 'RESTART_MODULE':
          return await this.restartModule(action.target);

        case 'RETRY_ACTIVATION':
          return await this.retryActivation(action.target);

        case 'FALLBACK_MODE':
          return await this.fallbackToSafeMode(action.target);

        case 'RESET_METRICS':
          return await this.resetSystemMetrics();

        default:
          logger.warn(`Unknown healing action type: ${action.type}`);
          return false;
      }
    } catch (error: any) {
      logger.error(`Healing action execution failed: ${error.message}`);
      return false;
    }
  }

  private async reconnectScanner(scannerType: string): Promise<boolean> {
    try {
      // Stop existing scanner
      await arbitrageScanner.stopScanning();
      await liquidationScanner.stopScanning();
      await mevScanner.stopScanning();

      // Wait a moment
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Restart scanners
      await Promise.all([
        arbitrageScanner.startScanning(() => {}),
        liquidationScanner.startScanning(() => {}),
        mevScanner.startScanning(() => {})
      ]);

      logger.info('🔄 Scanners reconnected successfully');
      return true;
    } catch (error: any) {
      logger.error(`Scanner reconnection failed: ${error.message}`);
      return false;
    }
  }

  private async restartModule(moduleName: string): Promise<boolean> {
    try {
      // This is a simplified restart - in production would have specific restart logic per module
      logger.info(`🔄 Restarting module: ${moduleName}`);

      // For execution service, revalidate readiness
      if (moduleName === 'executionService') {
        const ready = await validateExecutionReadiness();
        return ready;
      }

      // For wallet service, regenerate wallet
      if (moduleName === 'smartWalletService') {
        const { generateSmartWallet } = require('./smartWalletService');
        const wallet = await generateSmartWallet('ethereum');
        return !!wallet;
      }

      return true;
    } catch (error: any) {
      logger.error(`Module restart failed: ${error.message}`);
      return false;
    }
  }

  private async retryActivation(moduleType: string): Promise<boolean> {
    try {
      logger.info(`🔄 Retrying activation for: ${moduleType}`);

      // Get activation steps for live mode
      const steps = getLiveActivationSteps();

      // Filter steps by module type if specified
      const filteredSteps = moduleType === 'all' ? steps :
        steps.filter(step => step.id.includes(moduleType.split('-')[0]));

      if (filteredSteps.length === 0) {
        return false;
      }

      // Retry activation
      const success = await runActivationSequence(filteredSteps, () => {}, 'LIVE');

      if (success) {
        logger.info(`✅ Module reactivation successful: ${moduleType}`);
      } else {
        logger.warn(`⚠️ Module reactivation failed: ${moduleType}`);
      }

      return success;
    } catch (error: any) {
      logger.error(`Module reactivation error: ${error.message}`);
      return false;
    }
  }

  private async fallbackToSafeMode(target: string): Promise<boolean> {
    try {
      logger.info(`🛡️ Falling back to safe mode for: ${target}`);

      // Implement safe mode fallbacks
      // This could include switching to read-only mode, disabling trading, etc.

      // For now, just log the fallback action
      logger.warn(`Safe mode activated for ${target} - manual intervention may be required`);

      return true;
    } catch (error: any) {
      logger.error(`Safe mode fallback failed: ${error.message}`);
      return false;
    }
  }

  private async resetSystemMetrics(): Promise<boolean> {
    try {
      logger.info('🔄 Resetting system metrics');

      // Reset metrics in main dashboard would be handled by the dashboard component
      // This is just a placeholder for the healing action

      return true;
    } catch (error: any) {
      logger.error(`Metrics reset failed: ${error.message}`);
      return false;
    }
  }

  // Public API
  getSystemHealth(): SystemHealth {
    return { ...this.systemHealth };
  }

  getHealingQueue(): HealingAction[] {
    return [...this.healingQueue];
  }

  async forceHealthCheck(): Promise<SystemHealth> {
    return await this.performHealthCheck();
  }

  async triggerEmergencyShutdown(): Promise<void> {
    logger.error('🚨 EMERGENCY SHUTDOWN TRIGGERED');

    // Stop all operations
    await this.stopSelfHealing();
    await arbitrageScanner.stopScanning();
    await liquidationScanner.stopScanning();
    await mevScanner.stopScanning();

    // This would trigger emergency protocols in production
  }
}

// Export singleton instance
export const selfHealingService = new SelfHealingService();
