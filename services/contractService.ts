import { ethers } from 'ethers';
import { getEthereumProvider, getArbitrumProvider, getBaseProvider } from '../blockchain/providers';

// CONTRACT SERVICE
// Manages Smart Contract ABIs and Instance Creation with enhanced reliability

// Minimal ERC20 ABI for balance/approval
export const ERC20_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function decimals() view returns (uint8)",
    "function symbol() view returns (string)",
    "function approve(address spender, uint256 amount) returns (bool)",
    "function allowance(address owner, address spender) view returns (uint256)"
];

// ApexDEXRouter Interface - Matches the deployed contract
export const ROUTER_ABI = [
    "function swapExactInput(address dexRouter, address tokenIn, address tokenOut, uint256 amountIn, uint256 minAmountOut, address recipient) external returns (uint256 amountOut)",
    "function emergencyWithdraw(address token, uint256 amount) external"
];

// Flash Loan Provider ABIs
export const AAVE_V3_POOL_ABI = [
    "function flashLoan(address receiverAddress, address[] calldata assets, uint256[] calldata amounts, uint256[] calldata modes, address onBehalfOf, bytes calldata params, uint16 referralCode) external",
    "function getReserveData(address asset) external view returns (tuple(uint256 configuration, uint128 liquidityIndex, uint128 variableBorrowIndex, uint128 currentLiquidityRate, uint128 currentVariableBorrowRate, uint128 currentStableBorrowRate, uint40 lastUpdateTimestamp, address aTokenAddress, address stableDebtTokenAddress, address variableDebtTokenAddress, address interestRateStrategyAddress, uint8 id))"
];

export const UNISWAP_V3_ROUTER_ABI = [
    "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
    "function multicall(uint256 deadline, bytes[] data) external payable returns (bytes[])"
];

