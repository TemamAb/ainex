import React, { useState } from 'react';
import {
    LayoutDashboard,
    PlayCircle,
    Activity,
    Wallet,
    Terminal,
    ChevronLeft,
    ChevronRight,
    Zap,
    Radio,
    ChevronDown,
    Settings
} from 'lucide-react';

interface SidebarProps {
    currentView: string;
    onViewChange: (view: string) => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
    currentMode: string;
    onModeChange: (mode: string) => void;
    preflightPassed: boolean;
    simConfidence: number;
    // New Settings Props
    tradeSettings: {
        profitTarget: { daily: string; unit: string };
        reinvestmentRate: number;
        riskProfile: string;
        isAIConfigured?: boolean;
    };
    onSettingsChange: (newSettings: any) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
    currentView,
    onViewChange,
    isCollapsed,
    onToggleCollapse,
    currentMode,
    onModeChange,
    preflightPassed,
    simConfidence,
    tradeSettings,
    onSettingsChange
}) => {
    const [isModeDropdownOpen, setIsModeDropdownOpen] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(true); // Default open for visibility

    // Helper to update settings - Automatically disables AI Config mode
    const updateSetting = (key: string, value: any) => {
        onSettingsChange({
            ...tradeSettings,
            [key]: value,
            isAIConfigured: false // Switch to Manual Mode
        });
    };

    const updateProfitTarget = (val: string) => {
        onSettingsChange({
            ...tradeSettings,
            profitTarget: { ...tradeSettings.profitTarget, daily: val },
            isAIConfigured: false // Switch to Manual Mode
        });
    };

    const menuItems = [
        { id: 'MONITOR', label: 'Live Monitor', icon: <LayoutDashboard className="w-5 h-5" /> },
        { id: 'WITHDRAWAL', label: 'Profit Withdrawal', icon: <Wallet className="w-5 h-5" /> },
        { id: 'EVENTS', label: 'Blockchain Events', icon: <Radio className="w-5 h-5" /> },
        { id: 'AI_CONSOLE', label: 'AI Terminal', icon: <Terminal className="w-5 h-5" /> },
    ];

    const modeOptions = [
        {
            id: 'PREFLIGHT',
            label: 'Preflight Check',
            icon: <Zap className="w-5 h-4" />,
            description: 'System readiness check',
            enabled: true
        },
        {
            id: 'SIM',
            label: 'SIM Mode',
            icon: <PlayCircle className="w-5 h-4" />,
            description: 'Real blockchain simulation',
            enabled: preflightPassed
        },
        {
            id: 'LIVE',
            label: 'Live Mode',
            icon: <Activity className="w-5 h-4" />,
            description: 'Active trading execution',
            enabled: preflightPassed && simConfidence >= 85
        }
    ];

    const handleModeSelect = (modeId: string) => {
        if (modeId === 'SIM' && !preflightPassed) return;
        if (modeId === 'LIVE' && (!preflightPassed || simConfidence < 85)) return;

        onModeChange(modeId);
        setIsModeDropdownOpen(false);

        // Navigate to the appropriate view
        if (modeId === 'PREFLIGHT') {
            onViewChange('PREFLIGHT');
        } else if (modeId === 'SIM') {
            onViewChange('SIM');
        } else if (modeId === 'LIVE') {
            onViewChange('LIVE');
        }
    };

    const getCurrentModeLabel = () => {
        const mode = modeOptions.find(m => m.id === currentMode);
        return mode ? mode.label : 'Select Mode';
    };

    const getCurrentModeIcon = () => {
        const mode = modeOptions.find(m => m.id === currentMode);
        return mode ? mode.icon : <Settings className="w-5 h-4" />;
    };

    return (
        <div
            className={`bg-slate-900 border-r border-slate-800 transition-all duration-300 flex flex-col ${isCollapsed ? 'w-16' : 'w-64'
                }`}
        >
            {/* Branding & Logo */}
            <div className={`p-4 flex items-center gap-3 border-b border-slate-800 ${isCollapsed ? 'justify-center' : ''}`}>
                <div className="relative w-8 h-8 flex-shrink-0">
                    <img
                        src="/assets/ainex-logo.png"
                        alt="AINEX"
                        className="w-full h-full object-contain rounded-lg shadow-lg shadow-emerald-500/20"
                    />
                    <div className="absolute -bottom-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full border border-slate-900 animate-pulse"></div>
                </div>
                {!isCollapsed && (
                    <div className="flex flex-col">
                        <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                            AINEX
                        </span>
                        <span className="text-[10px] uppercase tracking-[0.2em] text-emerald-500 font-semibold">
                            AI Engine
                        </span>
                    </div>
                )}
            </div>

            {/* Collapse Toggle */}
            <div className="p-2 flex justify-end border-b border-slate-800 bg-slate-900/50">
                <button
                    onClick={onToggleCollapse}
                    className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
                >
                    {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                </button>
            </div>

            {/* NEW: Settings Panel */}
            {!isCollapsed && (
                <div className="border-b border-slate-800">
                    <button
                        onClick={() => setIsSettingsOpen(!isSettingsOpen)}
                        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors"
                    >
                        <div className="flex items-center gap-2 text-slate-200">
                            <Settings className="w-4 h-4 text-emerald-500" />
                            <span className="font-semibold text-sm">Strategy Config</span>
                            {tradeSettings.isAIConfigured && (
                                <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30 animate-pulse">
                                    AI AUTO
                                </span>
                            )}
                        </div>
                        <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${isSettingsOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {isSettingsOpen && (
                        <div className="px-4 pb-4 space-y-4 bg-slate-900/50">
                            {/* Profit Target */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-400 flex justify-between">
                                    Target / Day
                                    <span className="text-emerald-500 text-[10px] animate-pulse">AI Whisper: 1.8 ETH</span>
                                </label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="number"
                                        value={tradeSettings.profitTarget.daily}
                                        onChange={(e) => updateProfitTarget(e.target.value)}
                                        className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:border-emerald-500 outline-none"
                                        placeholder="1.5"
                                    />
                                    <span className="text-xs font-bold text-slate-500">ETH</span>
                                </div>
                            </div>

                            {/* Reinvestment Rate */}
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-slate-400">Reinvestment</span>
                                    <span className="text-emerald-400">{tradeSettings.reinvestmentRate}%</span>
                                </div>
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    value={tradeSettings.reinvestmentRate}
                                    onChange={(e) => updateSetting('reinvestmentRate', Number(e.target.value))}
                                    className="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:rounded-full"
                                />
                            </div>

                            {/* Risk Profile */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-400">Risk Profile</label>
                                <div className="grid grid-cols-3 gap-1 bg-slate-800 p-1 rounded">
                                    {['LOW', 'MEDIUM', 'HIGH'].map((profile) => (
                                        <button
                                            key={profile}
                                            onClick={() => updateSetting('riskProfile', profile)}
                                            className={`text-[10px] font-bold py-1 rounded transition-colors ${tradeSettings.riskProfile === profile
                                                    ? profile === 'HIGH' ? 'bg-red-500/20 text-red-500' : profile === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-emerald-500/20 text-emerald-500'
                                                    : 'text-slate-500 hover:text-slate-300'
                                                }`}
                                        >
                                            {profile.slice(0, 3)}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Mode Selector Dropdown */}
            {!isCollapsed && (
                <div className="p-4 border-b border-t border-slate-800">
                    <div className="relative">
                        <button
                            onClick={() => setIsModeDropdownOpen(!isModeDropdownOpen)}
                            className="w-full flex items-center justify-between px-3 py-2 bg-slate-800 border border-slate-700 rounded text-left hover:bg-slate-700 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                {getCurrentModeIcon()}
                                <span className="text-sm font-medium">{getCurrentModeLabel()}</span>
                            </div>
                            <ChevronDown className={`w-4 h-4 transition-transform ${isModeDropdownOpen ? 'rotate-180' : ''}`} />
                        </button>

                        {isModeDropdownOpen && (
                            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded shadow-lg z-50">
                                {modeOptions.map((option) => (
                                    <button
                                        key={option.id}
                                        onClick={() => handleModeSelect(option.id)}
                                        disabled={!option.enabled}
                                        className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-700 transition-colors ${!option.enabled ? 'opacity-50 cursor-not-allowed' : ''
                                            } ${currentMode === option.id ? 'bg-blue-600/20 text-blue-400' : 'text-slate-300'}`}
                                    >
                                        {option.icon}
                                        <div>
                                            <div className="text-sm font-medium">{option.label}</div>
                                            <div className="text-xs text-slate-500">{option.description}</div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Menu Items */}
            <div className="flex-1 py-4 space-y-1 overflow-y-auto">
                {menuItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onViewChange(item.id)}
                        className={`w-full flex items-center px-4 py-3 transition-colors relative group ${currentView === item.id
                            ? 'bg-blue-600/10 text-blue-400 border-r-2 border-blue-500'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                            }`}
                        title={isCollapsed ? item.label : ''}
                    >
                        <div className={`${isCollapsed ? 'mx-auto' : 'mr-3'}`}>
                            {item.icon}
                        </div>
                        {!isCollapsed && (
                            <span className="font-medium text-sm whitespace-nowrap">
                                {item.label}
                            </span>
                        )}

                        {/* Tooltip for collapsed mode */}
                        {isCollapsed && (
                            <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-slate-700">
                                {item.label}
                            </div>
                        )}
                    </button>
                ))}
            </div>

            {/* Footer / Version */}
            <div className="p-4 border-t border-slate-800">
                {!isCollapsed && (
                    <div className="text-xs text-slate-500">
                        <p>AINEX Engine v3.0</p>
                        <p className="mt-1">© 2025 Enterprise</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Sidebar;
