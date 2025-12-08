import { ModuleStatus } from '../types';
import { getModulesByType, activateModule, activateAllModules } from './moduleRegistry';

export interface ActivationStep {
    id: string;
    label: string;
    status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
    details?: string;
    error?: string;
    startTime?: number;
    endTime?: number;
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
    onProgress: (steps: ActivationStep[]) => void,
    mode: 'SIM' | 'LIVE' = 'LIVE'
): Promise<boolean> => {
    const currentSteps = [...steps];
    let hasErrors = false;

    for (let i = 0; i < currentSteps.length; i++) {
        const step = currentSteps[i];

        try {
            // Set current step to IN_PROGRESS with timestamp
            currentSteps[i] = {
                ...step,
                status: 'IN_PROGRESS',
                startTime: Date.now()
            };
            onProgress([...currentSteps]);

            // Actually activate modules based on step type
            await activateStepModules(step.id, mode);

            // Complete step with success
            currentSteps[i] = {
                ...currentSteps[i],
                status: 'COMPLETED',
                endTime: Date.now()
            };

        } catch (error: any) {
            console.error(`Activation failed for step ${step.id}:`, error);

            // Mark step as failed
            currentSteps[i] = {
                ...currentSteps[i],
                status: 'FAILED',
                error: error.message,
                endTime: Date.now()
            };

            hasErrors = true;

            // Continue with other steps but mark overall failure
        }

        onProgress([...currentSteps]);
    }

    return !hasErrors;
};

const activateModulesForMode = async (mode: 'SIM' | 'LIVE') => {
    if (mode === 'LIVE') {
        // Activate ALL modules for LIVE
        await activateAllModules();
    } else if (mode === 'SIM') {
        // Activate all modules EXCEPT real fund execution related for SIM
        const allModules = [
            ...getModulesByType('STRATEGY'),
            ...getModulesByType('INFRA'),
            ...getModulesByType('SECURITY'),
            ...getModulesByType('MONITORING'),
            ...getModulesByType('AI'),
            ...getModulesByType('BLOCKCHAIN'),
            ...getModulesByType('SERVICES')
            // Exclude EXECUTION modules (real fund execution)
        ];

        for (const module of allModules) {
            await activateModule(module.id);
        }
    }
};
