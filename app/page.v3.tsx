'use client';
import React, { useState } from 'react';
import { MasterHeader } from '../components/Header/MasterHeader';
import { ModeOrchestrator } from '../components/Deployment/ModeOrchestrator';
import { ProviderMatrix } from '../components/Monitoring/FlashLoanHub/ProviderMatrix';
import { SeekerNetwork } from '../components/Monitoring/TriTierFleet/SeekerNetwork';
import { ConfigurationDashboard } from '../components/Admin/ConfigurationDashboard';

export default function AinexV3Dashboard() {
  const [activeTab, setActiveTab] = useState<'monitoring' | 'admin'>('monitoring');

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <MasterHeader />
      
      {/* Navigation Tabs */}
      <div className="border-b border-gray-700">
        <div className="container mx-auto px-6">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('monitoring')}
              className={`py-4 px-2 border-b-2 font-semibold ${
                activeTab === 'monitoring'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              Ì≥ä Live Monitoring
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`py-4 px-2 border-b-2 font-semibold ${
                activeTab === 'admin'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              ‚öôÔ∏è Admin Configuration
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto p-6">
        {activeTab === 'monitoring' ? (
          <div className="space-y-6">
            <ModeOrchestrator />
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SeekerNetwork />
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">AI Optimization Engine</h3>
                <div className="text-gray-400">
                  Connecting to AIOptimizer.ts...
                </div>
              </div>
            </div>

            <ProviderMatrix />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Security & MEV Defense</h3>
                <div className="text-gray-400">
                  Security monitoring initializing...
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Profit & Performance</h3>
                <div className="text-gray-400">
                  Real-time profit tracking active...
                </div>
              </div>
            </div>
          </div>
        ) : (
          <ConfigurationDashboard />
        )}
      </div>
    </div>
  );
}
