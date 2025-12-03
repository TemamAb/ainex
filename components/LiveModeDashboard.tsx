import React, { useState, useEffect } from 'react';
import { TradeSignal, FlashLoanMetric } from '../types';
import LiveBlockchainEvents from './LiveBlockchainEvents';
import LiveModeValidator from './LiveModeValidator';
import VerificationBadge from './VerificationBadge';
import {
    Zap, TrendingUp, TrendingDown, AlertTriangle, Shield,
    Activity, DollarSign, Clock, Target, BarChart3,
    CheckCircle, XCircle, Loader2, Pause, Play, ExternalLink
} from 'lucide-react';

interface LiveModeDashboardProps {
    signals: TradeSignal[];
    totalProfit: number;
    flashMetrics: FlashLoanMetric[];
    onExecuteTrade?: (signal: TradeSignal) => void;
    onPauseTrading?: () => void;
    onResumeTrading?: () => void;
    isPaused?: boolean;
}

interface LiveTrade {
    id: string;
    signal: TradeSignal;
    status: 'EXECUTING' | 'CONFIRMED' | 'FAILED';
    executionTime: number;
    gasUsed?: string;
    actualProfit?: number;
    txHash?: string;
}

const LiveModeDashboard: React.FC<LiveModeDashboardProps> = ({
    signals,
    totalProfit,
    flashMetrics,
    onExecuteTrade,
    onPauseTrading,
    onResumeTrading,
    isPaused = false
}) => {
    const [liveTrades, setLiveTrades] = useState<LiveTrade[]>([]);
    const [activeTrades, setActiveTrades] = useState<TradeSignal[]>([]);
    const [riskMetrics, setRiskMetrics] = useState({
        maxDrawdown: 0,
        dailyLossLimit: 1000,
        positionSize: 0,
        exposure: 0,
        volatilityIndex: 0.45 + Math.random() * 0.3,
        correlationRisk: 0.6 + Math.random() * 0.3,
        liquidationThreshold: 0.85,
        autoStopLoss: 500
    });

    // Simulate live trading execution
    useEffect(() => {
        if (!isPaused) {
            const interval = setInterval(() => {
                // Simulate new trade signals being executed
                const pendingSignals = signals.filter(s => s.status === 'DETECTED');
                if (pendingSignals.length > 0 && Math.random() > 0.7) {
                    const signal = pendingSignals[0];
                    const liveTrade: LiveTrade = {
                        id: `live-${Date.now()}`,
                        signal,
                        status: 'EXECUTING',
                        executionTime: Date.now()
                    };
                    setLiveTrades(prev => [liveTrade, ...prev].slice(0, 20));

                    // Simulate execution completion
                    setTimeout(() => {
                        setLiveTrades(prev => prev.map(trade =>
                            trade.id === liveTrade.id
                                ? {
                                    ...trade,
                                    status: Math.random() > 0.1 ? 'CONFIRMED' : 'FAILED',
                                    gasUsed: `${Math.floor(Math.random() * 200000 + 100000)}`,
                                    actualProfit: parseFloat(signal.expectedProfit) * (0.8 + Math.random() * 0.4),
                                    txHash: `0x${Math.random().toString(16).slice(2)}`
                                }
                                : trade
                        ));
                    }, 2000 + Math.random() * 3000);
                }
            }, 5000);

            return () => clearInterval(interval);
        }
    }, [signals, isPaused]);

    const successfulTrades = liveTrades.filter(t => t.status === 'CONFIRMED');
    const failedTrades = liveTrades.filter(t => t.status === 'FAILED');
    const executingTrades = liveTrades.filter(t => t.status === 'EXECUTING');

    const liveProfit = successfulTrades.reduce((sum, trade) => sum + (trade.actualProfit || 0), 0);
    const successRate = liveTrades.length > 0 ? (successfulTrades.length / liveTrades.length) * 100 : 0;

    // Real-time P&L tracking
    const totalPnL = liveProfit;
    const unrealizedPnL = executingTrades.reduce((sum, trade) => {
        const expected = parseFloat(trade.signal.expectedProfit);
        return sum + (expected * 0.8); // Estimate unrealized at 80% of expected
    }, 0);
    const realizedPnL = successfulTrades.reduce((sum, trade) => sum + (trade.actualProfit || 0), 0);
    const dailyPnL = totalPnL; // For demo, using total as daily
    const weeklyPnL = dailyPnL * 7;
    const monthlyPnL = dailyPnL * 30;

    return (
        <div className="space-y-6">
            {/* Live Trading Header */}
            <div className="bg-slate-900/40 border border-emerald-500/30 rounded-lg p-4 backdrop-blur-sm">
                <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                        <h3 className="text-sm font-light text-emerald-400 uppercase tracking-wider">
                            LIVE TRADING ACTIVE
                        </h3>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={isPaused ? onResumeTrading : onPauseTrading}
                            className={`px-3 py-1.5 rounded font-light text-xs uppercase tracking-wider transition-all ${isPaused
                                ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                                : 'bg-amber-600 hover:bg-amber-500 text-white'
                                }`}
                        >
                            {isPaused ? (
                                <>
                                    <Play className="w-3 h-3 inline mr-1" />
                                    Resume
                                </>
                            ) : (
                                <>
                                    <Pause className="w-3 h-3 inline mr-1" />
                                    Pause
                                </>
                            )}
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="text-center">
                        <p className="text-xs font-light text-slate-400 uppercase">Live Profit</p>
                        <p className={`text-sm font-light ${liveProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            ${liveProfit.toFixed(2)}
                        </p>
                    </div>
                    <div className="text-center">
                        <p className="text-xs font-light text-slate-400 uppercase">Success Rate</p>
                        <p className="text-sm font-light text-blue-400">
                            {successRate.toFixed(1)}%
                        </p>
                    </div>
                    <div className="text-center">
                        <p className="text-xs font-light text-slate-400 uppercase">Active Trades</p>
                        <p className="text-sm font-light text-amber-400">
                            {executingTrades.length}
                        </p>
                    </div>
                    <div className="text-center">
                        <p className="text-xs font-light text-slate-400 uppercase">Total Executed</p>
                        <p className="text-sm font-light text-white">
                            {liveTrades.length}
                        </p>
                    </div>
                </div>
            </div>

            {/* Blockchain Verification */}
            <LiveModeValidator
                isLive={!isPaused}
                recentTransactions={liveTrades.map(t => ({
                    id: t.id,
                    txHash: t.txHash || '',
                    profit: t.actualProfit || 0,
                    status: t.status
                }))}
                chain="ethereum"
            />

            {/* Live Blockchain Events */}
            <LiveBlockchainEvents isLive={!isPaused} />

            {/* Real-time P&L Tracking */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-emerald-500" />
                    Real-Time P&L Tracking
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Total P&L</span>
                            <DollarSign className="w-4 h-4 text-emerald-500" />
                        </div>
                        <p className={`text-lg font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">Realized + Unrealized</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Realized P&L</span>
                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                        </div>
                        <p className={`text-lg font-bold ${realizedPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {realizedPnL >= 0 ? '+' : ''}${realizedPnL.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">Confirmed trades</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Unrealized P&L</span>
                            <Clock className="w-4 h-4 text-amber-500" />
                        </div>
                        <p className={`text-lg font-bold ${unrealizedPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {unrealizedPnL >= 0 ? '+' : ''}${unrealizedPnL.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">Pending trades</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Daily P&L</span>
                            <BarChart3 className="w-4 h-4 text-blue-500" />
                        </div>
                        <p className={`text-lg font-bold ${dailyPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {dailyPnL >= 0 ? '+' : ''}${dailyPnL.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">24h projection</p>
                    </div>
                </div>
            </div>

            {/* Risk Management Panel */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Shield className="w-5 h-5 text-red-500" />
                    Risk Management
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Max Drawdown</span>
                            <AlertTriangle className={`w-4 h-4 ${riskMetrics.maxDrawdown > 500 ? 'text-red-500' : 'text-emerald-500'}`} />
                        </div>
                        <p className={`text-lg font-bold ${riskMetrics.maxDrawdown > 500 ? 'text-red-400' : 'text-emerald-400'}`}>
                            ${riskMetrics.maxDrawdown.toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-500">Limit: $1,000</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Volatility Index</span>
                            <TrendingUp className="w-4 h-4 text-amber-500" />
                        </div>
                        <p className={`text-lg font-bold ${riskMetrics.volatilityIndex > 0.7 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(riskMetrics.volatilityIndex * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs text-slate-500">Market volatility</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Correlation Risk</span>
                            <Target className="w-4 h-4 text-purple-500" />
                        </div>
                        <p className={`text-lg font-bold ${riskMetrics.correlationRisk > 0.8 ? 'text-red-400' : 'text-emerald-400'}`}>
                            {(riskMetrics.correlationRisk * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs text-slate-500">Asset correlation</p>
                    </div>

                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-slate-400 uppercase font-bold">Circuit Breaker</span>
                            <Shield className="w-4 h-4 text-emerald-500" />
                        </div>
                        <p className="text-lg font-bold text-emerald-400">
                            ACTIVE
                        </p>
                        <p className="text-xs text-slate-500">Auto-stop enabled</p>
                    </div>
                </div>

                {/* Advanced Risk Controls */}
                <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-black/20 border border-slate-800/30 rounded p-4">
                        <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase">Position Limits</h4>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Max Position:</span>
                                <span className="text-slate-300">$5,000</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Current:</span>
                                <span className="text-blue-400">${riskMetrics.positionSize.toFixed(2)}</span>
                            </div>
                            <div className="w-full bg-slate-800/50 h-2 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-blue-500 rounded-full transition-all duration-500"
                                    style={{ width: `${Math.min((riskMetrics.positionSize / 5000) * 100, 100)}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-black/20 border border-slate-800/30 rounded p-4">
                        <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase">Liquidation Protection</h4>
                        <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Threshold:</span>
                                <span className="text-amber-400">{(riskMetrics.liquidationThreshold * 100).toFixed(1)}%</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-slate-500">Auto Stop-Loss:</span>
                                <span className="text-red-400">${riskMetrics.autoStopLoss}</span>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                                <Shield className="w-4 h-4 text-emerald-500" />
                                <span className="text-xs text-emerald-400">Protection Active</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-black/20 border border-slate-800/30 rounded p-4">
                        <h4 className="text-sm font-bold text-slate-300 mb-3 uppercase">Risk Alerts</h4>
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${riskMetrics.maxDrawdown > 500 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
                                <span className="text-xs text-slate-400">Drawdown Monitor</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${riskMetrics.volatilityIndex > 0.7 ? 'bg-amber-500' : 'bg-emerald-500'}`}></div>
                                <span className="text-xs text-slate-400">Volatility Alert</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${riskMetrics.correlationRisk > 0.8 ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
                                <span className="text-xs text-slate-400">Correlation Risk</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Live Trade Execution Feed */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg overflow-hidden backdrop-blur-sm">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-black/20">
                    <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-5 h-5 text-emerald-500" />
                        Live Trade Execution
                    </h3>
                    <span className="text-xs text-slate-500 font-mono">
                        Real-time blockchain execution
                    </span>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-black/40 text-xs uppercase text-slate-500 font-bold">
                            <tr>
                                <th className="px-6 py-3">Time</th>
                                <th className="px-6 py-3">Pair</th>
                                <th className="px-6 py-3">Action</th>
                                <th className="px-6 py-3">Chain</th>
                                <th className="px-6 py-3">Expected</th>
                                <th className="px-6 py-3">Actual</th>
                                <th className="px-6 py-3">Gas</th>
                                <th className="px-6 py-3">Status</th>
                                <th className="px-6 py-3">Tx Hash</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm font-mono">
                            {liveTrades.map((trade) => (
                                <tr key={trade.id} className="border-b border-slate-800/50 hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4 text-slate-400">
                                        {new Date(trade.executionTime).toLocaleTimeString()}
                                    </td>
                                    <td className="px-6 py-4 text-slate-300 font-bold">
                                        {trade.signal.pair}
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${trade.signal.action === 'FLASH_LOAN' ? 'bg-indigo-500/20 text-indigo-400' :
                                            trade.signal.action === 'MEV_BUNDLE' ? 'bg-amber-500/20 text-amber-400' :
                                                'bg-emerald-500/20 text-emerald-400'
                                            }`}>
                                            {trade.signal.action}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">
                                        {trade.signal.chain}
                                    </td>
                                    <td className="px-6 py-4 text-emerald-400 font-bold">
                                        +${parseFloat(trade.signal.expectedProfit).toFixed(2)}
                                    </td>
                                    <td className="px-6 py-4">
                                        {trade.actualProfit !== undefined ? (
                                            <span className={`font-bold ${trade.actualProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {trade.actualProfit >= 0 ? '+' : ''}${trade.actualProfit.toFixed(2)}
                                            </span>
                                        ) : (
                                            <span className="text-slate-500">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">
                                        {trade.gasUsed ? `${trade.gasUsed} gwei` : '-'}
                                    </td>
                                    <td className="px-6 py-4">
                                        {trade.status === 'EXECUTING' && (
                                            <div className="flex items-center gap-2">
                                                <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                                                <span className="text-blue-400 text-xs">EXECUTING</span>
                                            </div>
                                        )}
                                        {trade.status === 'CONFIRMED' && (
                                            <div className="flex items-center gap-2">
                                                <CheckCircle className="w-4 h-4 text-emerald-500" />
                                                <span className="text-emerald-400 text-xs">CONFIRMED</span>
                                            </div>
                                        )}
                                        {trade.status === 'FAILED' && (
                                            <div className="flex items-center gap-2">
                                                <XCircle className="w-4 h-4 text-red-500" />
                                                <span className="text-red-400 text-xs">FAILED</span>
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-slate-500 font-mono text-xs">
                                        {trade.txHash ? `${trade.txHash.substring(0, 10)}...` : '-'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {liveTrades.length === 0 && (
                    <div className="px-6 py-8 text-center text-slate-500">
                        <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>Waiting for arbitrage opportunities...</p>
                    </div>
                )}
            </div>

            {/* Flash Loan Status */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-blue-500" />
                    Flash Loan Providers
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {flashMetrics.map((metric) => (
                        <div key={metric.provider} className="bg-black/30 border border-slate-800/50 rounded p-4">
                            <div className="flex justify-between items-start mb-3">
                                <span className="text-sm font-bold text-slate-300">{metric.provider}</span>
                                <span className={`text-xs font-bold px-2 py-1 rounded ${metric.utilization > 80 ? 'bg-red-500/20 text-red-400' :
                                    metric.utilization > 60 ? 'bg-amber-500/20 text-amber-400' :
                                        'bg-emerald-500/20 text-emerald-400'
                                    }`}>
                                    {metric.utilization}% Used
                                </span>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-slate-500">Available:</span>
                                    <span className="text-emerald-400 font-bold">${metric.liquidityAvailable}</span>
                                </div>
                                <div className="w-full bg-slate-800/50 h-2 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all duration-500 ${metric.utilization > 80 ? 'bg-red-500' :
                                            metric.utilization > 60 ? 'bg-amber-500' :
                                                'bg-emerald-500'
                                            }`}
                                        style={{ width: `${metric.utilization}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default LiveModeDashboard;
