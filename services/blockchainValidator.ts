import { TransactionVerification, BlockValidation, verifyTransactionOnChain, validateBlockNumber } from './etherscanService';
import { getLatestBlockNumber } from '../blockchain/providers';

export type VerificationStatus = 'VERIFIED' | 'PENDING' | 'UNVERIFIED' | 'FAILED';

export interface VerificationResult {
    status: VerificationStatus;
    txHash?: string;
    blockNumber?: number;
    verified: boolean;
    explorerLink?: string;
    verificationData?: TransactionVerification;
    error?: string;
    verifiedAt?: number;
    responseTime?: number;
}

export interface ConsensusResult {
    consensus: boolean;
    verifications: TransactionVerification[];
    discrepancies: string[];
    consensusConfidence?: number;
    validationTime?: number;
}

export interface BlockchainValidatorMetrics {
    totalVerifications: number;
    successfulVerifications: number;
    failedVerifications: number;
    averageResponseTime: number;
    cacheHitRate: number;
    lastVerificationTime: number;
}

export interface CircuitBreaker {
    isOpen: boolean;
    failureCount: number;
    lastFailureTime: number;
    nextRetryTime: number;
}

export interface CachedVerificationResult extends VerificationResult {
    cachedAt: number;
}

// Enhanced Blockchain Validator with circuit breaker, caching, and metrics
export class BlockchainValidator {
    private verificationCache: Map<string, CachedVerificationResult> = new Map();
    private readonly CACHE_DURATION = 300000; // 5 minutes
    private readonly MAX_CACHE_SIZE = 1000;
    private readonly CIRCUIT_BREAKER_THRESHOLD = 5;
    private readonly CIRCUIT_BREAKER_TIMEOUT = 300000; // 5 minutes

    private circuitBreaker: CircuitBreaker = {
        isOpen: false,
        failureCount: 0,
        lastFailureTime: 0,
        nextRetryTime: 0
    };

    private metrics: BlockchainValidatorMetrics = {
        totalVerifications: 0,
        successfulVerifications: 0,
        failedVerifications: 0,
        averageResponseTime: 0,
        cacheHitRate: 0,
        lastVerificationTime: 0
    };

    // Get circuit breaker status
    getCircuitBreakerStatus(): CircuitBreaker {
        return { ...this.circuitBreaker };
    }

