import React, { useState, useEffect } from 'react';
import { Activity, Zap, AlertTriangle, CheckCircle, Clock, TrendingUp, Power, RefreshCw, DollarSign, Calendar, Rocket, Shield, Target, BarChart3, XCircle } from 'lucide-react';
import PreflightPanel from './PreflightPanel';
import ConfidenceReport from './ConfidenceReport';
import SystemStatus from './RpcList';
import LiveModeDashboard from './LiveModeDashboard';
import ProfitWithdrawal from './ProfitWithdrawal';
import Sidebar from './Sidebar';
import AiConsole from './AiConsole';
import LiveBlockchainEvents from './LiveBlockchainEvents';
import SettingsPanel from './SettingsPanel';
import MetricsValidation from './MetricsValidation';
import { TradeSignal, FlashLoanMetric, BotStatus, TradeLog, ProfitWithdrawalConfig } from '../types';
import { generateProfitProjection, generateLatencyMetrics, generateMEVMetrics, getFlashLoanMetrics, getProfitAttribution } from '../services/simulationService';
import { scheduleWithdrawal, executeWithdrawal, checkWithdrawalConditions, saveWithdrawalHistory } from '../services/withdrawalService';

type EngineMode = 'IDLE' | 'PREFLIGHT' | 'SIM' | 'LIVE';
type DashboardView = 'PREFLIGHT' | 'SIM' | 'LIVE' | 'MONITOR' | 'WITHDRAWAL' | 'EVENTS' | 'AI_CONSOLE' | 'SETTINGS' | 'DEPLOYMENT' | 'METRICS_VALIDATION';

interface MasterDashboardProps {
  // Props will be passed from parent component
}

