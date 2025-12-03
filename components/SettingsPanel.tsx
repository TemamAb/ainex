import React, { useState } from 'react';
import { Sliders, Target, Shield, RefreshCw, Save } from 'lucide-react';

interface SettingsPanelProps {
    onSettingsChange: (settings: any) => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onSettingsChange }) => {
    const [profitTarget, setProfitTarget] = useState({
        daily: '1.5',
        unit: 'ETH'
    });
    const [reinvestmentRate, setReinvestmentRate] = useState(50);
    const [riskProfile, setRiskProfile] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('MEDIUM');
    const [isSaved, setIsSaved] = useState(false);

    const handleSave = () => {
        onSettingsChange({
            profitTarget,
            reinvestmentRate,
            riskProfile
        });
        setIsSaved(true);
        setTimeout(() => setIsSaved(false), 2000);
    };

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 max-w-2xl mx-auto">
            <div className="flex items-center gap-3 mb-8 border-b border-slate-700 pb-4">
                <Sliders className="w-6 h-6 text-blue-400" />
                <h2 className="text-xl font-bold text-white">Trade Parameters & Risk Configuration</h2>
            </div>

            <div className="space-y-8">
                {/* Profit Target Section */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-slate-300 mb-2">
                        <Target className="w-5 h-5 text-green-400" />
                        <h3 className="font-semibold">Daily Profit Target</h3>
                    </div>
                    <div className="flex items-center gap-4 bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                        <div className="flex-1">
                            <label className="text-xs text-slate-500 block mb-1">Target Amount</label>
                            <input
                                type="number"
                                value={profitTarget.daily}
                                onChange={(e) => setProfitTarget({ ...profitTarget, daily: e.target.value })}
                                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
                            />
                        </div>
                        <div className="w-32">
                            <label className="text-xs text-slate-500 block mb-1">Currency</label>
                            <select
                                value={profitTarget.unit}
                                onChange={(e) => setProfitTarget({ ...profitTarget, unit: e.target.value })}
                                className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
                            >
                                <option value="ETH">ETH</option>
                                <option value="USD">USD</option>
                                <option value="BTC">BTC</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Reinvestment Rate Section */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between text-slate-300 mb-2">
                        <div className="flex items-center gap-2">
                            <RefreshCw className="w-5 h-5 text-blue-400" />
                            <h3 className="font-semibold">Profit Reinvestment</h3>
                        </div>
                        <span className="text-blue-400 font-mono font-bold">{reinvestmentRate}%</span>
                    </div>
                    <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-700">
                        <input
                            type="range"
                            min="0"
                            max="100"
                            value={reinvestmentRate}
                            onChange={(e) => setReinvestmentRate(Number(e.target.value))}
                            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                        />
                        <div className="flex justify-between text-xs text-slate-500 mt-2">
                            <span>0% (Cash Out)</span>
                            <span>50% (Balanced)</span>
                            <span>100% (Compound)</span>
                        </div>
                    </div>
                </div>

                {/* Risk Profile Section */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-slate-300 mb-2">
                        <Shield className="w-5 h-5 text-purple-400" />
                        <h3 className="font-semibold">Risk Profile</h3>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                        {['LOW', 'MEDIUM', 'HIGH'].map((profile) => (
                            <button
                                key={profile}
                                onClick={() => setRiskProfile(profile as any)}
                                className={`p-4 rounded-lg border transition-all duration-200 ${riskProfile === profile
                                        ? 'bg-blue-600/20 border-blue-500 text-white shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                                        : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800 hover:border-slate-600'
                                    }`}
                            >
                                <div className="font-bold text-center mb-1">{profile}</div>
                                <div className="text-[10px] text-center opacity-70">
                                    {profile === 'LOW' && 'Conservative strategies, minimal drawdown.'}
                                    {profile === 'MEDIUM' && 'Balanced approach, moderate volatility.'}
                                    {profile === 'HIGH' && 'Aggressive arbitrage, max profit potential.'}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Save Button */}
                <div className="pt-4 flex justify-end">
                    <button
                        onClick={handleSave}
                        className={`flex items-center gap-2 px-8 py-3 rounded-lg font-bold transition-all duration-300 ${isSaved
                                ? 'bg-green-500 text-white'
                                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg hover:shadow-blue-500/25'
                            }`}
                    >
                        {isSaved ? (
                            <>Saved Successfully</>
                        ) : (
                            <>
                                <Save className="w-4 h-4" />
                                Save Configuration
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SettingsPanel;
