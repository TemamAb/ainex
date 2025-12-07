import { ModuleStatus } from '../types';

export interface ActivationStep {
    id: string;
    label: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    details?: string;
}

export const getSimActivationSteps = (): ActivationStep[] => [
    { id: 'market-data', label: 'Connecting to Real Market Data', status: 'PENDING', details: 'Source: Coingecko API / Chainlink Oracles' },
    { id: 'paper-wallet', label: 'Initializing Paper Trading Wallet', status: 'PENDING', details: 'Mode: Virtual Sandbox' },
    { id: 'strategy-engine', label: 'Loading Strategy Engine', status: 'PENDING', details: 'Arbitrage Scanner: Active' },
    { id: 'engine-loop', label: 'Starting Real-Time Analysis Loop', status: 'PENDING', details: 'Latency: <50ms' }
];

export const getLiveActivationSteps = (): ActivationStep[] => [
    { id: 'wallet-check', label: 'Verifying Wallet & Funds', status: 'PENDING', details: 'Checking Native ETH / Paymaster availability' },
    { id: 'mainnet-rpc', label: 'Connecting to Mainnet RPCs', status: 'PENDING', details: 'Ethereum, Arbitrum, Base' },
    { id: 'security-check', label: 'Final Security Handshake', status: 'PENDING', details: 'MEV Protection: Armed' },
    { id: 'live-execution', label: 'Enabling Live Execution', status: 'PENDING', details: 'Real Funds at Risk' }
];

export const runActivationSequence = async (
    steps: ActivationStep[],
    onProgress: (steps: ActivationStep[]) => void
): Promise<boolean> => {
    const currentSteps = [...steps];

    for (let i = 0; i < currentSteps.length; i++) {
        // Set current step to IN_PROGRESS
        currentSteps[i] = { ...currentSteps[i], status: 'IN_PROGRESS' };
        onProgress([...currentSteps]);

        // Simulate work (1.5s per step for visual clarity)
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Complete step
        currentSteps[i] = { ...currentSteps[i], status: 'COMPLETED' };
        onProgress([...currentSteps]);
    }

    return true;
};
