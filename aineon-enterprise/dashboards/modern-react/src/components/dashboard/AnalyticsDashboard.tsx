import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchAnalytics } from '../../store/slices/analyticsSlice'
import { websocketService } from '../../services/websocket'

const AnalyticsDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isLoading } = useSelector((state: RootState) => state.analytics)

  useEffect(() => {
    dispatch(fetchAnalytics())
    
    // Subscribe to WebSocket updates
    websocketService.on('analytics:update', (data) => {
      dispatch(fetchAnalytics())
    })

    // Poll every 5 seconds
    const interval = setInterval(() => {
      dispatch(fetchAnalytics())
    }, 5000)

    return () => {
      clearInterval(interval)
      websocketService.off('analytics:update', () => {})
    }
  }, [dispatch])

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading analytics...</div>
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">No analytics data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics Dashboard</h1>
        <p className="text-gray-400 mt-1">AI/ML Intelligence & Performance Metrics</p>
      </div>

      {/* Deep RL Accuracy */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Deep RL Accuracy</h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Current Accuracy</span>
                <span className="text-green-400 font-bold">{(metrics.deepRL.accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${metrics.deepRL.accuracy * 100}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Confidence Score: {(metrics.deepRL.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>

        {/* Market Regime */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Market Regime</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Current</span>
              <span className="px-3 py-1 bg-blue-900 text-blue-200 rounded-full text-sm font-semibold">
                {metrics.marketRegime.type.toUpperCase()}
              </span>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Volatility</span>
                <span className="text-yellow-400">{(metrics.marketRegime.volatility * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className="bg-yellow-500 h-2 rounded-full"
                  style={{ width: `${metrics.marketRegime.volatility * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Transformer Predictor */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Profit Prediction</p>
          <p className="text-2xl font-bold text-green-400">{metrics.transformer.profitPrediction.toFixed(2)} ETH</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Opportunity Score</p>
          <p className="text-2xl font-bold text-blue-400">{(metrics.transformer.opportunityScore * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Direction Bias</p>
          <p className="text-2xl font-bold text-purple-400">{metrics.transformer.directionBias}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Liquidity Trend</p>
          <p className="text-2xl font-bold text-orange-400">{(metrics.transformer.liquidityTrend * 100).toFixed(1)}%</p>
        </div>
      </div>

      {/* Strategy Performance */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Strategy Performance Breakdown</h3>
        <div className="space-y-3">
          {metrics.strategies.map((strategy, idx) => (
            <div key={idx} className="border border-gray-800 rounded p-4">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-white">{strategy.name}</span>
                <span className="text-green-400 font-bold">{(strategy.profitContribution).toFixed(2)} ETH</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Weight</span>
                  <p className="text-white font-semibold">{(strategy.weight * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <span className="text-gray-400">Win Rate</span>
                  <p className="text-white font-semibold">{(strategy.winRate * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div
                      className="bg-green-500 h-1.5 rounded-full"
                      style={{ width: `${strategy.weight * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Latency Monitoring */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Latency Monitoring</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-gray-400 text-sm mb-2">P50</p>
            <p className="text-2xl font-bold text-blue-400">{metrics.latency.p50.toFixed(0)} µs</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">P95</p>
            <p className="text-2xl font-bold text-yellow-400">{metrics.latency.p95.toFixed(0)} µs</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">P99</p>
            <p className="text-2xl font-bold text-orange-400">{metrics.latency.p99.toFixed(0)} µs</p>
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Target</p>
            <p className="text-2xl font-bold text-green-400">{metrics.latency.target.toFixed(0)} µs</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalyticsDashboard
