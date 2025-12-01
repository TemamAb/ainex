import { checkProviderHealth, getLatestBlockNumber, getCurrentGasPrice } from '../blockchain/providers';
import { getEthereumProvider, getArbitrumProvider, getBaseProvider } from '../blockchain/providers';
import { activateAllModules, getCriticalModules, ModuleActivationResult } from './moduleRegistry';
import { analyzeDirectoryStructure, validateCriticalDirectories, DirectoryAnalysisResult } from './directoryAnalysisService';
import { ethers } from 'ethers';

export interface PreflightCheck {
    id: string;
    name: string;
    status: 'pending' | 'running' | 'passed' | 'failed';
    message: string;
    timestamp?: number;
    category?: 'network' | 'modules' | 'security';
}

export interface PreflightResults {
    allPassed: boolean;
    checks: PreflightCheck[];
    moduleActivations: ModuleActivationResult[];
    timestamp: number;
}

// Run all preflight checks
export const runPreflightChecks = async (): Promise<PreflightResults> => {
    const checks: PreflightCheck[] = [
        { id: 'eth-rpc', name: 'Ethereum RPC Connection', status: 'pending', message: '' },
        { id: 'arb-rpc', name: 'Arbitrum RPC Connection', status: 'pending', message: '' },
        { id: 'base-rpc', name: 'Base RPC Connection', status: 'pending', message: '' },
        { id: 'eth-block', name: 'Ethereum Block Sync', status: 'pending', message: '' },
        { id: 'gas-price', name: 'Gas Price Feed', status: 'pending', message: '' },
    ];

    // Check Ethereum RPC
    checks[0].status = 'running';
    try {
        const ethProvider = getEthereumProvider();
        const isHealthy = await checkProviderHealth(ethProvider);
        if (isHealthy) {
            checks[0].status = 'passed';
            checks[0].message = 'Connected to Ethereum mainnet';
        } else {
            checks[0].status = 'failed';
            checks[0].message = 'Failed to connect to Ethereum RPC';
        }
    } catch (error: any) {
        checks[0].status = 'failed';
        checks[0].message = error.message || 'Unknown error';
    }
    checks[0].timestamp = Date.now();

    // Check Arbitrum RPC
    checks[1].status = 'running';
    try {
        const arbProvider = getArbitrumProvider();
        const isHealthy = await checkProviderHealth(arbProvider);
        if (isHealthy) {
            checks[1].status = 'passed';
            checks[1].message = 'Connected to Arbitrum mainnet';
        } else {
            checks[1].status = 'failed';
            checks[1].message = 'Failed to connect to Arbitrum RPC';
        }
    } catch (error: any) {
        checks[1].status = 'failed';
        checks[1].message = error.message || 'Unknown error';
    }
    checks[1].timestamp = Date.now();

    // Check Base RPC
    checks[2].status = 'running';
    try {
        const baseProvider = getBaseProvider();
        const isHealthy = await checkProviderHealth(baseProvider);
        if (isHealthy) {
            checks[2].status = 'passed';
            checks[2].message = 'Connected to Base mainnet';
        } else {
            checks[2].status = 'failed';
            checks[2].message = 'Failed to connect to Base RPC';
        }
    } catch (error: any) {
        checks[2].status = 'failed';
        checks[2].message = error.message || 'Unknown error';
    }
    checks[2].timestamp = Date.now();

    // Check Ethereum block sync
    checks[3].status = 'running';
    try {
        const blockNumber = await getLatestBlockNumber('ethereum');
        if (blockNumber > 0) {
            checks[3].status = 'passed';
            checks[3].message = `Latest block: ${blockNumber}`;
        } else {
            checks[3].status = 'failed';
            checks[3].message = 'Block number is 0';
        }
    } catch (error: any) {
        checks[3].status = 'failed';
        checks[3].message = error.message || 'Unknown error';
    }
    checks[3].timestamp = Date.now();

    // Check gas price feed
    checks[4].status = 'running';
    try {
        const gasPrice = await getCurrentGasPrice('ethereum');
        const gasPriceGwei = Number(gasPrice) / 1e9;
        if (gasPriceGwei > 0) {
            checks[4].status = 'passed';
            checks[4].message = `Current gas: ${gasPriceGwei.toFixed(2)} Gwei`;
        } else {
            checks[4].status = 'failed';
            checks[4].message = 'Gas price is 0';
        }
    } catch (error: any) {
        checks[4].status = 'failed';
        checks[4].message = error.message || 'Unknown error';
    }
    checks[4].timestamp = Date.now();

    const allPassed = checks.every(check => check.status === 'passed');

    return {
        allPassed,
        checks,
        timestamp: Date.now(),
    };
};
