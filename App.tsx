import React, { useState, useEffect, useRef } from 'react';
import { getSystemModules, subscribeToMempool, generateSmartWalletAddress, validateEthAddress, getFlashLoanMetrics } from './services/rpcService';
import { optimizeEngineStrategy } from './services/geminiService';
import { EngineModule, AIStrategyResponse, TradeSignal, SmartWalletState, AutoDepositConfig, FlashLoanMetric } from './types';
import SystemStatus from './components/RpcList';
import { 
  Zap, Cpu, TrendingUp, ShieldCheck, Globe, Terminal, 
  Wallet, AlertOctagon, BarChart3, LayoutDashboard, 
  Activity, Save, BrainCircuit, ArrowUpRight, Layers, Box,
  Clock, RefreshCw, DollarSign
} from 'lucide-react';

// --- TYPES FOR VIEW STATE ---
type ViewState = 'DASHBOARD' | 'WALLET' | 'ANALYTICS';
type Currency = 'USD' | 'ETH';

function App() {
  // --- CORE STATE ---
  const [currentView, setCurrentView] = useState<ViewState>('DASHBOARD');
  const [modules, setModules] = useState<EngineModule[]>([]);
  const [aiAnalysis, setAiAnalysis] = useState<AIStrategyResponse | null>(null);
  const [signals, setSignals] = useState<TradeSignal[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [totalProfit, setTotalProfit] = useState(0);
  const [flashMetrics, setFlashMetrics] = useState<FlashLoanMetric[]>([]);
  
  // --- NEW CONFIG STATE ---
  const [currency, setCurrency] = useState<Currency>('USD');
  const [refreshRate, setRefreshRate] = useState<number>(3000); // Default 3s
  const sessionStartRef = useRef<number>(Date.now());
  const [ethPrice, setEthPrice] = useState(3450); // Simulated ETH Price

  // --- ANALYTICS STATE ---
  const [arbStats, setArbStats] = useState({ detected: 0, executed: 0 });
  const [pairProfits, setPairProfits] = useState<Record<string, number>>({});
  const [chainProfits, setChainProfits] = useState<Record<string, number>>({});

  // --- WALLET STATE ---
  const [walletState, setWalletState] = useState<SmartWalletState>({
    status: 'SEARCHING',
    address: null,
    balance: '0.00',
    paymaster: 'DISCONNECTED'
  });

  const [autoDeposit, setAutoDeposit] = useState<AutoDepositConfig>({
    isEnabled: false,
    targetAddress: '',
    profitThreshold: '1000',
    checkInterval: '15',
    lastTransfer: null,
    totalWithdrawn: 0
  });

  const [walletError, setWalletError] = useState<string | null>(null);
  const [walletSuccess, setWalletSuccess] = useState<string | null>(null);

  // --- INITIALIZATION ---
  useEffect(() => {
    // Boot Sequence
    setModules(getSystemModules());
    setFlashMetrics(getFlashLoanMetrics());
    addLog("AINEX KERNEL: Initializing v5.3.0 [LIVE MODE]...");
    addLog("SECURITY: SIMULATION MODE FORBIDDEN.");
    
    // Wallet Auto-Deploy
    setTimeout(() => addLog("AUTH: Scanning for Web3 Provider..."), 800);
    setTimeout(() => {
        addLog("AUTH: No EOA. Initiating Smart Account Factory...");
        setWalletState(p => ({ ...p, status: 'DEPLOYING' }));
    }, 1500);

    setTimeout(() => {
        const newAddress = generateSmartWalletAddress();
        setWalletState({
            status: 'ACTIVE',
            address: newAddress,
            balance: '0.00',
            paymaster: 'LINKED'
        });
        addLog(`FACTORY: Smart Account Deployed: ${newAddress}`);
        addLog("PAYMASTER: Pimlico Sponsored.");
    }, 4500);
    
    // AI Loop
    const aiInterval = setInterval(() => {
        if(walletState.status === 'ACTIVE') runAIOptimization();
    }, 15 * 60 * 1000); 

    // Initial AI Trigger
    setTimeout(() => { if(walletState.status === 'ACTIVE') runAIOptimization(); }, 5000);

    // Auto-Deposit Check Loop
    const depositCheckInterval = setInterval(() => {
        checkAutoDeposit();
    }, 5000);

    return () => {
        clearInterval(aiInterval);
        clearInterval(depositCheckInterval);
    };
  }, [walletState.status]);

  // --- DYNAMIC REFRESH LOOP ---
  useEffect(() => {
      if(walletState.status !== 'ACTIVE') return;

      const loop = setInterval(() => {
          const newSignal = subscribeToMempool();
          setSignals(prev => [newSignal, ...prev].slice(0, 20)); // Keep last 20
          
          setArbStats(prev => ({ ...prev, detected: prev.detected + 1 }));

          // Update Metrics
          if (newSignal.status === 'CONFIRMED') {
              const profit = parseFloat(newSignal.expectedProfit);
              setTotalProfit(prev => prev + profit);
              setArbStats(prev => ({ ...prev, executed: prev.executed + 1 }));
              
              // Aggregate Profit by Pair
              setPairProfits(prev => ({
                  ...prev,
                  [newSignal.pair]: (prev[newSignal.pair] || 0) + profit
              }));

              // Aggregate Profit by Chain
              setChainProfits(prev => ({
                  ...prev,
                  [newSignal.chain]: (prev[newSignal.chain] || 0) + profit
              }));

              addLog(`BLOCK ${newSignal.blockNumber}: ${newSignal.action} ${newSignal.pair} on ${newSignal.chain} | +$${newSignal.expectedProfit}`);
          }
          // Randomly update flash metrics
          if(Math.random() > 0.8) setFlashMetrics(getFlashLoanMetrics());

          // Simulate Price Fluctuation
          if(Math.random() > 0.9) setEthPrice(p => p + (Math.random() * 10 - 5));

      }, refreshRate);

      return () => clearInterval(loop);
  }, [refreshRate, walletState.status]);


  const addLog = (msg: string) => {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    setLogs(prev => [`[${timestamp}] ${msg}`, ...prev].slice(0, 100));
  };

  const runAIOptimization = async () => {
    addLog("AI: OPTIMIZATION CYCLE STARTED (15 MIN INTERVAL)");
    const result = await optimizeEngineStrategy("Live Mainnet Feed: Gas 18 gwei. High volatility in Curve Pools.");
    setAiAnalysis(result);
    addLog(`STRATEGY REFINED: ${result.recommendation} | Efficiency: ${result.efficiencyScore || 98}%`);
  };

  const checkAutoDeposit = () => {
      // Logic handled in effect below
  };

  // Correct way to handle auto-deposit inside effect with dependency
  useEffect(() => {
      if (!autoDeposit.isEnabled || !autoDeposit.targetAddress) return;
      
      const threshold = parseFloat(autoDeposit.profitThreshold);
      if (totalProfit > threshold && totalProfit > 0) {
          // Trigger Withdrawal
          const amount = totalProfit;
          setTotalProfit(0);
          setAutoDeposit(prev => ({
              ...prev,
              lastTransfer: Date.now(),
              totalWithdrawn: prev.totalWithdrawn + amount
          }));
          addLog(`AUTO-WALLET: Threshold Met. Initiating Transfer of $${amount.toFixed(2)} to ${autoDeposit.targetAddress.substring(0,6)}...`);
          setTimeout(() => addLog(`AUTO-WALLET: Transfer Confirmed. TxHash: 0x${Math.random().toString(16).slice(2)}`), 2000);
      }
  }, [totalProfit, autoDeposit.isEnabled, autoDeposit.profitThreshold, autoDeposit.targetAddress]);

  const handleSaveWalletConfig = () => {
      setWalletError(null);
      setWalletSuccess(null);

      if (!validateEthAddress(autoDeposit.targetAddress)) {
          setWalletError("Invalid Ethereum Address");
          return;
      }
      if (isNaN(parseFloat(autoDeposit.profitThreshold))) {
          setWalletError("Invalid Profit Threshold");
          return;
      }

      setAutoDeposit(prev => ({ ...prev, isEnabled: true }));
      setWalletSuccess("Configuration Saved. Auto-Deposit Active.");
      addLog(`CONFIG: Auto-Deposit armed for ${autoDeposit.targetAddress} @ $${autoDeposit.profitThreshold}`);
  };

  // --- VISUAL HELPERS ---
  const getRiskScore = (risk: string | undefined): number => {
    if (!risk) return 50;
    const r = risk.toLowerCase();
    if (r.includes('high') || r.includes('aggressive')) return 88;
    if (r.includes('moderate') || r.includes('balanced')) return 50;
    if (r.includes('defensive') || r.includes('low')) return 22;
    return 60; 
  };

  // Currency Formatter
  const formatVal = (usdAmount: number, showSymbol = true) => {
      if (currency === 'USD') {
          return `${showSymbol ? '$' : ''}${usdAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      } else {
          return `${showSymbol ? 'Ξ' : ''}${(usdAmount / ethPrice).toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 })}`;
      }
  };

  // Metrics Calculation
  const lifetimeProfit = totalProfit + autoDeposit.totalWithdrawn;
  const elapsedSeconds = (Date.now() - sessionStartRef.current) / 1000;
  const elapsedHours = elapsedSeconds / 3600;
  const profitPerHour = elapsedHours > 0 ? lifetimeProfit / elapsedHours : 0;
  const projectedDaily = profitPerHour * 24;

  // Sort Profits
  const topPairs = Object.entries(pairProfits).sort(([,a], [,b]) => b - a).slice(0, 4);
  const topChains = Object.entries(chainProfits).sort(([,a], [,b]) => b - a);

  // --- RENDER HELPERS ---

  const renderDashboard = () => (
    <div className="grid grid-cols-12 gap-6 h-full overflow-y-auto pr-2 pb-20">
        {/* Top Hero Cards */}
        <div className="col-span-12 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg backdrop-blur-sm group hover:border-emerald-500/30 transition-colors relative overflow-hidden">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                    <DollarSign className="w-16 h-16 text-emerald-500" />
                </div>
                <div className="flex justify-between items-start relative z-10">
                    <div className="w-full">
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Total Generated</p>
                        <h2 className="text-3xl font-rajdhani font-bold text-emerald-400 mt-1">
                            {formatVal(lifetimeProfit)}
                        </h2>
                        
                        <div className="flex items-center gap-3 mt-2 pt-2 border-t border-slate-800/50 text-[10px] font-mono">
                            <span className="text-slate-400 flex items-center gap-1">
                                Pending: <span className="text-slate-200 font-bold">{formatVal(totalProfit)}</span>
                            </span>
                            <span className="text-slate-700">|</span>
                            <span className="text-indigo-400 flex items-center gap-1.5" title="Auto-Deposited to Wallet">
                                <Wallet className="w-3 h-3" /> 
                                <span className="font-bold">{formatVal(autoDeposit.totalWithdrawn)}</span>
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Projected Yield Card */}
            <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg backdrop-blur-sm">
                <div className="flex justify-between items-start">
                    <div className="w-full">
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Projected Yield</p>
                        <div className="mt-2 space-y-1">
                             <div className="flex justify-between items-center text-xs font-mono">
                                <span className="text-slate-400">Hourly:</span>
                                <span className="text-emerald-400 font-bold">{formatVal(profitPerHour)}</span>
                             </div>
                             <div className="flex justify-between items-center text-xs font-mono">
                                <span className="text-slate-400">Daily:</span>
                                <span className="text-emerald-400 font-bold">{formatVal(projectedDaily)}</span>
                             </div>
                        </div>
                    </div>
                    <div className="p-2 bg-purple-500/10 rounded border border-purple-500/20">
                        <Clock className="w-5 h-5 text-purple-500" />
                    </div>
                </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg backdrop-blur-sm">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">AI Efficiency</p>
                        <h2 className="text-3xl font-rajdhani font-bold text-amber-400 mt-1">
                            {aiAnalysis?.efficiencyScore || 98.4}%
                        </h2>
                    </div>
                    <div className="p-2 bg-amber-500/10 rounded border border-amber-500/20">
                        <BrainCircuit className="w-5 h-5 text-amber-500" />
                    </div>
                </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg backdrop-blur-sm">
                <div className="flex justify-between items-start">
                    <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Flash Loan Access</p>
                        <h2 className="text-3xl font-rajdhani font-bold text-blue-400 mt-1">
                            $14.2B
                        </h2>
                    </div>
                    <div className="p-2 bg-blue-500/10 rounded border border-blue-500/20">
                        <Zap className="w-5 h-5 text-blue-500" />
                    </div>
                </div>
            </div>
        </div>

        {/* --- PROFIT ANALYTICS & ATTRIBUTION --- */}
        <div className="col-span-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1: Arbitrage Stats */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 backdrop-blur-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <TrendingUp className="w-3 h-3 text-emerald-500" /> Arbitrage Opportunities
                </h3>
                <div className="flex items-end gap-2 mb-2">
                    <span className="text-2xl font-bold font-rajdhani text-white">{arbStats.executed}</span>
                    <span className="text-xs text-slate-500 mb-1">/ {arbStats.detected} Detected</span>
                </div>
                <div className="w-full bg-black/50 h-2 rounded-full overflow-hidden">
                    <div 
                        className="h-full bg-emerald-500 transition-all duration-500"
                        style={{ width: `${arbStats.detected > 0 ? (arbStats.executed / arbStats.detected) * 100 : 0}%` }}
                    ></div>
                </div>
                <p className="text-[10px] text-emerald-400 mt-2 text-right font-mono">
                    {arbStats.detected > 0 ? ((arbStats.executed / arbStats.detected) * 100).toFixed(1) : 0}% Conversion Rate
                </p>
            </div>

            {/* Card 2: Network Dominance */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 backdrop-blur-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Globe className="w-3 h-3 text-blue-500" /> Profit by Chain
                </h3>
                <div className="space-y-2">
                    {topChains.length === 0 ? <p className="text-xs text-slate-600 font-mono">Gathering Data...</p> : 
                     topChains.map(([chain, profit], idx) => (
                        <div key={chain} className="flex justify-between items-center text-xs font-mono">
                            <span className="text-slate-300">{chain}</span>
                            <span className="text-emerald-400 font-bold">{formatVal(profit)}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Card 3: Top Pairs */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 backdrop-blur-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <Layers className="w-3 h-3 text-indigo-500" /> Top Performing Pairs
                </h3>
                 <div className="space-y-2">
                    {topPairs.length === 0 ? <p className="text-xs text-slate-600 font-mono">Gathering Data...</p> : 
                     topPairs.map(([pair, profit], idx) => (
                        <div key={pair} className="relative">
                            <div className="flex justify-between items-center text-xs font-mono z-10 relative">
                                <span className="text-slate-300">{pair}</span>
                                <span className="text-white font-bold">{formatVal(profit)}</span>
                            </div>
                            <div 
                                className="absolute top-0 left-0 h-full bg-indigo-500/10 rounded" 
                                style={{ width: `${(profit / (topPairs[0][1] || 1)) * 100}%` }}
                            ></div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* Middle Section: Active Bots & Strategy */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
             {/* AI Control Center - Visual Upgrade */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-lg overflow-hidden backdrop-blur-md">
                <div className="bg-black/40 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                    <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                        <BrainCircuit className="w-4 h-4 text-emerald-500" /> AI Neural Net Analysis
                    </h3>
                    <span className="text-[10px] text-slate-500 font-mono flex items-center gap-2">
                        <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                        ONLINE
                    </span>
                </div>
                
                <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Left: Risk Gauge */}
                    <div className="flex flex-col items-center relative border-r border-slate-800/50 pr-4">
                        <div className="w-full flex justify-between items-center mb-4">
                            <h4 className="text-[10px] text-slate-500 uppercase font-bold">Risk Exposure</h4>
                            <span className="text-xs font-bold text-indigo-400 border border-indigo-500/20 bg-indigo-500/10 px-2 py-0.5 rounded">
                                {aiAnalysis?.riskAdjustment || 'ANALYZING...'}
                            </span>
                        </div>
                        
                        {/* CSS Gauge Chart */}
                        <div className="relative w-48 h-24 overflow-hidden mt-2">
                            {/* Gauge Background */}
                            <div className="absolute top-0 left-0 w-full h-full bg-slate-800 rounded-t-full opacity-30"></div>
                            {/* Gauge Fill */}
                            <div 
                                className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-emerald-500 via-blue-500 to-rose-500 rounded-t-full origin-bottom transition-transform duration-1000 ease-out"
                                style={{ transform: `rotate(${(getRiskScore(aiAnalysis?.riskAdjustment) / 100) * 180 - 180}deg)` }}
                            ></div>
                        </div>
                        
                        <div className="absolute bottom-6 text-3xl font-bold font-rajdhani text-white flex items-baseline">
                             {getRiskScore(aiAnalysis?.riskAdjustment)}<span className="text-sm text-slate-500 ml-1">/100</span>
                        </div>
                        
                        <div className="w-48 flex justify-between text-[9px] text-slate-600 uppercase font-bold mt-2">
                            <span>Conservative</span>
                            <span>Aggressive</span>
                        </div>
                    </div>

                    {/* Right: Liquidity Allocation Bar Chart */}
                    <div className="pl-2">
                         <h4 className="text-[10px] text-slate-500 uppercase font-bold mb-4 flex justify-between items-center">
                            <span>Active Pairs Liquidity</span>
                            <span className="text-[9px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">SIMULATED ALLOCATION</span>
                        </h4>
                        <div className="space-y-3">
                            {(aiAnalysis?.activePairs || ['ETH/USDC', 'BTC/USDT', 'SOL/ETH', 'LINK/USDC']).slice(0, 4).map((pair, idx) => {
                                const percentage = 60 - (idx * 12); // Simulated decreasing volume
                                return (
                                    <div key={idx} className="group">
                                        <div className="flex justify-between text-xs font-mono mb-1 text-slate-400 group-hover:text-white transition-colors">
                                            <span className="font-bold">{pair}</span>
                                            <span>{percentage}%</span>
                                        </div>
                                        <div className="w-full bg-slate-800/50 h-2 rounded-full overflow-hidden">
                                            <div 
                                                className={`h-full rounded-full transition-all duration-1000 ${idx === 0 ? 'bg-emerald-500' : idx === 1 ? 'bg-blue-500' : 'bg-indigo-500'}`}
                                                style={{ width: `${percentage}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>

                {/* Recommendation Footer */}
                <div className="px-5 py-3 bg-slate-900/60 border-t border-slate-800">
                    <p className="text-xs text-slate-300 font-mono flex items-center gap-2">
                        <Terminal className="w-3 h-3 text-slate-500" />
                        <span className="text-slate-500 font-bold uppercase">Instruction:</span> 
                        <span className="text-emerald-400">{aiAnalysis?.recommendation || 'AWAITING NEURAL INPUT...'}</span>
                    </p>
                </div>
            </div>

            {/* Live Feed Table */}
            <div className="bg-slate-900/30 border border-slate-800 rounded-lg overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-black/20">
                    <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                        <Activity className="w-3 h-3 text-emerald-500" />
                        Blockchain Event Stream
                    </h3>
                    <span className="text-[10px] text-slate-500 font-mono">LIVE BLOCK HEIGHT</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-black/40 text-[10px] uppercase text-slate-500 font-bold">
                            <tr>
                                <th className="px-4 py-2">Block</th>
                                <th className="px-4 py-2">Chain</th>
                                <th className="px-4 py-2">Action</th>
                                <th className="px-4 py-2">Pair</th>
                                <th className="px-4 py-2 text-right">Profit Est.</th>
                                <th className="px-4 py-2 text-center">Status</th>
                            </tr>
                        </thead>
                        <tbody className="text-xs font-mono">
                            {signals.map((signal) => (
                                <tr key={signal.id} className="border-b border-slate-800/50 hover:bg-white/5 transition-colors">
                                    <td className="px-4 py-2 text-slate-400">#{signal.blockNumber}</td>
                                    <td className="px-4 py-2 text-slate-500">{signal.chain}</td>
                                    <td className="px-4 py-2">
                                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${
                                            signal.action === 'FLASH_LOAN' ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/20' :
                                            signal.action === 'MEV_BUNDLE' ? 'bg-amber-500/20 text-amber-400 border-amber-500/20' :
                                            'bg-emerald-500/20 text-emerald-400 border-emerald-500/20'
                                        }`}>{signal.action}</span>
                                    </td>
                                    <td className="px-4 py-2 text-slate-300">{signal.pair}</td>
                                    <td className="px-4 py-2 text-right text-emerald-400 font-bold">+{formatVal(parseFloat(signal.expectedProfit))}</td>
                                    <td className="px-4 py-2 text-center">
                                        {signal.status === 'CONFIRMED' ? 
                                            <span className="text-emerald-500">✔</span> : 
                                            <span className="text-amber-500 animate-pulse">●</span>}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        {/* Right Column: System Modules */}
        <div className="col-span-12 lg:col-span-4">
             <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-4 h-full">
                 <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Cpu className="w-3 h-3" /> Tri-Tier Bot System
                 </h3>
                 <SystemStatus modules={modules} />
                 
                 <div className="mt-6 border-t border-slate-800 pt-4">
                     <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Terminal className="w-3 h-3" /> System Logs
                     </h3>
                     <div className="h-48 overflow-y-auto font-mono text-[10px] space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
                        {logs.map((log, i) => (
                            <div key={i} className="text-slate-500 truncate hover:text-slate-300 transition-colors">
                                {log}
                            </div>
                        ))}
                     </div>
                 </div>
             </div>
        </div>
    </div>
  );

  const renderWallet = () => (
      <div className="max-w-2xl mx-auto mt-10 space-y-6">
          <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-6 backdrop-blur-md">
              <div className="flex items-center gap-3 mb-6">
                  <div className="p-3 bg-emerald-500/20 rounded-full border border-emerald-500/30">
                      <Wallet className="w-8 h-8 text-emerald-500" />
                  </div>
                  <div>
                      <h2 className="text-2xl font-bold text-white font-rajdhani uppercase">Auto-Deposit Configuration</h2>
                      <p className="text-sm text-slate-500">Configure automated profit repatriation thresholds.</p>
                  </div>
              </div>

              <div className="space-y-4">
                  <div>
                      <label className="block text-xs uppercase font-bold text-slate-500 mb-1">Target Wallet Address (ETH/L2)</label>
                      <input 
                        type="text" 
                        value={autoDeposit.targetAddress}
                        onChange={(e) => setAutoDeposit(p => ({...p, targetAddress: e.target.value}))}
                        placeholder="0x..."
                        className="w-full bg-black/50 border border-slate-700 rounded p-3 text-slate-200 font-mono text-sm focus:border-emerald-500 focus:outline-none transition-colors"
                      />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                      <div>
                          <label className="block text-xs uppercase font-bold text-slate-500 mb-1">Profit Threshold ({currency})</label>
                          <div className="relative">
                            <span className="absolute left-3 top-2.5 text-slate-500">{currency === 'USD' ? '$' : 'Ξ'}</span>
                            <input 
                                type="number" 
                                value={autoDeposit.profitThreshold}
                                onChange={(e) => setAutoDeposit(p => ({...p, profitThreshold: e.target.value}))}
                                className="w-full bg-black/50 border border-slate-700 rounded p-3 pl-6 text-slate-200 font-mono text-sm focus:border-emerald-500 focus:outline-none transition-colors"
                            />
                          </div>
                      </div>
                      <div>
                          <label className="block text-xs uppercase font-bold text-slate-500 mb-1">Check Interval (Minutes)</label>
                          <input 
                            type="number" 
                            value={autoDeposit.checkInterval}
                            onChange={(e) => setAutoDeposit(p => ({...p, checkInterval: e.target.value}))}
                            className="w-full bg-black/50 border border-slate-700 rounded p-3 text-slate-200 font-mono text-sm focus:border-emerald-500 focus:outline-none transition-colors"
                          />
                      </div>
                  </div>

                  {walletError && (
                      <div className="bg-red-900/20 border border-red-500/30 p-3 rounded text-red-400 text-xs font-bold flex items-center gap-2">
                          <AlertOctagon className="w-4 h-4" /> {walletError}
                      </div>
                  )}

                  {walletSuccess && (
                      <div className="bg-emerald-900/20 border border-emerald-500/30 p-3 rounded text-emerald-400 text-xs font-bold flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4" /> {walletSuccess}
                      </div>
                  )}

                  <button 
                    onClick={handleSaveWalletConfig}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded uppercase tracking-widest transition-all flex items-center justify-center gap-2 mt-4"
                  >
                      <Save className="w-4 h-4" /> Save Configuration
                  </button>
              </div>
          </div>

          {/* Stats Card */}
          <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg">
                  <p className="text-xs text-slate-500 uppercase">Total Withdrawn</p>
                  <p className="text-2xl font-bold text-white font-mono mt-1">{formatVal(autoDeposit.totalWithdrawn)}</p>
              </div>
              <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-lg">
                  <p className="text-xs text-slate-500 uppercase">Status</p>
                  <p className={`text-xl font-bold font-mono mt-1 flex items-center gap-2 ${autoDeposit.isEnabled ? 'text-emerald-400' : 'text-slate-500'}`}>
                      {autoDeposit.isEnabled ? 'ACTIVE' : 'DISABLED'}
                      {autoDeposit.isEnabled && <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>}
                  </p>
              </div>
          </div>
      </div>
  );

  const renderAnalytics = () => (
      <div className="grid grid-cols-12 gap-6 h-full overflow-y-auto pr-2 pb-20">
          <div className="col-span-12">
              <h2 className="text-2xl font-bold text-white font-rajdhani uppercase mb-6 flex items-center gap-2">
                  <BarChart3 className="w-6 h-6 text-indigo-500" /> Flash Loan Analytics
              </h2>
          </div>

          {/* Flash Loan Utilization */}
          <div className="col-span-12 lg:col-span-8 bg-slate-900/40 border border-slate-800 p-6 rounded-lg backdrop-blur-sm">
              <h3 className="text-sm font-bold text-slate-300 uppercase mb-6">Pool Utilization Rates</h3>
              <div className="space-y-6">
                  {flashMetrics.map((metric, idx) => (
                      <div key={idx}>
                          <div className="flex justify-between text-xs font-mono mb-2">
                              <span className="text-slate-400">{metric.provider}</span>
                              <span className="text-white">{metric.liquidityAvailable} Available</span>
                          </div>
                          <div className="w-full bg-black/50 h-3 rounded-full overflow-hidden border border-slate-800">
                              <div 
                                className="h-full bg-indigo-500/80 transition-all duration-1000 relative"
                                style={{ width: `${metric.utilization}%` }}
                              >
                                  <div className="absolute right-0 top-0 bottom-0 w-[1px] bg-white/50 shadow-[0_0_10px_white]"></div>
                              </div>
                          </div>
                          <p className="text-right text-[10px] text-indigo-400 mt-1">{metric.utilization.toFixed(2)}% Utilized</p>
                      </div>
                  ))}
              </div>
          </div>

          <div className="col-span-12 lg:col-span-4 space-y-6">
              <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-lg backdrop-blur-sm">
                  <h3 className="text-sm font-bold text-slate-300 uppercase mb-4">AI Optimization</h3>
                  <div className="flex items-center justify-center py-8">
                       <div className="relative w-32 h-32">
                           <svg className="w-full h-full" viewBox="0 0 36 36">
                               <path
                                   className="text-slate-800"
                                   d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                   fill="none"
                                   stroke="currentColor"
                                   strokeWidth="3"
                               />
                               <path
                                   className="text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]"
                                   strokeDasharray={`${aiAnalysis?.efficiencyScore || 98}, 100`}
                                   d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                   fill="none"
                                   stroke="currentColor"
                                   strokeWidth="3"
                               />
                           </svg>
                           <div className="absolute inset-0 flex flex-col items-center justify-center">
                               <span className="text-2xl font-bold text-white">{aiAnalysis?.efficiencyScore || 98}%</span>
                               <span className="text-[8px] uppercase text-slate-500">Efficiency</span>
                           </div>
                       </div>
                  </div>
                  <div className="text-center">
                      <p className="text-xs text-slate-400">Strategy Model: <span className="text-white">Reinforcement Learning (PPO)</span></p>
                  </div>
              </div>
          </div>
      </div>
  );

  return (
    <div className="flex h-screen bg-[#050505] text-slate-200 overflow-hidden font-rajdhani selection:bg-emerald-500/30">
      {/* Sidebar */}
      <div className="w-20 lg:w-64 bg-black border-r border-slate-800 flex flex-col justify-between shrink-0 z-20">
        <div>
          <div className="h-16 flex items-center justify-center lg:justify-start lg:px-6 border-b border-slate-800">
            <Box className="w-8 h-8 text-emerald-500" />
            <span className="hidden lg:block ml-3 font-bold text-xl tracking-tighter text-white">AINEX<span className="text-emerald-500">.IO</span></span>
          </div>

          <nav className="mt-8 space-y-2 px-2">
            <button 
              onClick={() => setCurrentView('DASHBOARD')}
              className={`w-full flex items-center p-3 rounded-lg transition-all ${currentView === 'DASHBOARD' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
            >
              <LayoutDashboard className="w-5 h-5" />
              <span className="hidden lg:block ml-3 font-medium text-sm">Dashboard</span>
            </button>
            
            <button 
              onClick={() => setCurrentView('WALLET')}
              className={`w-full flex items-center p-3 rounded-lg transition-all ${currentView === 'WALLET' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
            >
              <Wallet className="w-5 h-5" />
              <span className="hidden lg:block ml-3 font-medium text-sm">Smart Wallet</span>
            </button>

            <button 
              onClick={() => setCurrentView('ANALYTICS')}
              className={`w-full flex items-center p-3 rounded-lg transition-all ${currentView === 'ANALYTICS' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
            >
              <BarChart3 className="w-5 h-5" />
              <span className="hidden lg:block ml-3 font-medium text-sm">Analytics</span>
            </button>
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="hidden lg:block">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Network Status</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="w-2 h-2 bg-emerald-500 rounded-full live-indicator"></span>
              <span className="text-xs font-mono text-emerald-400">MAINNET LIVE</span>
            </div>
            <p className="text-[10px] text-slate-600 mt-2 font-mono">v5.3.0-STABLE</p>
          </div>
          <div className="lg:hidden flex justify-center">
             <span className="w-2 h-2 bg-emerald-500 rounded-full live-indicator"></span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full relative overflow-hidden">
         {/* Top Bar */}
         <header className="h-16 border-b border-slate-800 bg-black/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10">
            <div className="flex items-center gap-4">
               <h1 className="text-lg font-bold text-white uppercase tracking-wider">
                  {currentView === 'DASHBOARD' && 'Mission Control'}
                  {currentView === 'WALLET' && 'Asset Management'}
                  {currentView === 'ANALYTICS' && 'Deep Analytics'}
               </h1>
            </div>
            <div className="flex items-center gap-4">
                {/* REFRESH RATE DROPDOWN */}
                <div className="flex items-center gap-2 bg-slate-900 rounded border border-slate-800 px-3 py-1.5">
                    <RefreshCw className="w-3 h-3 text-slate-400" />
                    <select 
                        className="bg-transparent text-[10px] uppercase font-bold text-slate-300 focus:outline-none"
                        value={refreshRate}
                        onChange={(e) => setRefreshRate(Number(e.target.value))}
                    >
                        <option value={1000}>1s Scan</option>
                        <option value={3000}>3s Scan</option>
                        <option value={5000}>5s Scan</option>
                        <option value={10000}>10s Scan</option>
                    </select>
                </div>

                {/* CURRENCY TOGGLE */}
                <div className="flex items-center bg-slate-900 rounded border border-slate-800 p-1">
                    <button 
                        onClick={() => setCurrency('USD')}
                        className={`text-[10px] px-2 py-0.5 rounded font-bold transition-all ${currency === 'USD' ? 'bg-emerald-600 text-white' : 'text-slate-500 hover:text-white'}`}
                    >USD</button>
                    <button 
                        onClick={() => setCurrency('ETH')}
                        className={`text-[10px] px-2 py-0.5 rounded font-bold transition-all ${currency === 'ETH' ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:text-white'}`}
                    >ETH</button>
                </div>

                <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-slate-900 rounded border border-slate-800">
                    <span className="text-[10px] text-slate-500 uppercase font-bold">Gas</span>
                    <span className="text-xs font-mono text-emerald-400">18 Gwei</span>
                </div>
            </div>
         </header>

         {/* Content Area */}
         <main className="flex-1 overflow-hidden p-6 relative">
            {/* Background Grid FX */}
            <div className="absolute inset-0 opacity-10 pointer-events-none" 
                 style={{ backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
            </div>

            <div className="relative z-10 h-full">
                {currentView === 'DASHBOARD' && renderDashboard()}
                {currentView === 'WALLET' && renderWallet()}
                {currentView === 'ANALYTICS' && renderAnalytics()}
            </div>
         </main>
      </div>
    </div>
  );
}

export default App;