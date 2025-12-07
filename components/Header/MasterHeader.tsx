'use client';
import React from 'react';
import { useRealMetrics } from '../../hooks/useRealMetrics';

interface MasterHeaderProps {
  refreshRates?: number[];
  defaultCurrency?: 'USD' | 'ETH';
}

export const MasterHeader: React.FC<MasterHeaderProps> = ({
  refreshRates = [1000, 2000, 5000, 10000],
  defaultCurrency = 'USD'
}) => {
  const { metrics, loading } = useRealMetrics();
  const [currency, setCurrency] = React.useState<'USD' | 'ETH'>(defaultCurrency);
  const [lastUpdate, setLastUpdate] = React.useState<string>('');

  React.useEffect(() => {
    const updateTime = () => setLastUpdate(new Date().toLocaleTimeString());
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number): string => {
    if (currency === 'USD') {
      return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    } else {
      return `${(value / 3500).toFixed(4)} ETH`;
    }
  };

  if (loading || !metrics) {
    return (
      <header className="flex justify-between items-center p-4 bg-gray-900 border-b border-gray-700">
        <div className="text-white">Loading real metrics from AInex engine...</div>
      </header>
    );
  }

  return (
    <header className="flex justify-between items-center p-4 bg-gray-900 border-b border-gray-700">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-mono text-green-400">AInex ENGINE LIVE</span>
        </div>
        <div className="text-sm text-gray-400">Updated: {lastUpdate}</div>
      </div>

      <div className="flex items-center space-x-8">
        <div className="flex items-center space-x-4">
          <button 
            className={`px-3 py-1 rounded text-sm font-mono ${
              currency === 'USD' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'
            }`}
            onClick={() => setCurrency('USD')}
          >
            USD
          </button>
          <button 
            className={`px-3 py-1 rounded text-sm font-mono ${
              currency === 'ETH' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300'
            }`}
            onClick={() => setCurrency('ETH')}
          >
            ETH
          </button>
        </div>

        <div className="flex items-center space-x-6">
          <div className="text-center">
            <div className="text-sm text-gray-400">Total Profit</div>
            <div className="text-lg font-mono text-green-400">
              {formatCurrency(metrics.total)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-400">Today</div>
            <div className="text-md font-mono text-green-400">
              {formatCurrency(metrics.daily)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-400">Profit/Trade</div>
            <div className="text-md font-mono text-green-400">
              {formatCurrency(metrics.profitPerTrade)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-400">Trades/Hour</div>
            <div className="text-md font-mono text-white">
              {metrics.tradesPerHour}
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="text-right">
          <div className="text-sm text-gray-400">Win Rate</div>
          <div className="text-md font-mono text-green-400">
            {(metrics.winRate * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    </header>
  );
};
