import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, Zap, CheckCircle, AlertTriangle, Settings, Save, RotateCcw } from 'lucide-react';
import { ProfitTargetSettings, TradeSettings } from '../types';
import { profitTargetService } from '../services/profitTargetService';

interface ProfitTargetPanelProps {
  tradeSettings: TradeSettings;
  onSettingsChange: (settings: TradeSettings) => void;
  currentProfit: {
    hourly: number;
    daily: number;
    weekly: number;
  };
}

const ProfitTargetPanel: React.FC<ProfitTargetPanelProps> = ({
  tradeSettings,
  onSettingsChange,
  currentProfit
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [overrideValues, setOverrideValues] = useState({
    hourly: tradeSettings.profitTarget.override.hourly,
    daily: tradeSettings.profitTarget.override.daily,
    weekly: tradeSettings.profitTarget.override.weekly,
    unit: tradeSettings.profitTarget.override.unit
  });
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    setOverrideValues({
      hourly: tradeSettings.profitTarget.override.hourly,
      daily: tradeSettings.profitTarget.override.daily,
      weekly: tradeSettings.profitTarget.override.weekly,
      unit: tradeSettings.profitTarget.override.unit
    });
  }, [tradeSettings.profitTarget.override]);

  const handleOverrideToggle = () => {
    const newEnabled = !tradeSettings.profitTarget.override.enabled;
    const updatedSettings: TradeSettings = {
      ...tradeSettings,
      profitTarget: {
        ...tradeSettings.profitTarget,
        override: {
          ...tradeSettings.profitTarget.override,
          enabled: newEnabled
        },
        active: newEnabled
          ? tradeSettings.profitTarget.override
          : tradeSettings.profitTarget.optimal
      }
    };
    onSettingsChange(updatedSettings);
  };

  const handleOverrideChange = (field: keyof typeof overrideValues, value: string) => {
    const newOverrideValues = { ...overrideValues, [field]: value };
    setOverrideValues(newOverrideValues);

    // Validate in real-time
    const validation = profitTargetService.validateOverrideTargets({
      enabled: true,
      ...newOverrideValues
    });
    setValidationErrors(validation.warnings);
  };

  const handleSaveOverride = () => {
    const validation = profitTargetService.validateOverrideTargets({
      enabled: true,
      ...overrideValues
    });

    if (!validation.isValid) {
      setValidationErrors(validation.warnings);
      return;
    }

    const updatedSettings: TradeSettings = {
      ...tradeSettings,
      profitTarget: {
        ...tradeSettings.profitTarget,
        override: {
          enabled: true,
          ...overrideValues
        },
        active: overrideValues
      }
    };

    onSettingsChange(updatedSettings);
    setIsEditing(false);
    setValidationErrors([]);
  };

  const handleResetToOptimal = () => {
    const updatedSettings: TradeSettings = {
      ...tradeSettings,
      profitTarget: {
        ...tradeSettings.profitTarget,
        override: {
          enabled: false,
          ...tradeSettings.profitTarget.optimal
        },
        active: tradeSettings.profitTarget.optimal
      }
    };
    onSettingsChange(updatedSettings);
    setIsEditing(false);
    setValidationErrors([]);
  };

  const targetStatus = profitTargetService.getTargetStatus(
    currentProfit,
    tradeSettings.profitTarget.active
  );

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700 pb-4">
        <div className="flex items-center gap-3">
          <Target className="w-6 h-6 text-green-400" />
          <h2 className="text-xl font-bold text-white">Profit Target Management</h2>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-bold ${
          tradeSettings.profitTarget.override.enabled
            ? 'bg-yellow-900/30 border border-yellow-500/50 text-yellow-400'
            : 'bg-blue-900/30 border border-blue-500/50 text-blue-400'
        }`}>
          {tradeSettings.profitTarget.override.enabled ? 'Override Active' : 'AI Optimized'}
        </div>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'Hourly', key: 'hourly' as const, current: currentProfit.hourly, target: parseFloat(tradeSettings.profitTarget.active.hourly) },
          { label: 'Daily', key: 'daily' as const, current: currentProfit.daily, target: parseFloat(tradeSettings.profitTarget.active.daily) },
          { label: 'Weekly', key: 'weekly' as const, current: currentProfit.weekly, target: parseFloat(tradeSettings.profitTarget.active.weekly) }
        ].map(({ label, key, current, target }) => (
          <div key={key} className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-400">{label} Target</span>
              {targetStatus[key].achieved ? (
                <CheckCircle className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingUp className="w-4 h-4 text-blue-400" />
              )}
            </div>
            <div className="text-lg font-bold text-white">
              {current.toFixed(key === 'weekly' ? 2 : 4)} / {target.toFixed(key === 'weekly' ? 2 : 4)} ETH
            </div>
            <div className="text-xs text-slate-500 mt-1">
              {targetStatus[key].percentage.toFixed(1)}% complete
            </div>
          </div>
        ))}
      </div>

      {/* AI Optimal Targets */}
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-blue-400">AI Optimal Targets</h3>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-slate-500">Hourly</div>
            <div className="text-lg font-bold text-blue-400">{tradeSettings.profitTarget.optimal.hourly} ETH</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Daily</div>
            <div className="text-lg font-bold text-blue-400">{tradeSettings.profitTarget.optimal.daily} ETH</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Weekly</div>
            <div className="text-lg font-bold text-blue-400">{tradeSettings.profitTarget.optimal.weekly} ETH</div>
          </div>
        </div>
      </div>

      {/* Active Targets */}
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white">Active Targets</h3>
          {tradeSettings.profitTarget.override.enabled && (
            <span className="text-xs bg-yellow-900/30 text-yellow-400 px-2 py-1 rounded">Override</span>
          )}
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-slate-500">Hourly</div>
            <div className="text-lg font-bold text-white">{tradeSettings.profitTarget.active.hourly} ETH</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Daily</div>
            <div className="text-lg font-bold text-white">{tradeSettings.profitTarget.active.daily} ETH</div>
          </div>
          <div>
            <div className="text-xs text-slate-500">Weekly</div>
            <div className="text-lg font-bold text-white">{tradeSettings.profitTarget.active.weekly} ETH</div>
          </div>
        </div>
      </div>

      {/* Dynamic Adjustment Factors */}
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-4">Dynamic Adjustment Factors</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xs text-slate-500">Market Volatility</div>
            <div className="text-lg font-bold text-purple-400">
              {(tradeSettings.profitTarget.dynamicAdjustment.marketVolatility * 100).toFixed(0)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500">Opportunity Density</div>
            <div className="text-lg font-bold text-blue-400">
              {(tradeSettings.profitTarget.dynamicAdjustment.opportunityDensity * 100).toFixed(0)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500">AI Confidence</div>
            <div className="text-lg font-bold text-green-400">
              {(tradeSettings.profitTarget.dynamicAdjustment.aiConfidence * 100).toFixed(0)}%
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-slate-500">Risk Score</div>
            <div className="text-lg font-bold text-red-400">
              {(tradeSettings.profitTarget.dynamicAdjustment.riskScore * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* User Override Section */}
      <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-yellow-400" />
            <h3 className="font-semibold text-yellow-400">User Override</h3>
          </div>
          <button
            onClick={handleOverrideToggle}
            className={`px-4 py-2 rounded-lg font-bold text-sm transition-all ${
              tradeSettings.profitTarget.override.enabled
                ? 'bg-yellow-600 hover:bg-yellow-500 text-white'
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            }`}
          >
            {tradeSettings.profitTarget.override.enabled ? 'Disable Override' : 'Enable Override'}
          </button>
        </div>

        {tradeSettings.profitTarget.override.enabled && (
          <div className="space-y-4">
            {!isEditing ? (
              <div className="flex justify-center">
                <button
                  onClick={() => setIsEditing(true)}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-bold transition-all"
                >
                  Edit Override Values
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">Hourly Target (ETH)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={overrideValues.hourly}
                      onChange={(e) => handleOverrideChange('hourly', e.target.value)}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">Daily Target (ETH)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={overrideValues.daily}
                      onChange={(e) => handleOverrideChange('daily', e.target.value)}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">Weekly Target (ETH)</label>
                    <input
                      type="number"
                      step="1"
                      value={overrideValues.weekly}
                      onChange={(e) => handleOverrideChange('weekly', e.target.value)}
                      className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
                    />
                  </div>
                </div>

                {validationErrors.length > 0 && (
                  <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                      <span className="text-red-400 font-semibold">Validation Warnings</span>
                    </div>
                    <ul className="text-sm text-red-300 space-y-1">
                      {validationErrors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex justify-between">
                  <button
                    onClick={handleResetToOptimal}
                    className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-slate-300 px-4 py-2 rounded-lg font-bold transition-all"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset to AI Optimal
                  </button>
                  <button
                    onClick={handleSaveOverride}
                    disabled={validationErrors.length > 0}
                    className={`flex items-center gap-2 px-6 py-2 rounded-lg font-bold transition-all ${
                      validationErrors.length > 0
                        ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                        : 'bg-green-600 hover:bg-green-500 text-white'
                    }`}
                  >
                    <Save className="w-4 h-4" />
                    Save Override
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfitTargetPanel;
