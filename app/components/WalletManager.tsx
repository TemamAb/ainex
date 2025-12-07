import React, { useState, useEffect } from 'react';
import { Wallet, ArrowRight, History, Settings, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { ethers } from 'ethers';

interface WithdrawalRecord {
    timestamp: number;
    amount: number;
    txHash: string;
    status: 'PENDING' | 'COMPLETED' | 'FAILED';
}

export const WalletManager = ({
    balance,
    onWithdraw
}: {
    balance: number;
    onWithdraw: (amount: number) => Promise<void>;
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [account, setAccount] = useState<string | null>(null);
    const [threshold, setThreshold] = useState("1.0");
    const [maxTime, setMaxTime] = useState("24");
    const [history, setHistory] = useState<WithdrawalRecord[]>([]);
    const [isConnecting, setIsConnecting] = useState(false);

    // Auto-Detect Wallet
    useEffect(() => {
        if (typeof window !== 'undefined' && (window as any).ethereum) {
            (window as any).ethereum.request({ method: 'eth_accounts' })
                .then((accounts: string[]) => {
                    if (accounts.length > 0) setAccount(accounts[0]);
                });
        }
    }, []);

    const connectWallet = async () => {
        if (typeof window === 'undefined' || !(window as any).ethereum) {
            alert("MetaMask not found!");
            return;
        }
        setIsConnecting(true);
        try {
            const accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' });
            setAccount(accounts[0]);
        } catch (e) {
            console.error(e);
        } finally {
            setIsConnecting(false);
        }
    };

    const handleWithdraw = async () => {
        if (!account) return;
        const amount = parseFloat(threshold); // For demo, withdraw threshold amount
        if (amount > balance) {
            alert("Insufficient Balance");
            return;
        }

        // Optimistic UI update
        const newRecord: WithdrawalRecord = {
            timestamp: Date.now(),
            amount: amount,
            txHash: `0x${Math.random().toString(16).slice(2)}...`,
            status: 'PENDING'
        };
        setHistory(prev => [newRecord, ...prev]);

        await onWithdraw(amount);

        // Update status after "tx"
        setTimeout(() => {
            setHistory(prev => prev.map(r => r.timestamp === newRecord.timestamp ? { ...r, status: 'COMPLETED' } : r));
        }, 2000);
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`flex items-center gap-2 px-4 py-2 rounded border transition-colors ${account ? 'border-[#00FF9D] text-[#00FF9D] bg-[#00FF9D]/10' : 'border-gray-600 text-gray-400 hover:border-white'}`}
            >
                <Wallet size={16} />
                <span className="text-xs font-bold">
                    {account ? `${account.slice(0, 6)}...${account.slice(-4)}` : "CONNECT WALLET"}
                </span>
            </button>

            {isOpen && (
                <div className="absolute right-0 top-12 w-[350px] bg-[#181b1f] border border-[#22252b] shadow-2xl z-50 p-4 rounded-sm">

                    {/* HEADER */}
                    <div className="flex justify-between items-center mb-4 border-b border-[#22252b] pb-2">
                        <h3 className="text-white font-bold text-sm flex items-center gap-2">
                            <Settings size={14} /> WALLET SETTINGS
                        </h3>
                        {!account && (
                            <button
                                onClick={connectWallet}
                                disabled={isConnecting}
                                className="text-[10px] bg-[#5794F2] text-black px-2 py-1 rounded font-bold hover:bg-white"
                            >
                                {isConnecting ? "CONNECTING..." : "CONNECT METAMASK"}
                            </button>
                        )}
                    </div>

                    {/* SETTINGS */}
                    <div className="space-y-3 mb-6">
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">AUTO-WITHDRAW THRESHOLD (ETH)</label>
                            <input
                                type="number"
                                value={threshold}
                                onChange={(e) => setThreshold(e.target.value)}
                                className="w-full bg-black border border-[#22252b] text-white text-xs p-2 focus:border-[#5794F2] outline-none"
                            />
                        </div>
                        <div>
                            <label className="text-[10px] text-gray-500 block mb-1">MAX ACCUMULATION TIME (HOURS)</label>
                            <input
                                type="number"
                                value={maxTime}
                                onChange={(e) => setMaxTime(e.target.value)}
                                className="w-full bg-black border border-[#22252b] text-white text-xs p-2 focus:border-[#5794F2] outline-none"
                            />
                        </div>
                        <button
                            onClick={handleWithdraw}
                            disabled={!account || balance < parseFloat(threshold)}
                            className={`w-full py-2 font-bold text-xs flex items-center justify-center gap-2 ${!account || balance < parseFloat(threshold) ? 'bg-[#22252b] text-gray-500 cursor-not-allowed' : 'bg-[#00FF9D] text-black hover:bg-white'}`}
                        >
                            WITHDRAW PROFIT <ArrowRight size={12} />
                        </button>
                    </div>

                    {/* HISTORY */}
                    <div>
                        <h4 className="text-[10px] text-gray-500 font-bold mb-2 flex items-center gap-1">
                            <History size={10} /> TRANSFER HISTORY
                        </h4>
                        <div className="max-h-[150px] overflow-y-auto space-y-2">
                            {history.length === 0 ? (
                                <div className="text-center text-[10px] text-gray-600 py-4">NO TRANSFERS RECORDED</div>
                            ) : (
                                history.map((rec, i) => (
                                    <div key={i} className="flex justify-between items-center bg-black p-2 border border-[#22252b]">
                                        <div className="flex flex-col">
                                            <span className="text-white text-xs font-bold">{rec.amount.toFixed(4)} ETH</span>
                                            <span className="text-[10px] text-gray-500">{new Date(rec.timestamp).toLocaleTimeString()}</span>
                                        </div>
                                        <div className="flex items-center gap-1">
                                            {rec.status === 'COMPLETED' ? <CheckCircle size={12} className="text-[#00FF9D]" /> : <Loader2 size={12} className="animate-spin text-[#5794F2]" />}
                                            <span className={`text-[10px] ${rec.status === 'COMPLETED' ? 'text-[#00FF9D]' : 'text-[#5794F2]'}`}>{rec.status}</span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
};
