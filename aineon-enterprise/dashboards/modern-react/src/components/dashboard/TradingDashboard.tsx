import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchTrading } from '../../store/slices/tradingSlice'
import { websocketService } from '../../services/websocket'

const TradingDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isLoading } = useSelector((state: RootState) => state.trading)

  useEffect(() => {
    dispatch(fetchTrading())

    websocketService.on('trading:update', () => {
      dispatch(fetchTrading())
    })

    const interval = setInterval(() => {
      dispatch(fetchTrading())
    }, 5000)

    return () => {
      clearInterval(interval)
      websocketService.off('trading:update', () => {})
    }
  }, [dispatch])

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading trading data...</div>
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">No trading data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Trading Dashboard</h1>
        <p className="text-gray-400 mt-1">Execution Status & Multi-Chain Activity</p>
      </div>

      {/* MEV Capture Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Total MEV Captured</p>
          <p className="text-2xl font-bold text-green-400">{metrics.mev.totalCaptured.toFixed(2)} ETH</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Capture Rate</p>
          <p className="text-2xl font-bold text-blue-400">{(metrics.mev.captureRate * 100).toFixed(1)}%</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Bundles Participated</p>
          <p className="text-2xl font-bold text-purple-400">{metrics.mev.bundles}</p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-2">Avg Profit per Bundle</p>
          <p className="text-2xl font-bold text-orange-400">{metrics.mev.avgProfit.toFixed(2)} ETH</p>
        </div>
      </div>

      {/* Multi-Chain Execution Status */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Multi-Chain Execution Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { name: 'Ethereum', data: metrics.multiChain.ethereum },
            { name: 'Arbitrum', data: metrics.multiChain.arbitrum },
            { name: 'Optimism', data: metrics.multiChain.optimism },
            { name: 'Polygon', data: metrics.multiChain.polygon },
          ].map((chain, idx) => (
            <div key={idx} className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-white">{chain.name}</span>
                <span
                  className={`w-2 h-2 rounded-full ${
                    chain.data.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                  }`}
                />
              </div>
              <div className="space-y-2">
                <div>
                  <p className="text-gray-400 text-xs mb-1">Trades</p>
                  <p className="text-lg font-bold text-blue-400">{chain.data.trades}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs mb-1">Profit</p>
                  <p className="text-lg font-bold text-green-400">{chain.data.profit.toFixed(2)} ETH</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Flash Loans */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Active Flash Loans</h3>
        {metrics.flashLoans.length === 0 ? (
          <p className="text-gray-400 text-sm">No active flash loans</p>
        ) : (
          <div className="space-y-2">
            {metrics.flashLoans.map((loan, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-3 border-l-4 border-blue-500">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-white font-semibold">{loan.provider}</p>
                    <p className="text-gray-400 text-sm">{loan.amount.toFixed(2)} USDC</p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded font-semibold ${
                      loan.status === 'active'
                        ? 'bg-blue-900 text-blue-200'
                        : loan.status === 'repaid'
                        ? 'bg-green-900 text-green-200'
                        : 'bg-red-900 text-red-200'
                    }`}
                  >
                    {loan.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-gray-400 text-xs">Fee: {loan.fee.toFixed(4)} USDC</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Liquidations */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Liquidation Activity</h3>
        {metrics.liquidations.length === 0 ? (
          <p className="text-gray-400 text-sm">No liquidation activity</p>
        ) : (
          <div className="space-y-2">
            {metrics.liquidations.slice(0, 5).map((liq, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-3">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-white font-semibold">{liq.protocol}</p>
                    <p className="text-gray-400 text-sm">{liq.amount.toFixed(2)} USD</p>
                  </div>
                  <div className="text-right">
                    <p className="text-green-400 font-semibold">{liq.profit.toFixed(2)} ETH</p>
                    <span
                      className={`text-xs px-2 py-1 rounded font-semibold ${
                        liq.status === 'executed'
                          ? 'bg-green-900 text-green-200'
                          : liq.status === 'pending'
                          ? 'bg-yellow-900 text-yellow-200'
                          : 'bg-red-900 text-red-200'
                      }`}
                    >
                      {liq.status.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bridge Activity */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Cross-Chain Bridge Activity</h3>
        {metrics.bridges.length === 0 ? (
          <p className="text-gray-400 text-sm">No bridge activity</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.bridges.map((bridge, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-4">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-semibold text-white">{bridge.protocol}</span>
                  <span
                    className={`w-2 h-2 rounded-full ${
                      bridge.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                    }`}
                  />
                </div>
                <div className="space-y-2">
                  <div>
                    <p className="text-gray-400 text-xs">Volume</p>
                    <p className="text-lg font-bold text-blue-400">${bridge.volume.toFixed(0)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Fees Paid</p>
                    <p className="text-lg font-bold text-orange-400">${bridge.fees.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TradingDashboard
