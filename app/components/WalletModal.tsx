import React, { useState } from 'react';
import { X, Wallet, Hash, ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';
import { WalletState } from '../types';

interface WalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (wallet: WalletState) => void;
}

const WalletModal: React.FC<WalletModalProps> = ({ isOpen, onClose, onConnect }) => {
  const [inputAddress, setInputAddress] = useState('');
  const [error, setError] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  if (!isOpen) return null;

  const handleManualConnect = () => {
    if (!inputAddress.startsWith('0x') || inputAddress.length !== 42) {
      setError('Invalid Ethereum Address format.');
      return;
    }
    
    setIsConnecting(true);
    // Simulate verification delay
    setTimeout(() => {
        onConnect({
            isConnected: true,
            address: inputAddress,
            type: 'EOA',
            balance: Math.random() * 100
        });
        setIsConnecting(false);
        onClose();
    }, 1500);
  };

  const handleWeb3Connect = () => {
    setIsConnecting(true);
    // Mock Web3 Connection sequence
    setTimeout(() => {
        onConnect({
            isConnected: true,
            address: '0x71C...9A2',
            type: 'SMART_WALLET',
            balance: 145.2
        });
        setIsConnecting(false);
        onClose();
    }, 2000);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl relative animate-fadeIn">
        <button 
            onClick={onClose} 
            className="absolute top-4 right-4 text-slate-500 hover:text-white transition-colors"
            disabled={isConnecting}
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-8">
            <div className="w-16 h-16 bg-cyan-900/30 rounded-full flex items-center justify-center mx-auto mb-4 border border-cyan-500/30 shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                <ShieldCheck className="w-8 h-8 text-cyan-400" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">Authenticate Execution Node</h2>
            <p className="text-slate-400 text-sm mt-2">Connect a whitelisted wallet or input your institutional executor address to access the Engine.</p>
        </div>

        <div className="space-y-4">
            <button 
                onClick={handleWeb3Connect}
                disabled={isConnecting}
                className="w-full flex items-center justify-between p-4 bg-slate-800 hover:bg-slate-750 border border-slate-700 rounded-xl transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
            >
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-500/20 rounded-lg">
                        <Wallet className="w-5 h-5 text-orange-400" />
                    </div>
                    <div className="text-left">
                        <p className="font-bold text-slate-200 group-hover:text-white transition-colors">Browser Wallet</p>
                        <p className="text-xs text-slate-500">MetaMask, Rabby, Frame</p>
                    </div>
                </div>
                {isConnecting ? <Loader2 className="w-5 h-5 animate-spin text-cyan-400" /> : <div className="w-2 h-2 rounded-full bg-slate-600 group-hover:bg-emerald-400 transition-colors"></div>}
            </button>

            <div className="relative py-2">
                <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-800"></div>
                </div>
                <div className="relative flex justify-center text-xs uppercase font-bold tracking-wider">
                    <span className="bg-slate-900 px-2 text-slate-600">Or Manual Entry</span>
                </div>
            </div>

            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <div className="flex items-center gap-2 mb-2">
                    <Hash className="w-4 h-4 text-slate-500" />
                    <span className="text-sm font-medium text-slate-300">Executor Address</span>
                </div>
                <div className="flex gap-2">
                    <input 
                        type="text" 
                        value={inputAddress}
                        disabled={isConnecting}
                        onChange={(e) => {
                            setInputAddress(e.target.value);
                            setError('');
                        }}
                        placeholder="0x..."
                        className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none font-mono placeholder:text-slate-600 disabled:opacity-50"
                    />
                    <button 
                        onClick={handleManualConnect}
                        disabled={isConnecting}
                        className="bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-colors flex items-center justify-center min-w-[70px]"
                    >
                        {isConnecting ? <Loader2 className="w-4 h-4 animate-spin" /> : "Load"}
                    </button>
                </div>
                {error && (
                    <div className="flex items-center gap-2 mt-2 text-red-400 text-xs animate-pulse">
                        <AlertTriangle className="w-3 h-3" />
                        {error}
                    </div>
                )}
            </div>
        </div>
        
        <div className="mt-6 text-center border-t border-slate-800 pt-4">
            <p className="text-[10px] text-slate-500">
                By connecting, you verify that you hold an Institutional License for AiNex Engine v2.4. Unauthorized access attempts will be logged.
            </p>
        </div>
      </div>
    </div>
  );
};

export default WalletModal;