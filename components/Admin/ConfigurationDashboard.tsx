'use client';
import React, { useState, useEffect } from 'react';
import { AdminConfigService } from '../../../services/adminConfigService';
import { AdminConfig } from '../../../types/admin';
import { ProfitTargetPanel } from './ProfitTargetPanel';
import { ReinvestmentPanel } from './ReinvestmentPanel';
import { RiskProfilePanel } from './RiskProfilePanel';

export const ConfigurationDashboard: React.FC = () => {
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const adminService = new AdminConfigService();

  useEffect(() => {
    const loadConfig = async () => {
      const loadedConfig = adminService.getCurrentConfig();
      setConfig(loadedConfig);
    };
    loadConfig();
  }, []);

  const handleSave = async () => {
    if (!config) return;
    
    setSaveStatus('saving');
    const success = await adminService.saveConfig(config);
    setSaveStatus(success ? 'success' : 'error');
    
    setTimeout(() => setSaveStatus('idle'), 3000);
  };

  if (!config) {
    return <div className="text-white">Loading configuration...</div>;
  }

  return (
    <div className="admin-configuration space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Admin Configuration</h2>
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className={`px-4 py-2 rounded font-semibold ${
            saveStatus === 'saving' ? 'bg-gray-600 cursor-not-allowed' :
            saveStatus === 'success' ? 'bg-green-600' :
            saveStatus === 'error' ? 'bg-red-600' : 'bg-blue-600 hover:bg-blue-700'
          } text-white`}
        >
          {saveStatus === 'saving' ? 'Saving...' :
           saveStatus === 'success' ? 'Saved!' :
           saveStatus === 'error' ? 'Error!' : 'Save Configuration'}
        </button>
      </div>

      <ProfitTargetPanel 
        config={config} 
        onConfigChange={setConfig} 
      />
      
      <ReinvestmentPanel 
        config={config} 
        onConfigChange={setConfig} 
      />
      
      <RiskProfilePanel 
        config={config} 
        onConfigChange={setConfig} 
      />
    </div>
  );
};
