import React, { useState, useEffect } from 'react';
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
    Settings,
    Save,
    CheckCircle,
    AlertCircle,
    Brain,
    Shield,
    TrendingUp,
    RefreshCw,
    Eye,
    EyeOff
} from 'lucide-react';
import { AIOptimizerService } from '../services/aiOptimizerService';

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
        aiOptimizationCycle: number; // minutes (1-60)
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

    // AI Optimization State
    const [aiOptimizer] = useState(() => new AIOptimizerService());
    const [aiSuggestions, setAiSuggestions] = useState<any>(null);
    const [isAISuggestionsVisible, setIsAISuggestionsVisible] = useState(false);
    const [lastOptimizationTime, setLastOptimizationTime] = useState<Date | null>(null);

    // Wallet State
    const [withdrawalWallet, setWithdrawalWallet] = useState('');
    const [walletValidation, setWalletValidation] = useState<'valid' | 'invalid' | null>(null);
    const [withdrawalThreshold, setWithdrawalThreshold] = useState('0.5');

    // AI Optimization Effects
    useEffect(() => {
        const fetchAISuggestions = async () => {
            try {
                const suggestions = await aiOptimizer.getAIStrategySuggestions();
                setAiSuggestions(suggestions);
            } catch (error) {
                console.error('Failed to fetch AI suggestions:', error);
            }
        };

        if (tradeSettings.isAIConfigured) {
            fetchAISuggestions();
        }
    }, [tradeSettings.isAIConfigured, aiOptimizer]);

    // Wallet validation
    const validateWallet = (address: string) => {
        const ethRegex = /^0x[a-fA-F0-9]{40}$/;
        return ethRegex.test(address);
    };

    const handleWalletInput = (value: string) => {
        setWithdrawalWallet(value);
        if (value.length === 0) {
            setWalletValidation(null);
        } else {
            setWalletValidation(validateWallet(value) ? 'valid' : 'invalid');
        }
    };

    const formatAddress = (address: string) => {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

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

                            {/* AI Optimization Cycle */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-400 flex justify-between">
                                    AI Optimization Cycle
                                    <span className="text-emerald-500 text-[10px] animate-pulse">AI Whisper: 15min</span>
                                </label>
                                <div className="flex items-center gap-2">
                                    <input
                                        type="range"
                                        min="1"
                                        max="60"
                                        value={tradeSettings.aiOptimizationCycle}
                                        onChange={(e) => updateSetting('aiOptimizationCycle', Number(e.target.value))}
                                        className="flex-1 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-emerald-500 [&::-webkit-slider-thumb]:rounded-full"
                                    />
                                    <span className="text-xs font-bold text-emerald-400 min-w-[3rem] text-right">
                                        {tradeSettings.aiOptimizationCycle}min
                                    </span>
                                </div>
                                <div className="flex justify-between text-[10px] text-slate-500">
                                    <span>1min</span>
                                    <span>60min</span>
                                </div>
                            </div>

                            {/* AI Optimization Controls */}
                            <div className="space-y-3 border-t border-slate-700 pt-3">
                                <div className="flex items-center justify-between">
                                    <label className="text-xs text-slate-400 flex items-center gap-2">
                                        <Brain className="w-3 h-3 text-emerald-500" />
                                        AI Strategy Optimization
                                    </label>
                                    <button
                                        onClick={() => setIsAISuggestionsVisible(!isAISuggestionsVisible)}
                                        className={`p-1 rounded transition-colors ${isAISuggestionsVisible ? 'bg-emerald-500/20 text-emerald-400' : 'text-slate-500 hover:text-slate-300'}`}
                                    >
                                        {isAISuggestionsVisible ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                                    </button>
                                </div>

                                {/* AI Suggestions Panel */}
                                {isAISuggestionsVisible && aiSuggestions && (
                                    <div className="bg-slate-800/50 rounded p-3 space-y-2 border border-slate-700">
                                        <div className="flex items-center gap-2 text-[10px] text-emerald-400">
                                            <TrendingUp className="w-3 h-3" />
                                            AI Recommendations
                                        </div>

                                        <div className="space-y-2">
                                            <div className="flex justify-between text-[10px]">
                                                <span className="text-slate-400">Suggested Target:</span>
                                                <span className="text-emerald-400 font-bold">{aiSuggestions.profitTarget} ETH</span>
                                            </div>
                                            <div className="flex justify-between text-[10px]">
                                                <span className="text-slate-400">Risk Profile:</span>
                                                <span className="text-emerald-400 font-bold">{aiSuggestions.riskProfile}</span>
                                            </div>
                                            <div className="flex justify-between text-[10px]">
                                                <span className="text-slate-400">Reinvestment:</span>
                                                <span className="text-emerald-400 font-bold">{aiSuggestions.reinvestmentRate}%</span>
                                            </div>
                                        </div>

                                        <div className="flex gap-2 pt-2 border-t border-slate-700">
                                            <button
                                                onClick={() => {
                                                    onSettingsChange({
                                                        ...tradeSettings,
                                                        profitTarget: { ...tradeSettings.profitTarget, daily: aiSuggestions.profitTarget },
                                                        riskProfile: aiSuggestions.riskProfile,
                                                        reinvestmentRate: aiSuggestions.reinvestmentRate,
                                                        isAIConfigured: true
                                                    });
                                                    setLastOptimizationTime(new Date());
                                                }}
                                                className="flex-1 flex items-center justify-center gap-1 px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-semibold rounded transition-colors"
                                            >
                                                <Brain className="w-3 h-3" />
                                                Apply AI
                                            </button>
                                            <button
                                                onClick={async () => {
                                                    try {
                                                        await aiOptimizer.optimizeStrategy(tradeSettings);
                                                        setLastOptimizationTime(new Date());
                                                        // Refresh suggestions
                                                        const newSuggestions = await aiOptimizer.getAIStrategySuggestions();
                                                        setAiSuggestions(newSuggestions);
                                                    } catch (error) {
                                                        console.error('AI optimization failed:', error);
                                                    }
                                                }}
                                                className="flex items-center justify-center gap-1 px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-semibold rounded transition-colors"
                                            >
                                                <RefreshCw className="w-3 h-3" />
                                                Optimize
                                            </button>
                                        </div>

                                        {lastOptimizationTime && (
                                            <div className="text-[9px] text-slate-500 text-center pt-1">
                                                Last optimized: {lastOptimizationTime.toLocaleTimeString()}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* AI Mode Toggle */}
                                <div className="flex items-center justify-between bg-slate-800/30 rounded p-2">
                                    <div className="flex items-center gap-2">
                                        <Shield className="w-3 h-3 text-emerald-500" />
                                        <span className="text-[10px] text-slate-400">AI Auto-Mode</span>
                                    </div>
                                    <button
                                        onClick={() => onSettingsChange({
                                            ...tradeSettings,
                                            isAIConfigured: !tradeSettings.isAIConfigured
                                        })}
                                        className={`relative inline-flex h-4 w-7 items-center rounded-full transition-colors ${tradeSettings.isAIConfigured ? 'bg-emerald-500' : 'bg-slate-600'}`}
                                    >
                                        <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${tradeSettings.isAIConfigured ? 'translate-x-4' : 'translate-x-0.5'}`} />
                                    </button>
                                </div>

                                {/* Audit & Enhance */}
                                <div className="space-y-2">
                                    <button
                                        onClick={async () => {
                                            try {
                                                const auditResult = await aiOptimizer.auditStrategy(tradeSettings);
                                                console.log('Strategy audit result:', auditResult);
                                                // Could show audit results in a modal or toast
                                            } catch (error) {
                                                console.error('Strategy audit failed:', error);
                                            }
                                        }}
                                        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white text-xs font-semibold rounded transition-colors border border-slate-600"
                                    >
                                        <Shield className="w-3 h-3" />
                                        Audit Strategy
                                    </button>

                                    <button
                                        onClick={async () => {
                                            try {
                                                const enhancedSettings = await aiOptimizer.enhanceStrategy(tradeSettings);
                                                onSettingsChange({
                                                    ...enhancedSettings,
                                                    isAIConfigured: true
                                                });
                                                setLastOptimizationTime(new Date());
                                            } catch (error) {
                                                console.error('Strategy enhancement failed:', error);
                                            }
                                        }}
                                        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-emerald-600 to-blue-600 hover:from-emerald-500 hover:to-blue-500 text-white text-xs font-semibold rounded transition-colors shadow-lg"
                                    >
                                        <TrendingUp className="w-3 h-3" />
                                        Enhance Strategy
                                    </button>
                                </div>
                            </div>

                            {/* Profit Withdrawal Wallet */}
                            <div className="space-y-2 border-t border-slate-700 pt-3">
                                <label className="text-xs text-slate-400 flex items-center gap-2">
                                    <Wallet className="w-3 h-3" />
                                    Profit Withdrawal Wallet
                                </label>
                                <div className="space-y-2">
                                    <input
                                        type="text"
                                        value={withdrawalWallet}
                                        onChange={(e) => handleWalletInput(e.target.value)}
                                        placeholder="0x..."
                                        className={`w-full bg-slate-800 border rounded px-2 py-1 text-xs text-white focus:outline-none ${
                                            walletValidation === 'valid' ? 'border-emerald-500' :
                                            walletValidation === 'invalid' ? 'border-red-500' :
                                            'border-slate-700'
                                        }`}
                                    />
                                    {withdrawalWallet && (
                                        <div className="flex items-center gap-2">
                                            {walletValidation === 'valid' ? (
                                                <CheckCircle className="w-3 h-3 text-emerald-500" />
                                            ) : (
                                                <AlertCircle className="w-3 h-3 text-red-500" />
                                            )}
                                            <span className={`text-[10px] ${
                                                walletValidation === 'valid' ? 'text-emerald-400' : 'text-red-400'
                                            }`}>
                                                {walletValidation === 'valid' ? formatAddress(withdrawalWallet) : 'Invalid Ethereum address'}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Withdrawal Threshold */}
                            <div className="space-y-1">
                                <label className="text-xs text-slate-400">Withdrawal Threshold (ETH)</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    value={withdrawalThreshold}
                                    onChange={(e) => setWithdrawalThreshold(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:border-emerald-500 outline-none"
                                    placeholder="0.5"
                                />
                            </div>

                            {/* Save Button */}
                            <div className="pt-2 border-t border-slate-700">
                                <button
                                    onClick={() => {
                                        // Save settings logic - could trigger persistence or validation
                                        console.log('Saving strategy settings:', tradeSettings);
                                        // You could add toast notification or API call here
                                    }}
                                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded transition-colors shadow-lg shadow-emerald-500/25"
                                >
                                    <Save className="w-3 h-3" />
                                    Save Settings
                                </button>
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
