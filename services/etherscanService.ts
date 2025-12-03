import axios from 'axios';

// Etherscan API configuration
const ETHERSCAN_API_KEYS = {
    ethereum: process.env.ETHERSCAN_API_KEY || 'YourApiKeyToken',
    arbitrum: process.env.ARBISCAN_API_KEY || 'YourApiKeyToken',
    base: process.env.BASESCAN_API_KEY || 'YourApiKeyToken'
};

const ETHERSCAN_URLS = {
    ethereum: 'https://api.etherscan.io/api',
    arbitrum: 'https://api.arbiscan.io/api',
    base: 'https://api.basescan.org/api'
};

const EXPLORER_URLS = {
    ethereum: 'https://etherscan.io',
    arbitrum: 'https://arbiscan.io',
    base: 'https://basescan.org'
};

export interface TransactionVerification {
    verified: boolean;
    txHash: string;
    blockNumber: number;
    timestamp: number;
    from: string;
    to: string;
    value: string;
    gasUsed: string;
    gasPrice: string;
    status: 'success' | 'failed';
    explorerLink: string;
    verificationTimestamp: number;
}

export interface BlockValidation {
    valid: boolean;
    blockNumber: number;
    blockHash: string;
    timestamp: number;
    miner: string;
    confirmations: number;
}

// Rate limiting queue
class RequestQueue {
    private queue: Array<() => Promise<any>> = [];
    private processing = false;
    private lastRequestTime = 0;
    private minInterval = 200; // 5 requests per second

    async add<T>(request: () => Promise<T>): Promise<T> {
        return new Promise((resolve, reject) => {
            this.queue.push(async () => {
                try {
                    const result = await request();
                    resolve(result);
                } catch (error) {
                    reject(error);
                }
            });
            this.process();
        });
    }

    private async process() {
        if (this.processing || this.queue.length === 0) return;

        this.processing = true;

        while (this.queue.length > 0) {
            const now = Date.now();
            const timeSinceLastRequest = now - this.lastRequestTime;

            if (timeSinceLastRequest < this.minInterval) {
                await new Promise(resolve => setTimeout(resolve, this.minInterval - timeSinceLastRequest));
            }

            const request = this.queue.shift();
            if (request) {
                this.lastRequestTime = Date.now();
                await request();
            }
        }

        this.processing = false;
    }
}

const requestQueue = new RequestQueue();

/**
 * Verify transaction on blockchain via Etherscan API
 */
export const verifyTransactionOnChain = async (
    txHash: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<TransactionVerification> => {
    const apiUrl = ETHERSCAN_URLS[chain];
    const apiKey = ETHERSCAN_API_KEYS[chain];
    const explorerUrl = EXPLORER_URLS[chain];

    try {
        // Get transaction details
        const txResponse = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_getTransactionByHash',
                    txhash: txHash,
                    apikey: apiKey
                }
            })
        );

        // Get transaction receipt
        const receiptResponse = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_getTransactionReceipt',
                    txhash: txHash,
                    apikey: apiKey
                }
            })
        );

        const tx = txResponse.data.result;
        const receipt = receiptResponse.data.result;

        if (!tx || !receipt) {
            throw new Error('Transaction not found on blockchain');
        }

        const verification: TransactionVerification = {
            verified: true,
            txHash: tx.hash,
            blockNumber: parseInt(receipt.blockNumber, 16),
            timestamp: Date.now(), // Will be updated with actual block timestamp
            from: tx.from,
            to: tx.to,
            value: parseInt(tx.value, 16).toString(),
            gasUsed: parseInt(receipt.gasUsed, 16).toString(),
            gasPrice: parseInt(tx.gasPrice, 16).toString(),
            status: receipt.status === '0x1' ? 'success' : 'failed',
            explorerLink: `${explorerUrl}/tx/${txHash}`,
            verificationTimestamp: Date.now()
        };

        // Get block timestamp
        const blockResponse = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_getBlockByNumber',
                    tag: receipt.blockNumber,
                    boolean: 'false',
                    apikey: apiKey
                }
            })
        );

        if (blockResponse.data.result) {
            verification.timestamp = parseInt(blockResponse.data.result.timestamp, 16) * 1000;
        }

        return verification;
    } catch (error: any) {
        console.error('Etherscan verification failed:', error);
        throw new Error(`Failed to verify transaction: ${error.message}`);
    }
};

