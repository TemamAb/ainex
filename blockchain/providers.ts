import { ethers } from 'ethers';

// RPC Provider Configuration
export const RPC_ENDPOINTS = {
    ethereum: {
        mainnet: process.env.NEXT_PUBLIC_ETH_RPC_URL || 'https://eth.llamarpc.com',
        ws: process.env.NEXT_PUBLIC_ETH_WS_URL || 'wss://eth.llamarpc.com',
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

export const getEthereumProvider = (): ethers.JsonRpcProvider => {
    if (!ethereumProvider) {
        ethereumProvider = new ethers.JsonRpcProvider(RPC_ENDPOINTS.ethereum.mainnet);
    }
    return ethereumProvider;
};

export const getArbitrumProvider = (): ethers.JsonRpcProvider => {
    if (!arbitrumProvider) {
        arbitrumProvider = new ethers.JsonRpcProvider(RPC_ENDPOINTS.arbitrum.mainnet);
    }
    return arbitrumProvider;
};

export const getBaseProvider = (): ethers.JsonRpcProvider => {
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

// Health check for RPC endpoint
export const checkProviderHealth = async (provider: ethers.JsonRpcProvider): Promise<boolean> => {
    try {
        const blockNumber = await provider.getBlockNumber();
        return blockNumber > 0;
    } catch (error) {
        console.error('Provider health check failed:', error);
        return false;
    }
};

// Get current gas price
export const getCurrentGasPrice = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<bigint> => {
    const provider = chain === 'ethereum' ? getEthereumProvider() :
        chain === 'arbitrum' ? getArbitrumProvider() :
            getBaseProvider();

    const feeData = await provider.getFeeData();
    return feeData.gasPrice || BigInt(0);
};

// Get latest block number
export const getLatestBlockNumber = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<number> => {
    const provider = chain === 'ethereum' ? getEthereumProvider() :
        chain === 'arbitrum' ? getArbitrumProvider() :
            getBaseProvider();

    return await provider.getBlockNumber();
};
