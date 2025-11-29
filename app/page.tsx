'use client';
import React, { useState } from 'react';
import { EngineProvider, useEngine } from './engine/EngineContext';
import { ActivationOverlay } from './components/ActivationOverlay';
import ErrorBoundary from './components/ErrorBoundary';
import { Zap, Activity, Sun, Moon, AlertTriangle, CheckCircle } from 'lucide-react';
import { GrafanaCard } from './components/GrafanaCard';
import { WalletManager } from './components/WalletManager';
import { Sidebar } from './components/Sidebar';
import { ProfitChart } from './components/ProfitChart';
import { AdminPanel } from './components/AdminPanel';

const DashboardContent = () => {
  const {
    state, metrics, confidence, aiState,
    startEngine, confirmLive, withdrawFunds,
    isPaused, missingReq, resolveIssue
  } = useEngine();

  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [showProjection, setShowProjection] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [fixValue, setFixValue] = useState('');

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

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
      <div className="flex-1 p-4 overflow-y-auto">
        <header className={`flex justify-between items-center mb-6 border-b pb-4 ${theme === 'dark' ? 'border-[#22252b]' : 'border-gray-300'}`}>
          <div className="flex items-center gap-2">
            <Activity className={state === 'LIVE' ? "text-[#00FF9D] animate-pulse" : "text-[#5794F2]"} />
            <h1 className="font-bold text-xl">QUANTUMNEX <span className="text-xs text-gray-500 ml-2">v2.1.0</span></h1>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={toggleTheme} className="p-2 rounded hover:bg-gray-800 hover:text-white transition-colors">
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <WalletManager balance={metrics.balance} onWithdraw={withdrawFunds} />
            <div className={`px-3 py-1 rounded border text-xs ${state === 'SIMULATION' ? 'border-[#5794F2] text-[#5794F2] bg-[#5794F2]/10' : 'border-[#00FF9D] text-[#00FF9D] bg-[#00FF9D]/10'}`}>
              MODE: {state}
            </div>
          </div>
        </header>

        {/* 5-COLUMN METRICS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">

          {/* 1. PROFIT VELOCITY */}
          <GrafanaCard title="Profit Velocity" accent="amber">
            <div className="flex flex-col gap-1">
              <div className="flex justify-between text-xs"><span className="text-gray-500">HOURLY</span> <span className="text-amber-500">{metrics.profitPerHour.toFixed(4)} ETH</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">PER TRADE</span> <span className="text-white">{metrics.profitPerTrade.toFixed(5)}</span></div>
              <div className="flex justify-between text-xs"><span className="text-gray-500">FREQ</span> <span className="text-purple-500">{metrics.tradesPerHour} T/H</span></div>
            </div>
          </GrafanaCard>

          {/* 2. THEORETICAL MAX */}
          <GrafanaCard title="Theoretical Max" accent="blue">
            <div className="text-2xl text-[#5794F2] font-bold">{metrics.theoreticalMaxProfit.toFixed(4)}</div>
            <div className="text-[10px] text-gray-500">ETH / BLOCK</div>
          </GrafanaCard>

          {/* 3. AI CAPTURED */}
          <GrafanaCard title="Total Profit" accent="green">
            <div className="text-2xl text-white font-bold">{metrics.totalProfitCumulative.toFixed(4)}</div>
            <div className="text-[10px] text-gray-500">LIFETIME ETH</div>
          </GrafanaCard>

          {/* 4. EFFICIENCY DELTA */}
          <GrafanaCard title="AI Optimization" accent="purple">
            <div className="text-2xl text-purple-400 font-bold">+{metrics.aiEfficiencyDelta.toFixed(1)}%</div>
            <div className="text-[10px] text-gray-500">VS BASELINE</div>
          </GrafanaCard>

          {/* 5. CONFIDENCE GAUGE */}
          <GrafanaCard title="Confidence" accent={confidence >= 85 ? "neon" : "gray"}>
            <div className="flex flex-col items-center justify-center h-full">
              <div className={`text-3xl font-bold ${confidence >= 85 ? "text-[#00FF9D]" : "text-gray-400"}`}>
                {confidence.toFixed(1)}%
              </div>
              <div className="w-full bg-gray-800 h-1 rounded mt-2">
                <div className="bg-[#00FF9D] h-1 rounded transition-all duration-500" style={{ width: `${confidence}%` }}></div>
              </div>
            </div>
          </GrafanaCard>
        </div>

        {/* FLASHING LIVE BUTTON TRIGGER (SAFETY INTERLOCK) */}
        {state === 'SIMULATION' && (
          <div className="fixed bottom-8 left-0 right-0 flex justify-center z-50">
            <button
              onClick={confirmLive}
              disabled={confidence < 85}
              className={`
                font-bold text-xl px-12 py-4 rounded-full shadow-[0_0_50px_rgba(0,255,157,0.5)] flex items-center gap-3 transition-all
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

        {/* STRATEGY VISUALIZATION */}
        <div className="grid grid-cols-1 gap-4">
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
        </div>
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

export default function Home() {
  return (
    <ErrorBoundary>
      <EngineProvider>
        <DashboardContent />
      </EngineProvider>
    </ErrorBoundary>
  );
}
