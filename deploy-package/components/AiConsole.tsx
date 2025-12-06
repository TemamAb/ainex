import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Send, Cpu, Shield, Zap } from 'lucide-react';

const AiConsole: React.FC = () => {
    const [logs, setLogs] = useState<string[]>([
        '> AINEX Neural Core Initialized...',
        '> Loading predictive models (v4.2)...',
        '> Connecting to decentralized liquidity pools...',
        '> System ready. Waiting for input...'
    ]);
    const [input, setInput] = useState('');
    const logsEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [logs]);

    const handleCommand = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const newLog = `> user@ainex:~$ ${input}`;
        setLogs(prev => [...prev, newLog]);

        // Simulate AI response
        setTimeout(() => {
            const response = `> Executing command: ${input}... [DONE]`;
            setLogs(prev => [...prev, response]);
        }, 500);

        setInput('');
    };

    return (
        <div className="h-full flex flex-col bg-black/50 border border-slate-800 rounded-lg overflow-hidden font-mono text-sm">
            {/* Header */}
            <div className="bg-slate-900/80 p-3 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-emerald-400">
                    <Terminal className="w-4 h-4" />
                    <span className="font-bold">AI Command Terminal</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                        <Cpu className="w-3 h-3" />
                        <span>Core: IDLE</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        <span>Secure</span>
                    </div>
                </div>
            </div>

            {/* Logs Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-black/80">
                {logs.map((log, index) => (
                    <div key={index} className="text-slate-300 break-all">
                        {log}
                    </div>
                ))}
                <div ref={logsEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleCommand} className="p-3 bg-slate-900/80 border-t border-slate-800 flex gap-2">
                <span className="text-emerald-500 pt-2">➜</span>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="flex-1 bg-transparent border-none outline-none text-slate-200 placeholder-slate-600"
                    placeholder="Enter command..."
                    autoFocus
                />
                <button
                    type="submit"
                    className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
                >
                    <Send className="w-4 h-4" />
                </button>
            </form>
        </div>
    );
};

export default AiConsole;
