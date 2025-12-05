import React from 'react';
import { PreflightCheck, PreflightResults } from '../services/preflightService';
import { CheckCircle, XCircle, Loader2, Clock, Cpu, Shield, Zap, Database, Globe, AlertTriangle } from 'lucide-react';

interface PreflightPanelProps {
    checks: PreflightCheck[];
    isRunning: boolean;
    allPassed: boolean;
    criticalPassed: boolean;
    onRunPreflight: () => void;
    onStartSim: () => void;
    isIdle?: boolean;
    moduleActivations?: PreflightResults['moduleActivations'];
}

export const PreflightPanel: React.FC<PreflightPanelProps> = ({
    checks,
    isRunning,
    allPassed,
    criticalPassed,
    onRunPreflight,
    onStartSim,
    isIdle = false,
    moduleActivations
}) => {
    const getStatusIcon = (status: PreflightCheck['status']) => {
        switch (status) {
            case 'passed':
                return <CheckCircle className="w-3 h-3 text-emerald-500" />;
            case 'failed':
                return <XCircle className="w-3 h-3 text-red-500" />;
            case 'running':
                return <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />;
            case 'pending':
                return <Clock className="w-3 h-3 text-slate-500" />;
        }
    };

    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded overflow-hidden backdrop-blur-sm">
            <div className="p-3 border-b border-slate-800 flex justify-between items-center">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Shield className="w-3 h-3 text-blue-500" />
                    System Preflight
                </h3>
                <div className="flex gap-2">
                    <span className="text-xs font-mono text-slate-500">
                        v2.4.0
                    </span>
                </div>
            </div>

            <div className="p-3">
                {/* Status Overview */}
                <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-2">
                    <div className="bg-black/30 p-2 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">Status</span>
                        <div className="flex items-center gap-2 mt-1">
                            <div className={`w-1.5 h-1.5 rounded-full ${allPassed ? 'bg-emerald-500' : isRunning ? 'bg-blue-500 animate-pulse' : 'bg-amber-500'}`}></div>
                            <span className="text-xs font-bold text-slate-200">
                                {isRunning ? 'RUNNING' : allPassed ? 'READY' : 'PENDING'}
                            </span>
                        </div>
                    </div>
                    <div className="bg-black/30 p-2 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">Critical</span>
                        <div className="flex items-center gap-2 mt-1">
                            <Shield className={`w-3 h-3 ${criticalPassed ? 'text-emerald-500' : 'text-red-500'}`} />
                            <span className={`text-xs font-bold ${criticalPassed ? 'text-emerald-400' : 'text-red-400'}`}>
                                {criticalPassed ? 'OK' : 'ATTENTION'}
                            </span>
                        </div>
                    </div>
                    <div className="bg-black/30 p-2 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">Env</span>
                        <div className="flex items-center gap-2 mt-1">
                            <Globe className="w-3 h-3 text-blue-500" />
                            <span className="text-xs font-bold text-slate-200">Mainnet</span>
                        </div>
                    </div>
                </div>

                {/* Check List */}
                <div className="space-y-1 mb-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                    {checks.length === 0 && isIdle && (
                        <div className="text-center py-6 text-slate-500">
                            <Shield className="w-8 h-8 mx-auto mb-2 opacity-20" />
                            <p className="text-xs">System Idle. Run preflight.</p>
                        </div>
                    )}
                    {checks.map((check) => (
                        <div key={check.id} className={`flex items-center justify-between p-2 rounded border hover:border-slate-700 transition-colors ${check.status === 'failed' ? 'bg-red-900/30 border-red-500 border-l-4 text-white' : 'bg-black/20 border-slate-800/50'}`}>>>
                            <div className="flex items-center gap-2">
                                {getStatusIcon(check.status)}
                                <div>
                                    <p className={`text-xs font-medium ${check.status === 'failed' ? 'text-white' : (check.status === 'failed' && check.isCritical ? 'text-red-400' : 'text-slate-300')}`}>
                                        {check.name}
                                        {check.isCritical && <span className="ml-2 text-[10px] bg-red-500/20 text-red-400 px-1 py-0.5 rounded uppercase">Crit</span>}
                                        {!check.isCritical && <span className="ml-2 text-[10px] bg-slate-700 text-slate-400 px-1 py-0.5 rounded uppercase">Opt</span>}
                                    </p>
                                    {check.message && (
                                        <p className="text-[10px] text-slate-500">{check.message}</p>
                                    )}
                                </div>
                            </div>
                            <div className="text-[10px] font-mono text-slate-600">
                                {check.timestamp ? new Date(check.timestamp).toLocaleTimeString() : '--:--'}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Module Activation Results */}
                {moduleActivations && moduleActivations.length > 0 && (
                    <div className="space-y-1 mt-3 mb-3">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                            <Cpu className="w-3 h-3 text-emerald-500" />
                            Modules ({moduleActivations.filter(m => m.success).length}/{moduleActivations.length})
                        </h4>
                        {moduleActivations.map((activation) => (
                            <div
                                key={activation.moduleId}
                                className="bg-black/30 border border-slate-800/50 rounded p-2 hover:border-slate-700 transition-colors"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        {activation.success ? (
                                            <CheckCircle className="w-3 h-3 text-emerald-500" />
                                        ) : (
                                            <XCircle className="w-3 h-3 text-red-500" />
                                        )}
                                        <span className="text-xs font-bold text-slate-300">{activation.message}</span>
                                    </div>
                                    <span className={`text-[10px] font-mono font-bold uppercase ${activation.success ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {activation.success ? 'OK' : 'FAIL'}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Action Bar */}
                <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                    <button
                        onClick={onRunPreflight}
                        disabled={isRunning}
                        className={`px-4 py-1.5 rounded font-bold text-xs uppercase tracking-wider transition-all ${isIdle
                            ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_10px_rgba(37,99,235,0.4)] animate-pulse'
                            : 'text-slate-400 hover:text-white hover:bg-slate-800'
                            }`}
                    >
                        {isRunning ? 'Running...' : isIdle ? 'Run Preflight' : 'Rerun'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PreflightPanel;
