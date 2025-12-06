import React from 'react';
import { TrendingUp, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';

interface ConfidenceMetrics {
    totalTrades: number;
    successfulTrades: number;
    averageProfit: number;
    predictedVsActual: number; // percentage accuracy
    riskScore: number; // 0-100
}

interface ConfidenceReportProps {
    confidence: number;
    metrics: ConfidenceMetrics;
    mode: 'SIM' | 'LIVE';
}

const ConfidenceReport: React.FC<ConfidenceReportProps> = ({ confidence, metrics, mode }) => {
    const isReadyForLive = confidence >= 85;
    const textColor = mode === 'SIM' ? 'text-white' : 'text-emerald-400';
    const accentColor = mode === 'SIM' ? 'border-white/20' : 'border-emerald-500/30';

    return (
        <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Confidence Report
            </h3>

            {/* Confidence Score */}
            <div className={`border ${accentColor} rounded-lg p-6 mb-6`}>
                <p className="text-xs text-slate-400 uppercase font-bold mb-3">Overall Confidence</p>
                <div className="flex items-end gap-4 mb-4">
                    <span className={`text-5xl font-bold font-rajdhani ${textColor}`}>{confidence}%</span>
                    {isReadyForLive ? (
                        <CheckCircle className="w-6 h-6 text-emerald-500 mb-2" />
                    ) : (
                        <AlertTriangle className="w-6 h-6 text-amber-500 mb-2" />
                    )}
                </div>
                <div className="w-full bg-black/30 h-3 rounded-full overflow-hidden">
                    <div
                        className={`h-full transition-all duration-500 ${mode === 'SIM' ? 'bg-white' : 'bg-emerald-500'
                            }`}
                        style={{ width: `${confidence}%` }}
                    ></div>
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-2">
                    <span>0%</span>
                    <span className="text-amber-400">85% Threshold</span>
                    <span>100%</span>
                </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                    <p className="text-xs text-slate-500 uppercase mb-2">Total Trades</p>
                    <p className={`text-2xl font-bold font-rajdhani ${textColor}`}>{metrics.totalTrades}</p>
                </div>
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                    <p className="text-xs text-slate-500 uppercase mb-2">Success Rate</p>
                    <p className={`text-2xl font-bold font-rajdhani ${textColor}`}>
                        {metrics.totalTrades > 0
                            ? ((metrics.successfulTrades / metrics.totalTrades) * 100).toFixed(1)
                            : 0}
                        %
                    </p>
                </div>
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                    <p className="text-xs text-slate-500 uppercase mb-2">Avg Profit</p>
                    <p className={`text-2xl font-bold font-rajdhani ${textColor}`}>
                        ${metrics.averageProfit.toFixed(2)}
                    </p>
                </div>
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                    <p className="text-xs text-slate-500 uppercase mb-2">Prediction Accuracy</p>
                    <p className={`text-2xl font-bold font-rajdhani ${textColor}`}>
                        {metrics.predictedVsActual.toFixed(1)}%
                    </p>
                </div>
            </div>

            {/* Risk Assessment */}
            <div className="bg-black/30 border border-slate-800/50 rounded p-4 mb-6">
                <p className="text-xs text-slate-500 uppercase mb-3">Risk Score</p>
                <div className="flex items-center gap-3">
                    <div className="flex-1 bg-black/50 h-2 rounded-full overflow-hidden">
                        <div
                            className={`h-full transition-all duration-500 ${metrics.riskScore < 30
                                    ? 'bg-emerald-500'
                                    : metrics.riskScore < 70
                                        ? 'bg-amber-500'
                                        : 'bg-red-500'
                                }`}
                            style={{ width: `${metrics.riskScore}%` }}
                        ></div>
                    </div>
                    <span className="text-sm font-bold text-slate-300 font-mono">{metrics.riskScore}/100</span>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                    {metrics.riskScore < 30
                        ? 'Low risk - conditions favorable'
                        : metrics.riskScore < 70
                            ? 'Moderate risk - proceed with caution'
                            : 'High risk - not recommended'}
                </p>
            </div>

            {/* Recommendation */}
            <div
                className={`border rounded p-4 ${isReadyForLive
                        ? 'bg-emerald-900/20 border-emerald-500/30'
                        : 'bg-amber-900/20 border-amber-500/30'
                    }`}
            >
                <p className="text-xs font-bold uppercase mb-2 flex items-center gap-2">
                    {isReadyForLive ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                    )}
                    <span className={isReadyForLive ? 'text-emerald-400' : 'text-amber-400'}>
                        Recommendation
                    </span>
                </p>
                <p className="text-sm text-slate-300">
                    {isReadyForLive
                        ? 'Confidence threshold met. You may proceed to LIVE mode when ready.'
                        : `Continue in SIM mode. Confidence must reach 85% (currently ${confidence}%).`}
                </p>
            </div>
        </div>
    );
};

export default ConfidenceReport;
