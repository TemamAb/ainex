import React, { useEffect, useState } from 'react'
import { opportunitiesAPI } from '../../services/api'
import { Opportunity } from '../../types'

const OpportunitiesGrid: React.FC = () => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await opportunitiesAPI.list()
        setOpportunities(response.data.opportunities)
      } catch (error) {
        console.error('Failed to fetch opportunities:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchOpportunities()
    const interval = setInterval(fetchOpportunities, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-6">🔍 Opportunities</h2>

      {isLoading ? (
        <div className="text-center py-8 text-gray-400">Loading opportunities...</div>
      ) : opportunities.length === 0 ? (
        <div className="text-center py-8 text-gray-400">No opportunities found</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {opportunities.map((opp, idx) => (
            <div
              key={idx}
              className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-aineon-blue/50 transition-all"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <p className="text-sm font-semibold text-white">{opp.pair}</p>
                  <p className="text-xs text-gray-400">{opp.dex}</p>
                </div>
                <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium">
                  {(opp.profit).toFixed(2)} ETH
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Confidence</span>
                  <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-aineon-blue"
                      style={{ width: `${(opp.confidence * 100).toFixed(0)}%` }}
                    />
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Status</span>
                  <span className="text-xs font-mono text-gray-300">{opp.tx}</span>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-white/10">
                <button className="w-full py-1.5 bg-aineon-blue hover:bg-blue-600 text-white text-xs font-medium rounded transition-colors">
                  Execute
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default OpportunitiesGrid
