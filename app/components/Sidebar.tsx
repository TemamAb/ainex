import React, { useState } from 'react';
import { LayoutDashboard, Bot, Zap, Settings, ChevronRight, ChevronLeft, LineChart, Shield } from 'lucide-react';

export const Sidebar = ({
  onToggleProjection,
  onToggleAdmin
}: {
  onToggleProjection: () => void;
  onToggleAdmin: () => void;
}) => {
  const [collapsed, setCollapsed] = useState(true);

  const NavItem = ({ icon: Icon, label, onClick, active = false }: any) => (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-4 p-3 transition-all duration-300 hover:bg-[#22252b] ${active ? 'text-[#00FF9D] border-r-2 border-[#00FF9D] bg-[#00FF9D]/5' : 'text-gray-400'}`}
    >
      <Icon size={20} />
      <span className={`whitespace-nowrap overflow-hidden transition-all duration-300 ${collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
        {label}
      </span>
    </button>
  );

  return (
    <div
      className={`h-screen bg-[#0b0c0f] border-r border-[#22252b] flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}
      onMouseEnter={() => setCollapsed(false)}
      onMouseLeave={() => setCollapsed(true)}
    >
      {/* LOGO AREA */}
      <div className="h-16 flex items-center justify-center border-b border-[#22252b]">
        <Shield className="text-[#5794F2]" size={24} />
        <span className={`ml-3 font-bold text-xl tracking-widest text-white overflow-hidden transition-all duration-300 ${collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'}`}>
          AINEX
        </span>
      </div>

      {/* NAV ITEMS */}
      <div className="flex-1 py-4 px-2 space-y-2 overflow-y-auto">
        {/* PREFLIGHT CHECK - TOP PRIORITY */}
        <div className="mb-4">
          <div className="text-[10px] uppercase text-gray-600 px-2 mb-2 tracking-widest font-bold">
            Deployment Phase
          </div>
        </div>

        <NavItem icon={LayoutDashboard} label="Mission Control" active />
        <NavItem icon={Bot} label="Bot Swarm" />
        <NavItem icon={Zap} label="Flash Loans" />
        <NavItem icon={LineChart} label="Profit Projection" onClick={onToggleProjection} />
        <NavItem icon={Settings} label="Engine Settings" onClick={onToggleAdmin} />
      </div>

      {/* FOOTER */}
      <div className="p-4 border-t border-[#22252b]">
        <div className={`text-[10px] text-gray-600 transition-all duration-300 ${collapsed ? 'opacity-0' : 'opacity-100'}`}>
          v2.1.0 STABLE
        </div>
      </div>
    </div>
  );
};