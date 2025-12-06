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
        const fallbackUrls = [
            process.env.NEXT_PUBLIC_ETH_RPC_URL,
            'https://ethereum.publicnode.com',
            'https://cloudflare-eth.com',
            'https://rpc.ankr.com/eth'
        ].filter(Boolean); // Remove undefined values

        for (const url of fallbackUrls) {
            try {
                console.log(`Trying Ethereum RPC: ${url}`);
                const testProvider = new ethers.JsonRpcProvider(url);
                // Test the connection with timeout
                const network = await Promise.race([
                    testProvider.getNetwork(),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
                ]);
                ethereumProvider = testProvider;
                console.log(`Successfully connected to Ethereum RPC: ${url} (Chain ID: ${(network as any).chainId})`);
                break;
            } catch (error) {
                console.warn(`Failed to connect to Ethereum RPC ${url}:`, error.message);
            }
        }

        if (!ethereumProvider) {
            throw new Error('All Ethereum RPC endpoints failed');
        }
    }
    return ethereumProvider;
};

export const getArbitrumProvider = async (): Promise<ethers.JsonRpcProvider> => {
    if (!arbitrumProvider) {
        const fallbackUrls = [
            process.env.NEXT_PUBLIC_ARBITRUM_RPC_URL,
            'https://arb1.arbitrum.io/rpc',
            'https://arbitrum-one.publicnode.com',
            'https://rpc.ankr.com/arbitrum'
        ].filter(Boolean); // Remove undefined values

        for (const url of fallbackUrls) {
            try {
                console.log(`Trying Arbitrum RPC: ${url}`);
                const testProvider = new ethers.JsonRpcProvider(url);
                // Test the connection with timeout
                const network = await Promise.race([
                    testProvider.getNetwork(),
                    new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
                ]);
                arbitrumProvider = testProvider;
                console.log(`Successfully connected to Arbitrum RPC: ${url} (Chain ID: ${(network as any).chainId})`);
                break;
            } catch (error) {
                console.warn(`Failed to connect to Arbitrum RPC ${url}:`, error.message);
            }
        }

        if (!arbitrumProvider) {
            throw new Error('All Arbitrum RPC endpoints failed');
        }
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
    const wsUrls: { [key: string]: string[] } = {
        ethereum: [
            'wss://mainnet.infura.io/ws/v3/9aa3d95b3bc440fa88ea12eaa4456161',
            'wss://eth-mainnet.g.alchemy.com/v2/demo',
            'wss://rpc.ankr.com/eth/ws'
        ],
        arbitrum: [
            'wss://arb-mainnet.g.alchemy.com/v2/demo',
            'wss://arbitrum-one.publicnode.com'
        ],
        base: [
            'wss://base-mainnet.g.alchemy.com/v2/demo',
            'wss://base.publicnode.com'
        ]
    };

    const urls = wsUrls[chain] || wsUrls.ethereum;

    for (const url of urls) {
        try {
            const provider = new ethers.WebSocketProvider(url);
            console.log(`WebSocket connected to ${chain}: ${url}`);
            return provider;
        } catch (error) {
            console.warn(`Failed to connect to ${url}, trying next...`);
        }
    }

    throw new Error(`Unable to connect to ${chain} WebSocket provider`);
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
