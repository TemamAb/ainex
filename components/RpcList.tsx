import React from 'react';
import { EngineModule, ModuleStatus } from '../types';
import { Activity, CheckCircle, AlertTriangle, Loader2, Server } from 'lucide-react';

interface RpcListProps {
    modules: EngineModule[];
}

const SystemStatus: React.FC<RpcListProps> = ({ modules }) => {
    const getStatusColor = (status: ModuleStatus) => {
        switch (status) {
            case ModuleStatus.ACTIVE: return 'text-emerald-400';
            case ModuleStatus.EXECUTING: return 'text-blue-400';
            case ModuleStatus.OPTIMIZING: return 'text-amber-400';
            case ModuleStatus.ERROR: return 'text-red-400';
            default: return 'text-slate-500';
        }
    };

    const getStatusIcon = (status: ModuleStatus) => {
        switch (status) {
            case ModuleStatus.ACTIVE: return <CheckCircle className="w-3 h-3 text-emerald-500" />;
            case ModuleStatus.EXECUTING: return <Activity className="w-3 h-3 text-blue-500 animate-pulse" />;
            case ModuleStatus.OPTIMIZING: return <Loader2 className="w-3 h-3 text-amber-500 animate-spin" />;
            case ModuleStatus.ERROR: return <AlertTriangle className="w-3 h-3 text-red-500" />;
            default: return <Server className="w-3 h-3 text-slate-500" />;
        }
    };

    return (
        <div className="space-y-3">
            {modules.map((module) => (
                <div key={module.id} className="bg-slate-900/50 border border-slate-800 rounded p-3 hover:border-slate-700 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                            {getStatusIcon(module.status)}
                            {module.name}
                        </h4>
                        <span className={`text-[10px] font-mono font-bold ${getStatusColor(module.status)}`}>
                            {module.status}
                        </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-mono text-slate-500 pl-5">
                        <span>{module.details}</span>
                        {module.metrics && <span className="text-slate-400">{module.metrics}</span>}
                    </div>
                </div>
            ))}

            {modules.length === 0 && (
                <div className="text-center py-8 text-slate-600 text-xs font-mono">
                    Initializing System Modules...
                </div>
            )}
        </div>
    );
};

export default SystemStatus;
