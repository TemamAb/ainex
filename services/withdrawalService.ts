import { ProfitWithdrawalConfig, WithdrawalHistory } from '../types';
import { ethers } from 'ethers';

/**
 * Validates Ethereum wallet address format
 */
export const validateWalletAddress = (address: string): boolean => {
    try {
        return ethers.isAddress(address);
    } catch {
        return false;
    }
};

/**
 * Calculates randomized transfer time within max window
 * @param maxTransferTime - Maximum time in minutes
 * @returns Timestamp for scheduled transfer
 */
export const scheduleWithdrawal = (maxTransferTime: number): number => {
    // Random delay in milliseconds within the max time window
    const randomDelayMs = Math.random() * maxTransferTime * 60 * 1000;
    return Date.now() + randomDelayMs;
};

/**
 * Checks if withdrawal conditions are met
 */
export const checkWithdrawalConditions = (
    config: ProfitWithdrawalConfig,
    currentBalance: number
): boolean => {
    if (!config.isEnabled) return false;
    if (!validateWalletAddress(config.walletAddress)) return false;

    const threshold = parseFloat(config.thresholdAmount);
    const balance = parseFloat(config.smartBalance);

    return balance >= threshold && currentBalance >= threshold;
};

/**
 * Simulates blockchain withdrawal transaction
 */
export const executeWithdrawal = async (
    amount: string,
    address: string
): Promise<WithdrawalHistory> => {
    // Simulate transaction delay
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Generate mock transaction hash
    const txHash = '0x' + Array.from({ length: 64 }, () =>
        Math.floor(Math.random() * 16).toString(16)
    ).join('');

    const withdrawal: WithdrawalHistory = {
        id: `withdrawal-${Date.now()}`,
        timestamp: Date.now(),
        amount,
        txHash,
        status: Math.random() > 0.1 ? 'COMPLETED' : 'FAILED', // 90% success rate
        walletAddress: address
    };

    return withdrawal;
};

/**
 * Retrieves withdrawal history from storage
 */
export const getWithdrawalHistory = (): WithdrawalHistory[] => {
    try {
        const history = localStorage.getItem('withdrawalHistory');
        return history ? JSON.parse(history) : [];
    } catch {
        return [];
    }
};

/**
 * Saves withdrawal to history
 */
export const saveWithdrawalHistory = (withdrawal: WithdrawalHistory): void => {
    try {
        const history = getWithdrawalHistory();
        history.unshift(withdrawal);
        // Keep only last 50 withdrawals
        const trimmedHistory = history.slice(0, 50);
        localStorage.setItem('withdrawalHistory', JSON.stringify(trimmedHistory));
    } catch (error) {
        console.error('Failed to save withdrawal history:', error);
    }
};

/**
 * Formats time remaining until next transfer
 */
export const formatTimeRemaining = (timestamp: number | null): string => {
    if (!timestamp) return 'Not scheduled';

    const now = Date.now();
    const diff = timestamp - now;

    if (diff <= 0) return 'Processing...';

    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (minutes > 60) {
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours}h ${mins}m`;
    }

    return `${minutes}m ${seconds}s`;
};
