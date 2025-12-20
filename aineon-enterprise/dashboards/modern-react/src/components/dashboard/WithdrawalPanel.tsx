import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import {
  fetchWithdrawalMetrics,
  executeManualWithdrawal,
  updateAutoWithdrawalConfig,
  getWithdrawalHistory,
  clearError,
  clearSuccessMessage,
} from '../../store/slices/withdrawalSlice'
import { websocketService } from '../../services/websocket'

const WithdrawalPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isWithdrawing, error, successMessage } = useSelector(
    (state: RootState) => state.withdrawal
  )

  const [withdrawalAmount, setWithdrawalAmount] = useState('')
  const [toAddress, setToAddress] = useState('')
  const [autoThreshold, setAutoThreshold] = useState('')
  const [activeTab, setActiveTab] = useState<'manual' | 'auto' | 'history'>('manual')

  useEffect(() => {
    dispatch(fetchWithdrawalMetrics())
    dispatch(getWithdrawalHistory(20))

    websocketService.on('profit:update', () => {
      dispatch(fetchWithdrawalMetrics())
    })

    const interval = setInterval(() => {
      dispatch(fetchWithdrawalMetrics())
    }, 10000)

    return () => {
      clearInterval(interval)
      websocketService.off('profit:update', () => {})
    }
  }, [dispatch])

  const handleManualWithdrawal = async () => {
    if (!withdrawalAmount || !toAddress) {
      alert('Please fill in all fields')
      return
    }

    const amount = parseFloat(withdrawalAmount)
    if (amount <= 0 || amount > (metrics?.availableBalance || 0)) {
      alert('Invalid withdrawal amount')
      return
    }

    await dispatch(
      executeManualWithdrawal({
        amount,
        toAddress,
      })
    )

    setWithdrawalAmount('')
    setToAddress('')

    setTimeout(() => {
      dispatch(clearSuccessMessage())
    }, 5000)
  }

  const handleAutoConfig = async () => {
    const threshold = parseFloat(autoThreshold)
    if (threshold <= 0) {
      alert('Invalid threshold')
      return
    }

    await dispatch(
      updateAutoWithdrawalConfig({
        enabled: true,
        threshold,
      })
    )

    setAutoThreshold('')

    setTimeout(() => {
      dispatch(clearSuccessMessage())
    }, 5000)
  }

  const handleDisableAuto = async () => {
    await dispatch(
      updateAutoWithdrawalConfig({
        enabled: false,
        threshold: metrics?.autoThreshold || 0,
      })
    )

    setTimeout(() => {
      dispatch(clearSuccessMessage())
    }, 5000)
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">Loading withdrawal data...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">Profit Withdrawal</h2>
        <p className="text-gray-400">Manage manual and automatic profit withdrawals</p>
      </div>

      {/* Alert Messages */}
      {error && (
        <div className="bg-red-900 border border-red-700 rounded-lg p-4">
          <p className="text-red-200">❌ Error: {error}</p>
          <button
            onClick={() => dispatch(clearError())}
            className="text-red-300 text-sm mt-2 hover:text-red-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-900 border border-green-700 rounded-lg p-4">
          <p className="text-green-200">✅ {successMessage}</p>
        </div>
      )}

      {/* Balance Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Available Balance</p>
          <p className="text-3xl font-bold text-green-400">{metrics.availableBalance.toFixed(2)} ETH</p>
          <p className="text-gray-500 text-xs mt-1">Ready to withdraw</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Pending Withdrawals</p>
          <p className="text-3xl font-bold text-yellow-400">{metrics.pendingWithdrawals.toFixed(2)} ETH</p>
          <p className="text-gray-500 text-xs mt-1">In progress</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total Withdrawn</p>
          <p className="text-3xl font-bold text-blue-400">{metrics.totalWithdrawn.toFixed(2)} ETH</p>
          <p className="text-gray-500 text-xs mt-1">All time</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg">
        <div className="flex border-b border-gray-800">
          {(['manual', 'auto', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-4 px-6 font-semibold transition ${
                activeTab === tab
                  ? 'text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab === 'manual' && '💳 Manual Withdrawal'}
              {tab === 'auto' && '⚙️ Auto Withdrawal'}
              {tab === 'history' && '📋 History'}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Manual Withdrawal */}
          {activeTab === 'manual' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white mb-4">Manual Withdrawal</h3>

              <div>
                <label className="block text-gray-400 text-sm mb-2">Withdrawal Amount (ETH)</label>
                <input
                  type="number"
                  value={withdrawalAmount}
                  onChange={(e) => setWithdrawalAmount(e.target.value)}
                  placeholder="0.00"
                  step="0.01"
                  min="0"
                  max={metrics.availableBalance}
                  disabled={isWithdrawing}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 disabled:opacity-50"
                />
                <p className="text-gray-500 text-xs mt-1">Available: {metrics.availableBalance.toFixed(2)} ETH</p>
              </div>

              <div>
                <label className="block text-gray-400 text-sm mb-2">Recipient Address</label>
                <input
                  type="text"
                  value={toAddress}
                  onChange={(e) => setToAddress(e.target.value)}
                  placeholder="0x..."
                  disabled={isWithdrawing}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 disabled:opacity-50"
                />
              </div>

              <button
                onClick={handleManualWithdrawal}
                disabled={isWithdrawing || !withdrawalAmount || !toAddress}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition"
              >
                {isWithdrawing ? 'Processing...' : 'Execute Withdrawal'}
              </button>

              <div className="bg-gray-800 rounded p-4 text-sm text-gray-400">
                <p className="mb-2">⚠️ Manual Withdrawal Notes:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Amount must be within available balance</li>
                  <li>Address must be valid Ethereum address</li>
                  <li>Withdrawal will be processed immediately</li>
                  <li>Transaction will appear on Etherscan</li>
                </ul>
              </div>
            </div>
          )}

          {/* Auto Withdrawal */}
          {activeTab === 'auto' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white mb-4">Automatic Withdrawal</h3>

              <div className="bg-gray-800 rounded p-4 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white">Auto Withdrawal Status</span>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      metrics.autoEnabled
                        ? 'bg-green-900 text-green-200'
                        : 'bg-gray-700 text-gray-300'
                    }`}
                  >
                    {metrics.autoEnabled ? 'ENABLED' : 'DISABLED'}
                  </span>
                </div>

                {metrics.autoEnabled && (
                  <div>
                    <p className="text-gray-400 text-sm">Threshold: {metrics.autoThreshold.toFixed(2)} ETH</p>
                    <p className="text-gray-500 text-xs mt-1">
                      Withdrawals trigger automatically when profit exceeds this amount
                    </p>
                  </div>
                )}
              </div>

              {!metrics.autoEnabled ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-gray-400 text-sm mb-2">Set Withdrawal Threshold (ETH)</label>
                    <input
                      type="number"
                      value={autoThreshold}
                      onChange={(e) => setAutoThreshold(e.target.value)}
                      placeholder="e.g., 5.00"
                      step="0.01"
                      min="0.01"
                      disabled={isWithdrawing}
                      className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 disabled:opacity-50"
                    />
                    <p className="text-gray-500 text-xs mt-1">Withdrawal will trigger when profit exceeds this amount</p>
                  </div>

                  <button
                    onClick={handleAutoConfig}
                    disabled={isWithdrawing || !autoThreshold}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition"
                  >
                    {isWithdrawing ? 'Configuring...' : 'Enable Auto Withdrawal'}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleDisableAuto}
                  disabled={isWithdrawing}
                  className="w-full bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-bold py-2 px-4 rounded transition"
                >
                  {isWithdrawing ? 'Processing...' : 'Disable Auto Withdrawal'}
                </button>
              )}

              <div className="bg-gray-800 rounded p-4 text-sm text-gray-400">
                <p className="mb-2">📊 Auto Withdrawal Features:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Automatically withdraws when threshold is reached</li>
                  <li>Runs continuously 24/7</li>
                  <li>Sends to configured withdrawal address</li>
                  <li>No manual intervention required</li>
                  <li>Can be disabled anytime</li>
                </ul>
              </div>

              <div className="bg-gray-800 rounded p-4 text-sm text-gray-400">
                <p className="mb-2">ℹ️ Auto Withdrawal Stats:</p>
                <div className="space-y-1">
                  <p>Daily Withdrawn: {metrics.stats.dailyWithdrawn.toFixed(2)} ETH</p>
                  <p>Weekly Withdrawn: {metrics.stats.weeklyWithdrawn.toFixed(2)} ETH</p>
                  <p>Monthly Withdrawn: {metrics.stats.monthlyWithdrawn.toFixed(2)} ETH</p>
                  <p>Success Rate: {(metrics.stats.successRate * 100).toFixed(1)}%</p>
                </div>
              </div>
            </div>
          )}

          {/* History */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-white mb-4">Withdrawal History</h3>

              {metrics.history.length === 0 ? (
                <p className="text-gray-400 text-sm">No withdrawal history</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {metrics.history.map((tx, idx) => (
                    <div key={idx} className="bg-gray-800 rounded p-4 border-l-4 border-blue-500">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="text-white font-semibold">{tx.amount.toFixed(4)} ETH</p>
                          <p className="text-gray-400 text-xs">To: {tx.to.slice(0, 10)}...{tx.to.slice(-8)}</p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded font-semibold ${
                            tx.status === 'completed'
                              ? 'bg-green-900 text-green-200'
                              : tx.status === 'pending'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-red-900 text-red-200'
                          }`}
                        >
                          {tx.status.toUpperCase()}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <p className="text-gray-500 text-xs">{new Date(tx.timestamp).toLocaleString()}</p>
                        {tx.txHash && (
                          <a
                            href={`https://etherscan.io/tx/${tx.txHash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-400 hover:text-blue-300 text-xs"
                          >
                            View on Etherscan
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default WithdrawalPanel
