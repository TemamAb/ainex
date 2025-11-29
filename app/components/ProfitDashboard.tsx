'use client';
import React, { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { TrendingUp, DollarSign, Activity, Download } from 'lucide-react';

interface ProfitMetrics {
    today: { gross: number; gas: number; net: number; trades: number; winRate: number };
    week: { gross: number; gas: number; net: number; trades: number; winRate: number };
    month: { gross: number; gas: number; net: number; trades: number; winRate: number };
    accumulated: number;
}

export const ProfitDashboard = ({ contract, userAddress }: { contract: any; userAddress: string }) => {
    const [metrics, setMetrics] = useState<ProfitMetrics>({
        today: { gross: 0, gas: 0, net: 0, trades: 0, winRate: 0 },
        week: { gross: 0, gas: 0, net: 0, trades: 0, winRate: 0 },
        month: { gross: 0, gas: 0, net: 0, trades: 0, winRate: 0 },
        accumulated: 0
    });
    const [withdrawing, setWithdrawing] = useState(false);

    useEffect(() => {
        loadProfitMetrics();
        const interval = setInterval(loadProfitMetrics, 30000); // Update every 30s
        return () => clearInterval(interval);
    }, [contract]);

    const loadProfitMetrics = async () => {
        if (!contract) return;

        try {
            const accumulated = await contract.viewProfits();
            // In production, fetch real metrics from events/logs
            // For now, using mock data structure
            setMetrics(prev => ({
                ...prev,
                accumulated: parseFloat(ethers.formatEther(accumulated))
            }));
        } catch (error) {
            console.error("Failed to load profits:", error);
        }
    };

    const handleWithdraw = async () => {
        if (!contract || metrics.accumulated === 0) return;

        setWithdrawing(true);
        try {
            const tx = await contract.withdrawProfits();
            await tx.wait();
            alert(`Successfully withdrew ${metrics.accumulated.toFixed(4)} ETH!`);
            loadProfitMetrics();
        } catch (error: any) {
            alert(`Withdrawal failed: ${error.message}`);
        } finally {
            setWithdrawing(false);
        }
    };

    return (
        <div className="space-y-4">
            {/* Accumulated Profits Card */}
            <div className="bg-gradient-to-br from-green-900/20 to-green-800/10 border border-green-500/30 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <p className="text-sm text-gray-400">Available to Withdraw</p>
                        <p className="text-4xl font-bold text-green-400">
                            {metrics.accumulated.toFixed(4)} ETH
                        </p>
                        <p className="text-sm text-gray-500">
                            ≈ ${(metrics.accumulated * 3500).toFixed(2)} USD
                        </p>
                    </div>
                    <DollarSign className="text-green-400" size={48} />
                </div>
                <button
                    onClick={handleWithdraw}
                    disabled={withdrawing || metrics.accumulated === 0}
                    className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                    <Download size={20} />
                    {withdrawing ? 'Withdrawing...' : 'Withdraw to Wallet'}
                </button>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                    title="Today"
                    profit={metrics.today.net}
                    trades={metrics.today.trades}
                    winRate={metrics.today.winRate}
                    icon={<Activity className="text-blue-400" size={24} />}
                />
                <MetricCard
                    title="This Week"
                    profit={metrics.week.net}
                    trades={metrics.week.trades}
                    winRate={metrics.week.winRate}
                    icon={<TrendingUp className="text-purple-400" size={24} />}
                />
                <MetricCard
                    title="This Month"
                    profit={metrics.month.net}
                    trades={metrics.month.trades}
                    winRate={metrics.month.winRate}
                    icon={<DollarSign className="text-amber-400" size={24} />}
                />
            </div>
        </div>
    );
};

const MetricCard = ({ title, profit, trades, winRate, icon }: any) => (
    <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">{title}</p>
            {icon}
        </div>
        <p className="text-2xl font-bold text-white mb-1">
            {profit > 0 ? '+' : ''}{profit.toFixed(4)} ETH
        </p>
        <div className="flex items-center justify-between text-xs text-gray-500">
            <span>{trades} trades</span>
            <span className={winRate >= 80 ? 'text-green-400' : 'text-amber-400'}>
                {winRate.toFixed(1)}% win rate
            </span>
        </div>
    </div>
);
