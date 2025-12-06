import React from 'react';
import { TradeSignal, FlashLoanMetric, BotStatus } from '../types';
import {
    Zap, TrendingUp, TrendingDown, AlertTriangle, Shield,
    Activity, DollarSign, Clock, Target, BarChart3,
    CheckCircle, XCircle, Loader2, Pause, Play, ExternalLink,
    Bot, Signal, Coins, Gauge
} from 'lucide-react';

interface SimModeDashboardProps {
    signals: TradeSignal[];
    totalProfit: number;
    flashMetrics: FlashLoanMetric[];
    confidence: number;
    botStatuses: BotStatus[];
    profitProjection: {
        hourly: number;
        daily: number;
        weekly: number;
        monthly: number;
    };
}

const SimModeDashboard: React.FC<SimModeDashboardProps> = ({
    signals,
    totalProfit,
    flashMetrics,
    confidence,
    botStatuses,
    profitProjection
}) => {
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
                    <Gauge className="w-8 h-8 text-blue-500" />
                    SIMULATION MODE DASHBOARD
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">Confidence</span>
                            <Gauge className="w-4 h-4 text-blue-500" />
                        </div>
                        <p className="text-2xl font-bold text-blue-400">{confidence.toFixed(1)}%</p>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">Active Signals</span>
                            <Signal className="w-4 h-4 text-green-500" />
                        </div>
                        <p className="text-2xl font-bold text-green-400">{signals.length}</p>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">Projected Daily</span>
                            <DollarSign className="w-4 h-4 text-emerald-500" />
                        </div>
                        <p className="text-2xl font-bold text-emerald-400">${profitProjection.daily.toFixed(2)}</p>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">System Health</span>
                            <Shield className="w-4 h-4 text-emerald-500" />
                        </div>
                        <p className="text-lg font-bold text-emerald-400">ONLINE</p>
                    </div>
                </div>
            </div>

            {/* Profit Projections */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-emerald-500" />
                    Profit Projections
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="text-sm text-slate-400 mb-1">Hourly</div>
                        <div className="text-xl font-bold text-emerald-400">{profitProjection.hourly.toFixed(4)} ETH</div>
                        <div className="text-xs text-slate-500">${(profitProjection.hourly * 3000).toFixed(2)} USD</div>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="text-sm text-slate-400 mb-1">Daily</div>
                        <div className="text-xl font-bold text-emerald-400">{profitProjection.daily.toFixed(4)} ETH</div>
                        <div className="text-xs text-slate-500">${(profitProjection.daily * 3000).toFixed(2)} USD</div>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="text-sm text-slate-400 mb-1">Weekly</div>
                        <div className="text-xl font-bold text-emerald-400">{profitProjection.weekly.toFixed(2)} ETH</div>
                        <div className="text-xs text-slate-500">${(profitProjection.weekly * 3000).toFixed(2)} USD</div>
                    </div>
                    <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                        <div className="text-sm text-slate-400 mb-1">Monthly</div>
                        <div className="text-xl font-bold text-emerald-400">{profitProjection.monthly.toFixed(2)} ETH</div>
                        <div className="text-xs text-slate-500">${(profitProjection.monthly * 3000).toFixed(2)} USD</div>
                    </div>
                </div>
            </div>

            {/* Trade Signals */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Signal className="w-5 h-5 text-blue-500" />
                    Trade Signals
                </h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                    {signals.length === 0 ? (
                        <div className="text-center text-slate-500 py-8">
                            <Signal className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No active signals detected</p>
                        </div>
                    ) : (
                        signals.slice(0, 10).map((signal) => (
                            <div key={signal.id} className="bg-black/30 border border-slate-800/50 rounded p-4">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <span className="text-sm font-bold text-slate-300">{signal.pair}</span>
                                        <span className="text-xs text-slate-500 ml-2">Block #{signal.blockNumber}</span>
                                    </div>
                                    <div className={`text-xs px-2 py-1 rounded ${
                                        signal.status === 'DETECTED' ? 'bg-blue-500/20 text-blue-400' :
                                        signal.status === 'EXECUTING' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-green-500/20 text-green-400'
                                    }`}>
                                        {signal.status}
                                    </div>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-400">Expected Profit:</span>
                                    <span className="text-emerald-400 font-bold">{signal.expectedProfit} ETH</span>
                                </div>
                                <div className="flex justify-between text-sm mt-1">
                                    <span className="text-slate-400">Confidence:</span>
                                    <span className="text-blue-400 font-bold">{signal.confidence}%</span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Flash Loan Providers */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-purple-500" />
                    Flash Loan Providers
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {flashMetrics.map((metric) => (
                        <div key={metric.provider} className="bg-black/30 border border-slate-800/50 rounded p-4">
                            <div className="flex justify-between items-start mb-3">
                                <span className="text-sm font-bold text-slate-300">{metric.provider}</span>
                                <span className={`text-xs font-bold px-2 py-1 rounded ${
                                    metric.utilization > 80 ? 'bg-red-500/20 text-red-400' :
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
                                        className={`h-full rounded-full transition-all duration-500 ${
                                            metric.utilization > 80 ? 'bg-red-500' :
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

            {/* Bot Statuses */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Bot className="w-5 h-5 text-cyan-500" />
                    Bot Statuses
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {botStatuses.length === 0 ? (
                        <div className="col-span-full text-center text-slate-500 py-8">
                            <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
                            <p>No bots configured</p>
                        </div>
                    ) : (
                        botStatuses.map((bot) => (
                            <div key={bot.id} className="bg-black/30 border border-slate-800/50 rounded p-4">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <span className="text-sm font-bold text-slate-300">{bot.name}</span>
                                        <div className="text-xs text-slate-500">{bot.type} • {bot.tier}</div>
                                    </div>
                                    <div className={`text-xs px-2 py-1 rounded ${
                                        bot.status === 'ACTIVE' ? 'bg-green-500/20 text-green-400' :
                                        bot.status === 'EXECUTING' ? 'bg-blue-500/20 text-blue-400' :
                                        bot.status === 'STANDBY' ? 'bg-yellow-500/20 text-yellow-400' :
                                        'bg-red-500/20 text-red-400'
                                    }`}>
                                        {bot.status}
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-500">Uptime:</span>
                                        <span className="text-emerald-400 font-bold">{bot.uptime}</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-500">Efficiency:</span>
                                        <span className="text-cyan-400 font-bold">{bot.efficiency}%</span>
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

export default SimModeDashboard;
