import React, { useState } from 'react'
import Dashboard from '../components/dashboard/Dashboard'
import AnalyticsDashboard from '../components/dashboard/AnalyticsDashboard'
import OperationsDashboard from '../components/dashboard/OperationsDashboard'
import RiskDashboard from '../components/dashboard/RiskDashboard'
import TradingDashboard from '../components/dashboard/TradingDashboard'
import ComplianceDashboard from '../components/dashboard/ComplianceDashboard'

type DashboardType = 'overview' | 'analytics' | 'operations' | 'risk' | 'trading' | 'compliance'

const DashboardRouter: React.FC = () => {
  const [activeDashboard, setActiveDashboard] = useState<DashboardType>('overview')

  const dashboards: Record<DashboardType, { label: string; icon: string; component: React.FC }> = {
    overview: { label: 'Overview', icon: '📊', component: Dashboard },
    analytics: { label: 'Analytics', icon: '🤖', component: AnalyticsDashboard },
    operations: { label: 'Operations', icon: '⚙️', component: OperationsDashboard },
    risk: { label: 'Risk', icon: '⚠️', component: RiskDashboard },
    trading: { label: 'Trading', icon: '📈', component: TradingDashboard },
    compliance: { label: 'Compliance', icon: '✓', component: ComplianceDashboard },
  }

  const CurrentComponent = dashboards[activeDashboard].component

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 border-r border-gray-800 overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-8">AINEON Dashboards</h2>
          <nav className="space-y-2">
            {(Object.entries(dashboards) as [DashboardType, typeof dashboards[DashboardType]][]).map(
              ([key, dashboard]) => (
                <button
                  key={key}
                  onClick={() => setActiveDashboard(key)}
                  className={`w-full text-left px-4 py-3 rounded-lg transition flex items-center gap-3 ${
                    activeDashboard === key
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <span className="text-lg">{dashboard.icon}</span>
                  <span className="font-medium">{dashboard.label}</span>
                </button>
              )
            )}
          </nav>
        </div>

        {/* Dashboard Info */}
        <div className="p-6 mt-8 border-t border-gray-800">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Dashboard Status</h3>
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-gray-400">All Systems Operational</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-gray-400">Real-time Updates Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="min-h-screen p-8 bg-gray-950">
          <CurrentComponent />
        </div>
      </div>
    </div>
  )
}

export default DashboardRouter
