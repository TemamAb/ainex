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
}

export interface ConsensusResult {
    consensus: boolean;
    verifications: TransactionVerification[];
    discrepancies: string[];
}

/**
 * Verify transaction across multiple sources
 */
export const crossValidateTransaction = async (
    txHash: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<ConsensusResult> => {
    try {
        // Verify via Etherscan API
        const etherscanVerification = await verifyTransactionOnChain(txHash, chain);

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

        return {
            consensus,
            verifications,
            discrepancies
        };
    } catch (error: any) {
        return {
            consensus: false,
            verifications: [],
            discrepancies: [error.message]
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
