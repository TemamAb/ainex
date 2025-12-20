import React from 'react'
import { ProfitMetrics as IProfitMetrics } from '../../types'

interface Props {
  metrics: IProfitMetrics
}

const ProfitMetrics: React.FC<Props> = ({ metrics }) => {
  return (
    <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-6">💰 Profit Metrics</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-green-500/10 border border-green-500/30 rounded p-4">
          <p className="text-sm text-gray-400">Accumulated ETH</p>
          <p className="text-2xl font-bold text-green-400 mt-1">
            {metrics.accumulatedEthVerified.toFixed(4)} ETH
          </p>
          <p className="text-xs text-gray-500 mt-1">Verified</p>
        </div>

        <div className="bg-blue-500/10 border border-blue-500/30 rounded p-4">
          <p className="text-sm text-gray-400">USD Value</p>
          <p className="text-2xl font-bold text-blue-400 mt-1">
            ${metrics.accumulatedUsdVerified.toFixed(2)}
          </p>
          <p className="text-xs text-gray-500 mt-1">@${metrics.ethPrice}/ETH</p>
        </div>

        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded p-4">
          <p className="text-sm text-gray-400">Pending</p>
          <p className="text-2xl font-bold text-yellow-400 mt-1">
            {metrics.accumulatedEthPending.toFixed(4)} ETH
          </p>
          <p className="text-xs text-gray-500 mt-1">Awaiting verification</p>
        </div>

        <div className="bg-purple-500/10 border border-purple-500/30 rounded p-4">
          <p className="text-sm text-gray-400">Active Trades</p>
          <p className="text-2xl font-bold text-purple-400 mt-1">
            {metrics.activeTrades}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {metrics.successfulTrades} successful
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div className="bg-white/5 rounded p-4">
          <p className="text-sm text-gray-400">Threshold</p>
          <p className="text-xl font-bold text-white mt-1">{metrics.thresholdEth} ETH</p>
          <p className="text-xs text-gray-500 mt-1">Auto-transfer trigger</p>
        </div>

        <div className="bg-white/5 rounded p-4">
          <p className="text-sm text-gray-400">Auto-Transfer</p>
          <p className="text-xl font-bold text-white mt-1">
            {metrics.autoTransferEnabled ? '✅ Enabled' : '❌ Disabled'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Status</p>
        </div>

        <div className="bg-white/5 rounded p-4">
          <p className="text-sm text-gray-400">Wallet</p>
          <p className="text-xs font-mono text-white mt-1 truncate">{metrics.targetWallet}</p>
          <p className="text-xs text-gray-500 mt-1">Target address</p>
        </div>
      </div>
    </div>
  )
}

export default ProfitMetrics
