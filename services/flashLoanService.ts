import { ethers } from 'ethers';
import { getEthereumProvider, getArbitrumProvider, getBaseProvider } from '../blockchain/providers';
import { getAaveV3Pool } from './contractService';

export interface FlashLoanProvider {
  name: string;
  address: string;
  chain: 'ethereum' | 'arbitrum' | 'base';
  maxLoanAmount: string;
  fee: number; // Fee in basis points (e.g., 5 = 0.05%)
  supportedAssets: string[];
  active: boolean;
}

export interface FlashLoanMetrics {
  provider: string;
  totalLoans: number;
  successfulLoans: number;
  failedLoans: number;
  totalVolume: string;
  averageLoanSize: string;
  averageFee: string;
  uptime: number;
  lastActivity: number;
}

export interface FlashLoanExecution {
  provider: string;
  asset: string;
  amount: string;
  fee: string;
  txHash?: string;
  status: 'PENDING' | 'EXECUTING' | 'SUCCESS' | 'FAILED';
  timestamp: number;
  error?: string;
}

export interface FlashLoanServiceMetrics {
  totalLoans: number;
  successfulLoans: number;
  failedLoans: number;
  totalVolume: string;
  totalFeesPaid: string;
  averageExecutionTime: number;
  cacheHitRate: number;
  lastActivity: number;
}

export interface CircuitBreaker {
  isOpen: boolean;
  failureCount: number;
  lastFailureTime: number;
  nextRetryTime: number;
}

export interface CachedFlashLoanResult {
  result: any;
  cachedAt: number;
}

// Enhanced Flash Loan Service with circuit breaker, caching, and metrics
export class FlashLoanService {
  private loanCache: Map<string, CachedFlashLoanResult> = new Map();
  private readonly CACHE_DURATION = 300000; // 5 minutes
  private readonly MAX_CACHE_SIZE = 500;
  private readonly CIRCUIT_BREAKER_THRESHOLD = 5;
  private readonly CIRCUIT_BREAKER_TIMEOUT = 300000; // 5 minutes

  private circuitBreaker: CircuitBreaker = {
    isOpen: false,
    failureCount: 0,
    lastFailureTime: 0,
    nextRetryTime: 0
  };

  private metrics: FlashLoanServiceMetrics = {
    totalLoans: 0,
    successfulLoans: 0,
    failedLoans: 0,
    totalVolume: '0',
    totalFeesPaid: '0',
    averageExecutionTime: 0,
    cacheHitRate: 0,
    lastActivity: 0
  };

  private providers: FlashLoanProvider[] = [
    {
      name: 'Aave V3',
      address: '0x87870Bcd2C42b5e4e4F9e06c1C2E9c8Fc8e8bEf',
      chain: 'ethereum',
      maxLoanAmount: '1000000000000000000000', // 1000 ETH
      fee: 5, // 0.05%
      supportedAssets: ['WETH', 'USDC', 'WBTC', 'USDT', 'DAI'],
      active: true
    },
    {
      name: 'Aave V3 Arbitrum',
      address: '0x794a61358D6845594F94dc1DB02A252b5b4814aD',
      chain: 'arbitrum',
      maxLoanAmount: '500000000000000000000', // 500 ETH
      fee: 5,
      supportedAssets: ['WETH', 'USDC.e', 'WBTC', 'USDT', 'DAI'],
      active: true
    },
    {
      name: 'Aave V3 Base',
      address: '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5',
      chain: 'base',
      maxLoanAmount: '200000000000000000000', // 200 ETH
      fee: 5,
      supportedAssets: ['WETH', 'USDC', 'cbETH'],
      active: true
    }
  ];

  // Get circuit breaker status
  getCircuitBreakerStatus(): CircuitBreaker {
    return { ...this.circuitBreaker };
  }

  // Get current metrics
  getMetrics(): FlashLoanServiceMetrics {
    return { ...this.metrics };
  }

  // Get available providers
  getProviders(): FlashLoanProvider[] {
    return this.providers.filter(p => p.active);
  }

