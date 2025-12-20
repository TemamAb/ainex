import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchStatus } from '../../store/slices/systemSlice'
import { fetchMetrics } from '../../store/slices/profitSlice'
import StatusCard from '../shared/StatusCard'
import ProfitMetrics from '../shared/ProfitMetrics'
import OpportunitiesGrid from '../shared/OpportunitiesGrid'
import WithdrawalPanel from './WithdrawalPanel'

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { user } = useSelector((state: RootState) => state.auth)
  const { status, isLoading: statusLoading } = useSelector((state: RootState) => state.system)
  const { metrics, isLoading: profitLoading } = useSelector((state: RootState) => state.profit)
  const [withdrawalCollapsed, setWithdrawalCollapsed] = useState(false)

  useEffect(() => {
    dispatch(fetchStatus())
    dispatch(fetchMetrics())
    
    // Refresh every 5 seconds
    const interval = setInterval(() => {
      dispatch(fetchStatus())
      dispatch(fetchMetrics())
    }, 5000)

    return () => clearInterval(interval)
  }, [dispatch])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Welcome back, {user?.firstName}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-400">Organization</p>
          <p className="text-lg font-semibold text-white">{user?.organizationName}</p>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statusLoading ? (
          <div className="col-span-4 text-center py-8 text-gray-400">Loading...</div>
        ) : status ? (
          <>
            <StatusCard 
              label="System Status" 
              value={status.status} 
              icon="🔗"
            />
            <StatusCard 
              label="Mode" 
              value={status.mode} 
              icon="⚙️"
            />
            <StatusCard 
              label="AI Active" 
              value={status.aiActive ? 'Yes' : 'No'} 
              icon="🤖"
            />
            <StatusCard 
              label="Execution Mode" 
              value={status.executionMode ? 'Enabled' : 'Disabled'} 
              icon="⚡"
            />
          </>
        ) : null}
      </div>

      {/* Profit Metrics */}
      {profitLoading ? (
        <div className="text-center py-8 text-gray-400">Loading profit metrics...</div>
      ) : metrics ? (
        <ProfitMetrics metrics={metrics} />
      ) : null}

      {/* Opportunities */}
      <OpportunitiesGrid />

      {/* Profit Withdrawal System - Collapsible Section */}
      <div className="border-t border-gray-800 mt-8 pt-8">
        <button
          onClick={() => setWithdrawalCollapsed(!withdrawalCollapsed)}
          className="flex items-center justify-between w-full mb-6 focus:outline-none group"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">💰</span>
            <h2 className="text-2xl font-bold text-white group-hover:text-green-400 transition">
              Profit Withdrawal System
            </h2>
          </div>
          <span className={`text-xl text-gray-400 transition-transform ${withdrawalCollapsed ? 'rotate-0' : 'rotate-180'}`}>
            ▼
          </span>
        </button>

        {!withdrawalCollapsed && (
          <div className="bg-gray-900 bg-opacity-50 rounded-lg p-6 border border-gray-800 border-dashed">
            <WithdrawalPanel />
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
