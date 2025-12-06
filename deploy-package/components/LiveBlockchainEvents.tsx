import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Zap, DollarSign, Clock } from 'lucide-react';
import { ethers } from 'ethers';

interface BlockchainEvent {
    id: string;
    timestamp: number;
    type: 'TRADE' | 'BLOCK' | 'MEV' | 'FLASH_LOAN';
    chain: 'Ethereum' | 'Arbitrum' | 'Base';
    description: string;
    value?: string;
    txHash?: string;
    status: 'SUCCESS' | 'PENDING' | 'FAILED';
}

interface LiveBlockchainEventsProps {
    isLive: boolean;
}

const LiveBlockchainEvents: React.FC<LiveBlockchainEventsProps> = ({ isLive }) => {
    const [events, setEvents] = useState<BlockchainEvent[]>([]);
    const [latestBlock, setLatestBlock] = useState<number>(0);
    const [wsProvider, setWsProvider] = useState<ethers.WebSocketProvider | null>(null);

    // Initialize WebSocket connection for real-time events
    useEffect(() => {
        if (!isLive) {
            if (wsProvider) {
                wsProvider.destroy();
                setWsProvider(null);
            }
            return;
        }

        const initWebSocket = async () => {
            try {
                const { getWebSocketProvider } = await import('../blockchain/providers');
                const provider = getWebSocketProvider('ethereum');
                setWsProvider(provider);

                // Listen for new blocks
                provider.on('block', async (blockNumber: number) => {
                    setLatestBlock(blockNumber);

                    // Get block details for real events
                    try {
                        const block = await provider.getBlock(blockNumber, true);
                        if (block && block.transactions.length > 0) {
                            // Process real transactions from the block
                            const blockEvents = await processBlockTransactions(block, provider);
                            setEvents(prev => [...blockEvents, ...prev].slice(0, 50)); // Keep last 50 events
                        }

                        // Add block mined event
                        const blockEvent: BlockchainEvent = {
                            id: `block-${blockNumber}`,
                            timestamp: Date.now(),
                            type: 'BLOCK',
                            chain: 'Ethereum',
                            description: `New block #${blockNumber} mined on Ethereum`,
                            status: 'SUCCESS'
                        };
                        setEvents(prev => [blockEvent, ...prev].slice(0, 50));

                    } catch (error) {
                        console.error('Error processing block:', error);
                    }
                });

                console.log('WebSocket connected for real-time blockchain events');

            } catch (error) {
                console.error('Failed to initialize WebSocket:', error);
                // Fallback to polling if WebSocket fails
                fallbackToPolling();
            }
        };

        const fallbackToPolling = async () => {
            console.log('Falling back to polling for blockchain events');
            const { getLatestBlockNumber, getEthereumProvider } = await import('../blockchain/providers');
            const provider = await getEthereumProvider();

            const pollBlockNumber = async () => {
                try {
                    const blockNum = await getLatestBlockNumber('ethereum');
                    if (blockNum !== latestBlock) {
                        setLatestBlock(blockNum);

                        // Get block details and process real transactions
                        try {
                            const block = await provider.getBlock(blockNum, true);
                            if (block && block.transactions.length > 0) {
                                // Process real transactions from the block
                                const blockEvents = await processBlockTransactions(block, provider);
                                setEvents(prev => [...blockEvents, ...prev].slice(0, 50)); // Keep last 50 events
                            }
                        } catch (blockError) {
                            console.error('Error processing polled block:', blockError);
                        }

                        // Add block mined event
                        const blockEvent: BlockchainEvent = {
                            id: `block-${blockNum}`,
                            timestamp: Date.now(),
                            type: 'BLOCK',
                            chain: 'Ethereum',
                            description: `New block #${blockNum} mined on Ethereum`,
                            status: 'SUCCESS'
                        };
                        setEvents(prev => [blockEvent, ...prev].slice(0, 50));
                    }
                } catch (error) {
                    console.error('Failed to poll block number:', error);
                }
            };

            pollBlockNumber();
            const interval = setInterval(pollBlockNumber, 12000); // Poll every 12 seconds
            return () => clearInterval(interval);
        };

        initWebSocket();

        return () => {
            if (wsProvider) {
                wsProvider.destroy();
                setWsProvider(null);
            }
        };
    }, [isLive]);

    // Process real transactions from a block to create meaningful events
    const processBlockTransactions = async (block: ethers.Block, provider: ethers.JsonRpcProvider | ethers.WebSocketProvider): Promise<BlockchainEvent[]> => {
        const events: BlockchainEvent[] = [];

        for (const txHash of block.transactions.slice(0, 5)) { // Process first 5 transactions
            try {
                const tx = await provider.getTransaction(txHash);
                if (!tx) continue;

                const valueInEth = parseFloat(ethers.formatEther(tx.value || BigInt(0)));

                // Detect potential arbitrage/flash loan patterns
                if (valueInEth > 0.1) {
                    // Check if transaction interacts with DEX contracts
                    const isDexTx = await isDexTransaction(tx, provider);

                    if (isDexTx) {
                        const event: BlockchainEvent = {
                            id: `trade-${tx.hash}`,
                            timestamp: Date.now(),
                            type: 'TRADE',
                            chain: 'Ethereum',
                            description: `DEX transaction detected (Block #${block.number})`,
                            value: `${valueInEth.toFixed(4)} ETH`,
                            txHash: `${tx.hash.substring(0, 10)}...`,
                            status: 'SUCCESS'
                        };
                        events.push(event);
                    }
                }

                // Detect flash loan patterns (large value with zero gas price or specific patterns)
                if (valueInEth > 10 && tx.gasPrice === BigInt(0)) {
                    const event: BlockchainEvent = {
                        id: `flash-${tx.hash}`,
                        timestamp: Date.now(),
                        type: 'FLASH_LOAN',
                        chain: 'Ethereum',
                        description: `Flash loan executed (Block #${block.number})`,
                        value: `${valueInEth.toFixed(4)} ETH`,
                        txHash: `${tx.hash.substring(0, 10)}...`,
                        status: 'SUCCESS'
                    };
                    events.push(event);
                }

            } catch (error) {
                console.error('Error processing transaction:', error);
            }
        }

        return events;
    };

    // Check if transaction interacts with known DEX contracts
    const isDexTransaction = async (tx: ethers.TransactionResponse, provider: ethers.JsonRpcProvider | ethers.WebSocketProvider): Promise<boolean> => {
        const dexContracts = [
            '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D', // Uniswap V2 Router
            '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Uniswap V3 Router
            '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F', // Sushiswap Router
            '0x1111111254fb6c44bac0bed2854e76f90643097d', // 1inch Router
        ];

        try {
            // Check if transaction is to a DEX contract
            if (dexContracts.some(addr => addr.toLowerCase() === tx.to?.toLowerCase())) {
                return true;
            }

            // Check transaction data for DEX function signatures
            const data = tx.data;
            if (data && data.length > 10) {
                const functionSignature = data.substring(0, 10);
                // Common DEX function signatures
                const dexSignatures = [
                    '0x7ff36ab5', // swapExactETHForTokens (Uniswap)
                    '0x18cbafe5', // swapExactTokensForETH (Uniswap)
                    '0x5c60da1b', // swap (Sushiswap)
                    '0x12aa3caf', // fillOrder (1inch)
                ];

                if (dexSignatures.includes(functionSignature)) {
                    return true;
                }
            }

            return false;
        } catch (error) {
            console.error('Error checking DEX transaction:', error);
            return false;
        }
    };

    const getEventIcon = (type: BlockchainEvent['type']) => {
        switch (type) {
            case 'TRADE': return <TrendingUp className="w-3 h-3" />;
            case 'BLOCK': return <Activity className="w-3 h-3" />;
            case 'MEV': return <Zap className="w-3 h-3" />;
            case 'FLASH_LOAN': return <DollarSign className="w-3 h-3" />;
        }
    };

    const getEventColor = (type: BlockchainEvent['type']) => {
        switch (type) {
            case 'TRADE': return 'text-green-400';
            case 'BLOCK': return 'text-blue-400';
            case 'MEV': return 'text-yellow-400';
            case 'FLASH_LOAN': return 'text-purple-400';
        }
    };

    const getStatusColor = (status: BlockchainEvent['status']) => {
        switch (status) {
            case 'SUCCESS': return 'text-green-400';
            case 'PENDING': return 'text-yellow-400';
            case 'FAILED': return 'text-red-400';
        }
    };

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-light text-white flex items-center gap-2">
                    <Activity className="w-3 h-3 text-green-400 animate-pulse" />
                    Live Blockchain Events {latestBlock > 0 && `(Latest Block: #${latestBlock})`}
                </h3>
                <div className="text-xs font-light text-slate-400">
                    {events.length} events
                </div>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
                {events.length === 0 ? (
                    <div className="text-xs font-light text-slate-500 text-center py-8">
                        {latestBlock === 0 ? 'Connecting to blockchain...' : 'Waiting for blockchain events...'}
                    </div>
                ) : (
                    events.map((event) => (
                        <div
                            key={event.id}
                            className="bg-slate-900/50 rounded p-2 border border-slate-700/50 hover:border-slate-600 transition-colors"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex items-start gap-2 flex-1">
                                    <div className={`mt-0.5 ${getEventColor(event.type)}`}>
                                        {getEventIcon(event.type)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs font-light text-white truncate">
                                            {event.description}
                                        </div>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="text-xs font-light text-slate-500">
                                                {event.chain}
                                            </span>
                                            {event.value && (
                                                <>
                                                    <span className="text-slate-600">•</span>
                                                    <span className="text-xs font-light text-green-400">
                                                        {event.value}
                                                    </span>
                                                </>
                                            )}
                                            {event.txHash && (
                                                <>
                                                    <span className="text-slate-600">•</span>
                                                    <span className="text-xs font-light text-slate-500 font-mono">
                                                        {event.txHash}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex flex-col items-end gap-1">
                                    <span className={`text-xs font-light ${getStatusColor(event.status)}`}>
                                        {event.status}
                                    </span>
                                    <span className="text-xs font-light text-slate-500">
                                        <Clock className="w-2.5 h-2.5 inline mr-1" />
                                        {new Date(event.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default LiveBlockchainEvents;
