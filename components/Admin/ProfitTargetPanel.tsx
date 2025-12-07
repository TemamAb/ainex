'use client';
import React from 'react';
import { AdminConfig } from '../../../types/admin';

interface ProfitTargetPanelProps {
  config: AdminConfig;
  onConfigChange: (config: AdminConfig) => void;
}

export const ProfitTargetPanel: React.FC<ProfitTargetPanelProps> = ({ config, onConfigChange }) => {
  return (
    <div className="config-panel bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">ï¿½ï¿½ Profit Target Settings</h3>
      
      <div className="mode-selection space-y-3 mb-4">
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="radio"
            value="adaptive"
            checked={config.profitTarget.mode === 'adaptive'}
            onChange={(e) => onConfigChange({
              ...config,
              profitTarget: { ...config.profitTarget, mode: e.target.value as 'adaptive' | 'manual' }
            })}
            className="text-blue-600"
          />
          <span className="text-white">í·  Adaptive Target (AI-Driven)</span>
        </label>
        
        <label className="flex items-center space-x-3 cursor-pointer">
          <input
            type="radio"
            value="manual"
            checked={config.profitTarget.mode === 'manual'}
            onChange={(e) => onConfigChange({
              ...config,
              profitTarget: { ...config.profitTarget, mode: e.target.value as 'adaptive' | 'manual' }
            })}
            className="text-blue-600"
          />
          <span className="text-white">í¾¯ Manual Target (Fixed)</span>
        </label>
      </div>

      {config.profitTarget.mode === 'adaptive' && (
        <div className="adaptive-settings space-y-4">
          <div className="setting-group">
            <label className="block text-gray-300 mb-2">Base Profit Threshold (%)</label>
            <input
              type="number"
              step="0.01"
              min="0.1"
              max="5.0"
              value={config.profitTarget.adaptiveSettings.baseThreshold}
              onChange={(e) => onConfigChange({
                ...config,
                profitTarget: {
                  ...config.profitTarget,
                  adaptiveSettings: {
                    ...config.profitTarget.adaptiveSettings,
                    baseThreshold: parseFloat(e.target.value)
                  }
                }
              })}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
            <span className="text-sm text-gray-400">Minimum profit percentage before execution</span>
          </div>

          <div className="setting-group">
            <label className="block text-gray-300 mb-2">Market Condition Multiplier</label>
            <input
              type="number"
              step="0.1"
              min="0.5"
              max="3.0"
              value={config.profitTarget.adaptiveSettings.marketConditionMultiplier}
              onChange={(e) => onConfigChange({
                ...config,
                profitTarget: {
                  ...config.profitTarget,
                  adaptiveSettings: {
                    ...config.profitTarget.adaptiveSettings,
                    marketConditionMultiplier: parseFloat(e.target.value)
                  }
                }
              })}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
            <span className="text-sm text-gray-400">Adjust threshold based on market volatility (1.0 = neutral)</span>
          </div>
        </div>
      )}

      {config.profitTarget.mode === 'manual' && (
        <div className="manual-settings space-y-4">
          <div className="setting-group">
            <label className="block text-gray-300 mb-2">Fixed Profit Threshold (%)</label>
            <input
              type="number"
              step="0.05"
              min="0.1"
              max="5.0"
              value={config.profitTarget.manualSettings.fixedThreshold}
              onChange={(e) => onConfigChange({
                ...config,
                profitTarget: {
                  ...config.profitTarget,
                  manualSettings: {
                    ...config.profitTarget.manualSettings,
                    fixedThreshold: parseFloat(e.target.value)
                  }
                }
              })}
              className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>

          <div className="setting-group">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={config.profitTarget.manualSettings.overrideAI}
                onChange={(e) => onConfigChange({
                  ...config,
                  profitTarget: {
                    ...config.profitTarget,
                    manualSettings: {
                      ...config.profitTarget.manualSettings,
                      overrideAI: e.target.checked
                    }
                  }
                })}
                className="text-blue-600"
              />
              <span className="text-white">Override AI Recommendations</span>
            </label>
            <span className="text-sm text-gray-400">Force manual threshold even when AI suggests different values</span>
          </div>
        </div>
      )}
    </div>
  );
};
