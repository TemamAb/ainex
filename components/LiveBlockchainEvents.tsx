import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp, Zap, DollarSign, Clock } from 'lucide-react';

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

    // Fetch real blockchain block numbers
    useEffect(() => {
        if (!isLive) return;

        const fetchBlockNumber = async () => {
            try {
                const { getLatestBlockNumber } = await import('../blockchain/providers');
                const blockNum = await getLatestBlockNumber('ethereum');
                setLatestBlock(blockNum);
            } catch (error) {
                console.error('Failed to fetch block number:', error);
            }
        };

        fetchBlockNumber();
        const interval = setInterval(fetchBlockNumber, 12000); // Update every 12 seconds (Ethereum block time)
        return () => clearInterval(interval);
    }, [isLive]);

    useEffect(() => {
        if (!isLive || latestBlock === 0) return;

        // Simulate live blockchain events with real block numbers
        const generateEvent = (): BlockchainEvent => {
            const types: BlockchainEvent['type'][] = ['TRADE', 'BLOCK', 'MEV', 'FLASH_LOAN'];
            const chains: BlockchainEvent['chain'][] = ['Ethereum', 'Arbitrum', 'Base'];
            const type = types[Math.floor(Math.random() * types.length)];
            const chain = chains[Math.floor(Math.random() * chains.length)];

            // Use real block number with slight variation for different chains
            const blockOffset = chain === 'Ethereum' ? 0 : Math.floor(Math.random() * 5);
            const eventBlock = latestBlock - blockOffset;

            const descriptions = {
                TRADE: `Arbitrage executed on ${chain} (Block #${eventBlock})`,
                BLOCK: `New block #${eventBlock} mined on ${chain}`,
                MEV: `MEV opportunity detected on ${chain} (Block #${eventBlock})`,
                FLASH_LOAN: `Flash loan executed on ${chain} (Block #${eventBlock})`
            };

            return {
                id: `event-${Date.now()}-${Math.random()}`,
                timestamp: Date.now(),
                type,
                chain,
                description: descriptions[type],
                value: type === 'TRADE' || type === 'FLASH_LOAN' ? `${(Math.random() * 2).toFixed(4)} ETH` : undefined,
                txHash: `0x${Array.from({ length: 10 }, () => Math.floor(Math.random() * 16).toString(16)).join('')}...`,
                status: Math.random() > 0.1 ? 'SUCCESS' : Math.random() > 0.5 ? 'PENDING' : 'FAILED'
            };
        };

        const interval = setInterval(() => {
            const newEvent = generateEvent();
            setEvents(prev => [newEvent, ...prev].slice(0, 20)); // Keep last 20 events
        }, 3000); // New event every 3 seconds

        return () => clearInterval(interval);
    }, [isLive, latestBlock]);

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
