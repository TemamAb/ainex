import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Terminal from './Terminal';
import StatsCard from './StatsCard';
import ControlPanel from './ControlPanel';
import Header from './Header';
import WalletModal from './WalletModal';
import { View, BotStatus, TradeLog, Currency, ExecutionMode, RefreshRate, WalletState } from '../types';
import { MOCK_BOTS, MOCK_TRADES } from '../constants';
import { generateCopilotResponse } from '../services/geminiService';
import { 
  Activity, 
  TrendingUp, 
  Zap, 
  Server, 
  CheckCircle, 
  XCircle,
  Cpu,
  RefreshCw,
  Search,
  ShieldAlert
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';

const ETH_PRICE = 3500;

const Dashboard: React.FC = () => {
  const [view, setView] = useState<View>('OVERVIEW');
  const [aiInput, setAiInput] = useState('');
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Institutional Features State
  const [currency, setCurrency] = useState<Currency>('USD');
  const [mode, setMode] = useState<ExecutionMode>('SIMULATION');
  const [refreshRate, setRefreshRate] = useState<RefreshRate>(1000);
  const [isWalletOpen, setIsWalletOpen] = useState(false);
  const [wallet, setWallet] = useState<WalletState>({
    isConnected: false,
    address: null,
    type: null,
    balance: 0
  });

  // Helpers for currency conversion
  const formatValue = (usdValue: number, isCurrency = true) => {
    if (currency === 'USD') {
      return isCurrency ? `$${usdValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}` : usdValue;
    } else {
      const ethVal = usdValue / ETH_PRICE;
      return isCurrency ? `Ξ${ethVal.toFixed(4)}` : Number(ethVal.toFixed(4));
    }
  };

  const getMockChartData = () => {
    return Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      profit: currency === 'USD' ? Math.floor(Math.random() * 5000) + 1000 : (Math.floor(Math.random() * 5000) + 1000) / ETH_PRICE,
      gas: Math.floor(Math.random() * 50) + 10,
    }));
  };

  const handleAiSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiInput.trim()) return;
    
    setIsAiLoading(true);
    const res = await generateCopilotResponse(aiInput, mode);
    setAiResponse(res);
    setIsAiLoading(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ONLINE': return 'text-emerald-400 bg-emerald-950/30 border-emerald-900';
      case 'WARNING': return 'text-yellow-400 bg-yellow-950/30 border-yellow-900';
      case 'OFFLINE': return 'text-red-400 bg-red-950/30 border-red-900';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className={`flex min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-cyan-500/30 selection:text-cyan-200 ${mode === 'LIVE' ? 'border-4 border-red-900/20' : ''}`}>
      <Sidebar activeView={view} setView={setView} />
      
      <WalletModal 
        isOpen={isWalletOpen} 
        onClose={() => setIsWalletOpen(false)}
        onConnect={(w) => setWallet(w)}
      />

      <main className="flex-1 ml-20 lg:ml-64 p-4 lg:p-8 overflow-y-auto relative h-screen">
        {/* Background Grid for tech feel */}
        <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none z-0"></div>
        
        <div className="relative z-10 pb-20">
            <Header 
                view={view}
                currency={currency}
                setCurrency={setCurrency}
                refreshRate={refreshRate}
                setRefreshRate={setRefreshRate}
                wallet={wallet}
                onConnectWallet={() => setIsWalletOpen(true)}
            />

            {/* Global Control Panel */}
            <ControlPanel mode={mode} setMode={setMode} />

            {/* Live Mode Warning Banner */}
            {mode === 'LIVE' && (
                <div className="mb-6 p-3 bg-red-950/30 border border-red-900/50 rounded-lg flex items-center justify-center gap-2 animate-pulse shadow-[0_0_15px_rgba(220,38,38,0.2)]">
                    <ShieldAlert className="w-5 h-5 text-red-500" />
                    <span className="text-red-400 font-bold tracking-widest text-sm">MAINNET LIVE EXECUTION ENABLED - REAL CAPITAL AT RISK</span>
                </div>
            )}

            {view === 'OVERVIEW' && (
                <div className="space-y-6">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatsCard 
                            title="Net Profit (24h)" 
                            value={formatValue(12450.00) as string} 
                            icon={TrendingUp} 
                            color="emerald" 
                            subtext={currency === 'USD' ? "+12.5% vs yesterday" : "+3.2 ETH vs yesterday"} 
                        />
                        <StatsCard title="Active Bots" value="3/4" icon={Server} color="purple" subtext="1 Warning state" />
                        <StatsCard 
                            title="Flash Volume" 
                            value={formatValue(4200000) as string} 
                            icon={Zap} 
                            color="orange" 
                            subtext="Across 145 txs" 
                        />
                        <StatsCard title="Avg Latency" value="45ms" icon={Activity} color="cyan" subtext="Optimized path" />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Main Chart */}
                        <div className="lg:col-span-2 bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl backdrop-blur-sm">
                            <h3 className="text-lg font-semibold text-white mb-6">Profitability Curve ({currency})</h3>
                            <div className="h-72 w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={getMockChartData()}>
                                        <defs>
                                            <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                        <XAxis dataKey="time" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => currency === 'USD' ? `$${val}` : `Ξ${val}`} />
                                        <Tooltip 
                                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f1f5f9' }}
                                            itemStyle={{ color: '#10b981' }}
                                            formatter={(value: number) => [currency === 'USD' ? `$${value}` : `Ξ${value.toFixed(4)}`, 'Profit']}
                                        />
                                        <Area type="monotone" dataKey="profit" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorProfit)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Live Terminal */}
                        <div className="lg:col-span-1 h-96 lg:h-auto">
                            <Terminal />
                        </div>
                    </div>

                    {/* Recent Trades Table */}
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
                        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center">
                            <h3 className="text-lg font-semibold text-white">Recent Execution</h3>
                            <button className="text-xs text-cyan-400 hover:text-cyan-300 font-bold uppercase tracking-wider">View All</button>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-950 text-slate-400 uppercase font-medium">
                                    <tr>
                                        <th className="px-6 py-3">Timestamp</th>
                                        <th className="px-6 py-3">Pair</th>
                                        <th className="px-6 py-3">Route</th>
                                        <th className="px-6 py-3 text-right">Profit ({currency})</th>
                                        <th className="px-6 py-3 text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {MOCK_TRADES.map((trade) => (
                                        <tr key={trade.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="px-6 py-4 font-mono text-slate-500">{trade.timestamp}</td>
                                            <td className="px-6 py-4 font-medium text-white">{trade.pair}</td>
                                            <td className="px-6 py-4 text-slate-400 text-xs">{trade.dex.join(' → ')}</td>
                                            <td className="px-6 py-4 text-right font-mono text-emerald-400 font-bold">
                                                {trade.profit > 0 ? formatValue(trade.profit) : '0.00'}
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                                                    trade.status === 'SUCCESS' ? 'bg-emerald-950/30 text-emerald-400 border-emerald-900' : 
                                                    'bg-red-950/30 text-red-400 border-red-900'
                                                }`}>
                                                    {trade.status === 'SUCCESS' ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                                                    {trade.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {view === 'BOTS' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {MOCK_BOTS.map((bot) => (
                        <div key={bot.id} className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden group hover:border-cyan-900/50 transition-all">
                            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                <BotStatusIcon type={bot.type} />
                            </div>
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-bold text-white">{bot.name}</h3>
                                    <p className="text-slate-500 text-xs uppercase tracking-wider mt-1">{bot.type} MODULE</p>
                                </div>
                                <span className={`px-2 py-1 rounded text-xs font-bold border ${getStatusColor(bot.status)}`}>
                                    {bot.status}
                                </span>
                            </div>
                            
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                                        <span>Efficiency</span>
                                        <span>{bot.efficiency}%</span>
                                    </div>
                                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                        <div 
                                            className={`h-full rounded-full ${bot.efficiency > 90 ? 'bg-emerald-500' : 'bg-yellow-500'}`} 
                                            style={{ width: `${bot.efficiency}%` }}
                                        ></div>
                                    </div>
                                </div>
                                <div className="flex justify-between text-sm pt-2 border-t border-slate-800">
                                    <span className="text-slate-400">Uptime</span>
                                    <span className="font-mono text-white">{bot.uptime}</span>
                                </div>
                                <div className="flex gap-2 pt-2">
                                    <button className="flex-1 py-2 rounded bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors">
                                        LOGS
                                    </button>
                                    <button className="flex-1 py-2 rounded bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors">
                                        CONFIG
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {view === 'AI_COPILOT' && (
                <div className="max-w-4xl mx-auto h-[75vh] flex flex-col">
                    <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl overflow-y-auto mb-4 space-y-4 scroll-smooth">
                        <div className="flex gap-4">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shrink-0">
                                <Cpu className="w-6 h-6 text-white" />
                            </div>
                            <div className="bg-slate-800/50 rounded-r-xl rounded-bl-xl p-4 text-slate-200 border border-slate-700/50">
                                <p className="font-semibold text-cyan-400 mb-2 text-sm uppercase tracking-wider">AiNex Oracle</p>
                                <p>System Online. Operating Mode: <strong className={mode === 'LIVE' ? 'text-red-400' : 'text-blue-400'}>{mode}</strong>.</p>
                                <p className="mt-2 text-sm text-slate-400">Accessing institutional strategies from <code className="bg-slate-950 px-1 py-0.5 rounded border border-slate-800">core-logic/ai/ainex-optimizer.py</code>.</p>
                            </div>
                        </div>

                        {aiResponse && (
                            <div className="flex gap-4 animate-fadeIn">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shrink-0">
                                    <Cpu className="w-6 h-6 text-white" />
                                </div>
                                <div className="bg-slate-800/50 rounded-r-xl rounded-bl-xl p-4 text-slate-200 border border-slate-700/50 w-full">
                                    <p className="font-semibold text-cyan-400 mb-2 text-sm uppercase tracking-wider">Analysis Result</p>
                                    <div className="prose prose-invert prose-sm max-w-none">
                                        <ReactMarkdown>{aiResponse}</ReactMarkdown>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <form onSubmit={handleAiSubmit} className="relative">
                        <input
                            type="text"
                            value={aiInput}
                            onChange={(e) => setAiInput(e.target.value)}
                            placeholder={`Command the Oracle (${mode} context active)...`}
                            className="w-full bg-slate-900 border border-slate-700 rounded-xl py-4 pl-6 pr-16 text-white placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 shadow-xl transition-all"
                        />
                        <button 
                            type="submit" 
                            disabled={isAiLoading}
                            className="absolute right-2 top-2 p-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-colors disabled:opacity-50"
                        >
                            {isAiLoading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5" />}
                        </button>
                    </form>

                    <div className="mt-4 flex gap-4 justify-center">
                         <button 
                            onClick={() => setAiInput("Analyze current gas fees and suggest paymaster optimization.")}
                            className="text-xs text-slate-500 hover:text-cyan-400 underline decoration-dotted underline-offset-4"
                        >
                            Gas Optimization
                        </button>
                        <button 
                            onClick={() => setAiInput("Simulate a multi-hop flash loan across Uniswap and SushiSwap.")}
                            className="text-xs text-slate-500 hover:text-cyan-400 underline decoration-dotted underline-offset-4"
                        >
                            Flash Loan Sim
                        </button>
                        <button 
                            onClick={() => setAiInput("Explain the MEV protection strategy for large trades.")}
                            className="text-xs text-slate-500 hover:text-cyan-400 underline decoration-dotted underline-offset-4"
                        >
                            MEV Strategy
                        </button>
                    </div>
                </div>
            )}

            {(view === 'FLASH' || view === 'CHAIN' || view === 'RISK' || view === 'TREASURY') && (
                <div className="flex flex-col items-center justify-center h-[60vh] text-slate-500">
                    <div className="w-24 h-24 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6 animate-pulse">
                        <Zap className="w-10 h-10 opacity-20" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-300">Module Under Construction</h3>
                    <p className="max-w-md text-center mt-2">The {view} interface is currently being compiled from the <code className="text-cyan-500">core-logic</code> artifacts.</p>
                </div>
            )}
        </div>
      </main>
    </div>
  );
};

const BotStatusIcon: React.FC<{ type: string }> = ({ type }) => {
    switch (type) {
        case 'SCANNER': return <Search className="w-32 h-32" />;
        case 'EXECUTOR': return <Zap className="w-32 h-32" />;
        case 'VALIDATOR': return <ShieldAlert className="w-32 h-32" />;
        default: return <Server className="w-32 h-32" />;
    }
}

export default Dashboard;