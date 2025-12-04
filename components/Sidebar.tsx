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
    FileText,
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
}

const Sidebar: React.FC<SidebarProps> = ({
    currentView,
    onViewChange,
    isCollapsed,
    onToggleCollapse,
    currentMode,
    onModeChange,
    preflightPassed,
    simConfidence
}) => {
    const [isModeDropdownOpen, setIsModeDropdownOpen] = useState(false);

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
            {/* Collapse Toggle */}
            <div className="p-4 flex justify-end border-b border-slate-800">
                <button
                    onClick={onToggleCollapse}
                    className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
                >
                    {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
                </button>
            </div>

            {/* Mode Selector Dropdown */}
            {!isCollapsed && (
                <div className="p-4 border-b border-slate-800">
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
                                        className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-700 transition-colors ${
                                            !option.enabled ? 'opacity-50 cursor-not-allowed' : ''
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
