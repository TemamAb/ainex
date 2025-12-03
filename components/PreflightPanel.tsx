import React from 'react';
import { PreflightCheck, PreflightResults } from '../services/preflightService';
import { DirectoryAnalysisResult } from '../services/directoryAnalysisService';
import { CheckCircle, XCircle, Loader2, Clock, Cpu, Shield, Zap, FolderOpen, Database, Globe, AlertTriangle } from 'lucide-react';

interface PreflightPanelProps {
    checks: PreflightCheck[];
    isRunning: boolean;
    onRunPreflight: () => void;
    onStartSim?: () => void;
    moduleActivations?: PreflightResults['moduleActivations'];
}

const PreflightPanel: React.FC<PreflightPanelProps> = ({ checks, isRunning, onRunPreflight, onStartSim, moduleActivations }) => {
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

    const allPassed = checks.length > 0 && checks.every(check => check.status === 'passed');

    // Check if all CRITICAL checks have passed
    const criticalPassed = checks.length > 0 && checks.every(check => {
        if (check.isCritical) return check.status === 'passed';
        return true; // Optional checks don't block critical pass
    });

    return (
        <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xs font-light text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></span>
                    Preflight Checks
                </h3>
                <button
                    onClick={onRunPreflight}
                    disabled={isRunning}
                    className={`px-3 py-1.5 rounded font-light text-xs uppercase tracking-wider transition-all ${isRunning
                        ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-500 text-white'
                        }`}
                >
                    {isRunning ? 'Running...' : 'Run Preflight'}
                </button>
            </div>

            {/* Network Connectivity Checks */}
            <div className="space-y-6">
                {['network', 'blockchain', 'ai', 'security'].map((category) => {
                    const categoryChecks = checks.filter(c => c.category === category);
                    if (categoryChecks.length === 0) return null;

                    const getCategoryIcon = (cat: string) => {
                        switch (cat) {
                            case 'network': return <Globe className="w-4 h-4 text-blue-500" />;
                            case 'blockchain': return <Database className="w-4 h-4 text-purple-500" />;
                            case 'ai': return <Cpu className="w-4 h-4 text-emerald-500" />;
                            case 'security': return <Shield className="w-4 h-4 text-red-500" />;
                            default: return <Globe className="w-4 h-4 text-slate-500" />;
                        }
                    };

                    const getCategoryTitle = (cat: string) => {
                        switch (cat) {
                            case 'network': return 'Network Connectivity';
                            case 'blockchain': return 'Blockchain & Contracts';
                            case 'ai': return 'AI & Execution Engine';
                            case 'security': return 'Security & Risk';
                            default: return 'Other Checks';
                        }
                    };

                    return (
                        <div key={category}>
                            <h4 className="text-xs font-light text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-2">
                                {getCategoryIcon(category)}
                                {getCategoryTitle(category)}
                            </h4>
                            <div className="space-y-2">
                                {categoryChecks.map((check) => (
                                    <div
                                        key={check.id}
                                        className={`border rounded p-3 transition-all duration-300 ${check.status === 'passed'
                                            ? 'bg-emerald-900/20 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.1)]'
                                            : 'bg-black/30 border-slate-800/50 hover:border-slate-700'
                                            }`}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-3">
                                                {getStatusIcon(check.status)}
                                                <span className={`text-sm font-bold ${check.status === 'passed' ? 'text-emerald-100' : 'text-slate-300'}`}>
                                                    {check.name}
                                                </span>
                                                {!check.isCritical && (
                                                    <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                                                        OPTIONAL
                                                    </span>
                                                )}
                                            </div>
                                            <span className={`text-xs font-light uppercase ${getStatusColor(check.status)}`}>
                                                {check.status}
                                            </span>
                                        </div>
                                        {check.message && (
                                            <p className={`text-xs font-light ml-7 ${check.status === 'passed' ? 'text-emerald-400/80' : 'text-slate-500'}`}>
                                                {check.message}
                                            </p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Module Activation Results */}
            {moduleActivations && moduleActivations.length > 0 && (
                <div className="space-y-3 mt-6">
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

            {/* Status Summary & Actions */}
            <div className="mt-8 pt-6 border-t border-slate-800">
                {allPassed ? (
                    <div className="bg-emerald-900/20 border border-emerald-500/30 rounded p-3 mb-3">
                        <p className="text-xs font-light text-emerald-400 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            All systems GO! Maximum performance mode enabled.
                        </p>
                    </div>
                ) : criticalPassed ? (
                    <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-3 mb-3">
                        <p className="text-xs font-light text-yellow-400 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            Minimum requirements met. Some optional checks failed.
                        </p>
                        <p className="text-xs font-light text-yellow-500/80 mt-1 ml-6">
                            You can start SIM mode, but some features may be unavailable.
                        </p>
                    </div>
                ) : (
                    <div className="bg-red-900/20 border border-red-500/30 rounded p-4 mb-4">
                        <p className="text-sm font-bold text-red-400 flex items-center gap-2">
                            <XCircle className="w-5 h-5" />
                            Critical systems failed. Cannot start engine.
                        </p>
                    </div>
                )}

                <div className="flex justify-end gap-4">
                    <button
                        onClick={onRunPreflight}
                        disabled={isRunning}
                        className="px-4 py-2 rounded font-bold text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                    >
                        Rerun Checks
                    </button>

                    {/* Start Button Logic */}
                    {(allPassed || criticalPassed) && (
                        <button
                            className={`px-6 py-2 rounded font-bold text-sm uppercase tracking-wider transition-all flex items-center gap-2 ${allPassed
                                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-[0_0_20px_rgba(16,185,129,0.4)]'
                                : 'bg-yellow-600 hover:bg-yellow-500 text-white shadow-[0_0_20px_rgba(234,179,8,0.4)]'
                                }`}
                        >
                            <Zap className="w-4 h-4" />
                            {allPassed ? 'Start SIM Mode' : 'Start SIM (Limited)'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PreflightPanel;
