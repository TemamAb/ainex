import { ModuleStatus } from '../types';
import { getModulesByType } from './moduleRegistry';

export interface ActivationStep {
    id: string;
    label: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    details?: string;
}

export const getSimActivationSteps = (): ActivationStep[] => [
    {
        id: 'strategy-modules',
        label: 'Activating Strategy Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('STRATEGY').length} strategy modules (Arbitrage, Liquidation, MEV scanners)`
    },
    {
        id: 'ai-modules',
        label: 'Activating AI Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('AI').length} AI modules (Strategy Engine, Gemini Integration)`
    },
    {
        id: 'blockchain-modules',
        label: 'Connecting Blockchain Providers',
        status: 'PENDING',
        details: `Connecting ${getModulesByType('BLOCKCHAIN').length} blockchain networks (Ethereum, Arbitrum, Base)`
    },
    {
        id: 'monitoring-modules',
        label: 'Activating Monitoring Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('MONITORING').length} monitoring modules (Performance, Profit tracking)`
    },
    {
        id: 'services-modules',
        label: 'Activating Service Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('SERVICES').length} service modules (Price feeds, RPC services)`
    }
];

export const getLiveActivationSteps = (): ActivationStep[] => [
    {
        id: 'strategy-modules',
        label: 'Activating Strategy Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('STRATEGY').length} strategy modules (Arbitrage, Liquidation, MEV scanners)`
    },
    {
        id: 'execution-modules',
        label: 'Activating Execution Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('EXECUTION').length} execution modules (Flash loans, MEV bundles, Atomic swaps)`
    },
    {
        id: 'infrastructure-modules',
        label: 'Activating Infrastructure Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('INFRA').length} infrastructure modules (Paymaster, Wallets, Gateway)`
    },
    {
        id: 'security-modules',
        label: 'Activating Security Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('SECURITY').length} security modules (Threat intelligence, Capital allocation)`
    },
    {
        id: 'ai-modules',
        label: 'Activating AI Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('AI').length} AI modules (Strategy Engine, Gemini Integration)`
    },
    {
        id: 'blockchain-modules',
        label: 'Connecting Blockchain Providers',
        status: 'PENDING',
        details: `Connecting ${getModulesByType('BLOCKCHAIN').length} blockchain networks (Ethereum, Arbitrum, Base)`
    },
    {
        id: 'monitoring-modules',
        label: 'Activating Monitoring Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('MONITORING').length} monitoring modules (Performance, Profit tracking)`
    },
    {
        id: 'services-modules',
        label: 'Activating Service Modules',
        status: 'PENDING',
        details: `Loading ${getModulesByType('SERVICES').length} service modules (Price feeds, RPC services)`
    }
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
