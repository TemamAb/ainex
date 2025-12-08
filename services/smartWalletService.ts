 const { ethers } = require('ethers');
const { getEthereumProvider } = require('../blockchain/providers');

// ERC-4337 Account Abstraction Addresses for Ethereum Mainnet
const ERC4337_ADDRESSES = {
    entryPoint: '0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789',
    factory: '0x9406Cc6185a346906296840746125a0E44976454',
    paymaster: '0x0000000000000000000000000000000000000000' // To be configured
};

// SmartWallet interface for TypeScript
interface SmartWallet {
    smartWalletAddress: string;
    ownerAddress: string;
    paymasterAddress: string;
    chain: string;
}

// Generate deterministic smart wallet address using CREATE2
const generateSmartWallet = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<SmartWallet> => {
    // Use a deterministic owner address for demo (in production, use user's address)
    const ownerAddress = '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'; // Demo owner

    // Generate deterministic smart wallet address based on chain and owner
    const salt = ethers.keccak256(ethers.toUtf8Bytes(`AINEX_TRADING_WALLET_${chain}_${ownerAddress}`));
    const smartWalletAddress = ethers.getCreate2Address(
        ERC4337_ADDRESSES.factory,
        salt,
        ethers.keccak256('0x') // Simple bytecode hash for demo
    );

    console.log(`Generated Smart Wallet for ${chain}: ${smartWalletAddress}`);

    return {
        smartWalletAddress,
        ownerAddress,
        paymasterAddress: ERC4337_ADDRESSES.paymaster,
        chain
    };
};

// Get signer for smart wallet operations
const getSmartWalletSigner = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<{
    signer: ethers.Signer;
    smartWallet: SmartWallet;
}> => {
    const provider = await getEthereumProvider();

    // For demo purposes, create a random signer
    // In production, this would connect to the user's wallet
    const signer = ethers.Wallet.createRandom().connect(provider);

    const smartWallet = await generateSmartWallet(chain);

    return { signer, smartWallet };
};

// Check if smart wallet is ready for operations
const isSmartWalletReady = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<boolean> => {
    try {
        const smartWallet = await generateSmartWallet(chain);
        const provider = await getEthereumProvider();

        // Check if smart wallet has been deployed
        const code = await provider.getCode(smartWallet.smartWalletAddress);
        return code !== '0x';
    } catch (error) {
        console.error('Smart wallet readiness check failed:', error);
        return false;
    }
};

// Deploy smart wallet if not already deployed
const deploySmartWallet = async (chain: 'ethereum' | 'arbitrum' | 'base'): Promise<string> => {
    try {
        const { signer, smartWallet } = await getSmartWalletSigner(chain);

        // Factory contract for deployment
        const factory = new ethers.Contract(ERC4337_ADDRESSES.factory, [
            'function createAccount(bytes32 salt, address owner) returns (address)'
        ], signer);

        const salt = ethers.keccak256(ethers.toUtf8Bytes(`AINEX_TRADING_WALLET_${chain}_${smartWallet.ownerAddress}`));

        const tx = await factory.createAccount(salt, smartWallet.ownerAddress);
        const receipt = await tx.wait();

        console.log(`Smart wallet deployed: ${receipt.contractAddress}`);
        return receipt.contractAddress || smartWallet.smartWalletAddress;
    } catch (error) {
        console.error('Smart wallet deployment failed:', error);
        throw error;
    }
};

// CommonJS exports
module.exports = {
    generateSmartWallet,
    getSmartWalletSigner,
    isSmartWalletReady,
    deploySmartWallet
};
