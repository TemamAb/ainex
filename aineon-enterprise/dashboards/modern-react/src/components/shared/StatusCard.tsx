import React from 'react'

interface StatusCardProps {
  label: string
  value: string | number
  icon?: string
  color?: 'green' | 'blue' | 'red' | 'yellow'
}

const StatusCard: React.FC<StatusCardProps> = ({ label, value, icon, color = 'blue' }) => {
  const colorClasses = {
    green: 'bg-green-500/10 border-green-500/50',
    blue: 'bg-aineon-blue/10 border-aineon-blue/50',
    red: 'bg-red-500/10 border-red-500/50',
    yellow: 'bg-yellow-500/10 border-yellow-500/50',
  }

  return (
    <div className={`bg-white/5 backdrop-blur border border-white/10 rounded-lg p-6 ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{label}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
        {icon && <span className="text-3xl">{icon}</span>}
      </div>
    </div>
  )
}

export default StatusCard
