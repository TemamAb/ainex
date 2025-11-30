'use client';
import React, { useState } from 'react';
import { MasterHeader } from '../components/Header/MasterHeader';
import { ModeOrchestrator } from '../components/Deployment/ModeOrchestrator';
import { ProviderMatrix } from '../components/Monitoring/FlashLoanHub/ProviderMatrix';
import { SeekerNetwork } from '../components/Monitoring/TriTierFleet/SeekerNetwork';
import { ConfigurationDashboard } from '../components/Admin/ConfigurationDashboard';

export default function AinexV3Dashboard() {
  const [activeTab, setActiveTab] = useState<'monitoring' | 'admin'>('monitoring');
  const [systemStatus, setSystemStatus] = useState<'preflight' | 'simulation' | 'live'>('preflight');

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
              
              {/* AI Optimization Panel */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Ì∑† AI Optimization Engine</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Last Optimization:</span>
                    <span className="font-mono text-green-400">2 minutes ago</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Next Optimization:</span>
                    <span className="font-mono text-blue-400">13 minutes</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Performance Delta:</span>
                    <span className="font-mono text-green-400">+2.4%</span>
                  </div>
                </div>
              </div>
            </div>

            <ProviderMatrix />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Security & MEV Defense */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Ìª°Ô∏è Security & MEV Defense</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Security Score:</span>
                    <span className="font-mono text-green-400">92/100</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Frontrun Attempts:</span>
                    <span className="font-mono text-red-400">3 (blocked)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">MEV Protection:</span>
                    <span className="font-mono text-green-400">Active</span>
                  </div>
                </div>
              </div>
              
              {/* Profit & Performance */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Ì≤∞ Profit & Performance</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Total Profit:</span>
                    <span className="font-mono text-green-400">$124,750.42</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Today's P&L:</span>
                    <span className="font-mono text-green-400">+$3,245.67</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Win Rate:</span>
                    <span className="font-mono text-green-400">78.3%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Trades/Hour:</span>
                    <span className="font-mono text-white">18</span>
                  </div>
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
