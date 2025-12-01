import React from 'react';
import { PreflightCheck, PreflightResults } from '../services/preflightService';
import { DirectoryAnalysisResult } from '../services/directoryAnalysisService';
import { CheckCircle, XCircle, Loader2, Clock, Cpu, Shield, Zap, FolderOpen, Database } from 'lucide-react';

interface PreflightPanelProps {
    checks: PreflightCheck[];
    isRunning: boolean;
    onRunPreflight: () => void;
    moduleActivations?: PreflightResults['moduleActivations'];
}

const PreflightPanel: React.FC<PreflightPanelProps> = ({ checks, isRunning, onRunPreflight, moduleActivations }) => {
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

    return (
        <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    Preflight Checks
                </h3>
                <button
                    onClick={onRunPreflight}
                    disabled={isRunning}
                    className={`px-4 py-2 rounded font-bold text-sm uppercase tracking-wider transition-all ${isRunning
                            ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-500 text-white'
                        }`}
                >
                    {isRunning ? 'Running...' : 'Run Preflight'}
                </button>
            </div>

            {/* Network Connectivity Checks */}
            <div className="space-y-3">
                <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2 mb-3">
                    <Globe className="w-4 h-4 text-blue-500" />
                    Network Connectivity
                </h4>
                {checks.map((check) => (
                    <div
                        key={check.id}
                        className="bg-black/30 border border-slate-800/50 rounded p-4 hover:border-slate-700 transition-colors"
                    >
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                                {getStatusIcon(check.status)}
                                <span className="text-sm font-bold text-slate-300">{check.name}</span>
                            </div>
                            <span className={`text-xs font-mono font-bold uppercase ${getStatusColor(check.status)}`}>
                                {check.status}
                            </span>
                        </div>
                        {check.message && (
                            <p className="text-xs font-mono text-slate-500 ml-7">{check.message}</p>
                        )}
                    </div>
                ))}
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

            {allPassed && (
                <div className="mt-6 bg-emerald-900/20 border border-emerald-500/30 rounded p-4">
                    <p className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        All preflight checks passed! You can now start SIM mode.
                    </p>
                </div>
            )}
        </div>
    );
};

export default PreflightPanel;
