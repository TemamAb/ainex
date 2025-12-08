import React, { useState, useEffect } from 'react';
import { Wallet, Clock, TrendingUp, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { ProfitWithdrawalConfig, WithdrawalHistory } from '../types';
import { withdrawalService } from '../services/withdrawalService';

interface ProfitWithdrawalProps {
    config: ProfitWithdrawalConfig;
    onConfigChange: (config: ProfitWithdrawalConfig) => void;
}

const ProfitWithdrawal: React.FC<ProfitWithdrawalProps> = ({ config, onConfigChange }) => {
    const [history, setHistory] = useState<WithdrawalHistory[]>([]);
    const [timeRemaining, setTimeRemaining] = useState<string>('');
    const [walletError, setWalletError] = useState<string>('');

    useEffect(() => {
        // Load withdrawal history
        setHistory(withdrawalService.getWithdrawalHistory());
    }, []);

    useEffect(() => {
        // Update countdown timer
        const interval = setInterval(() => {
            setTimeRemaining(withdrawalService.formatTimeRemaining(config.nextScheduledTransfer));
        }, 1000);

        return () => clearInterval(interval);
    }, [config.nextScheduledTransfer]);

    const handleWalletChange = (address: string) => {
        onConfigChange({ ...config, walletAddress: address });

        if (address && !withdrawalService.validateWalletAddress(address)) {
            setWalletError('Invalid Ethereum address');
        } else {
            setWalletError('');
        }
    };

    const handleThresholdChange = (value: string) => {
        onConfigChange({ ...config, thresholdAmount: value });
    };

    const handleMaxTimeChange = (value: string) => {
        const minutes = parseInt(value) || 0;
        onConfigChange({ ...config, maxTransferTime: minutes });
    };

    const handleToggle = () => {
        onConfigChange({ ...config, isEnabled: !config.isEnabled });
    };

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                        <Wallet className="w-5 h-5 text-blue-400" />
                    </div>
                    <div>
                        <h2 className="text-sm font-semibold text-white">Profit Withdrawal</h2>
                        <p className="text-xs font-light text-slate-400">Auto-deposit to non-custodial wallet</p>
                    </div>
                </div>
                <button
                    onClick={handleToggle}
                    className={`px-4 py-2 rounded-lg text-xs font-light transition-colors ${config.isEnabled
                            ? 'bg-green-600 text-white hover:bg-green-500'
                            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                        }`}
                >
                    {config.isEnabled ? 'ENABLED' : 'DISABLED'}
                </button>
            </div>

            {/* Smart Balance Display */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Smart Balance</div>
                    <div className="text-lg font-light text-green-400">
                        {parseFloat(config.smartBalance).toFixed(4)} ETH
                    </div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Total Withdrawn</div>
                    <div className="text-lg font-light text-blue-400">
                        {parseFloat(config.totalWithdrawn).toFixed(4)} ETH
                    </div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Next Transfer</div>
                    <div className="text-lg font-light text-yellow-400 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        {timeRemaining}
                    </div>
                </div>
            </div>

            {/* Configuration Form */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* Wallet Address */}
                <div className="md:col-span-2">
                    <label className="block text-xs font-light text-slate-400 mb-2">
                        Non-Custodial Wallet Address
                    </label>
                    <input
                        type="text"
                        value={config.walletAddress}
                        onChange={(e) => handleWalletChange(e.target.value)}
                        placeholder="0x..."
                        className={`w-full bg-slate-900 border ${walletError ? 'border-red-500' : 'border-slate-700'
                            } rounded-lg px-4 py-2 text-xs font-light text-white placeholder-slate-500 focus:outline-none focus:border-blue-500`}
                    />
                    {walletError && (
                        <div className="flex items-center gap-2 mt-2 text-xs font-light text-red-400">
                            <AlertCircle className="w-3 h-3" />
                            {walletError}
                        </div>
                    )}
                </div>

                {/* Threshold Amount */}
                <div>
                    <label className="block text-xs font-light text-slate-400 mb-2">
                        Threshold Amount (ETH)
                    </label>
                    <input
                        type="number"
                        step="0.01"
                        value={config.thresholdAmount}
                        onChange={(e) => handleThresholdChange(e.target.value)}
                        placeholder="0.5"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs font-light text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />
                </div>
            </div>

            {/* Max Transfer Time */}
            <div className="mb-6">
                <label className="block text-xs font-light text-slate-400 mb-2">
                    Maximum Transfer Time (minutes)
                </label>
                <div className="flex items-center gap-4">
                    <input
                        type="number"
                        value={config.maxTransferTime}
                        onChange={(e) => handleMaxTimeChange(e.target.value)}
                        placeholder="60"
                        className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs font-light text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                    />
                    <div className="text-xs font-light text-slate-400">
                        System will randomize transfer within this window
                    </div>
                </div>
            </div>

            {/* Withdrawal History */}
            <div>
                <h3 className="text-xs font-semibold text-white mb-3">Recent Withdrawals</h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                    {history.length === 0 ? (
                        <div className="text-xs font-light text-slate-500 text-center py-4">
                            No withdrawal history
                        </div>
                    ) : (
                        history.slice(0, 5).map((item) => (
                            <div
                                key={item.id}
                                className="bg-slate-900/50 rounded-lg p-3 border border-slate-700 flex items-center justify-between"
                            >
                                <div className="flex items-center gap-3">
                                    {item.status === 'COMPLETED' ? (
                                        <CheckCircle className="w-4 h-4 text-green-400" />
                                    ) : item.status === 'FAILED' ? (
                                        <XCircle className="w-4 h-4 text-red-400" />
                                    ) : (
                                        <Clock className="w-4 h-4 text-yellow-400" />
                                    )}
                                    <div>
                                        <div className="text-xs font-light text-white">
                                            {parseFloat(item.amount).toFixed(4)} ETH
                                        </div>
                                        <div className="text-xs font-light text-slate-500">
                                            {new Date(item.timestamp).toLocaleString()}
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-xs font-light ${item.status === 'COMPLETED' ? 'text-green-400' :
                                            item.status === 'FAILED' ? 'text-red-400' : 'text-yellow-400'
                                        }`}>
                                        {item.status}
                                    </div>
                                    <div className="text-xs font-light text-slate-500">
                                        {item.txHash.substring(0, 10)}...
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProfitWithdrawal;
