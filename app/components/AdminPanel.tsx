import React from 'react';
import { X, Shield, Activity, Target, Lock } from 'lucide-react';
import { useEngine } from '../engine/EngineContext';

interface AdminPanelProps {
    isOpen: boolean;
    onClose: () => void;
}

export const AdminPanel = ({ isOpen, onClose }: AdminPanelProps) => {
    const {
        riskProfile, setRiskProfile,
        profitMode, setProfitMode,
        fixedTarget, setFixedTarget,
        profitReinvestment, setProfitReinvestment
    } = useEngine();

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#111217] border border-[#22252b] w-full max-w-2xl rounded-lg shadow-2xl overflow-hidden">

                {/* HEADER */}
                <div className="flex justify-between items-center p-6 border-b border-[#22252b] bg-[#181b1f]">
                    <div className="flex items-center gap-3">
                        <Shield className="text-[#5794F2]" size={24} />
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-wider">ENGINE CONFIGURATION</h2>
                            <p className="text-gray-400 text-xs uppercase tracking-widest">Admin Access Only</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* CONTENT */}
                <div className="p-8 space-y-8">

                    {/* 1. PROFIT TARGET MODE */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-[#00FF9D]">
                            <Target size={20} />
                            <h3 className="font-bold text-sm tracking-widest">PROFIT TARGET MODE</h3>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <button
                                onClick={() => setProfitMode('ADAPTIVE')}
                                className={`p-4 rounded border transition-all flex flex-col items-center gap-2 ${profitMode === 'ADAPTIVE' ? 'bg-[#00FF9D]/10 border-[#00FF9D] text-[#00FF9D]' : 'bg-[#181b1f] border-[#22252b] text-gray-400 hover:border-gray-600'}`}
                            >
                                <span className="font-bold">ADAPTIVE (AI)</span>
                                <span className="text-[10px] opacity-70">Dynamic "Theoretical Max" Hunt</span>
                            </button>
                            <button
                                onClick={() => setProfitMode('FIXED')}
                                className={`p-4 rounded border transition-all flex flex-col items-center gap-2 ${profitMode === 'FIXED' ? 'bg-[#5794F2]/10 border-[#5794F2] text-[#5794F2]' : 'bg-[#181b1f] border-[#22252b] text-gray-400 hover:border-gray-600'}`}
                            >
                                <span className="font-bold">FIXED TARGET</span>
                                <span className="text-[10px] opacity-70">Manual Hard Limit</span>
                            </button>
                        </div>

                        {/* FIXED TARGET INPUT */}
                        {profitMode === 'FIXED' && (
                            <div className="mt-4 p-4 bg-[#181b1f] rounded border border-[#22252b] flex items-center gap-4 animate-in fade-in slide-in-from-top-2">
                                <span className="text-sm text-gray-400">Target Profit (ETH):</span>
                                <input
                                    type="number"
                                    value={fixedTarget}
                                    onChange={(e) => setFixedTarget(parseFloat(e.target.value))}
                                    className="bg-black border border-[#22252b] rounded px-3 py-1 text-white w-32 focus:border-[#5794F2] outline-none"
                                    step="0.01"
                                />
                            </div>
                        )}
                    </div>

                    {/* 2. RISK PROFILE */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-[#F25757]">
                            <Activity size={20} />
                            <h3 className="font-bold text-sm tracking-widest">RISK PROFILE</h3>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                            {['LOW', 'MEDIUM', 'HIGH'].map((profile) => (
                                <button
                                    key={profile}
                                    onClick={() => setRiskProfile(profile as any)}
                                    className={`p-3 rounded border transition-all text-xs font-bold ${riskProfile === profile ? 'bg-[#F25757]/10 border-[#F25757] text-[#F25757]' : 'bg-[#181b1f] border-[#22252b] text-gray-400 hover:border-gray-600'}`}
                                >
                                    {profile}
                                </button>
                            ))}
                        </div>
                        <p className="text-xs text-gray-500">
                            * High risk allows for larger slippage tolerance and aggressive gas bidding.
                        </p>
                    </div>

                    {/* 3. PROFIT REINVESTMENT */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-[#5794F2]">
                            <Activity size={20} />
                            <h3 className="font-bold text-sm tracking-widest">PROFIT REINVESTMENT</h3>
                        </div>
                        <div className="bg-[#181b1f] border border-[#22252b] rounded p-4">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-sm text-gray-400">Reinvest Ratio</span>
                                <span className="text-xl font-bold text-[#5794F2]">{profitReinvestment}%</span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="100"
                                value={profitReinvestment}
                                onChange={(e) => setProfitReinvestment(parseInt(e.target.value))}
                                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-[#5794F2]"
                            />
                            <div className="flex justify-between text-[10px] text-gray-500 mt-1">
                                <span>1% (Safety)</span>
                                <span>100% (Compound Growth)</span>
                            </div>
                        </div>
                    </div>

                    {/* 4. SECURITY STATUS */}
                    <div className="pt-6 border-t border-[#22252b]">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-gray-400">
                                <Lock size={16} />
                                <span className="text-xs">SAFETY INTERLOCKS ACTIVE</span>
                            </div>
                            <div className="text-xs text-[#00FF9D]">SYSTEM SECURE</div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
