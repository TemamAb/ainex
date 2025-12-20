import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Activity, DollarSign, Cpu, Zap } from 'lucide-react';
import { dashboardApi } from '../utils/api';
import { ProfitData } from '../types';
import ProfitChart from './ProfitChart';
import TradingPanel from './TradingPanel';

const Dashboard: React.FC = () => {
  const [profitData, setProfitData] = useState<ProfitData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    
    // Subscribe to real-time updates
    const unsubscribe = dashboardApi.subscribeToUpdates((data) => {
      setProfitData(data);
    });
    
    return unsubscribe;
  }, []);

  const loadDashboardData = async () => {
    try {
      const [profitRes, statusRes] = await Promise.all([
        dashboardApi.getProfit(),
        dashboardApi.getStatus()
      ]);
      
      setProfitData({
        ...statusRes.data,
        current_profit: profitRes.data.current_profit || 0,
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4,
      maximumFractionDigits: 8,
    }).format(value);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-12 h-12 text-aineon-primary animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Loading AINEON Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-lg border-b border-gray-700">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Zap className="w-8 h-8 text-aineon-primary" />
              <div>
                <h1 className="text-2xl font-bold">AINEON Trading Dashboard</h1>
                <p className="text-gray-400 text-sm">Real-time algorithmic trading system</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={loadDashboardData}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Refresh
              </button>
              <div className={`px-3 py-1 rounded-full ${profitData?.status === 'active' ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                {profitData?.status?.toUpperCase() || 'OFFLINE'}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <DollarSign className="w-8 h-8 text-green-400" />
              <span className={`text-sm font-semibold px-3 py-1 rounded-full ${(profitData?.current_profit || 0) >= 0 ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
                {(profitData?.current_profit || 0) >= 0 ? 'PROFIT' : 'LOSS'}
              </span>
            </div>
            <div className="text-3xl font-bold">
              {formatCurrency(profitData?.current_profit || 0)}
            </div>
            <p className="text-gray-400 mt-2">Current Profit</p>
          </div>

          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              <span className="text-sm font-semibold px-3 py-1 rounded-full bg-blue-900/50 text-blue-300">
                RATE
              </span>
            </div>
            <div className="text-3xl font-bold">
              {((profitData?.profit_rate || 0) * 100).toFixed(4)}%
            </div>
            <p className="text-gray-400 mt-2">Profit Rate</p>
          </div>

          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Activity className="w-8 h-8 text-purple-400" />
              <span className="text-sm font-semibold px-3 py-1 rounded-full bg-purple-900/50 text-purple-300">
                TRANSACTIONS
              </span>
            </div>
            <div className="text-3xl font-bold">
              {profitData?.metrics?.transactions?.toLocaleString() || '0'}
            </div>
            <p className="text-gray-400 mt-2">Total Trades</p>
          </div>

          <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <Cpu className="w-8 h-8 text-amber-400" />
              <span className="text-sm font-semibold px-3 py-1 rounded-full bg-amber-900/50 text-amber-300">
                EFFICIENCY
              </span>
            </div>
            <div className="text-3xl font-bold">
              {((profitData?.metrics?.efficiency || 0) * 100).toFixed(1)}%
            </div>
            <p className="text-gray-400 mt-2">System Efficiency</p>
          </div>
        </div>

        {/* Charts and Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ProfitChart profitData={profitData} />
          </div>
          <div>
            <TradingPanel />
          </div>
        </div>
      </main>

      <footer className="mt-12 border-t border-gray-800 py-6">
        <div className="container mx-auto px-6 text-center text-gray-500 text-sm">
          <p>AINEON Trading System • {new Date().getFullYear()} • Real-time Algorithmic Trading Dashboard</p>
          <p className="mt-2">Last Updated: {profitData?.timestamp ? new Date(profitData.timestamp).toLocaleString() : 'Never'}</p>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
