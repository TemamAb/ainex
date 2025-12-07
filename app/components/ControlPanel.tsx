import React, { useState } from 'react';
import { ExecutionMode } from '../../types';
import {
    Zap,
    Shield,
    Cpu,
    Key,
    Lock,
    Unlock,
    Layers,
    Fuel,
    Activity
} from 'lucide-react';

interface ControlPanelProps {
    mode: ExecutionMode;
    setMode: (mode: ExecutionMode) => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ mode, setMode }) => {
    const [activationKey, setActivationKey] = useState('');
    const [isUnlocked, setIsUnlocked] = useState(false);

    // Module States
    const [modules, setModules] = useState({
        erc4337: true,
        mevShield: true,
        multiFlash: true,
        aiOptimizer: true
    });

    const handleUnlock = (e: React.FormEvent) => {
        e.preventDefault();

        // Secure license key validation
        const validLicenseKey = import.meta.env.VITE_LICENSE_KEY;

        if (!validLicenseKey) {
            console.error('License key not configured. Set VITE_LICENSE_KEY in .env.local');
            return;
        }

        if (activationKey === validLicenseKey) {
            setIsUnlocked(true);
            setActivationKey(''); // Clear the input for security
        } else {
            // Optional: Add visual feedback for invalid key
            console.warn('Invalid license key attempt');
        }
    };

    const toggleModule = (key: keyof typeof modules) => {
        if (!isUnlocked) return;
        setModules(prev => ({ ...prev, [key]: !prev[key] }));
    };

    return (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 shadow-xl mb-6 backdrop-blur-md relative overflow-hidden">
            {/* Decorative background element */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2"></div>

            <div className="flex flex-col xl:flex-row gap-6 justify-between items-start xl:items-center relative z-10">

                {/* Left: Master Mode Switch */}
                <div className="flex flex-col w-full xl:w-auto gap-2">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center gap-1">
                        <Activity className="w-3 h-3" /> Execution Context
                    </span>
                    <div className="flex items-center bg-slate-950/50 p-1.5 rounded-lg border border-slate-800 w-full xl:w-auto">
                        <button
                            onClick={() => isUnlocked && setMode('SIMULATION')}
                            disabled={!isUnlocked}
                            className={`flex-1 xl:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-bold transition-all ${mode === 'SIMULATION'
                                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]'
                                : 'text-slate-500 hover:text-slate-300'
                                }`}
                        >
                            <Layers className="w-4 h-4" />
                            SIMULATION
                        </button>
                        <button
                            onClick={() => isUnlocked && setMode('LIVE')}
                            disabled={!isUnlocked}
                            className={`flex-1 xl:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-bold transition-all ${mode === 'LIVE'
                                ? 'bg-red-600/20 text-red-400 border border-red-500/50 shadow-[0_0_15px_rgba(220,38,38,0.3)]'
                                : 'text-slate-500 hover:text-slate-300'
                                }`}
                        >
                            <Zap className="w-4 h-4" />
                            LIVE MAINNET
                        </button>
                    </div>
                </div>

                {/* Center: Module Matrix */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full xl:w-auto flex-1 xl:mx-8">
                    <ModuleToggle
                        label="Gasless Paymaster"
                        sub="ERC-4337"
                        active={modules.erc4337}
                        icon={Fuel}
                        onClick={() => toggleModule('erc4337')}
                        disabled={!isUnlocked}
                    />
                    <ModuleToggle
                        label="MEV Shield"
                        sub="Private RPC"
                        active={modules.mevShield}
                        icon={Shield}
                        onClick={() => toggleModule('mevShield')}
                        disabled={!isUnlocked}
                    />
                    <ModuleToggle
                        label="Flash Aggregator"
                        sub="Multi-Source"
                        active={modules.multiFlash}
                        icon={Layers}
                        onClick={() => toggleModule('multiFlash')}
                        disabled={!isUnlocked}
                    />
                    <ModuleToggle
                        label="AI Optimizer"
                        sub="Neural Net"
                        active={modules.aiOptimizer}
                        icon={Cpu}
                        onClick={() => toggleModule('aiOptimizer')}
                        disabled={!isUnlocked}
                    />
                </div>

                {/* Right: Activation / License */}
                <div className="w-full xl:w-auto min-w-[300px]">
                    {!isUnlocked ? (
                        <form onSubmit={handleUnlock} className="flex gap-2">
                            <div className="relative flex-1">
                                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                                <input
                                    type="password"
                                    value={activationKey}
                                    onChange={(e) => setActivationKey(e.target.value)}
                                    placeholder="Institutional License Key"
                                    className="w-full bg-slate-950 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-cyan-500 placeholder:text-slate-600"
                                />
                            </div>
                            <button type="submit" className="px-4 py-2 bg-slate-800 hover:bg-cyan-900 hover:text-cyan-400 hover:border-cyan-700 text-slate-400 rounded-lg border border-slate-700 transition-all shadow-lg">
                                <Lock className="w-4 h-4" />
                            </button>
                        </form>
                    ) : (
                        <div className="flex items-center gap-3 p-2 bg-emerald-950/20 border border-emerald-900/50 rounded-lg">
                            <div className="p-1.5 bg-emerald-500/20 rounded-md">
                                <Unlock className="w-4 h-4 text-emerald-400" />
                            </div>
                            <div>
                                <p className="text-xs font-bold text-emerald-400">ACCESS GRANTED</p>
                                <p className="text-[10px] text-emerald-500/70">Institutional Tier • Uncapped Volume</p>
                            </div>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

interface ModuleToggleProps {
    label: string;
    sub: string;
    active: boolean;
    icon: React.ElementType;
    onClick: () => void;
    disabled: boolean;
}

const ModuleToggle: React.FC<ModuleToggleProps> = ({ label, sub, active, icon: Icon, onClick, disabled }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        className={`flex items-start gap-3 p-3 rounded-lg border transition-all text-left group ${active
            ? 'bg-cyan-950/30 border-cyan-900/50'
            : 'bg-slate-950/50 border-slate-800 opacity-60'
            } ${disabled ? 'cursor-not-allowed opacity-30' : 'hover:bg-slate-800 hover:border-slate-700'}`}
    >
        <div className={`p-1.5 rounded-md transition-colors ${active ? 'bg-cyan-500/20 text-cyan-400' : 'bg-slate-800 text-slate-500 group-hover:text-slate-300'}`}>
            <Icon className="w-4 h-4" />
        </div>
        <div>
            <p className={`text-xs font-bold transition-colors ${active ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`}>{label}</p>
            <p className="text-[10px] text-slate-500">{sub}</p>
        </div>
    </button>
);

export default ControlPanel;