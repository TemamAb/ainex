"use client"

import dynamic from 'next/dynamic'
import React from 'react'

// Import your actual dashboard from App.tsx with SSR disabled
const Dashboard = dynamic(() => import('../App'), {
  ssr: false, // Disable SSR for your complex dashboard
  loading: () => (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#050505',
      color: '#10b981',
      fontFamily: 'monospace'
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '24px', marginBottom: '20px' }}>⚡</div>
        <div style={{ fontSize: '18px' }}>Loading Ainex Dashboard...</div>
        <div style={{ fontSize: '12px', marginTop: '10px', color: '#666' }}>
          AI-Powered Flash Loan Arbitrage Platform
        </div>
      </div>
    </div>
  )
})

export default function HomePage() {
  return <Dashboard />
}
