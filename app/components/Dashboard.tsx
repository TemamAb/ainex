'use client';
import React, { useState } from 'react';
import { useEngine } from '../engine/EngineContext';
import { ActivationOverlay } from './ActivationOverlay';
import { Zap, Activity, Sun, Moon, AlertTriangle, CheckCircle, User } from 'lucide-react';
import { GrafanaCard } from './GrafanaCard';
import { WalletManager } from './WalletManager';
import { Sidebar } from './Sidebar';
import { ProfitChart } from './ProfitChart';
import { AdminPanel } from './AdminPanel';
import { PreflightCheck, PreflightRef } from './PreflightCheck';

export const Dashboard = () => {
  const {
    state, metrics, confidence, aiState,
    startEngine, confirmLive, withdrawFunds
  } = useEngine();

  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [showProjection, setShowProjection] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [fixValue, setFixValue] = useState('');
  const [preflightComplete, setPreflightComplete] = useState(false);
  const preflightRef = React.useRef<{ runChecks: () => Promise<void> }>(null);

  const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  const metricColor = state === 'SIMULATION' ? 'text-white' : 'text-[#00FF9D]';

  // REMOVED: BOOTING and IDLE states. Dashboard now renders immediately.

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#0b0c0f] text-white' : 'bg-gray-100 text-gray-900'} font-sans selection:bg-[#5794F2]/30`}>
      <div className="flex h-screen overflow-hidden">
        {/* SIDEBAR */}
        <Sidebar
          onToggleProjection={() => setShowProjection(!showProjection)}
          onToggleAdmin={() => setShowAdmin(!showAdmin)}
        />

        {/* MAIN CONTENT */}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* HEADER */}
          <header className="h-16 border-b border-[#22252b] bg-[#0b0c0f]/95 backdrop-blur flex items-center justify-between px-6 z-10">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-bold tracking-widest">
                <span className="text-[#5794F2]">AINEX</span>
                <span className="text-gray-600 mx-2">|</span>
                <span className="text-white">FLASH LOAN ENGINE</span>
              </h1>
              {/* MODE BADGE */}
              <div className={`px-3 py-1 rounded text-xs font-bold tracking-wider ${state === 'LIVE' ? 'bg-[#00FF9D]/20 text-[#00FF9D] animate-pulse' : 'bg-white/10 text-white'}`}>
                {state === 'LIVE' ? '● LIVE MODE' : '○ SIMULATION'}
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-right mr-4">
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">Wallet Balance</div>
                <div className="font-mono text-[#00FF9D]">{metrics.balance.toFixed(4)} ETH</div>
              </div>
              <button onClick={toggleTheme} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
              </button>
              <button className="p-2 hover:bg-white/5 rounded-full transition-colors">
                <User size={20} />
              </button>
            </div>
          </header>

          {/* DASHBOARD CONTENT */}
          <main className="flex-1 overflow-y-auto p-6 relative">

            {/* PREFLIGHT CHECK - ALWAYS VISIBLE AT TOP */}
            <PreflightCheck ref={preflightRef} onComplete={setPreflightComplete} />

            {/* METRICS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">

              {/* 1. PROFIT VELOCITY */}
              <GrafanaCard title="Profit Velocity" accent="amber">
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between text-xs"><span className="text-gray-500">PER TRADE</span> <span className={metricColor}>{metrics.profitPerTrade.toFixed(5)}</span></div>
                  <div className="flex justify-between text-xs"><span className="text-gray-500">FREQ</span> <span className={metricColor}>{metrics.tradesPerHour} T/H</span></div>
                  <div className="flex justify-between text-xs mt-1 border-t border-gray-800 pt-1">
                    <span className="text-gray-500">PROJ. HOURLY</span>
                    <span className="text-[#00FF9D]">${(metrics.profitPerHour * metrics.ethPrice).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">PROJ. DAILY</span>
                    <span className="text-[#00FF9D]">${(metrics.profitPerHour * 24 * metrics.ethPrice).toFixed(2)}</span>
                  </div>
                </div>
              </GrafanaCard>

              {/* 2. THEORETICAL MAX */}
              <GrafanaCard title="Theoretical Max" accent="blue">
                <div className={`text-2xl font-bold ${metricColor}`}>{metrics.theoreticalMaxProfit.toFixed(4)}</div>
                <div className="text-[10px] text-gray-500">ETH / BLOCK</div>
              </GrafanaCard>

              {/* 3. AI CAPTURED */}
              <GrafanaCard title="Total Profit" accent="green">
                <div className={`text-2xl font-bold ${metricColor}`}>{metrics.totalProfitCumulative.toFixed(4)}</div>
                <div className="text-[10px] text-gray-500">LIFETIME ETH</div>
              </GrafanaCard>

              {/* 4. EFFICIENCY DELTA */}
              <GrafanaCard title="AI Optimization" accent="purple">
                <div className={`text-2xl font-bold ${metricColor}`}>+{metrics.aiEfficiencyDelta.toFixed(1)}%</div>
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

            {/* START SIMULATION BUTTON - STRICT DEPENDENCY: PREFLIGHT MUST BE COMPLETE */}
            {state === 'READY' && (
              <div className="fixed bottom-8 left-0 right-0 flex justify-center z-50">
                <button
                  onClick={async () => {
                    if (preflightComplete) {
                      const { startSimulation } = useEngine(); // eslint-disable-line
                      await startSimulation();
                    }
                  }}
                  disabled={!preflightComplete}
                  className={`font-bold text-xl px-12 py-4 rounded-full shadow-[0_0_50px_rgba(87,148,242,0.5)] text-white flex items-center gap-3 transition-all
                    ${preflightComplete
                      ? 'bg-[#5794F2] animate-bounce hover:scale-105 cursor-pointer'
                      : 'bg-gray-800 text-gray-500 cursor-not-allowed opacity-50 shadow-none'
                    }
                  `}
                >
                  <Zap size={24} fill={preflightComplete ? "white" : "gray"} />
                  {preflightComplete ? 'START SIMULATION MODE' : 'COMPLETE PREFLIGHT TO START'}
                  <Zap size={24} fill={preflightComplete ? "white" : "gray"} />
                </button>
              </div>
            )}

            {/* LIVE MODE BUTTON - STRICT DEPENDENCY: SIMULATION MUST BE RUNNING */}
            {state === 'SIMULATION' && (
              <div className="fixed bottom-8 left-0 right-0 flex justify-center z-50">
                <button
                  onClick={() => {
                    confirmLive();
                  }}
                  disabled={false}
                  className={`
                font-bold text-xl px-12 py-4 rounded-full shadow-[0_0_50px_rgba(0,255,157,0.5)] flex items-center gap-3 transition-all
                bg-[#00FF9D] text-black animate-bounce hover:scale-105 cursor-pointer            }
              `}
                >
                  <Zap size={24} fill={confidence >= 85 ? "black" : "gray"} />
                  SWITCH TO LIVE MODE
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
          </main>

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
      </div>
    </div>
  );
};