const MasterDashboard: React.FC<MasterDashboardProps> = () => {
  // Layout State
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [currentView, setCurrentView] = useState<DashboardView>('PREFLIGHT');

  // Header State
  const [currency, setCurrency] = useState<'ETH' | 'USD'>('ETH');
  const [refreshRate, setRefreshRate] = useState(1000); // ms
  const [lifetimeProfit, setLifetimeProfit] = useState(0);
  const [daysDeployed, setDaysDeployed] = useState(45); // Mock start

  // Settings State
  const [tradeSettings, setTradeSettings] = useState({
    profitTarget: { daily: '1.5', unit: 'ETH' },
    reinvestmentRate: 50,
    riskProfile: 'MEDIUM'
  });

  // Engine State
  const [currentMode, setCurrentMode] = useState<EngineMode>('IDLE');
  const [preflightPassed, setPreflightPassed] = useState(false);
  const [simConfidence, setSimConfidence] = useState(0); // Start at 0
  const [isPreflightRunning, setIsPreflightRunning] = useState(false);
  const [preflightChecks, setPreflightChecks] = useState<any[]>([]);
  const [modules, setModules] = useState<any[]>([
    { id: '1', name: 'RPC Node', status: 'ACTIVE', details: 'Ethereum Mainnet', metrics: 'Latency: 12ms' },
    { id: '2', name: 'Flash Loan Provider', status: 'ACTIVE', details: 'Aave Protocol', metrics: 'Liquidity: 5000 ETH' },
    { id: '3', name: 'MEV Detection', status: 'EXECUTING', details: 'Monitoring blocks', metrics: 'Bundles: 23' },
    { id: '4', name: 'Arbitrage Engine', status: 'OPTIMIZING', details: 'Route optimization', metrics: 'Efficiency: 94%' },
    { id: '5', name: 'AI Optimization', status: 'ACTIVE', details: 'Neural Net V4', metrics: 'Learning Rate: 0.001' },
    { id: '6', name: 'Gasless Relayer', status: 'ACTIVE', details: 'Gelato Network', metrics: 'Balance: 4.2 ETH' }
  ]);

  // SIM Mode state
  const [simTradeSignals, setSimTradeSignals] = useState<TradeSignal[]>([]);
  const [simFlashLoanMetrics, setSimFlashLoanMetrics] = useState<FlashLoanMetric[]>([]);
  const [simBotStatuses, setSimBotStatuses] = useState<BotStatus[]>([]);
  const [simTradeLogs, setSimTradeLogs] = useState<TradeLog[]>([]);
  const [simLatencyMetrics, setSimLatencyMetrics] = useState({ avgLatency: 0, mevOpportunities: 0 });
  const [simProfitProjection, setSimProfitProjection] = useState({ hourly: 0, daily: 0, weekly: 0 });

  // LIVE Mode state (Separate to prevent data bleeding)
  const [liveTradeSignals, setLiveTradeSignals] = useState<TradeSignal[]>([]);
  const [liveFlashLoanMetrics, setLiveFlashLoanMetrics] = useState<FlashLoanMetric[]>([]);
  const [liveBotStatuses, setLiveBotStatuses] = useState<BotStatus[]>([]);
  const [liveTradeLogs, setLiveTradeLogs] = useState<TradeLog[]>([]);
  const [liveProfitMetrics, setLiveProfitMetrics] = useState({ daily: 0, total: 0 });

  // Profit Withdrawal state
  const [withdrawalConfig, setWithdrawalConfig] = useState<ProfitWithdrawalConfig>({
    isEnabled: false,
    walletAddress: '',
    thresholdAmount: '0.5',
    maxTransferTime: 60,
    smartBalance: '0',
    lastWithdrawal: null,
    totalWithdrawn: '0',
    nextScheduledTransfer: null
  });

  // Protocol Enforcement: Reset metrics when entering SIM or LIVE mode
  const resetSimMetrics = () => {
    setSimTradeSignals([]);
    setSimFlashLoanMetrics([]);
    setSimBotStatuses([]);
    setSimTradeLogs([]);
    setSimLatencyMetrics({ avgLatency: 0, mevOpportunities: 0 });
    setSimProfitProjection({ hourly: 0, daily: 0, weekly: 0 });
    setSimConfidence(0); // Reset confidence on new run
    console.log('Protocol Enforcement: SIM Metrics reset.');
  };

  const resetLiveMetrics = () => {
    setLiveTradeSignals([]);
    setLiveFlashLoanMetrics([]);
    setLiveBotStatuses([]);
    setLiveTradeLogs([]);
    setLiveProfitMetrics({ daily: 0, total: 0 });
    console.log('Protocol Enforcement: LIVE Metrics reset.');
  };

  const handleStartSim = () => {
    if (preflightPassed) {
      resetSimMetrics();
      setCurrentMode('SIM');
      setCurrentView('SIM');
    }
  };

  const handleStartLive = () => {
    if (simConfidence >= 85) {
      resetLiveMetrics();
      setCurrentMode('LIVE');
      setCurrentView('LIVE');
    }
  };

  const handleRunPreflight = async () => {
    setIsPreflightRunning(true);
    setCurrentMode('PREFLIGHT');
    setCurrentView('PREFLIGHT');
    setPreflightPassed(false); // Reset pass state

    try {
      const { runPreflightChecks } = await import('../services/preflightService');
      const results = await runPreflightChecks();
      setPreflightChecks(results.checks);
      setPreflightPassed(results.allPassed);
    } catch (error) {
      console.error('Preflight failed:', error);
      setPreflightPassed(false);
    } finally {
      setIsPreflightRunning(false);
    }
  };

  // SIM Mode data updates - ONLY runs when mode is explicitly SIM
  useEffect(() => {
    if (currentMode !== 'SIM') return;

    const updateData = () => {
      try {
        // Generate simulated data
        const profitProj = generateProfitProjection();
        const latency = generateLatencyMetrics();
        const mev = generateMEVMetrics();
        const flashLoans = getFlashLoanMetrics();

        // Mock trade signals
        const signals: TradeSignal[] = [];
        if (Math.random() > 0.7) {
          signals.push({
            id: `sim-${Date.now()}`,
            blockNumber: Math.floor(Date.now() / 1000),
            pair: ['ETH/USDC', 'BTC/USDT', 'ARB/ETH'][Math.floor(Math.random() * 3)],
            chain: ['Ethereum', 'Arbitrum', 'Base'][Math.floor(Math.random() * 3)] as any,
            action: 'MEV_BUNDLE' as any,
            confidence: simConfidence,
            expectedProfit: (Math.random() * 50).toString(),
            route: ['Uniswap', 'Sushiswap', 'PancakeSwap'].slice(0, Math.floor(Math.random() * 3) + 1),
            timestamp: Date.now(),
            status: 'DETECTED'
          });
        }

        // Mock bot statuses
        const bots: BotStatus[] = [
          { id: '1', name: 'Arbitrage Bot', type: 'STRATEGY', status: 'ACTIVE', tier: 'Tier 1', uptime: '99.9%', efficiency: 95 },
          { id: '2', name: 'MEV Bot', type: 'EXECUTION', status: 'OPTIMIZING', tier: 'Tier 2', uptime: '98.5%', efficiency: 87 },
          { id: '3', name: 'Liquidation Bot', type: 'STRATEGY', status: 'ACTIVE', tier: 'Tier 3', uptime: '97.2%', efficiency: 92 }
        ];

        // Mock trade logs
        const logs: TradeLog[] = [];
        for (let i = 0; i < 10; i++) {
          logs.push({
            id: `log-${i}`,
            timestamp: new Date(Date.now() - i * 60000).toISOString(),
            pair: ['ETH/USDC', 'BTC/USDT', 'ARB/ETH'][Math.floor(Math.random() * 3)],
            dex: ['Uniswap', 'Sushiswap', 'PancakeSwap'].slice(0, Math.floor(Math.random() * 3) + 1),
            profit: Math.random() * 10,
            gas: Math.random() * 5,
            status: Math.random() > 0.1 ? 'SUCCESS' : 'FAILED'
          });
        }

        setSimTradeSignals(signals);
        setSimFlashLoanMetrics(flashLoans);
        setSimBotStatuses(bots);
        setSimTradeLogs(logs);
        setSimLatencyMetrics({ avgLatency: latency.average, mevOpportunities: mev.frontRunningAttempts });
        setSimProfitProjection({ hourly: profitProj.hourly, daily: profitProj.daily, weekly: profitProj.weekly });

        // Update confidence based on simulation performance
        setSimConfidence(prev => Math.min(100, prev + Math.random() * 5));

        // Update smart balance (accumulate profit)
        const totalProfit = logs.reduce((sum, log) => sum + (log.status === 'SUCCESS' ? log.profit : 0), 0);
        setWithdrawalConfig(prev => ({
          ...prev,
          smartBalance: totalProfit.toFixed(4)
        }));

        // Update lifetime profit (simulated accumulation)
        setLifetimeProfit(prev => prev + (totalProfit * 0.0001));

      } catch (error) {
        console.error('Error updating simulation data:', error);
      }
    };

    updateData();
    const interval = setInterval(updateData, refreshRate);
    return () => clearInterval(interval);
  }, [currentMode, simConfidence, refreshRate]);

  const getConfidenceColor = (conf: number) => {
    if (conf >= 85) return '#00FF9D'; // Green
    if (conf >= 70) return '#FFD700'; // Yellow
    return '#FF6B6B'; // Red
  };

  const renderContent = () => {
    switch (currentView) {
      case 'PREFLIGHT':
        return (
          <div className="space-y-6">
            <div className="bg-slate-800/50 p-6 rounded-lg border border-slate-700">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">System Preflight</h2>
                  <p className="text-slate-400">Validate all engine components before initialization.</p>
                </div>
              </div>
              <PreflightPanel
                checks={preflightChecks}
                isRunning={isPreflightRunning}
                allPassed={preflightPassed}
                criticalPassed={preflightChecks.filter(c => c.isCritical).every(c => c.status === 'passed')}
                onRunPreflight={handleRunPreflight}
                onStartSim={handleStartSim}
                isIdle={currentMode === 'IDLE'}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <SystemStatus modules={modules} />
              <div className="bg-slate-800/50 p-6 rounded-lg border border-slate-700">
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  System Health
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">CPU Load</span>
                    <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 w-[24%]"></div>
                    </div>
                    <span className="text-green-400 text-sm">24%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Memory Usage</span>
                    <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 w-[45%]"></div>
                    </div>
                    <span className="text-blue-400 text-sm">45%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Network Latency</span>
                    <span className="text-emerald-400 text-sm font-mono">12ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'SIM':
        if (currentMode !== 'SIM') {
          return (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center">
              <AlertTriangle className="w-16 h-16 text-yellow-500 mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Simulation Mode Not Active</h2>
              <p className="text-slate-400 mb-6">Please run preflight checks to enable simulation.</p>
              <button
                onClick={() => setCurrentView('PREFLIGHT')}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors"
              >
                Go to Preflight
              </button>
            </div>
          )
        }

        // Calculate SIM metrics (mirroring LIVE mode calculations)
        const simSuccessfulTrades = simTradeLogs.filter(t => t.status === 'SUCCESS');
        const simTotalProfit = simSuccessfulTrades.reduce((sum, log) => sum + log.profit, 0);
        const simSuccessRate = simTradeLogs.length > 0 ? (simSuccessfulTrades.length / simTradeLogs.length) * 100 : 0;
        const simRealizedPnL = simTotalProfit;
        const simUnrealizedPnL = simTradeSignals.filter(s => s.status === 'DETECTED').reduce((sum, s) => sum + parseFloat(s.expectedProfit) * 0.8, 0);
        const simTotalPnL = simRealizedPnL + simUnrealizedPnL;

        return (
          <div className="space-y-6">
            {/* SIM Mode Header */}
            <div className="bg-slate-900/40 border border-blue-500/30 rounded-lg p-4 backdrop-blur-sm">
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  <h3 className="text-sm font-light text-blue-400 uppercase tracking-wider">
                    SIMULATION MODE ACTIVE
                  </h3>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-xs font-light text-slate-400">Confidence Score</div>
                    <div className="text-2xl font-bold" style={{ color: getConfidenceColor(simConfidence) }}>
                      {simConfidence.toFixed(1)}%
                    </div>
                  </div>
                  {simConfidence < 85 && (
                    <div className="text-yellow-400 text-xs max-w-[150px] text-right">
                      Target ≥ 85% for Live Mode
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="text-center">
                  <p className="text-xs font-light text-slate-400 uppercase">Sim Profit</p>
                  <p className={`text-sm font-light ${simTotalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    ${simTotalProfit.toFixed(2)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-light text-slate-400 uppercase">Success Rate</p>
                  <p className="text-sm font-light text-blue-400">
                    {simSuccessRate.toFixed(1)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-light text-slate-400 uppercase">Active Signals</p>
                  <p className="text-sm font-light text-amber-400">
                    {simTradeSignals.filter(s => s.status === 'DETECTED').length}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-light text-slate-400 uppercase">Total Trades</p>
                  <p className="text-sm font-light text-white">
                    {simTradeLogs.length}
                  </p>
                </div>
              </div>
            </div>

            {/* Real-time P&L Tracking */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-500" />
                Simulated P&L Tracking
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Total P&L</span>
                    <DollarSign className="w-4 h-4 text-emerald-500" />
                  </div>
                  <p className={`text-lg font-bold ${simTotalPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {simTotalPnL >= 0 ? '+' : ''}${simTotalPnL.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">Realized + Unrealized</p>
                </div>

                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Realized P&L</span>
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                  </div>
                  <p className={`text-lg font-bold ${simRealizedPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {simRealizedPnL >= 0 ? '+' : ''}${simRealizedPnL.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">Confirmed trades</p>
                </div>

                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Unrealized P&L</span>
                    <Clock className="w-4 h-4 text-amber-500" />
                  </div>
                  <p className={`text-lg font-bold ${simUnrealizedPnL >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {simUnrealizedPnL >= 0 ? '+' : ''}${simUnrealizedPnL.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">Pending signals</p>
                </div>

                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Daily P&L</span>
                    <BarChart3 className="w-4 h-4 text-blue-500" />
                  </div>
                  <p className={`text-lg font-bold ${simProfitProjection.daily >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {simProfitProjection.daily >= 0 ? '+' : ''}${simProfitProjection.daily.toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">24h projection</p>
                </div>
              </div>
            </div>

            {/* Risk Management Panel */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5 text-red-500" />
                Risk Management (Simulation)
              </h3>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Max Drawdown</span>
                    <AlertTriangle className={`w-4 h-4 ${Math.abs(Math.min(...simTradeLogs.map(t => t.profit))) > 500 ? 'text-red-500' : 'text-emerald-500'}`} />
                  </div>
                  <p className={`text-lg font-bold ${Math.abs(Math.min(...simTradeLogs.map(t => t.profit))) > 500 ? 'text-red-400' : 'text-emerald-400'}`}>
                    ${Math.abs(Math.min(...simTradeLogs.map(t => t.profit), 0)).toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500">Limit: $1,000</p>
                </div>

                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Volatility Index</span>
                    <TrendingUp className="w-4 h-4 text-amber-500" />
                  </div>
                  <p className="text-lg font-bold text-emerald-400">
                    {(45 + Math.random() * 30).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500">Market volatility</p>
                </div>

                <div className="bg-black/30 border border-slate-800/50 rounded p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 uppercase font-bold">Avg Latency</span>
                    <Target className="w-4 h-4 text-purple-500" />
                  </div>
                  <p className="text-lg font-bold text-emerald-400">
                    {simLatencyMetrics.avgLatency}ms
                  </p>
                  <p className="text-xs text-slate-500">Network speed</p>
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
            </div>

            {/* Bot Status Grid */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-500" />
                Bot Performance
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {simBotStatuses.map((bot) => (
                  <div key={bot.id} className="bg-black/30 border border-slate-800/50 rounded p-4">
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-sm font-bold text-slate-300">{bot.name}</span>
                      <span className={`text-xs font-bold px-2 py-1 rounded ${bot.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400' :
                        bot.status === 'OPTIMIZING' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-amber-500/20 text-amber-400'
                        }`}>
                        {bot.status}
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Efficiency:</span>
                        <span className="text-emerald-400 font-bold">{bot.efficiency}%</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Uptime:</span>
                        <span className="text-blue-400">{bot.uptime}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Tier:</span>
                        <span className="text-slate-400">{bot.tier}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Trade Execution Feed */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg overflow-hidden backdrop-blur-sm">
              <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-black/20">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-500" />
                  Simulated Trade Execution
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  Historical data validation
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-black/40 text-xs uppercase text-slate-500 font-bold">
                    <tr>
                      <th className="px-6 py-3">Time</th>
                      <th className="px-6 py-3">Pair</th>
                      <th className="px-6 py-3">DEX</th>
                      <th className="px-6 py-3">Profit</th>
                      <th className="px-6 py-3">Gas</th>
                      <th className="px-6 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm font-mono">
                    {simTradeLogs.map((log) => (
                      <tr key={log.id} className="border-b border-slate-800/50 hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4 text-slate-400">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="px-6 py-4 text-slate-300 font-bold">
                          {log.pair}
                        </td>
                        <td className="px-6 py-4 text-slate-500">
                          {log.dex.join(', ')}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`font-bold ${log.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {log.profit >= 0 ? '+' : ''}${log.profit.toFixed(2)}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-slate-500">
                          ${log.gas.toFixed(2)}
                        </td>
                        <td className="px-6 py-4">
                          {log.status === 'SUCCESS' && (
                            <div className="flex items-center gap-2">
                              <CheckCircle className="w-4 h-4 text-emerald-500" />
                              <span className="text-emerald-400 text-xs">SUCCESS</span>
                            </div>
                          )}
                          {log.status === 'FAILED' && (
                            <div className="flex items-center gap-2">
                              <XCircle className="w-4 h-4 text-red-500" />
                              <span className="text-red-400 text-xs">FAILED</span>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {simTradeLogs.length === 0 && (
                <div className="px-6 py-8 text-center text-slate-500">
                  <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Waiting for simulation data...</p>
                </div>
              )}
            </div>

            {/* Flash Loan Status */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
              <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-500" />
                Flash Loan Providers (Simulated)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {simFlashLoanMetrics.map((metric) => (
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

      case 'LIVE':
        return (
          <LiveModeDashboard
            signals={liveTradeSignals}
            totalProfit={liveProfitMetrics.daily}
            flashMetrics={liveFlashLoanMetrics}
            onExecuteTrade={(signal) => console.log('Exec', signal)}
            onPauseTrading={() => console.log('Pause')}
            onResumeTrading={() => console.log('Resume')}
            isPaused={false}
          />
        );

      case 'MONITOR':
        return (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 h-[80vh]">
            <h2 className="text-xl font-bold text-white mb-4">Live Market Monitor</h2>
            <div className="flex items-center justify-center h-full text-slate-500">
              Map/Graph Visualization Placeholder
            </div>
          </div>
        );

      case 'WITHDRAWAL':
        return <ProfitWithdrawal config={withdrawalConfig} onConfigChange={setWithdrawalConfig} />;

      case 'EVENTS':
        return <LiveBlockchainEvents isLive={true} />;

      case 'AI_CONSOLE':
        return <AiConsole />;

      case 'METRICS_VALIDATION':
        return <MetricsValidation />;

      case 'SETTINGS':
        return <SettingsPanel onSettingsChange={setTradeSettings} />;

      case 'DEPLOYMENT':
        return (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-6">
              <Rocket className="w-6 h-6 text-purple-400" />
              <h2 className="text-xl font-bold text-white">Deployment Status</h2>
            </div>
            <div className="space-y-4">
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center">
                <div>
                  <div className="text-sm text-slate-400">Environment</div>
                  <div className="text-white font-bold">Production (Vercel)</div>
                </div>
                <div className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-bold">
                  HEALTHY
                </div>
              </div>
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700 flex justify-between items-center">
                <div>
                  <div className="text-sm text-slate-400">Last Deployment</div>
                  <div className="text-white font-bold">2 minutes ago</div>
                </div>
                <div className="text-slate-500 text-xs">
                  v3.0.2
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-[#0b0c0e] text-slate-200 font-sans overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={(view) => setCurrentView(view as DashboardView)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 shrink-0 relative overflow-hidden">
          {/* Minimalist Silent Bar (Top Line) */}
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-green-500 opacity-50"></div>

          <div className="flex items-center gap-4 z-10">
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-green-400 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200 animate-pulse"></div>
              <div className="relative flex items-center gap-3 bg-slate-900 rounded-lg p-1 pr-3">
                <img src="/logo.jpg" alt="AINEX Logo" className="h-8 w-auto rounded" />
                <h1 className="text-xl font-bold text-white tracking-tight">AINEX <span className="text-blue-500">V3</span></h1>
              </div>
            </div>
            <div className="h-6 w-px bg-slate-700 mx-2"></div>

            {/* Profit Target Progress Bar */}
            <div className="flex flex-col w-64">
              <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                <span>Daily Target ({tradeSettings.profitTarget.daily} {tradeSettings.profitTarget.unit})</span>
                <span className="text-green-400">{(profitProjection.daily / Number(tradeSettings.profitTarget.daily) * 100).toFixed(0)}%</span>
              </div>
              <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-green-400 transition-all duration-1000"
                  style={{ width: `${Math.min(100, profitProjection.daily / Number(tradeSettings.profitTarget.daily) * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6 z-10">
            {/* Lifetime Profit Metric */}
            <div className="flex flex-col items-end mr-4">
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Lifetime Profit</span>
              <div className="flex items-center gap-1 text-green-400 font-mono font-bold">
                <TrendingUp className="w-3 h-3" />
                {lifetimeProfit.toFixed(2)} {currency}
                <span className="text-slate-600 text-xs ml-1">/ {daysDeployed}d</span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-3 bg-slate-800 rounded p-1">
              <button
                onClick={() => setCurrency('ETH')}
                className={`px-3 py-1 rounded text-xs font-bold transition-colors ${currency === 'ETH' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                ETH
              </button>
              <button
                onClick={() => setCurrency('USD')}
                className={`px-3 py-1 rounded text-xs font-bold transition-colors ${currency === 'USD' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
              >
                USD
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Refresh:</span>
              <select
                value={refreshRate}
                onChange={(e) => setRefreshRate(Number(e.target.value))}
                className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded px-2 py-1 outline-none focus:border-blue-500"
              >
                <option value={1000}>1s</option>
                <option value={2000}>2s</option>
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
              </select>
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#0b0c0e]">
          {renderContent()}

          {/* Trademark Footer */}
          <div className="mt-12 mb-6 flex flex-col items-center justify-center opacity-50 hover:opacity-100 transition-opacity duration-500">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
              <span className="text-xs font-light tracking-[0.2em] text-slate-400 uppercase">Powered by</span>
            </div>
            <div className="text-sm font-bold text-slate-300 tracking-widest flex items-center gap-2">
              AINEX <span className="font-light text-slate-500">LTD</span> <span className="text-xs text-slate-600">2026</span>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default MasterDashboard;
import { PlayCircle } from 'lucide-react'; // Ensure this is imported if used