  // Retry with exponential backoff
  private async retryWithBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3
  ): Promise<T> {
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

  // Get cached result
  private getCachedResult(cacheKey: string): CachedFlashLoanResult | null {
    const cached = this.loanCache.get(cacheKey);
    if (cached && Date.now() - cached.cachedAt < this.CACHE_DURATION) {
      this.metrics.cacheHitRate = (this.metrics.cacheHitRate + 1) / 2; // Running average
      return cached;
    }

    // Remove expired cache entry
    if (cached) {
      this.loanCache.delete(cacheKey);
    }

    return null;
  }

  // Set cached result
  private setCachedResult(cacheKey: string, result: any): void {
    // Manage cache size
    if (this.loanCache.size >= this.MAX_CACHE_SIZE) {
      const firstKey = this.loanCache.keys().next().value;
      this.loanCache.delete(firstKey);
    }

    this.loanCache.set(cacheKey, {
      result,
      cachedAt: Date.now()
    });
  }

  // Update metrics
  private updateMetrics(success: boolean, executionTime: number, volume?: string, fee?: string): void {
    this.metrics.lastActivity = Date.now();
    this.metrics.totalLoans++;

    if (success) {
      this.metrics.successfulLoans++;
      if (volume) {
        this.metrics.totalVolume = (BigInt(this.metrics.totalVolume) + BigInt(volume)).toString();
      }
      if (fee) {
        this.metrics.totalFeesPaid = (BigInt(this.metrics.totalFeesPaid) + BigInt(fee)).toString();
      }
    } else {
      this.metrics.failedLoans++;
    }

    // Update average execution time
    const totalCompleted = this.metrics.successfulLoans + this.metrics.failedLoans;
    this.metrics.averageExecutionTime = (
      (this.metrics.averageExecutionTime * (totalCompleted - 1)) + executionTime
    ) / totalCompleted;
  }

  // Update circuit breaker
  private updateCircuitBreaker(success: boolean): void {
    if (success) {
      this.circuitBreaker.failureCount = 0;
      this.circuitBreaker.isOpen = false;
      return;
    }

    this.circuitBreaker.failureCount++;
    this.circuitBreaker.lastFailureTime = Date.now();

    if (this.circuitBreaker.failureCount >= this.CIRCUIT_BREAKER_THRESHOLD) {
      this.circuitBreaker.isOpen = true;
      this.circuitBreaker.nextRetryTime = Date.now() + this.CIRCUIT_BREAKER_TIMEOUT;
      console.warn('🚫 Flash loan service circuit breaker opened due to consecutive failures');
    }
  }

  // Clear all cached data
  clearCache(): void {
    this.loanCache.clear();
    console.log('🧹 Flash loan service cache cleared');
  }

  // Reset circuit breaker
  resetCircuitBreaker(): void {
    this.circuitBreaker = {
      isOpen: false,
      failureCount: 0,
      lastFailureTime: 0,
      nextRetryTime: 0
    };
    console.log('🔄 Flash loan service circuit breaker reset');
  }

  async getProviderMetrics(): Promise<FlashLoanMetrics[]> {
    const startTime = Date.now();

    try {
      // Check circuit breaker
      if (this.circuitBreaker.isOpen) {
        throw new Error('Circuit breaker is open - flash loan service temporarily disabled');
      }

      const cacheKey = 'provider_metrics';
      const cached = this.getCachedResult(cacheKey);
      if (cached) {
        return cached.result;
      }

      // Fetch metrics from all providers
      const metrics = await this.retryWithBackoff(async () => {
        const response = await fetch('/api/flash-loan/metrics');
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        return data.providers || [];
      });

      // Cache the result
      this.setCachedResult(cacheKey, metrics);
      this.updateMetrics(true, Date.now() - startTime);

      return metrics;
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      this.updateMetrics(false, responseTime);
      this.updateCircuitBreaker(false);

      console.error('Failed to fetch flash loan metrics:', error);
      throw error;
    }
  }

  async getOptimalLoanSize(opportunity: any): Promise<string> {
    const startTime = Date.now();

    try {
      // Check circuit breaker
      if (this.circuitBreaker.isOpen) {
        throw new Error('Circuit breaker is open - flash loan service temporarily disabled');
      }

      // Validate opportunity
      if (!opportunity || !opportunity.asset || !opportunity.expectedProfit) {
        throw new Error('Invalid opportunity data provided');
      }

      const cacheKey = `optimal_size_${JSON.stringify(opportunity)}`;
      const cached = this.getCachedResult(cacheKey);
      if (cached) {
        return cached.result;
      }

      // Calculate optimal loan size based on opportunity
      const optimalSize = await this.retryWithBackoff(async () => {
        const response = await fetch('/api/flash-loan/calculate-size', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ opportunity })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data.optimalSize;
      });

      // Validate optimal size
      if (!optimalSize || isNaN(Number(optimalSize))) {
        throw new Error('Invalid optimal loan size received');
      }

      // Cache the result
      this.setCachedResult(cacheKey, optimalSize);
      this.updateMetrics(true, Date.now() - startTime);

      return optimalSize;
    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      this.updateMetrics(false, responseTime);
      this.updateCircuitBreaker(false);

      console.error('Failed to calculate optimal loan size:', error);
      throw error;
    }
  }

  // Execute flash loan
  async executeFlashLoan(
    providerName: string,
    asset: string,
    amount: string,
    borrowerAddress: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
  ): Promise<FlashLoanExecution> {
    const startTime = Date.now();

    try {
      // Check circuit breaker
      if (this.circuitBreaker.isOpen) {
        throw new Error('Circuit breaker is open - flash loan execution temporarily disabled');
      }

      // Find provider
      const provider = this.providers.find(p => p.name === providerName && p.chain === chain);
      if (!provider) {
        throw new Error(`Provider ${providerName} not found for chain ${chain}`);
      }

      // Validate asset is supported
      if (!provider.supportedAssets.includes(asset)) {
        throw new Error(`Asset ${asset} not supported by provider ${providerName}`);
      }

      // Validate amount
      const amountBigInt = BigInt(amount);
      const maxAmountBigInt = BigInt(provider.maxLoanAmount);
      if (amountBigInt > maxAmountBigInt) {
        throw new Error(`Loan amount exceeds maximum allowed: ${provider.maxLoanAmount}`);
      }

      // Get provider contract
      const poolContract = await getAaveV3Pool(chain);

      // Calculate fee
      const feeAmount = (amountBigInt * BigInt(provider.fee)) / BigInt(10000); // fee is in basis points

      // Prepare flash loan parameters
      const assets = [asset]; // Assuming asset is the contract address
      const amounts = [amount];
      const modes = [0]; // 0 = no debt, 1 = stable, 2 = variable

      // Execute flash loan
      const tx = await poolContract.flashLoan(
        borrowerAddress,
        assets,
        amounts,
        modes,
        borrowerAddress, // onBehalfOf
        '0x', // params (empty for now)
        0 // referralCode
      );

      // Wait for transaction confirmation
      const receipt = await tx.wait();

      const execution: FlashLoanExecution = {
        provider: providerName,
        asset,
        amount,
        fee: feeAmount.toString(),
        txHash: receipt.hash,
        status: receipt.status === 1 ? 'SUCCESS' : 'FAILED',
        timestamp: Date.now()
      };

      this.updateMetrics(true, Date.now() - startTime, amount, feeAmount.toString());
      return execution;

    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      this.updateMetrics(false, responseTime);
      this.updateCircuitBreaker(false);

      console.error('Flash loan execution failed:', error);

      return {
        provider: providerName,
        asset,
        amount,
        fee: '0',
        status: 'FAILED',
        timestamp: Date.now(),
        error: error.message
      };
    }
  }

  // Get flash loan quotes from multiple providers
  async getLoanQuotes(
    asset: string,
    amount: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
  ): Promise<Array<{ provider: string; fee: string; available: boolean }>> {
    const quotes: Array<{ provider: string; fee: string; available: boolean }> = [];

    for (const provider of this.providers.filter(p => p.chain === chain && p.active)) {
      try {
        // Check if asset is supported
        const available = provider.supportedAssets.includes(asset);

        // Calculate fee
        const amountBigInt = BigInt(amount);
        const feeAmount = (amountBigInt * BigInt(provider.fee)) / BigInt(10000);

        quotes.push({
          provider: provider.name,
          fee: feeAmount.toString(),
          available
        });
      } catch (error) {
        console.warn(`Failed to get quote from ${provider.name}:`, error);
        quotes.push({
          provider: provider.name,
          fee: '0',
          available: false
        });
      }
    }

    return quotes;
  }

  // Validate flash loan opportunity
  validateLoanOpportunity(opportunity: any): { valid: boolean; reason?: string } {
    if (!opportunity) {
      return { valid: false, reason: 'Opportunity data is required' };
    }

    if (!opportunity.asset || !opportunity.amount) {
      return { valid: false, reason: 'Asset and amount are required' };
    }

    if (!opportunity.expectedProfit) {
      return { valid: false, reason: 'Expected profit is required' };
    }

    // Check if profit covers fees (basic validation)
    const amount = BigInt(opportunity.amount);
    const minFee = (amount * BigInt(5)) / BigInt(10000); // Minimum 0.05% fee
    const profit = BigInt(opportunity.expectedProfit);

    if (profit <= minFee) {
      return { valid: false, reason: 'Expected profit does not cover flash loan fees' };
    }

    return { valid: true };
  }
}

// Export singleton instance
export const flashLoanService = new FlashLoanService();
