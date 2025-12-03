import React, { useState, useEffect } from 'react';
import { TradeSignal, FlashLoanMetric, BotStatus, TradeLog } from '../types';
import { generateProfitProjection, generateLatencyMetrics, generateMEVMetrics, getFlashLoanMetrics, getProfitAttribution } from '../services/simulationService';

interface SimModeDashboardProps {
  confidence: number;
  onConfidenceUpdate: (newConfidence: number) => void;
}

const SimModeDashboard: React.FC<SimModeDashboardProps> = ({ confidence, onConfidenceUpdate }) => {
  const [tradeSignals, setTradeSignals] = useState<TradeSignal[]>([]);
  const [flashLoanMetrics, setFlashLoanMetrics] = useState<FlashLoanMetric[]>([]);
  const [botStatuses, setBotStatuses] = useState<BotStatus[]>([]);
  const [tradeLogs, setTradeLogs] = useState<TradeLog[]>([]);
  const [latencyMetrics, setLatencyMetrics] = useState({ avgLatency: 0, mevOpportunities: 0 });
  const [profitProjection, setProfitProjection] = useState({ hourly: 0, daily: 0, weekly: 0 });

  useEffect(() => {
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
            confidence: confidence,
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
        const newConfidence = Math.min(100, confidence + Math.random() * 5);
        onConfidenceUpdate(newConfidence);
      } catch (error) {
        console.error('Error updating simulation data:', error);
      }
    };

    updateData();
    const interval = setInterval(updateData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [confidence, onConfidenceUpdate]);

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
    return Object.entries(attribution).sort(([, a], [, b]) => b - a);
  };

  return (
    <div className="sim-mode-dashboard p-6 bg-gray-900 text-white min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">⚡ SIMULATION MODE DASHBOARD</h1>
        <div className="flex items-center gap-4">
          <div className="text-lg">Confidence Score:</div>
          <div className="flex-1 bg-gray-700 rounded-full h-4">
            <div
              className="h-4 rounded-full transition-all duration-500"
              style={{
                width: `${confidence}%`,
                backgroundColor: getConfidenceColor(confidence)
              }}
            ></div>
          </div>
          <div className="text-2xl font-bold" style={{ color: getConfidenceColor(confidence) }}>
            {confidence.toFixed(1)}%
          </div>
        </div>
        {confidence < 85 && (
          <div className="mt-2 text-yellow-400">
            ⚠️ Awaiting confidence ≥ 85% to unlock LIVE MODE
          </div>
        )}
      </div>

      {/* Profit Projection Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">💰 Profit/Hour</h3>
          <div className="text-2xl font-bold text-green-400">
            +{profitProjection.hourly.toFixed(4)} ETH
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">📈 Daily Projection</h3>
          <div className="text-2xl font-bold text-blue-400">
            +{profitProjection.daily.toFixed(4)} ETH
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">📊 Weekly Projection</h3>
          <div className="text-2xl font-bold text-purple-400">
            +{profitProjection.weekly.toFixed(4)} ETH
          </div>
        </div>
      </div>

      {/* Latency Metrics and MEV Monitoring */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">⚡ Latency Metrics</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Average Latency:</span>
              <span className="font-bold">{latencyMetrics.avgLatency}ms</span>
            </div>
            <div className="flex justify-between">
              <span>MEV Opportunities Detected:</span>
              <span className="font-bold text-orange-400">{latencyMetrics.mevOpportunities}</span>
            </div>
          </div>
        </div>

        {/* Front-running Detection Display */}
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">🚨 Front-running Detection</h3>
          <div className="space-y-2">
            {tradeSignals.filter(signal => signal.action === 'MEV_BUNDLE').slice(0, 3).map(signal => (
              <div key={signal.id} className="bg-red-900 p-2 rounded">
                <div className="text-sm">Block {signal.blockNumber}</div>
                <div className="text-sm font-bold">{signal.pair}</div>
                <div className="text-xs text-yellow-400">MEV Bundle Detected</div>
              </div>
            ))}
            {tradeSignals.filter(signal => signal.action === 'MEV_BUNDLE').length === 0 && (
              <div className="text-green-400">No front-running detected</div>
            )}
          </div>
        </div>
      </div>

      {/* Profit Attribution */}
      <div className="bg-gray-800 p-4 rounded-lg mb-8">
        <h3 className="text-lg font-semibold mb-4">📊 Profit Attribution by Strategies/Chains/Pairs</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {getProfitAttribution().slice(0, 6).map(([key, profit]) => (
            <div key={key} className="bg-gray-700 p-3 rounded">
              <div className="text-sm font-bold">{key}</div>
              <div className="text-lg text-green-400">+{profit.toFixed(4)} ETH</div>
            </div>
          ))}
        </div>
      </div>

      {/* Flash Loan Provider Availability */}
      <div className="bg-gray-800 p-4 rounded-lg mb-8">
        <h3 className="text-lg font-semibold mb-4">💸 Flash Loan Providers</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {flashLoanMetrics.map(provider => (
            <div key={provider.provider} className="bg-gray-700 p-3 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold">{provider.provider}</span>
                <span className={`text-sm ${provider.utilization > 80 ? 'text-red-400' : 'text-green-400'}`}>
                  {provider.utilization}%
                </span>
              </div>
              <div className="text-sm">Available: {provider.liquidityAvailable} ETH</div>
              <div className="w-full bg-gray-600 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-400 h-2 rounded-full"
                  style={{ width: `${provider.utilization}%` }}
                ></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tritier Bot System Status */}
      <div className="bg-gray-800 p-4 rounded-lg mb-8">
        <h3 className="text-lg font-semibold mb-4">🤖 Tritier Bot System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {botStatuses.map(bot => (
            <div key={bot.id} className="bg-gray-700 p-3 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold">{bot.name}</span>
                <span className={`text-sm ${bot.status === 'ACTIVE' ? 'text-green-400' :
                    bot.status === 'OPTIMIZING' ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                  {bot.status}
                </span>
              </div>
              <div className="text-sm">Tier: {bot.tier}</div>
              <div className="text-sm">Uptime: {bot.uptime}</div>
              <div className="text-sm">Efficiency: {bot.efficiency}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Trade Logs */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">📋 Recent Trade Activity</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Pair</th>
                <th className="text-left p-2">DEX</th>
                <th className="text-left p-2">Profit</th>
                <th className="text-left p-2">Gas</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {tradeLogs.slice(0, 10).map(log => (
                <tr key={log.id} className="border-b border-gray-700">
                  <td className="p-2">{log.timestamp}</td>
                  <td className="p-2">{log.pair}</td>
                  <td className="p-2">{log.dex.join(', ')}</td>
                  <td className="p-2 text-green-400">+{log.profit.toFixed(4)}</td>
                  <td className="p-2">{log.gas}</td>
                  <td className="p-2">
                    <span className={`px-2 py-1 rounded text-xs ${log.status === 'SUCCESS' ? 'bg-green-800 text-green-400' : 'bg-red-800 text-red-400'
                      }`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SimModeDashboard;
