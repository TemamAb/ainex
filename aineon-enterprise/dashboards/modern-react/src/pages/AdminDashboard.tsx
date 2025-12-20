import React, { useState } from 'react'
import PendingApprovals from '../components/admin/PendingApprovals'

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('approvals')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
        <p className="text-gray-400 mt-1">Manage users, organizations, and system settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10">
        <button
          onClick={() => setActiveTab('approvals')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'approvals'
              ? 'border-aineon-blue text-white'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          Pending Approvals
        </button>
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'users'
              ? 'border-aineon-blue text-white'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          All Users
        </button>
        <button
          onClick={() => setActiveTab('settings')}
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${
            activeTab === 'settings'
              ? 'border-aineon-blue text-white'
              : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          Settings
        </button>
      </div>

      {/* Content */}
      {activeTab === 'approvals' && <PendingApprovals />}
      {activeTab === 'users' && <div>Users management (coming soon)</div>}
      {activeTab === 'settings' && <div>System settings (coming soon)</div>}
    </div>
  )
}

export default AdminDashboard
