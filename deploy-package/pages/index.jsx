import dynamic from 'next/dynamic'
import React from 'react'

// Client component with dynamic import
const MasterDashboard = dynamic(
  () => import('../components/MasterDashboard'),
  {
    ssr: false,
    loading: () => <div>Loading dashboard...</div>
  }
)

export default function Home() {
  return <MasterDashboard />
}
