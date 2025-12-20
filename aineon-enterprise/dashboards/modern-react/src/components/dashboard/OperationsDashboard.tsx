import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchOperations } from '../../store/slices/operationsSlice'
import { websocketService } from '../../services/websocket'

const OperationsDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isLoading } = useSelector((state: RootState) => state.operations)

  useEffect(() => {
    dispatch(fetchOperations())

    websocketService.on('operations:update', () => {
      dispatch(fetchOperations())
    })

    const interval = setInterval(() => {
      dispatch(fetchOperations())
    }, 5000)

    return () => {
      clearInterval(interval)
      websocketService.off('operations:update', () => {})
    }
  }, [dispatch])

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading operations data...</div>
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">No operations data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Operations Dashboard</h1>
        <p className="text-gray-400 mt-1">Infrastructure Health & Real-time Monitoring</p>
      </div>

      {/* RPC Status */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">RPC Provider Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {metrics.rpc.map((provider, idx) => (
            <div key={idx} className="bg-gray-800 rounded p-4">
              <div className="flex items-center mb-2">
                <div
                  className={`w-2 h-2 rounded-full mr-2 ${
                    provider.status === 'healthy'
                      ? 'bg-green-500'
                      : provider.status === 'degraded'
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-white font-semibold">{provider.provider}</span>
              </div>
              <div className="space-y-2 text-sm">
                <p className="text-gray-400">
                  Latency: <span className="text-blue-400">{provider.latency}ms</span>
                </p>
                <p className="text-gray-400">
                  Uptime: <span className="text-green-400">{(provider.uptime * 100).toFixed(1)}%</span>
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Paymaster Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Paymaster Status</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Status</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  metrics.paymaster.status === 'active'
                    ? 'bg-green-900 text-green-200'
                    : 'bg-red-900 text-red-200'
                }`}
              >
                {metrics.paymaster.status.toUpperCase()}
              </span>
            </div>
            <div>
              <p className="text-gray-400 mb-2">Balance: {metrics.paymaster.balance.toFixed(2)} ETH</p>
              <p className="text-gray-400 mb-2">Cost Today: {metrics.paymaster.costToday.toFixed(3)} ETH</p>
              <p className="text-gray-400">Sponsor Rate: {(metrics.paymaster.sponsorRate * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>

        {/* Gas Optimization */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Gas Optimization</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Current Price</span>
                <span className="text-white font-bold">{metrics.gas.currentPrice} Gwei</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Predicted</span>
                <span className="text-white font-bold">{metrics.gas.predicted} Gwei</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Trend</span>
              <span
                className={`text-lg font-bold ${
                  metrics.gas.trend === 'up'
                    ? 'text-red-400'
                    : metrics.gas.trend === 'down'
                    ? 'text-green-400'
                    : 'text-gray-400'
                }`}
              >
                {metrics.gas.trend === 'up' ? '↑' : metrics.gas.trend === 'down' ? '↓' : '→'}
              </span>
            </div>
            <div>
              <p className="text-gray-400">Daily Savings: {metrics.gas.savings.toFixed(2)} ETH</p>
            </div>
          </div>
        </div>
      </div>

      {/* Bundle Metrics */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Bundle Analytics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm mb-2">Bundles Created</p>
            <p className="text-3xl font-bold text-blue-400">{metrics.bundles.created}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Successful</p>
            <p className="text-3xl font-bold text-green-400">{metrics.bundles.successful}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Failed</p>
            <p className="text-3xl font-bold text-red-400">{metrics.bundles.failed}</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Avg Time</p>
            <p className="text-3xl font-bold text-yellow-400">{metrics.bundles.avgTime.toFixed(0)}ms</p>
          </div>
        </div>
      </div>

      {/* Error Log */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Errors (Last 10)</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {metrics.errors.length === 0 ? (
            <p className="text-gray-400 text-sm">No errors detected</p>
          ) : (
            metrics.errors.slice(0, 10).map((error, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-3 border-l-4 border-red-500">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-white font-semibold text-sm">{error.component}</span>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      error.severity === 'high'
                        ? 'bg-red-900 text-red-200'
                        : error.severity === 'medium'
                        ? 'bg-yellow-900 text-yellow-200'
                        : 'bg-gray-700 text-gray-200'
                    }`}
                  >
                    {error.severity}
                  </span>
                </div>
                <p className="text-gray-400 text-xs mb-1">{error.message}</p>
                <p className="text-gray-500 text-xs">{new Date(error.timestamp).toLocaleString()}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

export default OperationsDashboard
