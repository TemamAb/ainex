import React, { useState, useEffect } from 'react';
import { Activity, Zap, AlertTriangle, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import PreflightPanel from './PreflightPanel';
import ModeControl from './ModeControl';
import ConfidenceReport from './ConfidenceReport';
import SystemStatus from './RpcList';
import LiveModeDashboard from './LiveModeDashboard';
import { TradeSignal, FlashLoanMetric, BotStatus, TradeLog } from '../types';
import { generateProfitProjection, generateLatencyMetrics, generateMEVMetrics, getFlashLoanMetrics, getProfitAttribution } from '../services/simulationService';

type EngineMode = 'IDLE' | 'PREFLIGHT' | 'SIM' | 'LIVE';

interface MasterDashboardProps {
  // Props will be passed from parent component
}

const MasterDashboard: React.FC<MasterDashboardProps> = () => {
  const [currentMode, setCurrentMode] = useState<EngineMode>('IDLE');
  const [preflightPassed, setPreflightPassed] = useState(false);
  const [simConfidence, setSimConfidence] = useState(50);
  const [isPreflightRunning, setIsPreflightRunning] = useState(false);
  const [preflightChecks, setPreflightChecks] = useState<any[]>([]);
  const [modules, setModules] = useState<any[]>([
    { id: '1', name: 'RPC Node', status: 'ACTIVE', details: 'Ethereum Mainnet', metrics: 'Latency: 12ms' },
    { id: '2', name: 'Flash Loan Provider', status: 'ACTIVE', details: 'Aave Protocol', metrics: 'Liquidity: 5000 ETH' },
    { id: '3', name: 'MEV Detection', status: 'EXECUTING', details: 'Monitoring blocks', metrics: 'Bundles: 23' },
    { id: '4', name: 'Arbitrage Engine', status: 'OPTIMIZING', details: 'Route optimization', metrics: 'Efficiency: 94%' }
  ]);

  // SIM Mode state
  const [tradeSignals, setTradeSignals] = useState<TradeSignal[]>([]);
  const [flashLoanMetrics, setFlashLoanMetrics] = useState<FlashLoanMetric[]>([]);
  const [botStatuses, setBotStatuses] = useState<BotStatus[]>([]);
  const [tradeLogs, setTradeLogs] = useState<TradeLog[]>([]);
  const [latencyMetrics, setLatencyMetrics] = useState({ avgLatency: 0, mevOpportunities: 0 });
  const [profitProjection, setProfitProjection] = useState({ hourly: 0, daily: 0, weekly: 0 });

  // SIM Mode data updates
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

        setTradeSignals(signals);
        setFlashLoanMetrics(flashLoans);
        setBotStatuses(bots);
        setTradeLogs(logs);
        setLatencyMetrics({ avgLatency: latency.average, mevOpportunities: mev.frontRunningAttempts });
        setProfitProjection({ hourly: profitProj.hourly, daily: profitProj.daily, weekly: profitProj.weekly });

        // Update confidence based on simulation performance
        setSimConfidence(prev => Math.min(100, prev + Math.random() * 5));
      } catch (error) {
        console.error('Error updating simulation data:', error);
      }
    };

    updateData();
    const interval = setInterval(updateData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [currentMode, simConfidence]);

  const handleStartSim = () => {
    if (preflightPassed) {
      setCurrentMode('SIM');
    }
  };

  const handleStartLive = () => {
    if (simConfidence >= 85) {
      setCurrentMode('LIVE');
    }
  };

  const handleStopMode = () => {
    setCurrentMode('IDLE');
  };

  const handleRunPreflight = () => {
    setIsPreflightRunning(true);
    // Simulate preflight checks
    setTimeout(() => {
      setPreflightPassed(true);
      setIsPreflightRunning(false);
      setCurrentMode('PREFLIGHT');
    }, 3000);
  };

  const handleStartSimFromPreflight = () => {
    setCurrentMode('SIM');
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 85) return '#00FF9D'; // Green
    if (conf >= 70) return '#FFD700'; // Yellow
    return '#FF6B6B'; // Red
  };

  const getProfitAttribution = () => {
    const attribution = tradeLogs.reduce((acc, log) => {
      const key = `${log.pair}-${log.dex.join(',')}`;
      acc[key] = (acc[key] || 0) + log.profit;
      return acc;
    }, {} as Record<string, number>);
    return Object.entries(attribution).sort(([,a], [,b]) => b - a);
  };

  const renderDashboardContent = () => {
    switch (currentMode) {
      case 'IDLE':
        return (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="text-center">
              <div className="w-24 h-24 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6">
                <Activity className="w-12 h-12 text-slate-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">AINEX Engine Ready</h2>
              <p className="text-slate-400 mb-8">Start with preflight checks to ensure system integrity</p>
              <button
                onClick={handleRunPreflight}
                disabled={isPreflightRunning}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors disabled:opacity-50"
              >
                {isPreflightRunning ? 'Running Preflight...' : 'Run Preflight Checks'}
              </button>
            </div>
          </div>
        );

      case 'PREFLIGHT':
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Preflight Complete</h2>
              <p className="text-slate-400">All systems checked and ready for simulation</p>
            </div>
            <PreflightPanel
              checks={preflightChecks}
              isRunning={isPreflightRunning}
              onRunPreflight={handleRunPreflight}
            />
          </div>
        );

      case 'SIM':
        return (
          <div className="space-y-8">
            {/* SIM Mode Header */}
            <div className="text-center">
              <h1 className="text-3xl font-bold text-white mb-2">⚡ SIMULATION MODE</h1>
              <div className="flex items-center justify-center gap-4 mb-4">
                <div className="text-lg text-white">Confidence Score:</div>
                <div className="flex-1 max-w-xs bg-gray-700 rounded-full h-4">
                  <div
                    className="h-4 rounded-full transition-all duration-500"
                    style={{
                      width: `${simConfidence}%`,
                      backgroundColor: getConfidenceColor(simConfidence)
                    }}
                  ></div>
                </div>
                <div className="text-2xl font-bold" style={{ color: getConfidenceColor(simConfidence) }}>
                  {simConfidence.toFixed(1)}%
                </div>
              </div>
              {simConfidence < 85 && (
                <div className="text-yellow-400 flex items-center justify-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Awaiting confidence ≥ 85% to unlock LIVE MODE
                </div>
              )}
            </div>

            {/* Profit Projection Dashboard */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 text-white">💰 Profit/Hour</h3>
                <div className="text-2xl font-bold text-green-400">
                  +{profitProjection.hourly.toFixed(4)} ETH
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 text-white">📈 Daily Projection</h3>
                <div className="text-2xl font-bold text-blue-400">
                  +{profitProjection.daily.toFixed(4)} ETH
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-2 text-white">📊 Weekly Projection</h3>
                <div className="text-2xl font-bold text-purple-400">
                  +{profitProjection.weekly.toFixed(4)} ETH
                </div>
              </div>
            </div>

            {/* Latency Metrics and MEV Monitoring */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4 text-white">⚡ Latency Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-white">
                    <span>Average Latency:</span>
                    <span className="font-bold">{latencyMetrics.avgLatency}ms</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>MEV Opportunities Detected:</span>
                    <span className="font-bold text-orange-400">{latencyMetrics.mevOpportunities}</span>
                  </div>
                </div>
              </div>

              {/* Front-running Detection Display */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4 text-white">🚨 Front-running Detection</h3>
                <div className="space-y-2">
                  {tradeSignals.filter(signal => signal.action === 'MEV_BUNDLE').slice(0, 3).map(signal => (
                    <div key={signal.id} className="bg-red-900 p-2 rounded">
                      <div className="text-sm text-white">Block {signal.blockNumber}</div>
                      <div className="text-sm font-bold text-white">{signal.pair}</div>
                      <div className="text-xs text-yellow-400">MEV Bundle Detected</div>
                    </div>
                  ))}
                  {tradeSignals.filter(signal => signal.action === 'MEV_BUNDLE').length === 0 && (
                    <div className="text-green-400">No front-running detected</div>
                  )}
                </div>
              </div>
            </div>

            {/* Additional SIM Mode Sections */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Flash Loan Provider Availability */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4 text-white">💸 Flash Loan Providers</h3>
                <div className="space-y-3">
                  {flashLoanMetrics.slice(0, 3).map(provider => (
                    <div key={provider.provider} className="bg-gray-700 p-3 rounded">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-white">{provider.provider}</span>
                        <span className={`text-sm ${provider.utilization > 80 ? 'text-red-400' : 'text-green-400'}`}>
                          {provider.utilization}%
                        </span>
                      </div>
                      <div className="text-sm text-gray-300">Available: {provider.liquidityAvailable} ETH</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tritier Bot System Status */}
              <div className="bg-gray-800 p-4 rounded-lg">
                <h3 className="text-lg font-semibold mb-4 text-white">🤖 Tritier Bot System Status</h3>
                <div className="space-y-3">
                  {botStatuses.map(bot => (
                    <div key={bot.id} className="bg-gray-700 p-3 rounded">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-white">{bot.name}</span>
                        <span className={`text-sm ${
                          bot.status === 'ACTIVE' ? 'text-green-400' :
                          bot.status === 'OPTIMIZING' ? 'text-yellow-400' : 'text-red-400'
                        }`}>
                          {bot.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300">Tier: {bot.tier} | Uptime: {bot.uptime}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 'LIVE':
        return (
          <LiveModeDashboard
            signals={tradeSignals}
            totalProfit={profitProjection.daily} // Using daily projection as total profit for demo
            flashMetrics={flashLoanMetrics}
            onExecuteTrade={(signal: TradeSignal) => {
              // Handle trade execution in LIVE mode
              console.log('Executing trade:', signal);
            }}
            onPauseTrading={() => {
              // Handle pause trading
              console.log('Pausing trading');
            }}
            onResumeTrading={() => {
              // Handle resume trading
              console.log('Resuming trading');
            }}
            isPaused={false}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">AINEX</h1>
              <p className="text-slate-400 text-sm">Autonomous Intelligence Neural Execution eXchange</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-slate-400">System Status</div>
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    currentMode === 'LIVE' ? 'bg-green-400 animate-pulse' :
                    currentMode === 'SIM' ? 'bg-blue-400' : 'bg-slate-400'
                  }`}></div>
                  <span className="text-white font-medium">{currentMode}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar - Mode Control */}
          <div className="lg:col-span-1">
            <ModeControl
              currentMode={currentMode}
              preflightPassed={preflightPassed}
              simConfidence={simConfidence}
              onStartSim={handleStartSim}
              onStartLive={handleStartLive}
              onStopMode={handleStopMode}
              onRunPreflight={handleRunPreflight}
              isPreflightRunning={isPreflightRunning}
            />

            {/* System Status */}
            <div className="mt-6">
              <SystemStatus modules={modules} />
            </div>
          </div>

          {/* Main Dashboard Area */}
          <div className="lg:col-span-3">
            {renderDashboardContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MasterDashboard;
