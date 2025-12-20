import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch, RootState } from '../../store/store'
import { fetchCompliance } from '../../store/slices/complianceSlice'
import { websocketService } from '../../services/websocket'

const ComplianceDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { metrics, isLoading } = useSelector((state: RootState) => state.compliance)
  const [activeTab, setActiveTab] = useState<'audit' | 'reports' | 'protocols'>('audit')

  useEffect(() => {
    dispatch(fetchCompliance())

    websocketService.on('compliance:update', () => {
      dispatch(fetchCompliance())
    })

    const interval = setInterval(() => {
      dispatch(fetchCompliance())
    }, 5000)

    return () => {
      clearInterval(interval)
      websocketService.off('compliance:update', () => {})
    }
  }, [dispatch])

  if (isLoading) {
    return <div className="text-center py-8 text-gray-400">Loading compliance data...</div>
  }

  if (!metrics) {
    return <div className="text-center py-8 text-gray-400">No compliance data available</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Compliance Dashboard</h1>
        <p className="text-gray-400 mt-1">Audit Trail, Reporting & Regulatory Compliance</p>
      </div>

      {/* Compliance Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Compliance Status</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Overall Status</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-semibold ${
                  metrics.compliance.status === 'compliant'
                    ? 'bg-green-900 text-green-200'
                    : metrics.compliance.status === 'warning'
                    ? 'bg-yellow-900 text-yellow-200'
                    : 'bg-red-900 text-red-200'
                }`}
              >
                {metrics.compliance.status.toUpperCase()}
              </span>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Compliance Score</span>
                <span className="text-white font-bold">{(metrics.compliance.score * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    metrics.compliance.score > 0.8
                      ? 'bg-green-500'
                      : metrics.compliance.score > 0.6
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${metrics.compliance.score * 100}%` }}
                />
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Last Audit: {metrics.compliance.lastAudit}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Etherscan Verification</h3>
          <div className="space-y-4">
            <div className="flex items-center">
              <div
                className={`w-3 h-3 rounded-full mr-3 ${metrics.verification.etherscan ? 'bg-green-500' : 'bg-red-500'}`}
              />
              <span className="text-white">
                {metrics.verification.etherscan ? 'Verified' : 'Not Verified'}
              </span>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Transactions Verified</p>
              <p className="text-2xl font-bold text-blue-400">{metrics.verification.transactionsVerified}</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Last Verified: {metrics.verification.lastVerified}</p>
            </div>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Available Reports</h3>
          <div className="space-y-2">
            {metrics.reports.length === 0 ? (
              <p className="text-gray-400 text-sm">No reports generated</p>
            ) : (
              <div>
                <p className="text-gray-400 text-sm mb-3">Total Reports: {metrics.reports.length}</p>
                <div className="space-y-2">
                  {metrics.reports.slice(0, 3).map((report, idx) => (
                    <div key={idx} className="bg-gray-800 rounded p-2">
                      <p className="text-white text-sm font-semibold">{report.type}</p>
                      <p className="text-gray-400 text-xs">{report.period}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg">
        <div className="flex border-b border-gray-800">
          {(['audit', 'reports', 'protocols'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-4 px-6 font-semibold transition ${
                activeTab === tab
                  ? 'text-white border-b-2 border-blue-500'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Audit Trail Tab */}
          {activeTab === 'audit' && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-white mb-4">Audit Trail (Last 20)</h3>
              {metrics.auditTrail.length === 0 ? (
                <p className="text-gray-400">No audit entries</p>
              ) : (
                <div className="max-h-96 overflow-y-auto space-y-2">
                  {metrics.auditTrail.slice(0, 20).map((entry, idx) => (
                    <div key={idx} className="bg-gray-800 rounded p-3 border-l-4 border-blue-500">
                      <div className="flex justify-between items-start mb-1">
                        <div>
                          <p className="text-white font-semibold text-sm">{entry.action}</p>
                          <p className="text-gray-400 text-xs">{entry.component}</p>
                        </div>
                        <span
                          className={`text-xs px-2 py-1 rounded font-semibold ${
                            entry.status === 'success'
                              ? 'bg-green-900 text-green-200'
                              : entry.status === 'pending'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-red-900 text-red-200'
                          }`}
                        >
                          {entry.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-400 text-xs mb-1">{entry.details}</p>
                      <p className="text-gray-500 text-xs">{new Date(entry.timestamp).toLocaleString()}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-white mb-4">Generated Reports</h3>
              {metrics.reports.length === 0 ? (
                <p className="text-gray-400">No reports available</p>
              ) : (
                <div className="space-y-2">
                  {metrics.reports.map((report, idx) => (
                    <div key={idx} className="bg-gray-800 rounded p-4 flex justify-between items-center">
                      <div>
                        <p className="text-white font-semibold">{report.type}</p>
                        <p className="text-gray-400 text-sm">Period: {report.period}</p>
                        <p className="text-gray-500 text-xs">Generated: {report.generatedAt}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span
                          className={`px-2 py-1 rounded text-xs font-semibold ${
                            report.status === 'completed'
                              ? 'bg-green-900 text-green-200'
                              : report.status === 'draft'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-blue-900 text-blue-200'
                          }`}
                        >
                          {report.status.toUpperCase()}
                        </span>
                        <button className="text-blue-400 hover:text-blue-300 font-semibold">
                          Download
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Protocols Tab */}
          {activeTab === 'protocols' && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-white mb-4">Protocol Risk Scores</h3>
              {metrics.protocols.length === 0 ? (
                <p className="text-gray-400">No protocol data</p>
              ) : (
                <div className="space-y-3">
                  {metrics.protocols.map((protocol, idx) => (
                    <div key={idx} className="bg-gray-800 rounded p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="text-white font-semibold">{protocol.name}</p>
                          <p className="text-gray-400 text-sm">
                            Liquidations: {protocol.liquidationCount}
                          </p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            protocol.status === 'active'
                              ? 'bg-green-900 text-green-200'
                              : protocol.status === 'monitoring'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-red-900 text-red-200'
                          }`}
                        >
                          {protocol.status.toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-gray-400 text-sm">Risk Score</span>
                          <span className="text-white text-sm font-semibold">
                            {(protocol.riskScore * 100).toFixed(0)}/100
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              protocol.riskScore < 0.3
                                ? 'bg-green-500'
                                : protocol.riskScore < 0.6
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${protocol.riskScore * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Available Exports */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Available Exports</h3>
        {metrics.exports.length === 0 ? (
          <p className="text-gray-400 text-sm">No exports available</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.exports.map((exp, idx) => (
              <div key={idx} className="bg-gray-800 rounded p-4 flex justify-between items-center">
                <div>
                  <p className="text-white font-semibold">{exp.name}</p>
                  <p className="text-gray-400 text-sm">
                    {exp.type.toUpperCase()} • {(exp.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <p className="text-gray-500 text-xs">{new Date(exp.createdAt).toLocaleString()}</p>
                </div>
                <button className="text-blue-400 hover:text-blue-300 font-semibold">
                  Download
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ComplianceDashboard
