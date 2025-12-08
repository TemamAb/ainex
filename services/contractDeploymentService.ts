import { ethers } from 'ethers';

// Contract Deployment Report Interface
export interface ContractDeployment {
  id: string;
  deploymentNumber: number;
  contractName: string;
  contractAddress: string;
  deployerAddress: string;
  network: string;
  chainId: number;
  gasUsed: string;
  gasPrice: string;
  deploymentCost: string;
  bytecodeSize: number;
  timestamp: number;
  blockNumber: number;
  txHash: string;
  status: 'SUCCESS' | 'FAILED' | 'PENDING';
  verificationStatus: 'VERIFIED' | 'PENDING' | 'FAILED';
  sourceCode?: string;
  abi?: any[];
  constructorArgs?: any[];
  libraries?: Record<string, string>;
  dependencies?: string[];
  tags?: string[];
  metadata?: {
    compiler: string;
    version: string;
    optimization: boolean;
    runs: number;
  };
}

// Deployment Report Interface
export interface DeploymentReport {
  reportId: string;
  totalDeployments: number;
  successfulDeployments: number;
  failedDeployments: number;
  totalGasUsed: string;
  totalDeploymentCost: string;
  averageGasPrice: string;
  networks: string[];
  contracts: ContractDeployment[];
  timestamp: number;
  generatedBy: string;
  version: string;
  summary: {
    totalValueDeployed: string;
    uniqueNetworks: number;
    uniqueContracts: number;
    averageDeploymentTime: number;
    successRate: number;
  };
}

// Contract Deployment Service
export class ContractDeploymentService {
  private deployments: Map<string, ContractDeployment> = new Map();
  private reports: Map<string, DeploymentReport> = new Map();
  private deploymentCounter: number = 0;
  private provider: ethers.JsonRpcProvider;

  constructor(rpcUrl: string = 'https://eth-mainnet.g.alchemy.com/v2/demo') {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
  }

  // Generate unique deployment number
  private generateDeploymentNumber(): number {
    this.deploymentCounter++;
    return this.deploymentCounter;
  }

  // Create deployment ID
  private generateDeploymentId(contractName: string, network: string): string {
    const timestamp = Date.now();
    return `${contractName}_${network}_${timestamp}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Record a new contract deployment
  async recordDeployment(
    contractName: string,
    contractAddress: string,
    deployerAddress: string,
    network: string,
    txHash: string,
    options: {
      sourceCode?: string;
      abi?: any[];
      constructorArgs?: any[];
      libraries?: Record<string, string>;
      dependencies?: string[];
      tags?: string[];
      metadata?: ContractDeployment['metadata'];
    } = {}
  ): Promise<ContractDeployment> {
    const startTime = Date.now();

    try {
      // Check circuit breaker
      if (this.circuitBreaker.isOpen) {
        throw new Error('Circuit breaker is open - deployment recording temporarily disabled');
      }

      // Check cache first
      const cacheKey = `${txHash}_${contractAddress}`;
      const cached = this.getCachedDeployment(cacheKey);
      if (cached) {
        console.log(`📋 Using cached deployment data for ${contractName}`);
        return cached;
      }

      // Validate inputs
      const validationErrors = deploymentUtils.validateDeploymentData({
        contractName,
        contractAddress,
        deployerAddress,
        network,
        txHash
      });

      if (validationErrors.length > 0) {
        throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
      }

      // Get transaction details with retry logic
      const tx = await this.retryWithBackoff(() => this.provider.getTransaction(txHash));
      if (!tx) {
        throw new Error(`Transaction ${txHash} not found`);
      }

      const receipt = await this.retryWithBackoff(() => this.provider.getTransactionReceipt(txHash));
      if (!receipt) {
        throw new Error(`Transaction receipt for ${txHash} not found`);
      }

      const block = await this.retryWithBackoff(() => this.provider.getBlock(receipt.blockNumber));
      const networkInfo = await this.provider.getNetwork();

      // Calculate deployment cost
      const gasUsed = receipt.gasUsed.toString();
      const gasPrice = tx.gasPrice?.toString() || '0';
      const deploymentCost = ethers.formatEther(
        BigInt(gasUsed) * BigInt(gasPrice)
      );

      // Get bytecode size
      const code = await this.retryWithBackoff(() => this.provider.getCode(contractAddress));
      const bytecodeSize = Math.floor((code.length - 2) / 2); // Remove 0x prefix and convert to bytes

      const deployment: ContractDeployment = {
        id: this.generateDeploymentId(contractName, network),
        deploymentNumber: this.generateDeploymentNumber(),
        contractName,
        contractAddress,
        deployerAddress,
        network,
        chainId: networkInfo.chainId,
        gasUsed,
        gasPrice: ethers.formatUnits(gasPrice, 'gwei'),
        deploymentCost,
        bytecodeSize,
        timestamp: block?.timestamp || Date.now(),
        blockNumber: receipt.blockNumber,
        txHash,
        status: receipt.status === 1 ? 'SUCCESS' : 'FAILED',
        verificationStatus: 'PENDING',
        ...options
      };

      // Store deployment
      this.deployments.set(deployment.id, deployment);

      // Cache the deployment
      this.setCachedDeployment(cacheKey, deployment);

      // Update metrics
      this.updateMetrics(deployment, Date.now() - startTime);

      // Reset circuit breaker on success
      this.circuitBreaker.failureCount = 0;
      this.circuitBreaker.isOpen = false;

      console.log(`✅ Contract deployment recorded: ${contractName} (#${deployment.deploymentNumber})`);
      return deployment;

    } catch (error) {
      const deploymentTime = Date.now() - startTime;

      // Update metrics for failure
      this.updateMetricsForFailure(deploymentTime);

      // Update circuit breaker
      this.updateCircuitBreaker();

      console.error('❌ Failed to record deployment:', error);
      throw error;
    }
  }

