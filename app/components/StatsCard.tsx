import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  subtext?: string;
  color?: string;
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, subtext, color = "cyan" }) => {
  const colorClasses = {
    cyan: "text-cyan-400 bg-cyan-950/30 border-cyan-900/50",
    purple: "text-purple-400 bg-purple-950/30 border-purple-900/50",
    emerald: "text-emerald-400 bg-emerald-950/30 border-emerald-900/50",
    orange: "text-orange-400 bg-orange-950/30 border-orange-900/50",
  }[color] || "text-cyan-400 bg-cyan-950/30 border-cyan-900/50";

  return (
    <div className={`p-6 rounded-xl border backdrop-blur-sm shadow-xl flex items-start justify-between ${colorClasses}`}>
      <div>
        <p className="text-slate-400 text-sm font-medium uppercase tracking-wider mb-1">{title}</p>
        <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
        {subtext && <p className="text-slate-500 text-xs mt-2">{subtext}</p>}
      </div>
      <div className={`p-3 rounded-lg bg-slate-950/50 border border-white/5`}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
  );
};

export default StatsCard;