"use client"

import dynamic from 'next/dynamic'
import React, { useContext } from 'react'
import { AuthProvider, AuthContext } from '../contexts/AuthContext'
import Auth from '../components/Auth/Auth'

// CHIEF ARCHITECT FIX: Pointing to the existing MasterDashboard component
// We use .then() to ensure we get the correct export (named or default)
const MasterDashboard = dynamic(
  () => import('../components/MasterDashboard').then((mod) => mod.MasterDashboard || mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-emerald-500 font-mono">
        <div className="text-center">
          <div className="text-xl">Initializing AINEX Engine...</div>
        </div>
      </div>
    )
  }
)

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useContext(AuthContext)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-emerald-500 font-mono">
        <div className="text-center">
          <div className="text-xl">Loading AINEX...</div>
        </div>
      </div>
    )
  }

  return isAuthenticated ? <MasterDashboard /> : <Auth />
}

export default function HomePage() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