  private async retryWithBackoff<T>(operation: () => Promise<T>, maxRetries: number = 3): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt < maxRetries) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000); // Exponential backoff, max 10s
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw lastError!;
  }

  private getCachedDeployment(cacheKey: string): ContractDeployment | null {
    const cached = this.deploymentCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < this.CACHE_DURATION) {
      this.metrics.cacheHitRate = (this.metrics.cacheHitRate + 1) / 2; // Running average
      return cached.deployment;
    }

    // Remove expired cache entry
    if (cached) {
      this.deploymentCache.delete(cacheKey);
    }

    return null;
  }

  private setCachedDeployment(cacheKey: string, deployment: ContractDeployment): void {
    // Manage cache size
    if (this.deploymentCache.size >= this.MAX_CACHE_SIZE) {
      const firstKey = this.deploymentCache.keys().next().value;
      this.deploymentCache.delete(firstKey);
    }

    this.deploymentCache.set(cacheKey, {
      deployment,
      timestamp: Date.now()
    });
  }

  private updateMetrics(deployment: ContractDeployment, deploymentTime: number): void {
    this.metrics.totalDeployments++;

    if (deployment.status === 'SUCCESS') {
      this.metrics.successfulDeployments++;
      this.metrics.totalGasUsed = this.metrics.totalGasUsed + BigInt(deployment.gasUsed);
      this.metrics.totalCost += parseFloat(deployment.deploymentCost);
    } else {
      this.metrics.failedDeployments++;
    }

    // Update averages
    const totalCompleted = this.metrics.successfulDeployments + this.metrics.failedDeployments;
    if (totalCompleted > 0) {
      this.metrics.averageDeploymentTime = (
        (this.metrics.averageDeploymentTime * (totalCompleted - 1)) + deploymentTime
      ) / totalCompleted;

      if (this.metrics.successfulDeployments > 0) {
        this.metrics.averageGasPrice = (
          (this.metrics.averageGasPrice * (this.metrics.successfulDeployments - 1)) +
          parseFloat(deployment.gasPrice)
        ) / this.metrics.successfulDeployments;
      }
    }
  }

  private updateMetricsForFailure(deploymentTime: number): void {
    this.metrics.totalDeployments++;
    this.metrics.failedDeployments++;

    const totalCompleted = this.metrics.successfulDeployments + this.metrics.failedDeployments;
    this.metrics.averageDeploymentTime = (
      (this.metrics.averageDeploymentTime * (totalCompleted - 1)) + deploymentTime
    ) / totalCompleted;
  }

  private updateCircuitBreaker(): void {
    this.circuitBreaker.failureCount++;
    this.circuitBreaker.lastFailureTime = Date.now();

    if (this.circuitBreaker.failureCount >= this.CIRCUIT_BREAKER_THRESHOLD) {
      this.circuitBreaker.isOpen = true;
      this.circuitBreaker.nextRetryTime = Date.now() + this.CIRCUIT_BREAKER_TIMEOUT;
      console.warn('🚫 Circuit breaker opened due to consecutive failures');
    }
  }

  // Update deployment verification status
  updateVerificationStatus(deploymentId: string, status: ContractDeployment['verificationStatus']): void {
    const deployment = this.deployments.get(deploymentId);
    if (deployment) {
      deployment.verificationStatus = status;
      this.deployments.set(deploymentId, deployment);
    }
  }

  // Get deployment by ID
  getDeployment(deploymentId: string): ContractDeployment | undefined {
    return this.deployments.get(deploymentId);
  }

  // Get all deployments
  getAllDeployments(): ContractDeployment[] {
    return Array.from(this.deployments.values());
  }

  // Get deployments by network
  getDeploymentsByNetwork(network: string): ContractDeployment[] {
    return Array.from(this.deployments.values()).filter(d => d.network === network);
  }

  // Get deployments by contract name
  getDeploymentsByContract(contractName: string): ContractDeployment[] {
    return Array.from(this.deployments.values()).filter(d => d.contractName === contractName);
  }

  // Generate deployment report
  generateDeploymentReport(
    deployments: ContractDeployment[] = this.getAllDeployments(),
    generatedBy: string = 'AINEX Dashboard'
  ): DeploymentReport {
    const reportId = `report_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const successfulDeployments = deployments.filter(d => d.status === 'SUCCESS');
    const failedDeployments = deployments.filter(d => d.status === 'FAILED');

    const totalGasUsed = successfulDeployments.reduce(
      (sum, d) => sum + BigInt(d.gasUsed), BigInt(0)
    ).toString();

    const totalDeploymentCost = successfulDeployments.reduce(
      (sum, d) => sum + parseFloat(d.deploymentCost), 0
    ).toString();

    const averageGasPrice = successfulDeployments.length > 0
      ? successfulDeployments.reduce((sum, d) => sum + parseFloat(d.gasPrice), 0) / successfulDeployments.length
      : 0;

    const networks = Array.from(new Set(deployments.map(d => d.network)));
    const uniqueContracts = new Set(deployments.map(d => d.contractName)).size;

    const totalValueDeployed = successfulDeployments.reduce(
      (sum, d) => sum + parseFloat(d.deploymentCost), 0
    );

    const timestamps = successfulDeployments.map(d => d.timestamp).sort((a, b) => a - b);
    const averageDeploymentTime = timestamps.length > 1
      ? (timestamps[timestamps.length - 1] - timestamps[0]) / (timestamps.length - 1) / 1000 // seconds
      : 0;

    const successRate = deployments.length > 0
      ? (successfulDeployments.length / deployments.length) * 100
      : 0;

    const report: DeploymentReport = {
      reportId,
      totalDeployments: deployments.length,
      successfulDeployments: successfulDeployments.length,
      failedDeployments: failedDeployments.length,
      totalGasUsed,
      totalDeploymentCost,
      averageGasPrice: averageGasPrice.toFixed(2),
      networks,
      contracts: deployments,
      timestamp: Date.now(),
      generatedBy,
      version: '1.0.0',
      summary: {
        totalValueDeployed: totalValueDeployed.toFixed(6),
        uniqueNetworks: networks.length,
        uniqueContracts,
        averageDeploymentTime,
        successRate
      }
    };

    // Store report
    this.reports.set(reportId, report);

    return report;
  }

  // Get deployment report by ID
  getDeploymentReport(reportId: string): DeploymentReport | undefined {
    return this.reports.get(reportId);
  }

  // Get all deployment reports
  getAllDeploymentReports(): DeploymentReport[] {
    return Array.from(this.reports.values()).sort((a, b) => b.timestamp - a.timestamp);
  }

  // Export deployment data as JSON
  exportDeploymentData(): string {
    const data = {
      deployments: this.getAllDeployments(),
      reports: this.getAllDeploymentReports(),
      metadata: {
        exportedAt: Date.now(),
        totalDeployments: this.deployments.size,
        totalReports: this.reports.size,
        version: '1.0.0'
      }
    };
    return JSON.stringify(data, null, 2);
  }

  // Import deployment data from JSON
  importDeploymentData(jsonData: string): void {
    try {
      const data = JSON.parse(jsonData);

      // Import deployments
      if (data.deployments) {
        data.deployments.forEach((deployment: ContractDeployment) => {
          this.deployments.set(deployment.id, deployment);
          if (deployment.deploymentNumber > this.deploymentCounter) {
            this.deploymentCounter = deployment.deploymentNumber;
          }
        });
      }

      // Import reports
      if (data.reports) {
        data.reports.forEach((report: DeploymentReport) => {
          this.reports.set(report.reportId, report);
        });
      }

      console.log(`Imported ${data.deployments?.length || 0} deployments and ${data.reports?.length || 0} reports`);
    } catch (error) {
      console.error('Failed to import deployment data:', error);
      throw error;
    }
  }

  // Clear all deployment data
  clearAllData(): void {
    this.deployments.clear();
    this.reports.clear();
    this.deploymentCounter = 0;
    console.log('All deployment data cleared');
  }

  // Get deployment statistics
  getDeploymentStatistics(): {
    totalDeployments: number;
    successfulDeployments: number;
    failedDeployments: number;
    totalGasUsed: string;
    totalCost: string;
    networksCount: number;
    contractsCount: number;
  } {
    const allDeployments = this.getAllDeployments();
    const successful = allDeployments.filter(d => d.status === 'SUCCESS');
    const failed = allDeployments.filter(d => d.status === 'FAILED');

    const totalGasUsed = successful.reduce(
      (sum, d) => sum + BigInt(d.gasUsed), BigInt(0)
    ).toString();

    const totalCost = successful.reduce(
      (sum, d) => sum + parseFloat(d.deploymentCost), 0
    ).toFixed(6);

    return {
      totalDeployments: allDeployments.length,
      successfulDeployments: successful.length,
      failedDeployments: failed.length,
      totalGasUsed,
      totalCost,
      networksCount: new Set(allDeployments.map(d => d.network)).size,
      contractsCount: new Set(allDeployments.map(d => d.contractName)).size
    };
  }
}

// Factory function to create contract deployment service
export function createContractDeploymentService(rpcUrl?: string): ContractDeploymentService {
  return new ContractDeploymentService(rpcUrl);
}

// Utility functions for deployment management
export const deploymentUtils = {
  // Format deployment number with leading zeros
  formatDeploymentNumber(num: number): string {
    return num.toString().padStart(6, '0');
  },

  // Generate deployment summary
  generateDeploymentSummary(deployment: ContractDeployment): string {
    return `Deployment #${deploymentUtils.formatDeploymentNumber(deployment.deploymentNumber)}: ${deployment.contractName} on ${deployment.network} - ${deployment.status}`;
  },

  // Calculate deployment efficiency
  calculateDeploymentEfficiency(deployment: ContractDeployment): number {
    // Efficiency based on gas used per bytecode byte
    return deployment.bytecodeSize > 0 ? parseInt(deployment.gasUsed) / deployment.bytecodeSize : 0;
  },

  // Validate deployment data
  validateDeploymentData(deployment: Partial<ContractDeployment>): string[] {
    const errors: string[] = [];

    if (!deployment.contractName) errors.push('Contract name is required');
    if (!deployment.contractAddress) errors.push('Contract address is required');
    if (!ethers.isAddress(deployment.contractAddress || '')) errors.push('Invalid contract address');
    if (!deployment.deployerAddress) errors.push('Deployer address is required');
    if (!ethers.isAddress(deployment.deployerAddress || '')) errors.push('Invalid deployer address');
    if (!deployment.network) errors.push('Network is required');
    if (!deployment.txHash) errors.push('Transaction hash is required');

    return errors;
  }
};

export default ContractDeploymentService;
