import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchRisk } from '../../store/slices/riskSlice'
import { websocketService } from '../../services/websocket'

const RiskDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isLoading } = useSelector((state: RootState) => state.risk)

  useEffect(() => {
    dispatch(fetchRisk())

    websocketService.on('risk:update', () => {
      dispatch(fetchRisk())
    })

    const interval = setInterval(() => {
      dispatch(fetchRisk())
    }, 5000)

    return () => {
      clearInterval(interval)
      websocketService.off('risk:update', () => {})
    }
  }, [dispatch])

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading risk metrics...</div>
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">No risk data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Risk Dashboard</h1>
        <p className="text-gray-400 mt-1">Position Management & Risk Metrics</p>
      </div>

      {/* Drawdown & Circuit Breaker */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Drawdown Tracking</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Current</span>
                <span className={`font-bold ${metrics.drawdown.current > -1 ? 'text-green-400' : 'text-red-400'}`}>
                  {(metrics.drawdown.current * 100).toFixed(2)}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${metrics.drawdown.current > -1 ? 'bg-green-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.min(Math.abs(metrics.drawdown.current) * 100, 100)}%` }}
                />
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <p className="text-gray-400">Daily</p>
                <p className="text-white font-semibold">{(metrics.drawdown.daily * 100).toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-gray-400">Weekly</p>
                <p className="text-white font-semibold">{(metrics.drawdown.weekly * 100).toFixed(2)}%</p>
              </div>
              <div>
                <p className="text-gray-400">Monthly</p>
                <p className="text-white font-semibold">{(metrics.drawdown.monthly * 100).toFixed(2)}%</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Circuit Breaker Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Status</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  metrics.circuitBreaker.status === 'active'
                    ? 'bg-green-900 text-green-200'
                    : metrics.circuitBreaker.status === 'triggered'
                    ? 'bg-red-900 text-red-200'
                    : 'bg-yellow-900 text-yellow-200'
                }`}
              >
                {metrics.circuitBreaker.status.toUpperCase()}
              </span>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Daily Loss</span>
                <span className="text-white font-bold">
                  {metrics.circuitBreaker.dailyLoss.toFixed(2)} / {metrics.circuitBreaker.dailyLimit} ETH
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.circuitBreaker.dailyLoss > metrics.circuitBreaker.dailyLimit * 0.8
                      ? 'bg-red-500'
                      : 'bg-yellow-500'
                  }`}
                  style={{
                    width: `${Math.min((metrics.circuitBreaker.dailyLoss / metrics.circuitBreaker.dailyLimit) * 100, 100)}%`,
                  }}
                />
              </div>
            </div>
            {metrics.circuitBreaker.status === 'recovery' && (
              <div>
                <p className="text-gray-400 text-sm mb-2">Recovery Progress</p>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${metrics.circuitBreaker.recoveryProgress * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Concentration Risk */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Concentration Risk Analysis</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-gray-400 text-sm mb-2">Highest Pool</p>
            <p className="text-2xl font-bold text-orange-400">{(metrics.concentration.highestPool * 100).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Average Concentration</p>
            <p className="text-2xl font-bold text-blue-400">{(metrics.concentration.averageConcentration * 100).toFixed(1)}%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Risk Level</p>
            <p
              className={`text-2xl font-bold ${
                metrics.concentration.riskLevel === 'low'
                  ? 'text-green-400'
                  : metrics.concentration.riskLevel === 'medium'
                  ? 'text-yellow-400'
                  : 'text-red-400'
              }`}
            >
              {metrics.concentration.riskLevel.toUpperCase()}
            </p>
          </div>
        </div>
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-gray-400">Concentration vs Limit ({metrics.concentration.limit}%)</span>
            <span className="text-white">{(metrics.concentration.highestPool * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${
                metrics.concentration.highestPool > metrics.concentration.limit
                  ? 'bg-red-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${(metrics.concentration.highestPool / metrics.concentration.limit) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Value at Risk */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Value at Risk (VaR)</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800 rounded p-4">
            <p className="text-gray-400 text-sm mb-2">VaR 95%</p>
            <p className="text-2xl font-bold text-blue-400">{metrics.valueAtRisk.var95.toFixed(2)} ETH</p>
            <p className="text-gray-500 text-xs mt-1">95% confidence</p>
          </div>
          <div className="bg-gray-800 rounded p-4">
            <p className="text-gray-400 text-sm mb-2">VaR 99%</p>
            <p className="text-2xl font-bold text-orange-400">{metrics.valueAtRisk.var99.toFixed(2)} ETH</p>
            <p className="text-gray-500 text-xs mt-1">99% confidence</p>
          </div>
          <div className="bg-gray-800 rounded p-4">
            <p className="text-gray-400 text-sm mb-2">Expected Shortfall</p>
            <p className="text-2xl font-bold text-red-400">{metrics.valueAtRisk.expectedShortfall.toFixed(2)} ETH</p>
            <p className="text-gray-500 text-xs mt-1">Avg loss if exceeded</p>
          </div>
        </div>
      </div>

      {/* Open Positions */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Open Positions</h3>
        {metrics.positions.length === 0 ? (
          <p className="text-gray-400 text-sm">No open positions</p>
        ) : (
          <div className="space-y-2">
            {metrics.positions.map((pos, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-4 flex justify-between items-center">
                <div>
                  <p className="text-white font-semibold">
                    {pos.asset} on {pos.chain}
                  </p>
                  <p className="text-gray-400 text-sm">{pos.amount.toFixed(2)} tokens</p>
                </div>
                <div className="text-right">
                  <p className="text-white font-semibold">${pos.value.toFixed(2)}</p>
                  <p className="text-orange-400 text-sm">{(pos.concentration * 100).toFixed(1)}% concentration</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Slippage Protection */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Slippage Protection</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <p className="text-gray-400 text-sm mb-2">Average Slippage</p>
            <p className="text-2xl font-bold text-blue-400">{(metrics.slippage.average * 100).toFixed(3)}%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Max Slippage</p>
            <p className="text-2xl font-bold text-orange-400">{(metrics.slippage.max * 100).toFixed(3)}%</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Protection Status</p>
            <p className={`text-xl font-bold ${metrics.slippage.protectionActive ? 'text-green-400' : 'text-red-400'}`}>
              {metrics.slippage.protectionActive ? 'ACTIVE' : 'INACTIVE'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RiskDashboard
