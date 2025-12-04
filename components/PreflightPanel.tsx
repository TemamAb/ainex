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
                return <CheckCircle className="w-4 h-4 text-emerald-500" />;
            case 'failed':
                return <XCircle className="w-4 h-4 text-red-500" />;
            case 'running':
                return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
            case 'pending':
                return <Clock className="w-4 h-4 text-slate-500" />;
        }
    };

    const getStatusColor = (status: PreflightCheck['status']) => {
        switch (status) {
            case 'passed':
                return 'text-emerald-400';
            case 'failed':
                return 'text-red-400';
            case 'running':
                return 'text-blue-400';
            case 'pending':
                return 'text-slate-500';
        }
    };

    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden backdrop-blur-sm">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Shield className="w-5 h-5 text-blue-500" />
                    System Preflight Checks
                </h3>
                <div className="flex gap-2">
                    <span className="text-xs font-mono text-slate-500">
                        v2.4.0-rc1
                    </span>
                </div>
            </div>

            <div className="p-6">
                {/* Status Overview */}
                <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-black/30 p-4 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">System Status</span>
                        <div className="flex items-center gap-2 mt-1">
                            <div className={`w-2 h-2 rounded-full ${allPassed ? 'bg-emerald-500' : isRunning ? 'bg-blue-500 animate-pulse' : 'bg-amber-500'}`}></div>
                            <span className="font-bold text-slate-200">
                                {isRunning ? 'DIAGNOSTICS RUNNING' : allPassed ? 'SYSTEM READY' : 'CHECKS PENDING'}
                            </span>
                        </div>
                    </div>
                    <div className="bg-black/30 p-4 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">Critical Systems</span>
                        <div className="flex items-center gap-2 mt-1">
                            <Shield className={`w-4 h-4 ${criticalPassed ? 'text-emerald-500' : 'text-red-500'}`} />
                            <span className={`font-bold ${criticalPassed ? 'text-emerald-400' : 'text-red-400'}`}>
                                {criticalPassed ? 'OPERATIONAL' : 'ATTENTION REQUIRED'}
                            </span>
                        </div>
                    </div>
                    <div className="bg-black/30 p-4 rounded border border-slate-800">
                        <span className="text-xs text-slate-500 uppercase">Environment</span>
                        <div className="flex items-center gap-2 mt-1">
                            <Globe className="w-4 h-4 text-blue-500" />
                            <span className="font-bold text-slate-200">Production (Mainnet)</span>
                        </div>
                    </div>
                </div>

                {/* Check List */}
                <div className="space-y-3 mb-6 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                    {checks.length === 0 && isIdle && (
                        <div className="text-center py-12 text-slate-500">
                            <Shield className="w-12 h-12 mx-auto mb-4 opacity-20" />
                            <p>System Idle. Run preflight checks to initialize engine.</p>
                        </div>
                    )}
                    {checks.map((check) => (
                        <div key={check.id} className="flex items-center justify-between p-3 bg-black/20 rounded border border-slate-800/50 hover:border-slate-700 transition-colors">
                            <div className="flex items-center gap-3">
                                {getStatusIcon(check.status)}
                                <div>
                                    <p className={`text-sm font-medium ${check.status === 'failed' && check.isCritical ? 'text-red-400' : 'text-slate-300'}`}>
                                        {check.name}
                                        {check.isCritical && <span className="ml-2 text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded uppercase">Critical</span>}
                                        {!check.isCritical && <span className="ml-2 text-[10px] bg-slate-700 text-slate-400 px-1.5 py-0.5 rounded uppercase">Optional</span>}
                                    </p>
                                    {check.message && (
                                        <p className="text-xs text-slate-500 mt-0.5">{check.message}</p>
                                    )}
                                </div>
                            </div>
                            <div className="text-xs font-mono text-slate-600">
                                {check.timestamp ? new Date(check.timestamp).toLocaleTimeString() : '--:--:--'}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Module Activation Results */}
                {moduleActivations && moduleActivations.length > 0 && (
                    <div className="space-y-3 mt-6 mb-6">
                        <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-3">
                            <Cpu className="w-4 h-4 text-emerald-500" />
                            Module Activation ({moduleActivations.filter(m => m.success).length}/{moduleActivations.length})
                        </h4>
                        {moduleActivations.map((activation) => (
                            <div
                                key={activation.moduleId}
                                className="bg-black/30 border border-slate-800/50 rounded p-4 hover:border-slate-700 transition-colors"
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <div className="flex items-center gap-3">
                                        {activation.success ? (
                                            <CheckCircle className="w-4 h-4 text-emerald-500" />
                                        ) : (
                                            <XCircle className="w-4 h-4 text-red-500" />
                                        )}
                                        <span className="text-sm font-bold text-slate-300">{activation.message}</span>
                                    </div>
                                    <span className={`text-xs font-mono font-bold uppercase ${activation.success ? 'text-emerald-400' : 'text-red-400'}`}>
                                        {activation.success ? 'ACTIVATED' : 'FAILED'}
                                    </span>
                                </div>
                                {activation.latency && (
                                    <p className="text-xs font-mono text-slate-500 ml-7">
                                        Latency: {activation.latency}ms
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Action Bar */}
                <div className="flex justify-end gap-4 pt-4 border-t border-slate-800">
                    <button
                        onClick={onRunPreflight}
                        disabled={isRunning}
                        className={`px-6 py-2 rounded font-bold text-sm uppercase tracking-wider transition-all ${isIdle
                                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_20px_rgba(37,99,235,0.4)] animate-pulse'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800'
                            }`}
                    >
                        {isRunning ? 'Running Diagnostics...' : isIdle ? 'Run Preflight Checks' : 'Rerun Checks'}
                    </button>

                    {/* Start Button Logic - Explicitly requires user action */}
                    <button
                        onClick={onStartSim}
                        disabled={!allPassed && !criticalPassed}
                        className={`px-6 py-2 rounded font-bold text-sm uppercase tracking-wider transition-all flex items-center gap-2 ${(allPassed || criticalPassed)
                                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.6)] cursor-pointer animate-pulse'
                                : 'bg-slate-800 text-slate-500 cursor-not-allowed opacity-50'
                            }`}
                    >
                        <Zap className="w-4 h-4" />
                        {allPassed ? 'Start SIM Mode' : criticalPassed ? 'Start SIM (Limited)' : 'Fix Critical Errors'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PreflightPanel;
