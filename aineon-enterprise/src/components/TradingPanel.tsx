import React, { useState } from 'react';
import { Play, Pause, Settings, AlertCircle } from 'lucide-react';
import { dashboardApi } from '../utils/api';

const TradingPanel: React.FC = () => {
  const [isTrading, setIsTrading] = useState(false);
  const [threshold, setThreshold] = useState(0.0005);
  const [isLoading, setIsLoading] = useState(false);

  const handleStartTrading = async () => {
    setIsLoading(true);
    try {
      await dashboardApi.initialize({
        service: 'AINEON',
        profit_threshold: threshold,
        auto_trading: true
      });
      await dashboardApi.startTrading();
      setIsTrading(true);
    } catch (error) {
      console.error('Failed to start trading:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopTrading = async () => {
    setIsLoading(true);
    try {
      await dashboardApi.stopTrading();
      setIsTrading(false);
    } catch (error) {
      console.error('Failed to stop trading:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Settings className="w-5 h-5" />
        Trading Controls
      </h2>
      
      <div className="space-y-6">
        {/* Status Indicator */}
        <div className="flex items-center justify-between">
          <span className="text-gray-300">Trading Status</span>
          <div className={`px-3 py-1 rounded-full ${isTrading ? 'bg-green-900/50 text-green-300' : 'bg-red-900/50 text-red-300'}`}>
            {isTrading ? 'ACTIVE' : 'PAUSED'}
          </div>
        </div>

        {/* Profit Threshold */}
        <div>
          <label className="block text-gray-300 mb-2">
            Profit Threshold: <span className="font-bold">{threshold}</span>
          </label>
          <input
            type="range"
            min="0.0001"
            max="0.01"
            step="0.0001"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>0.01%</span>
            <span>1%</span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleStartTrading}
            disabled={isTrading || isLoading}
            className={`flex-1 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2 ${
              isTrading || isLoading
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            <Play className="w-4 h-4" />
            {isLoading ? 'Starting...' : 'Start Trading'}
          </button>
          
          <button
            onClick={handleStopTrading}
            disabled={!isTrading || isLoading}
            className={`flex-1 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2 ${
              !isTrading || isLoading
                ? 'bg-gray-700 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-700'
            }`}
          >
            <Pause className="w-4 h-4" />
            {isLoading ? 'Stopping...' : 'Stop Trading'}
          </button>
        </div>

        {/* Alert */}
        <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-yellow-300">Trading Notice</p>
              <p className="text-yellow-200/80 text-sm mt-1">
                Ensure proper risk management settings are configured before starting automated trading.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingPanel;
