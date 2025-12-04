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
        <div className="bg-slate-900/40 border border-slate-800 rounded p-4 backdrop-blur-sm">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4">
                Mode Control
            </h3>

            {/* Current Mode Display */}
            <div className={`border rounded p-3 mb-4 ${getModeBackground()}`}>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[10px] text-slate-500 uppercase font-bold mb-1">Current Mode</p>
                        <p className={`text-sm font-bold font-mono uppercase ${getModeColor()}`}>
                            {currentMode}
                        </p>
                    </div>
                    {currentMode === 'SIM' && (
                        <Activity className="w-4 h-4 text-white opacity-50" />
                    )}
                    {currentMode === 'LIVE' && (
                        <Zap className="w-4 h-4 text-emerald-400 opacity-50" />
                    )}
                </div>

                {currentMode === 'SIM' && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                        <p className="text-[10px] text-slate-400 mb-1">Confidence</p>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 bg-black/30 h-1.5 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-white transition-all duration-500"
                                    style={{ width: `${simConfidence}%` }}
                                ></div>
                            </div>
                            <span className="text-xs font-bold text-white font-mono">{simConfidence}%</span>
                        </div>
                        {simConfidence >= 85 && (
                            <p className="text-[10px] text-emerald-400 mt-1">✓ Ready for LIVE</p>
                        )}
                    </div>
                )}

                {currentMode === 'LIVE' && (
                    <div className="mt-2 pt-2 border-t border-emerald-500/20">
                        <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                            LIVE TRADING ACTIVE
                        </p>
                    </div>
                )}
            </div>

            {/* Mode Control Buttons */}
            <div className="space-y-2">
                {/* SIM Mode Button */}
                <button
                    onClick={onStartSim}
                    disabled={currentMode === 'SIM' || !canStartSim}
                    className={`w-full py-2 px-3 rounded font-bold text-xs uppercase tracking-wider transition-all ${currentMode === 'SIM'
                        ? 'bg-white/10 text-white border border-white'
                        : canStartSim
                            ? 'bg-slate-700 hover:bg-slate-600 text-white border border-transparent'
                            : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-transparent'
                        }`}
                >
                    {currentMode === 'SIM' ? '● SIM Active' : 'Start SIM'}
                </button>

                {!canStartSim && currentMode !== 'SIM' && (
                    <p className="text-[10px] text-amber-400 flex items-center gap-1 px-1">
                        <AlertTriangle className="w-3 h-3" />
                        Run preflight first
                    </p>
                )}

                {/* LIVE Mode Button */}
                <button
                    onClick={onStartLive}
                    disabled={!canStartLive}
                    className={`w-full py-2 px-3 rounded font-bold text-xs uppercase tracking-wider transition-all ${currentMode === 'LIVE'
                        ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-500'
                        : canStartLive
                            ? 'bg-emerald-600 hover:bg-emerald-500 text-white border border-transparent animate-pulse'
                            : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-transparent'
                        }`}
                >
                    {currentMode === 'LIVE' ? '● LIVE Active' : 'Start LIVE'}
                </button>

                {!canStartLive && currentMode !== 'LIVE' && currentMode === 'SIM' && (
                    <p className="text-[10px] text-amber-400 flex items-center gap-1 px-1">
                        <AlertTriangle className="w-3 h-3" />
                        Need 85% confidence
                    </p>
                )}

                {/* Stop Button */}
                {(currentMode === 'SIM' || currentMode === 'LIVE') && (
                    <button
                        onClick={onStopMode}
                        className="w-full py-1.5 px-3 rounded font-bold uppercase tracking-wider bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-500/30 transition-all text-xs"
                    >
                        Stop {currentMode}
                    </button>
                )}
            </div>
        </div>
    );
};

export default ModeControl;
