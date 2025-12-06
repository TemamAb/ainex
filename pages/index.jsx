import dynamic from 'next/dynamic'
import React from 'react'

// Client component with dynamic import
const MasterDashboard = dynamic(
  () => import('../components/MasterDashboard'),
  {
    ssr: false,
    loading: () => <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '24px' }}>Loading AINEX Dashboard...</div>
  }
)

export default function Home() {
  return <MasterDashboard />
}
