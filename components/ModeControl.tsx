import React from 'react';
import { Activity, Zap, AlertTriangle } from 'lucide-react';

type EngineMode = 'IDLE' | 'PREFLIGHT' | 'SIM' | 'LIVE';

interface ModeControlProps {
    currentMode: EngineMode;
    preflightPassed: boolean;
    simConfidence: number;
    onStartSim: () => void;
    onStartLive: () => void;
    onStopMode: () => void;
    onRunPreflight?: () => void;
    isPreflightRunning?: boolean;
}

const ModeControl: React.FC<ModeControlProps> = ({
    currentMode,
    preflightPassed,
    simConfidence,
    onStartSim,
    onStartLive,
    onStopMode,
    onRunPreflight,
    isPreflightRunning = false,
}) => {
    const canStartSim = preflightPassed && (currentMode === 'IDLE' || currentMode === 'PREFLIGHT');
    const canStartLive = currentMode === 'SIM' && simConfidence >= 85;

    // Color coding: SIM = white, LIVE = green
    const getModeColor = () => {
        if (currentMode === 'SIM') return 'text-white';
        if (currentMode === 'LIVE') return 'text-emerald-400';
        return 'text-slate-400';
    };

    const getModeBackground = () => {
        if (currentMode === 'SIM') return 'bg-slate-700/50 border-white/20';
        if (currentMode === 'LIVE') return 'bg-emerald-900/30 border-emerald-500/30';
        return 'bg-slate-900/50 border-slate-700';
    };

    return (
        <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-white uppercase tracking-wider mb-6">
                Engine Mode Control
            </h3>

            {/* Current Mode Display */}
            <div className={`border rounded-lg p-6 mb-6 ${getModeBackground()}`}>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-xs text-slate-500 uppercase font-bold mb-2">Current Mode</p>
                        <p className={`text-3xl font-bold font-rajdhani uppercase ${getModeColor()}`}>
                            {currentMode}
                        </p>
                    </div>
                    {currentMode === 'SIM' && (
                        <Activity className="w-12 h-12 text-white opacity-50" />
                    )}
                    {currentMode === 'LIVE' && (
                        <Zap className="w-12 h-12 text-emerald-400 opacity-50" />
                    )}
                </div>

                {currentMode === 'SIM' && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                        <p className="text-xs text-slate-400 mb-2">Confidence Score</p>
                        <div className="flex items-center gap-3">
                            <div className="flex-1 bg-black/30 h-2 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-white transition-all duration-500"
                                    style={{ width: `${simConfidence}%` }}
                                ></div>
                            </div>
                            <span className="text-lg font-bold text-white font-mono">{simConfidence}%</span>
                        </div>
                        {simConfidence >= 85 && (
                            <p className="text-xs text-emerald-400 mt-2">✓ Ready for LIVE mode</p>
                        )}
                    </div>
                )}

                {currentMode === 'LIVE' && (
                    <div className="mt-4 pt-4 border-t border-emerald-500/20">
                        <p className="text-xs text-emerald-400 flex items-center gap-2">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                            Real trades executing on blockchain
                        </p>
                    </div>
                )}
            </div>

            {/* Mode Control Buttons */}
            <div className="space-y-3">
                {/* SIM Mode Button */}
                <button
                    onClick={onStartSim}
                    disabled={currentMode === 'SIM' || !canStartSim}
                    className={`w-full py-3 px-4 rounded font-bold uppercase tracking-wider transition-all ${currentMode === 'SIM'
                            ? 'bg-white/10 text-white border-2 border-white'
                            : canStartSim
                                ? 'bg-slate-700 hover:bg-slate-600 text-white border-2 border-transparent'
                                : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border-2 border-transparent'
                        }`}
                >
                    {currentMode === 'SIM' ? '● SIM Mode Active' : 'Start SIM Mode'}
                </button>

                {!canStartSim && currentMode !== 'SIM' && (
                    <p className="text-xs text-amber-400 flex items-center gap-2 px-2">
                        <AlertTriangle className="w-3 h-3" />
                        Complete preflight checks first
                    </p>
                )}

                {/* LIVE Mode Button */}
                <button
                    onClick={onStartLive}
                    disabled={!canStartLive}
                    className={`w-full py-3 px-4 rounded font-bold uppercase tracking-wider transition-all ${currentMode === 'LIVE'
                            ? 'bg-emerald-900/50 text-emerald-400 border-2 border-emerald-500'
                            : canStartLive
                                ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-2 border-transparent'
                                : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border-2 border-transparent'
                        }`}
                >
                    {currentMode === 'LIVE' ? '● LIVE Mode Active' : 'Start LIVE Mode'}
                </button>

                {!canStartLive && currentMode !== 'LIVE' && currentMode === 'SIM' && (
                    <p className="text-xs text-amber-400 flex items-center gap-2 px-2">
                        <AlertTriangle className="w-3 h-3" />
                        Confidence must reach 85% to enable LIVE mode
                    </p>
                )}

                {/* Stop Button */}
                {(currentMode === 'SIM' || currentMode === 'LIVE') && (
                    <button
                        onClick={onStopMode}
                        className="w-full py-2 px-4 rounded font-bold uppercase tracking-wider bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-500/30 transition-all text-sm"
                    >
                        Stop {currentMode} Mode
                    </button>
                )}
            </div>
        </div>
    );
};

export default ModeControl;
