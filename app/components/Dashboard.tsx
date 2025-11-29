'use client';
import React, { useState, useEffect } from 'react';
import { useEngine } from '../engine/EngineContext';
import { ActivationOverlay } from './ActivationOverlay';
import { Zap, Activity, Sun, Moon, AlertTriangle, CheckCircle, RefreshCw, Terminal as TerminalIcon, TrendingUp, TrendingDown } from 'lucide-react';
import { GrafanaCard } from './GrafanaCard';
import { WalletManager } from './WalletManager';
import { Sidebar } from './Sidebar';
import { ProfitChart } from './ProfitChart';
import { AdminPanel } from './AdminPanel';
import Terminal from './Terminal';
import { performanceConfidence } from '../engine/PerformanceConfidence';
import { CONFIDENCE_THRESHOLDS, PERFORMANCE_MODES, TOOLTIPS } from '../../constants';
import { Tooltip } from './Tooltip';

export const Dashboard = () => {
    const {
        state, metrics, confidence, aiState,
        startEngine, confirmLive, withdrawFunds,
        isPaused, missingReq, resolveIssue
    } = useEngine();

    const [theme, setTheme] = useState<'dark' | 'light'>('dark');
    const [showProjection, setShowProjection] = useState(false);
    const [showAdmin, setShowAdmin] = useState(false);
    const [fixValue, setFixValue] = useState('');

    // Header Features ported from legacy
    const [currency, setCurrency] = useState<'ETH' | 'USD'>('ETH');
    const [refreshRate, setRefreshRate] = useState(1000);
    const [showTerminal, setShowTerminal] = useState(true);

    // Performance Confidence Tracking
    const [perfMetrics, setPerfMetrics] = useState(() =>
        performanceConfidence.calculateConfidence(20, 25, 0.3)
    );
    const [showVarianceDetails, setShowVarianceDetails] = useState(false);

    // Update performance metrics periodically
    useEffect(() => {
        const interval = setInterval(() => {
            // Simulate real-time market conditions (would come from actual data)
            const gasPrice = 20 + Math.random() * 30; // 20-50 gwei
            const volatility = 25 + Math.random() * 20; // 25-45
            const mevRisk = 0.2 + Math.random() * 0.3; // 0.2-0.5

            const metrics = performanceConfidence.calculateConfidence(gasPrice, volatility, mevRisk);
            setPerfMetrics(metrics);
        }, refreshRate);

        return () => clearInterval(interval);
    }, [refreshRate]);

    const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    const toggleCurrency = () => setCurrency(prev => prev === 'ETH' ? 'USD' : 'ETH');

    // Currency Conversion Helper
    const displayValue = (ethValue: number) => {
        if (currency === 'ETH') return `${ethValue.toFixed(4)} ETH`;
        return `$${(ethValue * 3500).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    // SELF-HEALING MODAL
    if (isPaused && missingReq) {
        return (
            <div className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4">
                <div className="bg-[#181b1f] border border-red-500 w-full max-w-md rounded-lg p-6 shadow-[0_0_50px_rgba(239,68,68,0.3)] animate-in zoom-in-95">
                    <div className="flex items-center gap-3 mb-4 text-red-500">
                        <AlertTriangle size={32} />
                        <h2 className="text-xl font-bold">PREFLIGHT INTERRUPTED</h2>
                    </div>
                    <p className="text-gray-300 mb-6">
                        Critical dependency missing: <span className="font-bold text-white">{missingReq}</span>.
                        The engine has paused to prevent failure. Please resolve immediately.
                    </p>

                    {missingReq === 'WALLET' && (
                        <div className="space-y-4">
                            <input
                                type="text"
                                placeholder="Paste Valid Ethereum Address..."
                                className="w-full bg-black border border-[#22252b] rounded p-3 text-white focus:border-red-500 outline-none"
                                value={fixValue}
                                onChange={(e) => setFixValue(e.target.value)}
                            />
                            <button
                                onClick={() => resolveIssue(fixValue)}
                                className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded transition-colors flex items-center justify-center gap-2"
                            >
                                <CheckCircle size={20} />
                                VALIDATE & RESUME
                            </button>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    if (state === 'BOOTING') return <ActivationOverlay />;

    if (state === 'IDLE') {
        return (
            <div className="h-screen bg-[#111217] flex items-center justify-center">
                <button onClick={startEngine} className="group w-64 h-64 bg-[#181b1f] rounded-full border-4 border-[#22252b] hover:border-[#5794F2] transition-all flex flex-col items-center justify-center shadow-[0_0_50px_rgba(0,0,0,0.5)] hover:shadow-[0_0_80px_rgba(87,148,242,0.2)]">
                    <Zap className="text-gray-500 group-hover:text-[#5794F2] mb-4 transition-colors" size={48} />
                    <span className="text-white font-mono font-bold text-xl tracking-widest group-hover:text-blue-100">INITIATE</span>
                </button>
            </div>
        );
    }

    return (
        <div className={`min-h-screen font-mono flex transition-colors duration-300 ${theme === 'dark' ? 'bg-[#111217] text-gray-200' : 'bg-gray-100 text-gray-900'}`}>

            {/* SIDEBAR NAVIGATION */}
            <Sidebar
                onToggleProjection={() => setShowProjection(true)}
                onToggleAdmin={() => setShowAdmin(true)}
            />

            {/* MAIN CONTENT AREA */}
            <div className="flex-1 p-4 overflow-y-auto flex flex-col h-screen">
                <header className={`flex justify-between items-center mb-6 border-b pb-4 shrink-0 ${theme === 'dark' ? 'border-[#22252b]' : 'border-gray-300'}`}>
                    <div className="flex items-center gap-2">
                        <Activity className={state === 'LIVE' ? "text-[#00FF9D] animate-pulse" : "text-[#5794F2]"} />
                        <h1 className="font-bold text-xl">QUANTUMNEX <span className="text-xs text-gray-500 ml-2">v2.1.0</span></h1>
                    </div>
                    <div className="flex items-center gap-4">

                        {/* REFRESH RATE SELECTOR (Ported) */}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                            <RefreshCw size={12} />
                            <select
                                value={refreshRate}
                                onChange={(e) => setRefreshRate(Number(e.target.value))}
                                className="bg-[#181b1f] border border-[#22252b] rounded px-1 py-0.5 text-white focus:outline-none"
                            >
                                <option value={1000}>1s</option>
                                <option value={5000}>5s</option>
                                <option value={10000}>10s</option>
                            </select>
                        </div>

                        {/* CURRENCY TOGGLE (Ported) */}
                        <button
                            onClick={toggleCurrency}
                            className="flex items-center gap-2 px-3 py-1 bg-[#181b1f] border border-[#22252b] rounded hover:border-[#5794F2] transition-colors text-xs"
                        >
                            <span className={currency === 'ETH' ? 'text-[#5794F2]' : 'text-gray-500'}>ETH</span>
                            <span className="text-gray-600">|</span>
                            <span className={currency === 'USD' ? 'text-[#00FF9D]' : 'text-gray-500'}>USD</span>
                        </button>

                        <button onClick={toggleTheme} className="p-2 rounded hover:bg-gray-800 hover:text-white transition-colors">
                            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                        </button>
                        <WalletManager balance={metrics.balance} onWithdraw={withdrawFunds} />

                        {/* MODE INDICATOR WITH VARIANCE */}
                        <div className="flex items-center gap-2">
                            <Tooltip
                                title={state === 'SIMULATION' ? TOOLTIPS.SIM_MODE.title : TOOLTIPS.LIVE_MODE.title}
                                description={state === 'SIMULATION' ? TOOLTIPS.SIM_MODE.description : TOOLTIPS.LIVE_MODE.description}
                                example={state === 'SIMULATION' ? TOOLTIPS.SIM_MODE.example : TOOLTIPS.LIVE_MODE.example}
                            >
                                <div className={`px-3 py-1 rounded border text-xs ${state === 'SIMULATION' ? 'border-[#5794F2] text-[#5794F2] bg-[#5794F2]/10' : 'border-[#00FF9D] text-[#00FF9D] bg-[#00FF9D]/10'}`}>
                                    MODE: {state}
                                </div>
                            </Tooltip>
                            {state === 'SIMULATION' && (
                                <Tooltip {...TOOLTIPS.VARIANCE_VS_LIVE}>
                                    <div className="px-2 py-1 rounded bg-amber-500/10 border border-amber-500 text-amber-500 text-[10px] font-bold">
                                        ±{perfMetrics.expectedVariance.toFixed(1)}% vs LIVE
                                    </div>
                                </Tooltip>
                            )}
                        </div>
                    </div>
                </header>

                {/* 5-COLUMN METRICS GRID */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4 shrink-0">

                    {/* 1. PROFIT VELOCITY */}
                    <GrafanaCard title={
                        <Tooltip {...TOOLTIPS.PROFIT_VELOCITY}>
                            <span>Profit Velocity</span>
                        </Tooltip>
                    } accent="amber">
                        <div className="flex flex-col gap-1">
                            <div className="flex justify-between text-xs"><span className="text-gray-500">HOURLY</span> <span className="text-amber-500">{displayValue(metrics.profitPerHour)}</span></div>
                            <div className="flex justify-between text-xs"><span className="text-gray-500">PER TRADE</span> <span className="text-white">{displayValue(metrics.profitPerTrade)}</span></div>
                            <div className="flex justify-between text-xs"><span className="text-gray-500">FREQ</span> <span className="text-purple-500">{metrics.tradesPerHour} T/H</span></div>
                        </div>
                    </GrafanaCard>

                    {/* 2. THEORETICAL MAX */}
                    <GrafanaCard title={
                        <Tooltip {...TOOLTIPS.THEORETICAL_MAX}>
                            <span>Theoretical Max</span>
                        </Tooltip>
                    } accent="blue">
                        <div className="text-2xl text-[#5794F2] font-bold">{metrics.theoreticalMaxProfit.toFixed(4)}</div>
                        <div className="text-[10px] text-gray-500">ETH / BLOCK</div>
                    </GrafanaCard>

                    {/* 3. TOTAL PROFIT */}
                    <GrafanaCard title={
                        <Tooltip {...TOOLTIPS.TOTAL_PROFIT}>
                            <span>Total Profit</span>
                        </Tooltip>
                    } accent="green">
                        <div className="text-2xl text-white font-bold">{displayValue(metrics.totalProfitCumulative)}</div>
                        <div className="text-[10px] text-gray-500">LIFETIME</div>
                    </GrafanaCard>

                    {/* 4. EFFICIENCY DELTA */}
                    <GrafanaCard title={
                        <Tooltip {...TOOLTIPS.AI_OPTIMIZATION}>
                            <span>AI Optimization</span>
                        </Tooltip>
                    } accent="purple">
                        <div className="text-2xl text-purple-400 font-bold">+{metrics.aiEfficiencyDelta.toFixed(1)}%</div>
                        <div className="text-[10px] text-gray-500">VS BASELINE</div>
                    </GrafanaCard>

                    {/* 5. SIM/LIVE PERFORMANCE CONFIDENCE */}
                    <GrafanaCard
                        title={
                            <Tooltip {...TOOLTIPS.CONFIDENCE_SCORE}>
                                <span>{state === 'SIMULATION' ? "SIM Accuracy" : "Performance"}</span>
                            </Tooltip>
                        }
                        accent={perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.HIGH ? "neon" : perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.MEDIUM ? "blue" : "amber"}
                    >
                        <div className="flex flex-col h-full">
                            <div className="flex items-baseline gap-2 mb-2">
                                <div className={`text-2xl font-bold ${perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.HIGH ? "text-[#00FF9D]" :
                                    perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.MEDIUM ? "text-[#5794F2]" :
                                        "text-amber-500"
                                    }`}>
                                    {perfMetrics.confidenceScore}%
                                </div>
                                <Tooltip {...TOOLTIPS.MARKET_CONDITION}>
                                    <div className="text-[10px] text-gray-500 uppercase">
                                        {perfMetrics.marketCondition}
                                    </div>
                                </Tooltip>
                            </div>

                            {state === 'SIMULATION' && (
                                <Tooltip {...TOOLTIPS.EXPECTED_VARIANCE}>
                                    <div className="text-xs text-gray-400 mb-1">
                                        Expected variance: <span className="text-amber-400 font-bold">±{perfMetrics.expectedVariance.toFixed(1)}%</span>
                                    </div>
                                </Tooltip>
                            )}

                            <div className="w-full bg-gray-800 h-1 rounded">
                                <div
                                    className={`h-1 rounded transition-all duration-500 ${perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.HIGH ? "bg-[#00FF9D]" :
                                        perfMetrics.confidenceScore >= CONFIDENCE_THRESHOLDS.MEDIUM ? "bg-[#5794F2]" :
                                            "bg-amber-500"
                                        }`}
                                    style={{ width: `${perfMetrics.confidenceScore}%` }}
                                ></div>
                            </div>

                            <button
                                onClick={() => setShowVarianceDetails(!showVarianceDetails)}
                                className="text-[10px] text-gray-500 hover:text-[#5794F2] mt-2 transition-colors text-left"
                            >
                                {showVarianceDetails ? '▼ Hide Details' : '▶ Show Breakdown'}
                            </button>
                        </div>
                    </GrafanaCard>
                </div>

                {/* VARIANCE BREAKDOWN (Collapsible) */}
                {showVarianceDetails && state === 'SIMULATION' && (
                    <div className="mb-4 shrink-0">
                        <GrafanaCard title="Variance Factor Breakdown" accent="amber">
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.GAS_COSTS}>
                                        <span className="text-gray-500 mb-1">Gas Costs</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.gasCost.toFixed(2)}%</span>
                                </div>
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.SLIPPAGE}>
                                        <span className="text-gray-500 mb-1">Slippage</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.slippage.toFixed(2)}%</span>
                                </div>
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.MEV_RISK}>
                                        <span className="text-gray-500 mb-1">MEV Risk</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.mevRisk.toFixed(2)}%</span>
                                </div>
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.NETWORK_LATENCY}>
                                        <span className="text-gray-500 mb-1">Network Latency</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.networkLatency.toFixed(2)}%</span>
                                </div>
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.PRICE_MOVEMENT}>
                                        <span className="text-gray-500 mb-1">Price Movement</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.priceMovement.toFixed(2)}%</span>
                                </div>
                                <div className="flex flex-col">
                                    <Tooltip {...TOOLTIPS.REVERSION_RISK}>
                                        <span className="text-gray-500 mb-1">Reversion Risk</span>
                                    </Tooltip>
                                    <span className="text-amber-400 font-bold">±{perfMetrics.varianceFactors.reversion.toFixed(2)}%</span>
                                </div>
                            </div>
                            <div className="mt-3 pt-3 border-t border-gray-800 flex justify-between items-center">
                                <span className="text-gray-400 text-xs">Total Combined Variance:</span>
                                <span className="text-amber-400 font-bold text-sm">±{perfMetrics.expectedVariance.toFixed(1)}%</span>
                            </div>
                        </GrafanaCard>
                    </div>
                )}

                {/* MIDDLE SECTION: STRATEGY & TERMINAL */}
                <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 min-h-0">

                    {/* STRATEGY VISUALIZATION (Left 1/3) */}
                    <div className="lg:col-span-1 flex flex-col gap-4">
                        <GrafanaCard title="Active Strategy Weights" accent="purple">
                            <div className="flex flex-col gap-2">
                                {Object.entries(aiState?.weights || {}).map(([key, val]) => (
                                    <div key={key} className="flex items-center gap-4">
                                        <span className="w-24 text-xs text-gray-400 uppercase">{key}</span>
                                        <div className="flex-1 bg-gray-800 h-2 rounded overflow-hidden">
                                            <div className="bg-purple-500 h-full" style={{ width: `${(val as number) * 100}%` }}></div>
                                        </div>
                                        <span className="text-xs text-gray-200 w-12 text-right">{((val as number) * 100).toFixed(0)}%</span>
                                    </div>
                                ))}
                            </div>
                        </GrafanaCard>

                        {/* Terminal Toggle */}
                        <button
                            onClick={() => setShowTerminal(!showTerminal)}
                            className={`flex items-center justify-between p-3 rounded border transition-all ${showTerminal ? 'bg-[#181b1f] border-[#5794F2] text-[#5794F2]' : 'bg-[#111217] border-[#22252b] text-gray-500'}`}
                        >
                            <div className="flex items-center gap-2">
                                <TerminalIcon size={16} />
                                <span className="text-xs font-bold">LIVE EXECUTION LOG</span>
                            </div>
                            <div className={`w-2 h-2 rounded-full ${showTerminal ? 'bg-[#00FF9D] animate-pulse' : 'bg-gray-600'}`}></div>
                        </button>
                    </div>

                    {/* TERMINAL (Right 2/3) - INTEGRATED */}
                    <div className={`lg:col-span-2 transition-all duration-300 ${showTerminal ? 'opacity-100' : 'opacity-50 grayscale'}`}>
                        <Terminal />
                    </div>
                </div>

                {/* FLASHING LIVE BUTTON TRIGGER (SAFETY INTERLOCK) */}
                {state === 'SIMULATION' && (
                    <div className="fixed bottom-8 left-0 right-0 flex justify-center z-50 pointer-events-none">
                        <button
                            onClick={confirmLive}
                            disabled={confidence < 85}
                            className={`
                pointer-events-auto font-bold text-xl px-12 py-4 rounded-full shadow-[0_0_50px_rgba(0,255,157,0.5)] flex items-center gap-3 transition-all
                ${confidence >= 85
                                    ? 'bg-[#00FF9D] text-black animate-bounce hover:scale-105 cursor-pointer'
                                    : 'bg-gray-800 text-gray-500 cursor-not-allowed opacity-50'
                                }
              `}
                        >
                            <Zap size={24} fill={confidence >= 85 ? "black" : "gray"} />
                            {confidence >= 85 ? "SWITCH TO LIVE MODE" : `AWAITING CONFIDENCE (${confidence.toFixed(0)}%)`}
                            <Zap size={24} fill={confidence >= 85 ? "black" : "gray"} />
                        </button>
                    </div>
                )}
            </div>

            {/* MODALS */}
            {showProjection && (
                <ProfitChart
                    currentProfit={metrics.profitPerHour}
                    theoreticalMax={metrics.theoreticalMaxProfit}
                    onClose={() => setShowProjection(false)}
                />
            )}

            <AdminPanel
                isOpen={showAdmin}
                onClose={() => setShowAdmin(false)}
            />
        </div>
    );
};