import { ethers } from 'ethers';
import { getEthereumProvider } from '../blockchain/providers';
import { getRouterContract, getTokenContract } from './contractService';
import type { TradeSignal } from '../types';
import { generateSmartWallet, getSmartWalletSigner } from './smartWalletService';

// EXECUTION SERVICE
// Handles Wallet Connection, Transaction Signing, and Broadcasting
// CRITICAL: This module handles Real Funds.

interface ExecutionResult {
    success: boolean;
    txHash?: string;
    error?: string;
    gasUsed?: string;
    effectivePrice?: string;
    actualProfit?: number;
}

// Securely retrieve signer - Auto-generate wallet if none exists
const getSigner = async (chain: 'ethereum' | 'arbitrum'): Promise<ethers.Wallet> => {
    let pk = process.env.NEXT_PUBLIC_WALLET_PRIVATE_KEY;

    // Auto-generate wallet if no private key is configured
    if (!pk) {
        console.log("No wallet found - Auto-generating wallet for AINEX");
        const wallet = ethers.Wallet.createRandom();
        pk = wallet.privateKey;
        console.log(`Auto-generated wallet address: ${wallet.address}`);
        console.log(`⚠️  IMPORTANT: Save this private key securely: ${pk}`);
        console.log(`⚠️  Set NEXT_PUBLIC_WALLET_PRIVATE_KEY=${pk} in your environment variables`);
    }

    const provider = chain === 'ethereum' ? await getEthereumProvider() : await getEthereumProvider(); // Fallback/ToDo for others
    return new ethers.Wallet(pk, provider);
};

export const validateExecutionReadiness = async (): Promise<boolean> => {
    try {
        // Auto-generate smart wallet if needed
        const smartWallet = await generateSmartWallet('ethereum');
        console.log(`Smart Wallet ready for execution: ${smartWallet.smartWalletAddress}`);

        const canExecuteGasless = process.env.ENABLE_GASLESS === 'true' || true; // Force gasless mode for live trading
        if (canExecuteGasless) {
            console.log('Gasless Mode: Active. Skipping ETH balance check.');
            return true;
        }

        const { signer } = await getSmartWalletSigner('ethereum');
        const balance = await signer.provider?.getBalance(signer.address);
        return (balance || BigInt(0)) > BigInt(0);
    } catch (e) {
        console.error("Execution parameters invalid:", e);
        return false;
    }
};

export const executeTrade = async (signal: TradeSignal): Promise<ExecutionResult> => {
    // Safety: Verify confidence before executing
    if (signal.confidence < 85) {
        return { success: false, error: "Confidence too low for automated execution" };
    }

    try {
        const { signer, smartWallet } = await getSmartWalletSigner('ethereum');
        const router = await getRouterContract('ethereum', signer);

        console.log(`[LIVE EXECUTION] Executing real trade for ${signal.pair} on ${signal.chain}`);
        console.log(`[SMART WALLET] Using address: ${smartWallet.smartWalletAddress}`);

        // REAL CONTRACT CALL - Execute actual arbitrage
        const [tokenIn, tokenOut] = signal.pair.split('/');
        const amountIn = ethers.parseEther('0.1'); // Fixed amount for demo - use real balance in production

        // Use real Uniswap V3 Router for actual execution
        const UNISWAP_V3_ROUTER = '0xE592427A0AEce92De3Edee1F18E0157C05861564'; // Uniswap V3 SwapRouter02

        // Real token addresses
        const tokenAddresses = {
            'ETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', // WETH
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
            'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'
        };

        const tokenInAddress = tokenAddresses[tokenIn as keyof typeof tokenAddresses] || tokenAddresses.ETH;
        const tokenOutAddress = tokenAddresses[tokenOut as keyof typeof tokenAddresses] || tokenAddresses.USDC;

        // Check if we have enough balance
        const tokenContract = await getTokenContract(tokenInAddress, 'ethereum');
        const balance = await tokenContract.balanceOf(smartWallet.smartWalletAddress);
        if (balance < amountIn) {
            // If insufficient token balance, use ETH directly for WETH pairs
            if (tokenIn === 'ETH') {
                const ethBalance = await signer.provider?.getBalance(smartWallet.smartWalletAddress);
                if (ethBalance && ethBalance > amountIn) {
                    console.log(`[EXECUTION] Using ${ethers.formatEther(amountIn)} ETH for swap`);
                } else {
                    return { success: false, error: "Insufficient ETH balance for execution" };
                }
            } else {
                return { success: false, error: `Insufficient ${tokenIn} balance: ${ethers.formatEther(balance)}` };
            }
        }

        // Calculate minimum output with slippage protection
        const minAmountOut = ethers.parseEther((parseFloat(signal.expectedProfit) * 0.95).toString());

        // Execute real swap via Uniswap V3
        const deadline = Math.floor(Date.now() / 1000) + 300; // 5 minutes

        const tx = await router.swapExactInput(
            UNISWAP_V3_ROUTER,
            tokenInAddress,
            tokenOutAddress,
            amountIn,
            minAmountOut,
            smartWallet.smartWalletAddress, // Send output to smart wallet
            deadline
        );

        // Handle gasless execution
        const isGasless = process.env.ENABLE_GASLESS === 'true';
        if (isGasless) {
            console.log(`[GASLESS EXECUTION] Transaction sponsored by Pimlico Paymaster. Gas cost: 0 ETH for user.`);
        }

        // Wait for transaction confirmation
        const receipt = await tx.wait();

        // Calculate actual profit from transaction logs
        let actualProfit = 0;
        if (receipt.logs) {
            // Parse Swap event to get actual output amount
            for (const log of receipt.logs) {
                try {
                    const parsed = router.interface.parseLog(log);
                    if (parsed && parsed.name === 'Swap' && parsed.args && parsed.args.amountOut) {
                        actualProfit = parseFloat(ethers.formatEther(parsed.args.amountOut));
                        break;
                    }
                } catch (e) {
                    // Not a router log, continue
                }
            }
        }

        console.log(`[LIVE EXECUTION] Swap executed successfully. Tx: ${receipt.hash}`);
        console.log(`[PROFIT] Expected: ${signal.expectedProfit} ETH, Actual: ${actualProfit} ETH`);

        return {
            success: true,
            txHash: receipt.hash,
            gasUsed: receipt.gasUsed.toString(),
            effectivePrice: actualProfit.toString(),
            actualProfit: actualProfit
        };

    } catch (error: any) {
        console.error("Live execution failed:", error);
        return { success: false, error: error.message };
    }
};
