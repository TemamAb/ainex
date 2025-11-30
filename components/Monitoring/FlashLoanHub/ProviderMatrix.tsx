'use client';
import React from 'react';
import { useRealFlashLoanData } from '../../../hooks/useRealMetrics';

export const ProviderMatrix: React.FC = () => {
  const { flashData } = useRealFlashLoanData();

  if (!flashData) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Flash Loan Providers</h3>
        <div className="text-gray-400">Loading real provider data from flash-aggregator...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Flash Loan Providers</h3>
      <div className="grid grid-cols-3 gap-4">
        {flashData.map((provider) => (
          <div key={provider.name} className="bg-gray-700 rounded p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-white font-semibold">{provider.name}</span>
              <span className={`text-sm ${
                provider.utilization < 50 ? 'text-green-400' : 
                provider.utilization < 80 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {provider.utilization}%
              </span>
            </div>
            <div className="text-sm text-gray-300">
              Liquidity: ${(provider.liquidity / 1000000).toFixed(1)}M
            </div>
            <div className="text-sm text-gray-300">
              Health: {provider.health}/10
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
