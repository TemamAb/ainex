'use client';
import React from 'react';

export const ModeOrchestrator: React.FC = () => {
  const [currentMode, setCurrentMode] = React.useState<'preflight' | 'simulation' | 'live'>('preflight');
  const [status, setStatus] = React.useState<string>('System offline');

  const activateSimulationMode = async () => {
    setStatus('PROTOCOL: Activating Simulation Mode...');
    try {
      const response = await fetch('/api/deployment/simulation', { method: 'POST' });
      const result = await response.json();
      
      if (result.success) {
        setCurrentMode('simulation');
        setStatus('SIMULATION MODE ACTIVE: Running on live blockchain + real market data (Dry-fire execution)');
      } else {
        setStatus(`PROTOCOL FAILED: ${result.message}`);
      }
    } catch (error) {
      setStatus(`PROTOCOL VIOLATION: ${error.message}`);
    }
  };

  const activateLiveMode = async () => {
    setStatus('PROTOCOL: Activating Live Mode...');
    
    if (currentMode !== 'simulation') {
      setStatus('PROTOCOL: Simulation Mode must be active and stable before Live Mode');
      return;
    }

    try {
      const response = await fetch('/api/deployment/live', { method: 'POST' });
      const result = await response.json();
      
      if (result.success) {
        setCurrentMode('live');
        setStatus('LIVE MODE ACTIVE: Real execution enabled');
      } else {
        setStatus(`LIVE MODE FAILED: ${result.message}`);
      }
    } catch (error) {
      setStatus(`LIVE MODE ERROR: ${error.message}`);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Deployment Control</h3>
      
      <div className="space-y-4">
        <div className="flex space-x-4">
          <button
            onClick={activateSimulationMode}
            className={`px-4 py-2 rounded font-mono text-sm ${
              currentMode === 'simulation' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            ��� SIMULATION MODE
          </button>
          
          <button
            onClick={activateLiveMode}
            disabled={currentMode !== 'simulation'}
            className={`px-4 py-2 rounded font-mono text-sm ${
              currentMode === 'live'
                ? 'bg-red-600 text-white'
                : currentMode === 'simulation'
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            ⚡ LIVE MODE
          </button>
        </div>

        <div className="p-3 bg-gray-900 rounded">
          <div className="text-sm font-mono text-gray-300">
            STATUS: {status}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            PROTOCOL: Simulation Mode requires live blockchain + real market data
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-xs">
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-green-400 font-semibold">SIMULATION MODE</div>
            <div className="text-gray-400 mt-1">
              • Live Blockchain Connection<br/>
              • Real-time Market Data<br/>
              • Dry-fire Execution<br/>
              • Zero Financial Risk
            </div>
          </div>
          
          <div className="bg-gray-700 p-3 rounded">
            <div className="text-red-400 font-semibold">LIVE MODE</div>
            <div className="text-gray-400 mt-1">
              • Real Transaction Execution<br/>
              • Financial Risk Active<br/>
              • Requires Simulation Validation<br/>
              • Real P&L Impact
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
