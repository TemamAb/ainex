"use client"

import dynamic from 'next/dynamic'
import React from 'react'

// Import MasterDashboard with explicit module resolution to fix TypeScript/Build errors
const MasterDashboard = dynamic(
  () => import('../components/MasterDashboard').then((mod: any) => mod.MasterDashboard || mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-emerald-500 font-mono">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-pulse">⚡</div>
          <div className="text-xl">Initializing AINEX Engine...</div>
          <div className="text-sm text-slate-500 mt-2">Secure Arbitrage Environment</div>
        </div>
      </div>
    )
  }
)

export default function HomePage() {
  return <MasterDashboard />
}