const CONTRACT_ADDRESSES = {
    ethereum: {
        router: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", // DEPLOYED ApexDEXRouter - Replace with actual deployed address
        usdc: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        weth: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        uniswapV3Router: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        aaveV3Pool: "0x87870Bcd2C42b5e4e4F9e06c1C2E9c8Fc8e8bEf"
    },
    arbitrum: {
        router: "0x0000000000000000000000000000000000000000", // Deploy separately for Arbitrum
        usdc: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        weth: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        uniswapV3Router: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        aaveV3Pool: "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    },
    base: {
        router: "0x0000000000000000000000000000000000000000", // Deploy separately for Base
        usdc: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        weth: "0x4200000000000000000000000000000000000006",
        uniswapV3Router: "0x2626664c2603336E57B271c5ade5bF640772CcB5",
        aaveV3Pool: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
    }
};

export interface ContractServiceMetrics {
    totalContractsCreated: number;
    successfulCalls: number;
    failedCalls: number;
    averageResponseTime: number;
    cacheHitRate: number;
    lastActivity: number;
}

export interface CircuitBreaker {
    isOpen: boolean;
    failureCount: number;
    lastFailureTime: number;
    nextRetryTime: number;
}

export interface CachedContract {
    contract: ethers.Contract;
    createdAt: number;
    lastUsed: number;
}

// Enhanced Contract Service with circuit breaker, caching, and metrics
export class ContractService {
    private contractCache: Map<string, CachedContract> = new Map();
    private readonly CACHE_DURATION = 1800000; // 30 minutes
    private readonly MAX_CACHE_SIZE = 100;
    private readonly CIRCUIT_BREAKER_THRESHOLD = 5;
    private readonly CIRCUIT_BREAKER_TIMEOUT = 300000; // 5 minutes

    private circuitBreaker: CircuitBreaker = {
        isOpen: false,
        failureCount: 0,
        lastFailureTime: 0,
        nextRetryTime: 0
    };

    private metrics: ContractServiceMetrics = {
        totalContractsCreated: 0,
        successfulCalls: 0,
        failedCalls: 0,
        averageResponseTime: 0,
        cacheHitRate: 0,
        lastActivity: 0
    };

    // Get circuit breaker status
    getCircuitBreakerStatus(): CircuitBreaker {
        return { ...this.circuitBreaker };
    }

    // Get current metrics
    getMetrics(): ContractServiceMetrics {
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

    // Validate contract address
    private validateAddress(address: string): void {
        if (!ethers.isAddress(address)) {
            throw new Error(`Invalid contract address: ${address}`);
        }
    }

    // Validate ABI
    private validateAbi(abi: any[]): void {
        if (!Array.isArray(abi) || abi.length === 0) {
            throw new Error('Invalid ABI: must be a non-empty array');
        }
    }

    // Get cached contract
    private getCachedContract(cacheKey: string): ethers.Contract | null {
        const cached = this.contractCache.get(cacheKey);
        if (cached && Date.now() - cached.createdAt < this.CACHE_DURATION) {
            cached.lastUsed = Date.now();
            this.metrics.cacheHitRate = (this.metrics.cacheHitRate + 1) / 2; // Running average
            return cached.contract;
        }

        // Remove expired cache entry
        if (cached) {
            this.contractCache.delete(cacheKey);
        }

        return null;
    }

    // Set cached contract
    private setCachedContract(cacheKey: string, contract: ethers.Contract): void {
        // Manage cache size - remove least recently used if at capacity
        if (this.contractCache.size >= this.MAX_CACHE_SIZE) {
            let oldestKey = '';
            let oldestTime = Date.now();

            for (const entry of Array.from(this.contractCache.entries())) {
                const [key, cached] = entry;
                if (cached.lastUsed < oldestTime) {
                    oldestTime = cached.lastUsed;
                    oldestKey = key;
                }
            }

            if (oldestKey) {
                this.contractCache.delete(oldestKey);
            }
        }

        this.contractCache.set(cacheKey, {
            contract,
            createdAt: Date.now(),
            lastUsed: Date.now()
        });
    }

    // Update metrics
    private updateMetrics(success: boolean, responseTime: number): void {
        this.metrics.lastActivity = Date.now();

        if (success) {
            this.metrics.successfulCalls++;
        } else {
            this.metrics.failedCalls++;
        }

        // Update average response time
        const totalCalls = this.metrics.successfulCalls + this.metrics.failedCalls;
        this.metrics.averageResponseTime = (
            (this.metrics.averageResponseTime * (totalCalls - 1)) + responseTime
        ) / totalCalls;
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
            console.warn('🚫 Contract service circuit breaker opened due to consecutive failures');
        }
    }

    // Clear all cached contracts
    clearCache(): void {
        this.contractCache.clear();
        console.log('🧹 Contract service cache cleared');
    }

    // Reset circuit breaker
    resetCircuitBreaker(): void {
        this.circuitBreaker = {
            isOpen: false,
            failureCount: 0,
            lastFailureTime: 0,
            nextRetryTime: 0
        };
        console.log('🔄 Contract service circuit breaker reset');
    }
}

// Create singleton instance
const contractService = new ContractService();

export const getContract = async (
    address: string,
    abi: any[],
    chain: 'ethereum' | 'arbitrum' | 'base',
    signer?: ethers.Signer
): Promise<ethers.Contract> => {
    const startTime = Date.now();

    try {
        // Check circuit breaker
        if (contractService.getCircuitBreakerStatus().isOpen) {
            throw new Error('Circuit breaker is open - contract creation temporarily disabled');
        }

        // Validate inputs
        contractService['validateAddress'](address);
        contractService['validateAbi'](abi);

        // Create cache key
        const cacheKey = `${chain}_${address}_${signer ? 'signer' : 'provider'}`;

        // Check cache first
        const cachedContract = contractService['getCachedContract'](cacheKey);
        if (cachedContract) {
            contractService['updateMetrics'](true, Date.now() - startTime);
            return cachedContract;
        }

        // Get provider based on chain
        let provider: ethers.Provider;

        switch (chain) {
            case 'ethereum': provider = await getEthereumProvider(); break;
            case 'arbitrum': provider = await getArbitrumProvider(); break;
            case 'base': provider = await getBaseProvider(); break;
            default: throw new Error(`Unsupported chain: ${chain}`);
        }

        // Create contract instance
        const contract = new ethers.Contract(address, abi, signer || provider);

        // Test contract connectivity with a lightweight call
        try {
            await contract.runner?.provider?.getBlockNumber();
        } catch (error) {
            throw new Error(`Contract connectivity test failed: ${error}`);
        }

        // Cache the contract
        contractService['setCachedContract'](cacheKey, contract);
        contractService['updateMetrics'](true, Date.now() - startTime);

        // Reset circuit breaker on success
        contractService['updateCircuitBreaker'](true);

        return contract;

    } catch (error: any) {
        const responseTime = Date.now() - startTime;
        contractService['updateMetrics'](false, responseTime);
        contractService['updateCircuitBreaker'](false);

        console.error('Failed to create contract:', error.message);
        throw error;
    }
};

export const getRouterContract = async (chain: 'ethereum' | 'arbitrum', signer?: ethers.Signer) => {
    return getContract(CONTRACT_ADDRESSES[chain].router, ROUTER_ABI, chain, signer);
};

export const getTokenContract = async (address: string, chain: 'ethereum' | 'arbitrum' | 'base', signer?: ethers.Signer) => {
    return getContract(address, ERC20_ABI, chain, signer);
};

// Additional contract getters for common protocols
export const getUniswapV3Router = async (chain: 'ethereum' | 'arbitrum' | 'base', signer?: ethers.Signer) => {
    return getContract(CONTRACT_ADDRESSES[chain].uniswapV3Router, UNISWAP_V3_ROUTER_ABI, chain, signer);
};

export const getAaveV3Pool = async (chain: 'ethereum' | 'arbitrum' | 'base', signer?: ethers.Signer) => {
    return getContract(CONTRACT_ADDRESSES[chain].aaveV3Pool, AAVE_V3_POOL_ABI, chain, signer);
};

// Get contract service instance for advanced operations
export const getContractService = (): ContractService => {
    return contractService;
};
