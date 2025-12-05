import { ethers } from 'ethers';
import { getEthereumProvider, getArbitrumProvider, getBaseProvider } from '../blockchain/providers';

// CONTRACT SERVICE
// Manages Smart Contract ABIs and Instance Creation

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

const CONTRACT_ADDRESSES = {
    ethereum: {
        router: "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", // DEPLOYED ApexDEXRouter - Replace with actual deployed address
        usdc: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    },
    arbitrum: {
        router: "0x0000000000000000000000000000000000000000", // Deploy separately for Arbitrum
        usdc: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    }
};

export const getContract = async (
    address: string,
    abi: any[],
    chain: 'ethereum' | 'arbitrum' | 'base',
    signer?: ethers.Signer
): Promise<ethers.Contract> => {
    let provider: ethers.Provider;

    switch (chain) {
        case 'ethereum': provider = await getEthereumProvider(); break;
        case 'arbitrum': provider = await getArbitrumProvider(); break;
        case 'base': provider = await getBaseProvider(); break;
        default: throw new Error(`Unsupported chain: ${chain}`);
    }

    // Connect with signer if provided (for write ops), otherwise provider (read-only)
    return new ethers.Contract(address, abi, signer || provider);
};

export const getRouterContract = async (chain: 'ethereum' | 'arbitrum', signer?: ethers.Signer) => {
    return getContract(CONTRACT_ADDRESSES[chain].router, ROUTER_ABI, chain, signer);
};

export const getTokenContract = async (address: string, chain: 'ethereum' | 'arbitrum' | 'base', signer?: ethers.Signer) => {
    return getContract(address, ERC20_ABI, chain, signer);
};
