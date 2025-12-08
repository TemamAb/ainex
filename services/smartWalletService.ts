import { ethers } from 'ethers';
import { getEthereumProvider } from '../blockchain/providers';
import { logger } from '../utils/logger';

// Smart Wallet Service for Gasless Execution
// Uses ERC-4337 Account Abstraction for sponsored transactions

interface SmartWallet {
  smartWalletAddress: string;
  ownerAddress: string;
  chain: string;
  isDeployed: boolean;
  balance: string;
}

interface SmartWalletSigner {
  signer: ethers.Wallet;
  smartWallet: SmartWallet;
}

// In-memory storage for demo purposes
// In production, this would be stored in a database
const smartWallets: Map<string, SmartWallet> = new Map();

// Generate a deterministic smart wallet address for a user
export const generateSmartWallet = async (chain: 'ethereum' | 'arbitrum' = 'ethereum'): Promise<SmartWallet> => {
  try {
    // For demo purposes, generate a deterministic wallet
    // In production, this would use ERC-4337 factory contracts
    const provider = await getEthereumProvider();

    // Create a deterministic private key based on chain
    const privateKey = ethers.keccak256(ethers.toUtf8Bytes(`ainex-smart-wallet-${chain}`));
    const wallet = new ethers.Wallet(privateKey, provider);

    const smartWallet: SmartWallet = {
      smartWalletAddress: wallet.address,
      ownerAddress: wallet.address, // Self-owned for demo
      chain,
      isDeployed: true, // Assume deployed for demo
      balance: '0.0'
    };

    // Store in memory
    smartWallets.set(`${chain}-smart-wallet`, smartWallet);

    logger.info(`Smart wallet generated for ${chain}: ${wallet.address}`);
    return smartWallet;

  } catch (error) {
    logger.error('Failed to generate smart wallet:', error);
    throw new Error('Smart wallet generation failed');
  }
};

// Get signer for smart wallet operations
export const getSmartWalletSigner = async (chain: 'ethereum' | 'arbitrum' = 'ethereum'): Promise<SmartWalletSigner> => {
  try {
    const walletKey = `${chain}-smart-wallet`;

    // Check if wallet exists, generate if not
    if (!smartWallets.has(walletKey)) {
      await generateSmartWallet(chain);
    }

    const smartWallet = smartWallets.get(walletKey)!;
    const provider = await getEthereumProvider();

    // Create signer from deterministic private key
    const privateKey = ethers.keccak256(ethers.toUtf8Bytes(`ainex-smart-wallet-${chain}`));
    const signer = new ethers.Wallet(privateKey, provider);

    logger.info(`Smart wallet signer retrieved for ${chain}: ${signer.address}`);

    return {
      signer,
      smartWallet
    };

  } catch (error) {
    logger.error('Failed to get smart wallet signer:', error);
    throw new Error('Smart wallet signer retrieval failed');
  }
};

// Check if smart wallet is ready for execution
export const isSmartWalletReady = async (chain: 'ethereum' | 'arbitrum' = 'ethereum'): Promise<boolean> => {
  try {
    const walletKey = `${chain}-smart-wallet`;

    if (!smartWallets.has(walletKey)) {
      await generateSmartWallet(chain);
    }

    const smartWallet = smartWallets.get(walletKey)!;

    // For demo purposes, always return true
    // In production, check if wallet is deployed and has sufficient balance
    logger.info(`Smart wallet ready check for ${chain}: ${smartWallet.isDeployed}`);
    return smartWallet.isDeployed;

  } catch (error) {
    logger.error('Smart wallet readiness check failed:', error);
    return false;
  }
};

// Get smart wallet balance
export const getSmartWalletBalance = async (chain: 'ethereum' | 'arbitrum' = 'ethereum'): Promise<string> => {
  try {
    const { signer } = await getSmartWalletSigner(chain);
    const balance = await signer.provider?.getBalance(signer.address);

    const balanceEth = balance ? ethers.formatEther(balance) : '0.0';

    // Update stored balance
    const walletKey = `${chain}-smart-wallet`;
    if (smartWallets.has(walletKey)) {
      const wallet = smartWallets.get(walletKey)!;
      wallet.balance = balanceEth;
      smartWallets.set(walletKey, wallet);
    }

    logger.info(`Smart wallet balance for ${chain}: ${balanceEth} ETH`);
    return balanceEth;

  } catch (error) {
    logger.error('Failed to get smart wallet balance:', error);
    return '0.0';
  }
};

// Fund smart wallet (for demo purposes)
export const fundSmartWallet = async (chain: 'ethereum' | 'arbitrum' = 'ethereum', amount: string): Promise<boolean> => {
  try {
    // For demo purposes, this would normally fund the wallet
    // In production, this would interact with a paymaster service
    logger.info(`Funding smart wallet ${chain} with ${amount} ETH (demo)`);

    // Update balance in memory
    const walletKey = `${chain}-smart-wallet`;
    if (smartWallets.has(walletKey)) {
      const wallet = smartWallets.get(walletKey)!;
      const currentBalance = parseFloat(wallet.balance);
      const fundAmount = parseFloat(amount);
      wallet.balance = (currentBalance + fundAmount).toString();
      smartWallets.set(walletKey, wallet);
    }

    return true;

  } catch (error) {
    logger.error('Failed to fund smart wallet:', error);
    return false;
  }
};
