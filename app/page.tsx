'use client';
import React, { useState } from 'react';

export default function AinexV3Dashboard() {
  const [activeTab, setActiveTab] = useState('monitoring');
  const [systemStatus, setSystemStatus] = useState('preflight');

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="flex justify-between items-center p-4 bg-gray-900 border-b border-gray-700">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-mono text-green-400">AInex V3 ENGINE</span>
          </div>
          <div className="text-sm text-gray-400">Updated: Just now</div>
        </div>

        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-4">
            <button className="px-3 py-1 rounded text-sm font-mono bg-blue-600 text-white">
              USD
            </button>
            <button className="px-3 py-1 rounded text-sm font-mono bg-gray-700 text-gray-300">
              ETH
            </button>
          </div>

          <div className="flex items-center space-x-6">
            <div className="text-center">
              <div className="text-sm text-gray-400">Total Profit</div>
              <div className="text-lg font-mono text-green-400">
                $124,750.42
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-400">Today</div>
              <div className="text-md font-mono text-green-400">
                +$3,245.67
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-400">Win Rate</div>
            <div className="text-md font-mono text-green-400">
              78.3%
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
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
              Live Monitoring
            </button>
            <button
              onClick={() => setActiveTab('admin')}
              className={`py-4 px-2 border-b-2 font-semibold ${
                activeTab === 'admin'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300'
              }`}
            >
              Admin Configuration
            </button>
          </div>
        </div>
      </div>

      <div className="container mx-auto p-6">
        {activeTab === 'monitoring' ? (
          <div className="space-y-6">
            {/* Deployment Control */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Deployment Control</h3>
              <div className="flex space-x-4">
                <button className="px-4 py-2 bg-blue-600 text-white rounded font-mono text-sm">
                  Simulation Mode
                </button>
                <button className="px-4 py-2 bg-gray-600 text-gray-400 rounded font-mono text-sm cursor-not-allowed">
                  Live Mode
                </button>
              </div>
              <div className="mt-3 p-3 bg-gray-900 rounded">
                <div className="text-sm font-mono text-gray-300">
                  STATUS: System ready for simulation
                </div>
              </div>
            </div>

            {/* Bot Fleet Status */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Bot Fleet Status</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Seekers:</span>
                    <span className="font-mono text-green-400">25/25 Online</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Relayers:</span>
                    <span className="font-mono text-green-400">15/15 Online</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Orchestrator:</span>
                    <span className="font-mono text-green-400">Active</span>
                  </div>
                </div>
              </div>

              {/* AI Optimization */}
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">AI Optimization Engine</h3>
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

            {/* Flash Loan Providers */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Flash Loan Providers</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-700 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white font-semibold">AAVE v3</span>
                    <span className="text-sm text-green-400">65%</span>
                  </div>
                  <div className="text-sm text-gray-300">Liquidity: $45.0M</div>
                </div>
                <div className="bg-gray-700 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white font-semibold">Balancer</span>
                    <span className="text-sm text-yellow-400">42%</span>
                  </div>
                  <div className="text-sm text-gray-300">Liquidity: $28.0M</div>
                </div>
                <div className="bg-gray-700 rounded p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-white font-semibold">Uniswap</span>
                    <span className="text-sm text-green-400">38%</span>
                  </div>
                  <div className="text-sm text-gray-300">Liquidity: $15.0M</div>
                </div>
              </div>
            </div>

            {/* Security & Profit */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Security & MEV Defense</h3>
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
              
              <div className="bg-gray-800 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Profit & Performance</h3>
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
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Admin Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-gray-300 mb-2">Profit Target Mode</label>
                <select className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white">
                  <option>Adaptive (AI-Driven)</option>
                  <option>Manual (Fixed)</option>
                </select>
              </div>
              <div>
                <label className="block text-gray-300 mb-2">Reinvestment Rate: 70%</label>
                <input type="range" min="0" max="100" value="70" className="w-full" />
              </div>
              <div>
                <label className="block text-gray-300 mb-2">Risk Level: 6/10</label>
                <input type="range" min="1" max="10" value="6" className="w-full" />
              </div>
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Save Configuration
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
