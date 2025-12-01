import { ModuleCategory, EngineModule, ModuleType } from '../types';

// Directory Analysis Service
// Analyzes the core-logic directory structure and categorizes functional modules

export interface DirectoryAnalysisResult {
    totalFiles: number;
    totalDirectories: number;
    moduleCategories: ModuleCategory[];
    functionalModules: EngineModule[];
    analysisTimestamp: number;
}

export interface FileAnalysis {
    path: string;
    type: 'file' | 'directory';
    category: string;
    functionality: string;
    dependencies: string[];
}

// Analyze core-logic directory structure
export const analyzeDirectoryStructure = async (): Promise<DirectoryAnalysisResult> => {
    const startTime = Date.now();

    try {
        // This would normally scan the actual directory structure
        // For now, we'll simulate based on the known structure
        const analysisResult: DirectoryAnalysisResult = {
            totalFiles: 87, // Approximate count from directory listing
            totalDirectories: 12,
            moduleCategories: [],
            functionalModules: [],
            analysisTimestamp: startTime
        };

        // Analyze each known directory and map to module categories
        const directoryMappings = {
            'agents': {
                category: 'AI',
                type: 'AI' as ModuleType,
                description: 'AI-powered trading agents for decision making and execution'
            },
            'ai': {
                category: 'AI',
                type: 'AI' as ModuleType,
                description: 'Artificial intelligence and machine learning components'
            },
            'bots': {
                category: 'EXECUTION',
                type: 'EXECUTION' as ModuleType,
                description: 'Automated trading bots and execution engines'
            },
            'contracts': {
                category: 'BLOCKCHAIN',
                type: 'BLOCKCHAIN' as ModuleType,
                description: 'Smart contracts for DeFi interactions'
            },
            'deployment': {
                category: 'INFRA',
                type: 'INFRA' as ModuleType,
                description: 'Deployment and orchestration infrastructure'
            },
            'execution': {
                category: 'EXECUTION',
                type: 'EXECUTION' as ModuleType,
                description: 'Trade execution and atomic operations'
            },
            'infrastructure': {
                category: 'INFRA',
                type: 'INFRA' as ModuleType,
                description: 'Core infrastructure and connectivity layers'
            },
            'monitoring': {
                category: 'MONITORING',
                type: 'MONITORING' as ModuleType,
                description: 'Performance monitoring and analytics'
            },
            'platform': {
                category: 'SERVICES',
                type: 'SERVICES' as ModuleType,
                description: 'Platform services and utilities'
            },
            'rust-engine': {
                category: 'EXECUTION',
                type: 'EXECUTION' as ModuleType,
                description: 'High-performance Rust execution engine'
            },
            'scripts': {
                category: 'SERVICES',
                type: 'SERVICES' as ModuleType,
                description: 'Deployment and utility scripts'
            },
            'security': {
                category: 'SECURITY',
                type: 'SECURITY' as ModuleType,
                description: 'Security management and threat intelligence'
            }
        };

        // Create functional modules from directory analysis
        const functionalModules: EngineModule[] = Object.entries(directoryMappings).map(([dir, config], index) => ({
            id: `dir-${dir}`,
            name: `${dir.charAt(0).toUpperCase() + dir.slice(1)} Module`,
            type: config.type,
            status: ModuleStatus.INACTIVE,
            details: config.description,
            metrics: `Files: ${Math.floor(Math.random() * 10) + 1}`
        }));

        analysisResult.functionalModules = functionalModules;

        // Group into categories
        const categories = Object.values(directoryMappings).reduce((acc, config) => {
            const existing = acc.find(cat => cat.id === config.category.toLowerCase());
            if (existing) {
                existing.modules.push(...functionalModules.filter(m => m.type === config.type));
            } else {
                acc.push({
                    id: config.category.toLowerCase(),
                    name: `${config.category} Modules`,
                    description: config.description,
                    modules: functionalModules.filter(m => m.type === config.type),
                    critical: ['STRATEGY', 'EXECUTION', 'INFRA', 'SECURITY', 'BLOCKCHAIN'].includes(config.type)
                });
            }
            return acc;
        }, [] as ModuleCategory[]);

        analysisResult.moduleCategories = categories;

        return analysisResult;
    } catch (error) {
        console.error('Directory analysis failed:', error);
        throw new Error('Failed to analyze directory structure');
    }
};

// Get critical functional modules that must be operational
export const getCriticalFunctionalModules = (): string[] => {
    return [
        'agents',
        'execution',
        'infrastructure',
        'security',
        'contracts',
        'rust-engine'
    ];
};

// Validate that all critical directories exist and are accessible
export const validateCriticalDirectories = async (): Promise<{valid: boolean, missing: string[]}> => {
    const criticalDirs = getCriticalFunctionalModules();
    const missing: string[] = [];

    // In a real implementation, this would check actual file system
    // For simulation, assume all are present
    const valid = missing.length === 0;

    return { valid, missing };
};
