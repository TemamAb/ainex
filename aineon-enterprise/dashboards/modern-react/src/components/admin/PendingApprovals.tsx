import React, { useEffect, useState } from 'react'
import { adminAPI } from '../../services/api'
import { PendingUser } from '../../types'

const PendingApprovals: React.FC = () => {
  const [users, setUsers] = useState<PendingUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [approving, setApproving] = useState<string | null>(null)

  useEffect(() => {
    const fetchPendingUsers = async () => {
      try {
        const response = await adminAPI.pendingUsers()
        setUsers(response.data)
      } catch (error) {
        console.error('Failed to fetch pending users:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchPendingUsers()
  }, [])

  const handleApprove = async (userId: string) => {
    setApproving(userId)
    try {
      await adminAPI.approveUser(userId, { reason: 'Auto-approved' })
      setUsers(users.filter(u => u.id !== userId))
    } catch (error) {
      console.error('Failed to approve user:', error)
    } finally {
      setApproving(null)
    }
  }

  const handleReject = async (userId: string) => {
    setApproving(userId)
    try {
      await adminAPI.rejectUser(userId, { reason: 'Rejected by admin' })
      setUsers(users.filter(u => u.id !== userId))
    } catch (error) {
      console.error('Failed to reject user:', error)
    } finally {
      setApproving(null)
    }
  }

  return (
    <div className="bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-6">👥 Pending User Approvals</h2>

      {isLoading ? (
        <div className="text-center py-8 text-gray-400">Loading...</div>
      ) : users.length === 0 ? (
        <div className="text-center py-8 text-gray-400">No pending approvals</div>
      ) : (
        <div className="space-y-4">
          {users.map((user) => (
            <div
              key={user.id}
              className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-aineon-blue/50 transition-all"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">
                    {user.firstName} {user.lastName}
                  </h3>
                  <p className="text-sm text-gray-400">{user.email}</p>
                </div>
                <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs font-medium">
                  {user.subscriptionTier}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                <div>
                  <span className="text-gray-400">Organization</span>
                  <p className="text-white font-medium">{user.organizationName}</p>
                </div>
                <div>
                  <span className="text-gray-400">Country</span>
                  <p className="text-white font-medium">{user.country}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-400">Use Case</span>
                  <p className="text-white font-medium">{user.useCase}</p>
                </div>
              </div>

              {user.riskFlag && (
                <div className="mb-4 p-2 bg-red-500/10 border border-red-500/30 rounded text-red-400 text-xs">
                  ⚠️ {user.riskFlag}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(user.id)}
                  disabled={approving === user.id}
                  className="flex-1 py-2 bg-green-500 hover:bg-green-600 text-white font-medium rounded disabled:opacity-50 text-sm transition-colors"
                >
                  {approving === user.id ? 'Processing...' : 'Approve'}
                </button>
                <button
                  onClick={() => handleReject(user.id)}
                  disabled={approving === user.id}
                  className="flex-1 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded disabled:opacity-50 text-sm transition-colors"
                >
                  {approving === user.id ? 'Processing...' : 'Reject'}
                </button>
                <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded text-sm transition-colors">
                  Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PendingApprovals
