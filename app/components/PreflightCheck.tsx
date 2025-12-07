'use client';
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Shield, Zap, Wifi, Wallet, Database, AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react';
import { ethers, BrowserProvider } from 'ethers';

export interface PreflightRef {
  runChecks: () => Promise<void>;
}

interface PreflightCheckProps {
  onComplete?: (passed: boolean) => void;
}

interface CheckItem {
  status: 'pending' | 'pass' | 'fail';
  message: string;
}

interface PreflightChecks {
  blockchain: CheckItem;
  wallet: CheckItem;
  balance: CheckItem;
  gasPrice: CheckItem;
}

export const PreflightCheck = React.forwardRef<PreflightRef, PreflightCheckProps>(({ onComplete }, ref) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [checks, setChecks] = useState<PreflightChecks>({
    // REAL CHECKS ONLY
    blockchain: { status: 'pending', message: 'Waiting to check connection...' },
    wallet: { status: 'pending', message: 'Waiting to check wallet...' },
    balance: { status: 'pending', message: 'Waiting to check balance...' },
    gasPrice: { status: 'pending', message: 'Waiting to check gas price...' },
  });

  const [allPassed, setAllPassed] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  // Expose runChecks to parent
  React.useImperativeHandle(ref, () => ({
    runChecks: runPreflightChecks
  }));

  const runPreflightChecks = async () => {
    if (isRunning) return;
    setIsExpanded(true);
    setIsRunning(true);
    setProgress(10);
    setAllPassed(false);

    const newChecks = { ...checks };
    let passed = true;

    try {
      // 1. CHECK BLOCKCHAIN CONNECTION
      newChecks.blockchain = { status: 'pending', message: 'Connecting to provider...' };
      setChecks({ ...newChecks });

      if (typeof window === 'undefined' || !(window as any).ethereum) {
        throw new Error("No crypto wallet found. Please install MetaMask.");
      }

      const provider = new BrowserProvider((window as any).ethereum);
      const network = await provider.getNetwork();

      newChecks.blockchain = {
        status: 'pass',
        message: `Connected to ${network.name} (Chain ID: ${network.chainId})`
      };
      setChecks({ ...newChecks });
      setProgress(40);

      // 2. CHECK WALLET & BALANCE
      newChecks.wallet = { status: 'pending', message: 'Requesting account access...' };
      setChecks({ ...newChecks });

      const signer = await provider.getSigner();
      const address = await signer.getAddress();
      const balance = await provider.getBalance(address);
      const balanceEth = ethers.formatEther(balance);

      newChecks.wallet = { status: 'pass', message: `Wallet connected: ${address.slice(0, 6)}...${address.slice(-4)}` };
      newChecks.balance = { status: 'pass', message: `Balance: ${parseFloat(balanceEth).toFixed(4)} ETH` };
      setChecks({ ...newChecks });
      setProgress(70);

      // 3. CHECK GAS PRICE (ORACLE)
      newChecks.gasPrice = { status: 'pending', message: 'Fetching live gas price...' };
      setChecks({ ...newChecks });

      const feeData = await provider.getFeeData();
      const gasPrice = feeData.gasPrice ? ethers.formatUnits(feeData.gasPrice, 'gwei') : 'Unknown';

      newChecks.gasPrice = { status: 'pass', message: `Live Gas Price: ${parseFloat(gasPrice).toFixed(2)} Gwei` };
      setChecks({ ...newChecks });
      setProgress(100);

    } catch (error: any) {
      console.error("Preflight failed:", error);
      passed = false;

      const errorMessage = error?.message || "Unknown error occurred";

      // Mark current pending check as failed
      if (newChecks.blockchain.status === 'pending') newChecks.blockchain = { status: 'fail', message: errorMessage };
      else if (newChecks.wallet.status === 'pending') newChecks.wallet = { status: 'fail', message: errorMessage };
      else if (newChecks.gasPrice.status === 'pending') newChecks.gasPrice = { status: 'fail', message: errorMessage };

      setChecks({ ...newChecks });
    }

    setIsRunning(false);
    setAllPassed(passed);
    onComplete?.(passed);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass': return <CheckCircle size={16} className="text-[#00FF9D]" />;
      case 'fail': return <AlertCircle size={16} className="text-red-500" />;
      case 'pending': return <Clock size={16} className="text-yellow-500 animate-spin" />;
      default: return null;
    }
  };

  const passedCount = Object.values(checks).filter((c: any) => c.status === 'pass').length;
  const totalCount = Object.keys(checks).length;

  return (
    <div className="mb-6">
      {/* PREFLIGHT HEADER */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all border ${allPassed ? 'bg-[#00FF9D]/10 border-[#00FF9D]/50' : 'bg-red-500/10 border-red-500/50'}`}
      >
        <div className="flex-shrink-0">
          {isExpanded ? <ChevronDown size={20} className={allPassed ? 'text-[#00FF9D]' : 'text-red-500'} /> : <ChevronRight size={20} className={allPassed ? 'text-[#00FF9D]' : 'text-red-500'} />}
        </div>
        <Shield size={20} className={allPassed ? 'text-[#00FF9D]' : 'text-red-500'} />
        <div className="flex-1 text-left">
          <div className={`font-bold text-xs uppercase tracking-widest ${allPassed ? 'text-[#00FF9D]' : 'text-red-500'}`}>
            {allPassed ? 'SYSTEM READY' : isRunning ? 'VALIDATING LIVE DATA...' : 'PREFLIGHT REQUIRED'}
          </div>
          <div className="text-[10px] text-gray-400 mt-1">
            {isRunning ? 'Connecting to blockchain...' : allPassed ? 'Live connection established' : 'Click to validate connection'}
          </div>
        </div>
        <div className="flex-shrink-0 w-32 h-2 bg-gray-800 rounded overflow-hidden">
          <div className={`h-full transition-all duration-300 ${allPassed ? 'bg-[#00FF9D]' : 'bg-red-500'}`} style={{ width: `${progress}%` }} />
        </div>
        <div className={`text-xs font-bold ${allPassed ? 'text-[#00FF9D]' : 'text-red-500'}`}>{passedCount}/{totalCount}</div>
      </button>

      {/* DETAILS */}
      {isExpanded && (
        <div className="mt-2 bg-[#181b1f] border border-[#22252b] rounded-lg p-4 animate-in fade-in">
          <div className="space-y-2">
            {Object.entries(checks).map(([key, check]) => (
              <div key={key} className="flex items-center gap-3 text-xs">
                <div className="w-5">{getStatusIcon(check.status)}</div>
                <div className="w-24 uppercase text-gray-500 font-bold">{key}</div>
                <div className="flex-1 text-gray-300 font-mono">{check.message}</div>
              </div>
            ))}
          </div>

          {!isRunning && !allPassed && (
            <button onClick={runPreflightChecks} className="mt-4 w-full py-2 bg-[#5794F2] text-white font-bold rounded hover:bg-[#4a84db] transition-colors flex items-center justify-center gap-2">
              <RefreshCw size={16} /> RETRY CONNECTION
            </button>
          )}
        </div>
      )}
    </div>
  );
});

PreflightCheck.displayName = 'PreflightCheck';
