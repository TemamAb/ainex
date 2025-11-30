'use client';
import React from 'react';
import { useRealBotStatus } from '../../../hooks/useRealMetrics';

export const SeekerNetwork: React.FC = () => {
  const { botStatus } = useRealBotStatus();

  if (!botStatus) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Bot Fleet Status</h3>
        <div className="text-gray-400">Loading bot status from co-pilot-orchestrator...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Bot Fleet Status</h3>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Seekers:</span>
          <span className={`font-mono ${
            botStatus.seekers.scanning ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {botStatus.seekers.online}/{botStatus.seekers.total} Online
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Relayers:</span>
          <span className={`font-mono ${
            botStatus.relayers.executing ? 'text-green-400' : 'text-yellow-400'
          }`}>
            {botStatus.relayers.online}/{botStatus.relayers.total} Online
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Orchestrator:</span>
          <span className="font-mono text-green-400">
            {botStatus.orchestrator.status} ({botStatus.orchestrator.health}/10)
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Active Strategy:</span>
          <span className="font-mono text-blue-400">
            {botStatus.orchestrator.strategy}
          </span>
        </div>
      </div>
    </div>
  );
};
