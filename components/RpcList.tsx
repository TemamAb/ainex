import React from 'react';
import { EngineModule, ModuleStatus } from '../types';
import { Zap, Activity, ShieldCheck, Banknote, Cpu, Crosshair } from 'lucide-react';

interface SystemStatusProps {
  modules: EngineModule[];
}

const SystemStatus: React.FC<SystemStatusProps> = ({ modules }) => {
  const getIcon = (name: string) => {
    // Core Infra
    if (name.includes('Paymaster')) return <ShieldCheck className="w-5 h-5 text-emerald-400" />;
    if (name.includes('Flash Loan')) return <Banknote className="w-5 h-5 text-indigo-400" />;
    
    // Tri-Tier System
    if (name.includes('Scanner') || name.includes('Arbitrage')) return <Crosshair className="w-5 h-5 text-amber-400" />;
    if (name.includes('Executor') || name.includes('Liquidation')) return <Zap className="w-5 h-5 text-red-400" />;
    if (name.includes('Orchestrator') || name.includes('MEV')) return <Cpu className="w-5 h-5 text-blue-400" />;
    
    return <Activity className="w-5 h-5 text-slate-400" />;
  };

  return (
    <div className="space-y-3">
      {modules.map((mod) => (
        <div 
          key={mod.id} 
          className="flex items-center justify-between p-4 bg-black/40 rounded border border-slate-800 hover:border-emerald-500/30 transition-all group"
        >
          <div className="flex items-center space-x-4">
            <div className={`p-2 rounded bg-slate-900 border border-slate-700 group-hover:border-emerald-500/50 transition-colors`}>
              {getIcon(mod.name)}
            </div>
            
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-slate-100 font-mono tracking-tight">{mod.name}</span>
                {mod.status === ModuleStatus.ACTIVE && <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20">ONLINE</span>}
                {mod.status === ModuleStatus.EXECUTING && <span className="text-[10px] bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded border border-amber-500/20 animate-pulse">EXECUTING</span>}
                {mod.status === ModuleStatus.STANDBY && <span className="text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded">STANDBY</span>}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">{mod.details}</div>
            </div>
          </div>

          <div className="text-right">
             <div className="text-xs text-slate-400 font-mono">{mod.metrics}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SystemStatus;