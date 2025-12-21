import React, { useState, useEffect } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';

const EnhancedHeader = ({ 
  totalProfit, 
  currency, 
  onCurrencyToggle, 
  refreshRate, 
  onRefreshRateChange,
  lifetimeProfit = 314824.48 // Current total since deployment
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const refreshRates = [
    { value: 1000, label: '1 second' },
    { value: 2000, label: '2 seconds' },
    { value: 3000, label: '3 seconds' },
    { value: 5000, label: '5 seconds' },
    { value: 10000, label: '10 seconds' }
  ];

  const formatCurrency = (amount, curr = currency) => {
    if (curr === 'ETH') {
      return `${amount.toFixed(4)} ETH`;
    }
    return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatLifetimeProfit = (amount, curr = currency) => {
    if (curr === 'ETH') {
      return `${amount.toFixed(2)} ETH`;
    }
    return `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <header className="bg-gray-900 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        
        {/* Left Side - Logo & Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Aineon Master Dashboard
              </h1>
              <p className="text-gray-400 text-sm">Enterprise Trading & Analytics Platform</p>
            </div>
          </div>
        </div>

        {/* Center - Live Status & Time */}
        <div className="flex items-center space-x-6">
          <div className="text-center">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-sm font-medium">LIVE SYSTEM</span>
            </div>
            <p className="text-gray-400 text-xs mt-1">
              {currentTime.toLocaleTimeString('en-US', { 
                timeZone: 'UTC',
                hour12: false 
              })} UTC
            </p>
          </div>
        </div>

        {/* Right Side - Controls & Metrics */}
        <div className="flex items-center space-x-6">
          
          {/* Lifetime Profit Display */}
          <div className="text-right">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Lifetime Profit</p>
            <p className="text-green-400 text-lg font-bold">
              {formatLifetimeProfit(lifetimeProfit)}
            </p>
          </div>

          {/* Current Profit Display */}
          <div className="text-right border-l border-gray-700 pl-6">
            <p className="text-gray-400 text-xs uppercase tracking-wider">Current Profit</p>
            <p className="text-blue-400 text-lg font-bold">
              {formatCurrency(totalProfit)}
            </p>
          </div>

          {/* Currency Toggle */}
          <div className="border-l border-gray-700 pl-6">
            <button
              onClick={onCurrencyToggle}
              className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors border border-gray-600"
            >
              {currency}
            </button>
          </div>

          {/* Refresh Rate Control */}
          <div className="relative border-l border-gray-700 pl-6">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center space-x-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg font-medium transition-colors border border-gray-600"
            >
              <span>Refresh: {refreshRates.find(r => r.value === refreshRate)?.label || '5 seconds'}</span>
              <ChevronDownIcon className="h-4 w-4" />
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-40 bg-gray-800 rounded-lg shadow-lg border border-gray-600 z-50">
                {refreshRates.map((rate) => (
                  <button
                    key={rate.value}
                    onClick={() => {
                      onRefreshRateChange(rate.value);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors first:rounded-t-lg last:rounded-b-lg ${
                      refreshRate === rate.value ? 'bg-blue-600 text-white' : 'text-gray-300'
                    }`}
                  >
                    {rate.label}
                  </button>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Click outside to close dropdown */}
      {dropdownOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setDropdownOpen(false)}
        ></div>
      )}
    </header>
  );
};

export default EnhancedHeader;