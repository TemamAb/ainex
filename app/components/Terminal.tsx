import React, { useEffect, useRef } from 'react';
import { Terminal as TerminalIcon } from 'lucide-react';
import { SYSTEM_LOGS } from '../constants';

const Terminal: React.FC = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, []);

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl flex flex-col h-full font-mono text-xs">
      <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
            <TerminalIcon className="w-4 h-4 text-slate-400" />
            <span className="text-slate-400 font-semibold">Engine Execution Log</span>
        </div>
        <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/20 border border-yellow-500"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/20 border border-green-500"></div>
        </div>
      </div>
      <div ref={scrollRef} className="p-4 space-y-2 overflow-y-auto custom-scrollbar flex-1 bg-black/50">
        {SYSTEM_LOGS.map((log, index) => {
            const isError = log.includes('[RISK]') || log.includes('[WARN]');
            const isSuccess = log.includes('[EXEC]') || log.includes('Profit');
            
            return (
                <div key={index} className={`flex gap-2 ${isError ? 'text-red-400' : isSuccess ? 'text-emerald-400' : 'text-slate-300'}`}>
                    <span className="opacity-50 select-none">{`>`}</span>
                    <span>{log}</span>
                </div>
            )
        })}
        <div className="flex gap-2 animate-pulse">
            <span className="text-cyan-500 select-none">{`>`}</span>
            <span className="text-cyan-500">_</span>
        </div>
      </div>
    </div>
  );
};

export default Terminal;
