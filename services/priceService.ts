import { ethers } from 'ethers';
import { getEthereumProvider, getArbitrumProvider, getBaseProvider } from '../blockchain/providers';
import { ERC20_ABI, CONTRACT_ADDRESSES } from '../blockchain/contracts';

// Chainlink Price Feed ABI (minimal)
const CHAINLINK_PRICE_FEED_ABI = [
    'function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)',
    'function decimals() external view returns (uint8)',
];

// Chainlink ETH/USD Price Feed Addresses
const PRICE_FEED_ADDRESSES = {
    ethereum: '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419', // ETH/USD on Ethereum
    arbitrum: '0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612', // ETH/USD on Arbitrum
    base: '0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70', // ETH/USD on Base
};

// Get real ETH/USD price from Chainlink
export const getEthUsdPrice = async (chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'): Promise<number> => {
    try {
        const provider = chain === 'ethereum' ? getEthereumProvider() :
            chain === 'arbitrum' ? getArbitrumProvider() :
                getBaseProvider();

        const priceFeed = new ethers.Contract(
            PRICE_FEED_ADDRESSES[chain],
            CHAINLINK_PRICE_FEED_ABI,
            provider
        );

        const [, answer, , ,] = await priceFeed.latestRoundData();
        const decimals = await priceFeed.decimals();

        // Convert to USD (Chainlink returns price with 8 decimals)
        const price = Number(answer) / Math.pow(10, Number(decimals));

        return price;
    } catch (error) {
        console.error('Failed to fetch ETH/USD price:', error);
        // Return 0 instead of mock data - indicates price unavailable
        return 0;
    }
};

// Get token price in USD via Uniswap V3 TWAP
export const getTokenPriceUsd = async (
    tokenAddress: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<number> => {
    try {
        // TODO: Implement Uniswap V3 TWAP oracle integration
        // For now, return 0 to indicate unavailable
        return 0;
    } catch (error) {
        console.error('Failed to fetch token price:', error);
        return 0;
    }
};

// Get real-time gas price in Gwei
export const getGasPriceGwei = async (chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'): Promise<number> => {
    try {
        const provider = chain === 'ethereum' ? getEthereumProvider() :
            chain === 'arbitrum' ? getArbitrumProvider() :
                getBaseProvider();

        const feeData = await provider.getFeeData();
        const gasPrice = feeData.gasPrice || BigInt(0);

        // Convert from wei to gwei
        return Number(gasPrice) / 1e9;
    } catch (error) {
        console.error('Failed to fetch gas price:', error);
        return 0;
    }
};

// Get token balance
export const getTokenBalance = async (
    tokenAddress: string,
    walletAddress: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<string> => {
    try {
        const provider = chain === 'ethereum' ? getEthereumProvider() :
            chain === 'arbitrum' ? getArbitrumProvider() :
                getBaseProvider();

        const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, provider);
        const balance = await tokenContract.balanceOf(walletAddress);
        const decimals = await tokenContract.decimals();

        return ethers.formatUnits(balance, decimals);
    } catch (error) {
        console.error('Failed to fetch token balance:', error);
        return '0';
    }
};
