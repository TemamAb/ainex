import React from 'react';
import { 
  LayoutDashboard, 
  Bot, 
  Cpu, 
  Zap, 
  ShieldAlert, 
  Wallet, 
  Landmark,
  Settings,
  Activity
} from 'lucide-react';
import { View } from '../types';

interface SidebarProps {
  activeView: View;
  setView: (view: View) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeView, setView }) => {
  const menuItems = [
    { id: 'OVERVIEW', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'BOTS', label: 'Bot Swarm', icon: Bot },
    { id: 'AI_COPILOT', label: 'AiNex Oracle', icon: Cpu },
    { id: 'FLASH', label: 'Flash Loans', icon: Zap },
    { id: 'CHAIN', label: 'Cross-Chain', icon: Activity },
    { id: 'RISK', label: 'Risk Monitor', icon: ShieldAlert },
    { id: 'TREASURY', label: 'Treasury', icon: Landmark },
  ];

  return (
    <div className="w-20 lg:w-64 h-screen bg-slate-950 border-r border-slate-800 flex flex-col fixed left-0 top-0 z-50">
      {/* Brand */}
      <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-800">
        <div className="w-8 h-8 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="font-bold text-white">A</span>
        </div>
        <span className="hidden lg:block ml-3 font-bold text-lg tracking-wider bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          AI<span className="text-cyan-400">NEX</span>
        </span>
      </div>

      {/* Menu */}
      <nav className="flex-1 py-6 flex flex-col gap-2 px-3">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setView(item.id as View)}
            className={`flex items-center p-3 rounded-lg transition-all duration-200 group ${
              activeView === item.id 
                ? 'bg-cyan-900/20 text-cyan-400 border border-cyan-900/50' 
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-900'
            }`}
          >
            <item.icon className={`w-6 h-6 ${activeView === item.id ? 'animate-pulse' : ''}`} />
            <span className="hidden lg:block ml-3 font-medium text-sm">{item.label}</span>
            {activeView === item.id && (
                <div className="hidden lg:block ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]"></div>
            )}
          </button>
        ))}
      </nav>

      {/* User / Footer */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 p-2 rounded-lg bg-slate-900/50 border border-slate-800">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                <Wallet className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="hidden lg:block overflow-hidden">
                <p className="text-xs text-slate-500 uppercase font-bold">Connected</p>
                <p className="text-xs text-emerald-400 font-mono truncate">0x71C...9A2</p>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;