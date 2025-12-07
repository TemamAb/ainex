'use client';
import React, { useState } from 'react';
import { Shield, Zap, AlertTriangle } from 'lucide-react';

interface ModeSwitcherProps {
    currentMode: 'SIMULATION' | 'LIVE';
    confidence: number;
    onModeChange: (mode: 'SIMULATION' | 'LIVE') => void;
}

export const ModeSwitcher = ({ currentMode, confidence, onModeChange }: ModeSwitcherProps) => {
    const [showLiveWarning, setShowLiveWarning] = useState(false);
    const [licenseKey, setLicenseKey] = useState('');

    const canGoLive = confidence >= 85;

    const handleLiveClick = () => {
        if (!canGoLive) {
            alert(`SIM confidence too low (${confidence}%). Need 85%+ to go LIVE.`);
            return;
        }
        setShowLiveWarning(true);
    };

    const confirmLive = () => {
        if (!licenseKey) {
            alert('Please enter your license key');
            return;
        }
        // In production, validate license key
        onModeChange('LIVE');
        setShowLiveWarning(false);
    };

    return (
        <div className="space-y-4">
            {/* Mode Selector */}
            <div className="grid grid-cols-2 gap-4">
                {/* SIMULATION Card */}
                <div
                    className={`border rounded-lg p-6 cursor-pointer transition-all ${currentMode === 'SIMULATION'
                            ? 'border-blue-500 bg-blue-900/20'
                            : 'border-gray-700 bg-gray-900/50 hover:border-gray-600'
                        }`}
                    onClick={() => onModeChange('SIMULATION')}
                >
                    <div className="flex items-center gap-3 mb-3">
                        <Shield className="text-blue-400" size={32} />
                        <div>
                            <h3 className="text-lg font-bold text-white">SIMULATION</h3>
                            <p className="text-xs text-gray-400">Risk-Free Learning</p>
                        </div>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span className="text-gray-300">Zero risk</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span className="text-gray-300">AI training</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span className="text-gray-300">No license needed</span>
                        </div>
                    </div>
                    {currentMode === 'SIMULATION' && (
                        <div className="mt-4 bg-blue-500/20 border border-blue-500/50 rounded px-3 py-2 text-xs text-blue-300">
                            ACTIVE
                        </div>
                    )}
                </div>

                {/* LIVE Card */}
                <div
                    className={`border rounded-lg p-6 cursor-pointer transition-all ${currentMode === 'LIVE'
                            ? 'border-green-500 bg-green-900/20'
                            : 'border-gray-700 bg-gray-900/50 hover:border-gray-600'
                        } ${!canGoLive && 'opacity-50 cursor-not-allowed'}`}
                    onClick={handleLiveClick}
                >
                    <div className="flex items-center gap-3 mb-3">
                        <Zap className="text-green-400" size={32} />
                        <div>
                            <h3 className="text-lg font-bold text-white">LIVE</h3>
                            <p className="text-xs text-gray-400">Real Trading</p>
                        </div>
                    </div>
                    <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                            <span className="text-amber-400">⚠</span>
                            <span className="text-gray-300">Real funds</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-green-400">✓</span>
                            <span className="text-gray-300">Real profit</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-amber-400">⚠</span>
                            <span className="text-gray-300">License required</span>
                        </div>
                    </div>
                    {currentMode === 'LIVE' && (
                        <div className="mt-4 bg-green-500/20 border border-green-500/50 rounded px-3 py-2 text-xs text-green-300">
                            ACTIVE
                        </div>
                    )}
                </div>
            </div>

            {/* Confidence Indicator */}
            <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">SIM Confidence</span>
                    <span className={`text-lg font-bold ${confidence >= 85 ? 'text-green-400' : 'text-amber-400'}`}>
                        {confidence}%
                    </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                    <div
                        className={`h-2 rounded-full transition-all ${confidence >= 85 ? 'bg-green-500' : 'bg-amber-500'}`}
                        style={{ width: `${confidence}%` }}
                    ></div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                    {confidence >= 85 ? '✅ Ready for LIVE mode' : `Need ${85 - confidence}% more to unlock LIVE`}
                </p>
            </div>

            {/* LIVE Mode Warning Modal */}
            {showLiveWarning && (
                <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                    <div className="bg-gray-900 border border-amber-500 rounded-lg p-6 max-w-md w-full">
                        <div className="flex items-center gap-3 mb-4">
                            <AlertTriangle className="text-amber-400" size={32} />
                            <h3 className="text-xl font-bold text-white">Activate LIVE Mode?</h3>
                        </div>
                        <div className="space-y-3 mb-6">
                            <p className="text-gray-300">You're about to trade with REAL funds.</p>
                            <div className="bg-amber-900/20 border border-amber-500/30 rounded p-3 text-sm text-amber-200">
                                <p className="font-bold mb-2">Please confirm:</p>
                                <label className="flex items-center gap-2 mb-2">
                                    <input type="checkbox" className="rounded" />
                                    <span>I understand this uses my capital</span>
                                </label>
                                <label className="flex items-center gap-2 mb-2">
                                    <input type="checkbox" className="rounded" />
                                    <span>I have reviewed profit projections</span>
                                </label>
                                <label className="flex items-center gap-2">
                                    <input type="checkbox" className="rounded" />
                                    <span>I accept the risks</span>
                                </label>
                            </div>
                            <input
                                type="text"
                                placeholder="Enter License Key"
                                value={licenseKey}
                                onChange={(e) => setLicenseKey(e.target.value)}
                                className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                            />
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowLiveWarning(false)}
                                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmLive}
                                className="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition-colors"
                            >
                                Activate LIVE
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
