import dynamic from 'next/dynamic'
import React from 'react'

const MasterDashboard = dynamic(() => import('../components/MasterDashboard'), { 
  ssr: false,
  loading: () => <div>Loading...</div>
})

export default function Home() {
  return <MasterDashboard />
}