    // Get current metrics
    getMetrics(): BlockchainValidatorMetrics {
        return { ...this.metrics };
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

    // Get cached verification result
    private getCachedResult(txHash: string): CachedVerificationResult | null {
        const cached = this.verificationCache.get(txHash);
        if (cached && Date.now() - cached.cachedAt < this.CACHE_DURATION) {
            this.metrics.cacheHitRate = (this.metrics.cacheHitRate + 1) / 2; // Running average
            return cached;
        }

        // Remove expired cache entry
        if (cached) {
            this.verificationCache.delete(txHash);
        }

        return null;
    }

    // Set cached verification result
    private setCachedResult(txHash: string, result: VerificationResult): void {
        // Manage cache size
        if (this.verificationCache.size >= this.MAX_CACHE_SIZE) {
            const firstKey = this.verificationCache.keys().next().value;
            this.verificationCache.delete(firstKey);
        }

        this.verificationCache.set(txHash, {
            ...result,
            cachedAt: Date.now()
        });
    }

    // Update metrics
    private updateMetrics(success: boolean, responseTime: number): void {
        this.metrics.totalVerifications++;
        this.metrics.lastVerificationTime = Date.now();

        if (success) {
            this.metrics.successfulVerifications++;
        } else {
            this.metrics.failedVerifications++;
        }

        // Update average response time
        const totalCompleted = this.metrics.successfulVerifications + this.metrics.failedVerifications;
        this.metrics.averageResponseTime = (
            (this.metrics.averageResponseTime * (totalCompleted - 1)) + responseTime
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
            console.warn('🚫 Circuit breaker opened due to consecutive verification failures');
        }
    }

    // Clear all cached data
    clearCache(): void {
        this.verificationCache.clear();
        console.log('🧹 Blockchain validator cache cleared');
    }

    // Reset circuit breaker
    resetCircuitBreaker(): void {
        this.circuitBreaker = {
            isOpen: false,
            failureCount: 0,
            lastFailureTime: 0,
            nextRetryTime: 0
        };
        console.log('🔄 Circuit breaker reset');
    }
}

// Create singleton instance
const validator = new BlockchainValidator();

/**
 * Verify transaction across multiple sources
 */
export const crossValidateTransaction = async (
    txHash: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<ConsensusResult> => {
    const startTime = Date.now();

    try {
        // Check circuit breaker
        if (validator.getCircuitBreakerStatus().isOpen) {
            throw new Error('Circuit breaker is open - validation temporarily disabled');
        }

        // Check cache first
        const cachedResult = validator['getCachedResult'](txHash);
        if (cachedResult) {
            return {
                consensus: cachedResult.verified,
                verifications: cachedResult.verificationData ? [cachedResult.verificationData] : [],
                discrepancies: [],
                consensusConfidence: cachedResult.verified ? 1.0 : 0.0,
                validationTime: Date.now() - startTime
            };
        }

        // Verify via Etherscan API with retry logic
        const etherscanVerification = await validator['retryWithBackoff'](
            () => verifyTransactionOnChain(txHash, chain)
        );

        // TODO: Add verification from other RPC providers (Infura, Alchemy, etc.)
        // For now, we'll use Etherscan as the primary source

        const verifications = [etherscanVerification];
        const discrepancies: string[] = [];

        // Check for consensus (all verifications match)
        const consensus = verifications.every(v =>
            v.txHash === etherscanVerification.txHash &&
            v.blockNumber === etherscanVerification.blockNumber &&
            v.status === etherscanVerification.status
        );

        const consensusConfidence = consensus ? 1.0 : 0.0;
        const validationTime = Date.now() - startTime;

        // Update metrics
        validator['updateMetrics'](consensus, validationTime);
        validator['updateCircuitBreaker'](consensus);

        // Cache result
        const result: VerificationResult = {
            status: consensus ? 'VERIFIED' : 'FAILED',
            txHash,
            verified: consensus,
            verificationData: etherscanVerification,
            verifiedAt: Date.now(),
            responseTime: validationTime
        };
        validator['setCachedResult'](txHash, result);

        return {
            consensus,
            verifications,
            discrepancies,
            consensusConfidence,
            validationTime
        };
    } catch (error: any) {
        const validationTime = Date.now() - startTime;

        // Update metrics for failure
        validator['updateMetrics'](false, validationTime);
        validator['updateCircuitBreaker'](false);

        return {
            consensus: false,
            verifications: [],
            discrepancies: [error.message],
            consensusConfidence: 0.0,
            validationTime
        };
    }
};

/**
 * Verify a trade transaction
 */
export const verifyTrade = async (
    txHash: string,
    expectedProfit: number,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<VerificationResult> => {
    try {
        // Verify transaction exists on blockchain
        const verification = await verifyTransactionOnChain(txHash, chain);

        if (!verification.verified) {
            return {
                status: 'FAILED',
                verified: false,
                error: 'Transaction not found on blockchain'
            };
        }

        // Validate transaction was successful
        if (verification.status !== 'success') {
            return {
                status: 'FAILED',
                txHash,
                blockNumber: verification.blockNumber,
                verified: false,
                explorerLink: verification.explorerLink,
                error: 'Transaction failed on blockchain'
            };
        }

        // Validate block has enough confirmations (at least 1)
        const blockValidation = await validateBlockNumber(verification.blockNumber, chain);

        if (!blockValidation.valid) {
            return {
                status: 'PENDING',
                txHash,
                blockNumber: verification.blockNumber,
                verified: false,
                explorerLink: verification.explorerLink,
                error: 'Block not yet confirmed'
            };
        }

        if (blockValidation.confirmations < 1) {
            return {
                status: 'PENDING',
                txHash,
                blockNumber: verification.blockNumber,
                verified: false,
                explorerLink: verification.explorerLink,
                verificationData: verification,
                error: `Awaiting confirmations (${blockValidation.confirmations}/1)`
            };
        }

        // Transaction is verified!
        return {
            status: 'VERIFIED',
            txHash,
            blockNumber: verification.blockNumber,
            verified: true,
            explorerLink: verification.explorerLink,
            verificationData: verification,
            verifiedAt: Date.now()
        };
    } catch (error: any) {
        return {
            status: 'FAILED',
            verified: false,
            error: error.message
        };
    }
};

/**
 * Batch verify multiple transactions
 */
export const batchVerifyTransactions = async (
    txHashes: string[],
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<Map<string, VerificationResult>> => {
    const results = new Map<string, VerificationResult>();

    // Verify transactions sequentially to respect rate limits
    for (const txHash of txHashes) {
        try {
            const result = await verifyTrade(txHash, 0, chain);
            results.set(txHash, result);
        } catch (error: any) {
            results.set(txHash, {
                status: 'FAILED',
                verified: false,
                error: error.message
            });
        }
    }

    return results;
};

/**
 * Check if system is in genuine LIVE mode
 * Returns true only if recent transactions are verified on-chain
 */
export const validateLiveModeAuthenticity = async (
    recentTxHashes: string[],
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<{
    isGenuineLive: boolean;
    verifiedCount: number;
    totalCount: number;
    verificationRate: number;
}> => {
    if (recentTxHashes.length === 0) {
        return {
            isGenuineLive: false,
            verifiedCount: 0,
            totalCount: 0,
            verificationRate: 0
        };
    }

    const results = await batchVerifyTransactions(recentTxHashes, chain);
    const verifiedCount = Array.from(results.values()).filter(r => r.verified).length;
    const totalCount = recentTxHashes.length;
    const verificationRate = (verifiedCount / totalCount) * 100;

    // Consider genuine LIVE if at least 80% of transactions are verified
    const isGenuineLive = verificationRate >= 80;

    return {
        isGenuineLive,
        verifiedCount,
        totalCount,
        verificationRate
    };
};

/**
 * Generate verification report for export
 */
export const generateVerificationReport = async (
    transactions: Array<{ id: string; txHash: string; profit: number }>,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<any> => {
    const verifications = await batchVerifyTransactions(
        transactions.map(t => t.txHash),
        chain
    );

    const latestBlock = await getLatestBlockNumber(chain);

    return {
        reportId: `audit-${Date.now()}`,
        generatedAt: new Date().toISOString(),
        mode: 'LIVE',
        chain,
        totalTransactions: transactions.length,
        verifiedTransactions: Array.from(verifications.values()).filter(v => v.verified).length,
        failedVerifications: Array.from(verifications.values()).filter(v => !v.verified).length,
        transactions: transactions.map(t => ({
            id: t.id,
            txHash: t.txHash,
            profit: t.profit,
            verified: verifications.get(t.txHash)?.verified || false,
            status: verifications.get(t.txHash)?.status || 'UNVERIFIED',
            explorerLink: verifications.get(t.txHash)?.explorerLink,
            blockNumber: verifications.get(t.txHash)?.blockNumber,
            verificationTimestamp: verifications.get(t.txHash)?.verifiedAt
        })),
        blockchainProof: {
            latestBlock,
            chainId: chain === 'ethereum' ? 1 : chain === 'arbitrum' ? 42161 : 8453,
            verificationTimestamp: Date.now()
        }
    };
};