/**
 * Validate block number and get block details
 */
export const validateBlockNumber = async (
    blockNumber: number,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<BlockValidation> => {
    const apiUrl = ETHERSCAN_URLS[chain];
    const apiKey = ETHERSCAN_API_KEYS[chain];

    try {
        const blockHex = '0x' + blockNumber.toString(16);

        const response = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_getBlockByNumber',
                    tag: blockHex,
                    boolean: 'false',
                    apikey: apiKey
                }
            })
        );

        const block = response.data.result;

        if (!block) {
            throw new Error('Block not found');
        }

        // Get latest block to calculate confirmations
        const latestResponse = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_blockNumber',
                    apikey: apiKey
                }
            })
        );

        const latestBlock = parseInt(latestResponse.data.result, 16);
        const confirmations = latestBlock - blockNumber;

        return {
            valid: true,
            blockNumber,
            blockHash: block.hash,
            timestamp: parseInt(block.timestamp, 16) * 1000,
            miner: block.miner,
            confirmations
        };
    } catch (error: any) {
        console.error('Block validation failed:', error);
        return {
            valid: false,
            blockNumber,
            blockHash: '',
            timestamp: 0,
            miner: '',
            confirmations: 0
        };
    }
};

/**
 * Generate public verification link
 */
export const generateVerificationLink = (
    txHash: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): string => {
    const explorerUrl = EXPLORER_URLS[chain];
    return `${explorerUrl}/tx/${txHash}`;
};

/**
 * Generate address verification link
 */
export const generateAddressLink = (
    address: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): string => {
    const explorerUrl = EXPLORER_URLS[chain];
    return `${explorerUrl}/address/${address}`;
};

/**
 * Get transaction list for address
 */
export const getAddressTransactions = async (
    address: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum',
    startBlock: number = 0,
    endBlock: number = 99999999
): Promise<any[]> => {
    const apiUrl = ETHERSCAN_URLS[chain];
    const apiKey = ETHERSCAN_API_KEYS[chain];

    try {
        const response = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'account',
                    action: 'txlist',
                    address,
                    startblock: startBlock,
                    endblock: endBlock,
                    sort: 'desc',
                    apikey: apiKey
                }
            })
        );

        return response.data.result || [];
    } catch (error: any) {
        console.error('Failed to get address transactions:', error);
        return [];
    }
};

/**
 * Verify gas price is reasonable
 */
export const verifyGasPrice = async (
    actualGasPrice: string,
    chain: 'ethereum' | 'arbitrum' | 'base' = 'ethereum'
): Promise<{ reasonable: boolean; currentGasPrice: string }> => {
    const apiUrl = ETHERSCAN_URLS[chain];
    const apiKey = ETHERSCAN_API_KEYS[chain];

    try {
        const response = await requestQueue.add(() =>
            axios.get(apiUrl, {
                params: {
                    module: 'proxy',
                    action: 'eth_gasPrice',
                    apikey: apiKey
                }
            })
        );

        const currentGasPrice = parseInt(response.data.result, 16).toString();
        const actualGasPriceNum = parseInt(actualGasPrice);
        const currentGasPriceNum = parseInt(currentGasPrice);

        // Consider reasonable if within 2x of current gas price
        const reasonable = actualGasPriceNum <= currentGasPriceNum * 2;

        return {
            reasonable,
            currentGasPrice
        };
    } catch (error) {
        console.error('Failed to verify gas price:', error);
        return {
            reasonable: true, // Default to true if can't verify
            currentGasPrice: '0'
        };
    }
};
