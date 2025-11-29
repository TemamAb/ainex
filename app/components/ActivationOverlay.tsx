import React from 'react';
import { useEngine, BootStage } from '../engine/EngineContext';
import { Shield, Zap, Bot, Brain, CheckCircle, Loader2 } from 'lucide-react';

const ModuleRow = ({
  active,
  completed,
  icon: Icon,
  title,
  subtitle,
  color
}: {
  active: boolean;
  completed: boolean;
  icon: any;
  title: string;
  subtitle: string;
  color: string;
}) => {
  const opacity = active || completed ? 1 : 0.3;
  const glow = active ? `drop-shadow(0 0 10px ${color})` : 'none';

  return (
    <div className={`flex items-center gap-4 p-4 border border-[#22252b] bg-[#181b1f] transition-all duration-500 ${active ? 'scale-105 border-white' : ''}`} style={{ opacity }}>
      <div className="relative">
        <Icon size={24} style={{ color, filter: glow }} className={active ? 'animate-pulse' : ''} />
        {completed && <CheckCircle size={12} className="absolute -bottom-1 -right-1 text-[#00FF9D] bg-black rounded-full" />}
      </div>
      <div className="flex-1">
        <h3 className="font-bold text-sm text-white">{title}</h3>
        <p className="text-[10px] text-gray-400">{active ? <span className="animate-pulse">{subtitle}</span> : subtitle}</p>
      </div>
      {active && <Loader2 size={16} className="animate-spin text-white" />}
    </div>
  );
};

export const ActivationOverlay = () => {
  const { state, bootStage } = useEngine();

  if (state !== 'BOOTING') return null;

  const stages: BootStage[] = ['GASLESS', 'SMART_WALLET', 'FLASH_LOAN', 'BOT_SWARM', 'AI_OPTIMIZATION', 'COMPLETE'];
  const currentIndex = stages.indexOf(bootStage);

  return (
    <div className="fixed inset-0 z-50 bg-[#0b0c0f] flex items-center justify-center font-mono">
      <div className="w-[600px] space-y-4">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-white tracking-widest">SYSTEM ACTIVATION</h2>
          <p className="text-xs text-gray-500">INITIALIZING CORE PROTOCOLS</p>
        </div>

        <div className="space-y-2">
          {/* 1. GASLESS MODE (GREEN) */}
          <ModuleRow
            active={bootStage === 'GASLESS'}
            completed={currentIndex > 0}
            icon={Shield}
            title="GASLESS MODE PROTOCOL"
            subtitle={bootStage === 'GASLESS' ? "VERIFYING ZERO CAPITAL REQUIREMENTS..." : "ZERO CAPITAL VERIFIED"}
            color="#00FF9D"
          />

          {/* 2. SMART WALLET (CYAN) */}
          <ModuleRow
            active={bootStage === 'SMART_WALLET'}
            completed={currentIndex > 1}
            icon={Bot}
            title="SMART WALLET GENERATOR"
            subtitle={bootStage === 'SMART_WALLET' ? "AUTO-CREATING ABSTRACTED ACCOUNT..." : "SMART WALLET READY"}
            color="#06b6d4"
          />

          {/* 3. FLASH LOAN (GOLD) */}
          <ModuleRow
            active={bootStage === 'FLASH_LOAN'}
            completed={currentIndex > 2}
            icon={Zap}
            title="MULTI-MILLION FLASH LOAN ENGINE"
            subtitle={bootStage === 'FLASH_LOAN' ? "SCANNING PROVIDERS: AAVE, BALANCER, UNISWAP..." : "LIQUIDITY POOLS CONNECTED"}
            color="#FFD700"
          />

          {/* 4. BOT SWARM (BLUE) */}
          <ModuleRow
            active={bootStage === 'BOT_SWARM'}
            completed={currentIndex > 3}
            icon={Bot}
            title="TRI-TIER BOT SYSTEM"
            subtitle={bootStage === 'BOT_SWARM' ? "ACTIVATING SEEKERS, RELAYERS, ORCHESTRATOR..." : "SWARM LOGIC ACTIVE"}
            color="#5794F2"
          />

          {/* 5. AI OPTIMIZATION (PURPLE) */}
          <ModuleRow
            active={bootStage === 'AI_OPTIMIZATION'}
            completed={currentIndex > 4}
            icon={Brain}
            title="AI OPTIMIZATION INTELLIGENCE"
            subtitle={bootStage === 'AI_OPTIMIZATION' ? "CALIBRATING NEURAL WEIGHTS..." : "INTELLIGENCE ONLINE"}
            color="#A855F7"
          />
        </div>

        <div className="mt-8 text-center">
          <div className="text-xs text-gray-600">AINEXUS CORE ENGINE v2.1</div>
        </div>
      </div>
    </div>
  );
};
