import { ethers } from 'ethers';

// RPC Provider Configuration
export const RPC_ENDPOINTS = {
    ethereum: {
        mainnet: process.env.NEXT_PUBLIC_ETH_RPC_URL || 'https://cloudflare-eth.com',
        ws: process.env.NEXT_PUBLIC_ETH_WS_URL || 'wss://cloudflare-eth.com',
    },
    arbitrum: {
        mainnet: process.env.NEXT_PUBLIC_ARBITRUM_RPC_URL || 'https://arb1.arbitrum.io/rpc',
        ws: process.env.NEXT_PUBLIC_ARBITRUM_WS_URL || 'wss://arb1.arbitrum.io/rpc',
    },
    base: {
        mainnet: process.env.NEXT_PUBLIC_BASE_RPC_URL || 'https://mainnet.base.org',
        ws: process.env.NEXT_PUBLIC_BASE_WS_URL || 'wss://mainnet.base.org',
    },
};

// Provider instances with fallback
let ethereumProvider: ethers.JsonRpcProvider | null = null;
let arbitrumProvider: ethers.JsonRpcProvider | null = null;
let baseProvider: ethers.JsonRpcProvider | null = null;

export const getEthereumProvider = async (): Promise<ethers.JsonRpcProvider> => {
    if (!ethereumProvider) {
        // Try environment variable first, but fall back to free endpoint if it fails
        const envUrl = process.env.NEXT_PUBLIC_ETH_RPC_URL;
        if (envUrl) {
            try {
                // validate-env.js confirmed this URL is correct, but we wrap in try/catch for runtime safety
                const testProvider = new ethers.JsonRpcProvider(envUrl);
                // Test the connection by trying to get network info
                await testProvider.getNetwork();
                ethereumProvider = testProvider;
                console.log('Using environment RPC URL for Ethereum');
            } catch (error) {
                console.error('Environment RPC URL connection failed:', error);
                console.warn('Falling back to public PublicNode RPC...');
                ethereumProvider = new ethers.JsonRpcProvider('https://ethereum.publicnode.com');
            }
        } else {
            console.warn('NEXT_PUBLIC_ETH_RPC_URL not set. Using public PublicNode RPC.');
            ethereumProvider = new ethers.JsonRpcProvider('https://ethereum.publicnode.com');
        }
    }
    return ethereumProvider;
};

export const getArbitrumProvider = async (): Promise<ethers.JsonRpcProvider> => {
    if (!arbitrumProvider) {
        console.log('Initializing Arbitrum Provider with URL:', RPC_ENDPOINTS.arbitrum.mainnet);
        arbitrumProvider = new ethers.JsonRpcProvider(RPC_ENDPOINTS.arbitrum.mainnet);
    }
    return arbitrumProvider;
};

export const getBaseProvider = async (): Promise<ethers.JsonRpcProvider> => {
    if (!baseProvider) {
        baseProvider = new ethers.JsonRpcProvider(RPC_ENDPOINTS.base.mainnet);
    }
    return baseProvider;
};

// WebSocket Provider for real-time mempool monitoring
export const getWebSocketProvider = (chain: 'ethereum' | 'arbitrum' | 'base'): ethers.WebSocketProvider => {
    const wsUrl = RPC_ENDPOINTS[chain].ws;
    return new ethers.WebSocketProvider(wsUrl);
};

// Get current gas price
export const getCurrentGasPrice = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<bigint> => {
    const provider = chain === 'ethereum' ? await getEthereumProvider()
        : chain === 'arbitrum' ? await getArbitrumProvider()
            : await getBaseProvider();

    const feeData = await provider.getFeeData();
    return feeData.gasPrice || BigInt(0);
};

// Health check for RPC endpoint with Chain ID validation
export const checkProviderHealth = async (provider: ethers.JsonRpcProvider, expectedChainId: number): Promise<boolean> => {
    try {
        const network = await provider.getNetwork();
        const blockNumber = await provider.getBlockNumber();

        if (network.chainId !== BigInt(expectedChainId)) {
            console.warn(`Provider connected to chain ${network.chainId}, expected ${expectedChainId}`);
            return false;
        }
        return blockNumber > 0;
    } catch (error) {
        console.error('Provider health check failed:', error);
        return false;
    }
};

// Get latest block number
export const getLatestBlockNumber = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<number> => {
    const provider = chain === 'ethereum' ? await getEthereumProvider() :
        chain === 'arbitrum' ? await getArbitrumProvider() :
            await getBaseProvider();

    return await provider.getBlockNumber();
};

// Get recent transactions from mempool (simplified for SIM mode)
export const getRecentTransactions = async (chain: 'ethereum' | 'arbitrum' | 'base', limit: number = 10): Promise<any[]> => {
    try {
        const provider = chain === 'ethereum' ? await getEthereumProvider() :
            chain === 'arbitrum' ? await getArbitrumProvider() :
                await getBaseProvider();

        const latestBlock = await provider.getBlockNumber();
        const transactions: any[] = [];

        // Get transactions from recent blocks
        for (let i = 0; i < Math.min(limit, 5); i++) {
            const blockNumber = latestBlock - i;
            if (blockNumber > 0) {
                const block = await provider.getBlock(blockNumber, true);
                if (block && block.transactions) {
                    // Take first few transactions from each block
                    const blockTxs = block.transactions.slice(0, 2);
                    transactions.push(...blockTxs);
                }
            }
        }

        return transactions.slice(0, limit);
    } catch (error) {
        console.error('Error fetching recent transactions:', error);
        return [];
    }
};
