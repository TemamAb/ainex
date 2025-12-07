'use client';
import React, { useState } from 'react';
import { Rocket, Wallet, CheckCircle } from 'lucide-react';

interface OnboardingWizardProps {
    onComplete: (engineAddress: string) => void;
}

export const OnboardingWizard = ({ onComplete }: OnboardingWizardProps) => {
    const [step, setStep] = useState(1);
    const [deploying, setDeploying] = useState(false);

    const handleStart = async () => {
        setStep(2);
        // Auto-connect wallet
        if (typeof window !== 'undefined' && (window as any).ethereum) {
            try {
                await (window as any).ethereum.request({ method: 'eth_requestAccounts' });
                setStep(3);
                await handleDeploy();
            } catch (error) {
                alert('Please connect your wallet to continue');
            }
        }
    };

    const handleDeploy = async () => {
        setDeploying(true);
        // Simulate deployment (in production, call actual deploy script)
        await new Promise(resolve => setTimeout(resolve, 3000));
        const mockAddress = '0x' + Math.random().toString(16).slice(2, 42);
        setDeploying(false);
        setStep(4);
        setTimeout(() => onComplete(mockAddress), 1000);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full">
                {step === 1 && (
                    <div className="text-center space-y-6">
                        <Rocket className="mx-auto text-[#00FF9D]" size={80} />
                        <h1 className="text-5xl font-bold text-white">Welcome to AiNex</h1>
                        <p className="text-xl text-gray-400">
                            AI-Powered Flash Loan Arbitrage Engine
                        </p>
                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 space-y-3">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="text-green-400" size={20} />
                                <span className="text-gray-300">Zero capital required (Flash Loans)</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <CheckCircle className="text-green-400" size={20} />
                                <span className="text-gray-300">AI-optimized strategies</span>
                            </div>
                            <div className="flex items-center gap-3">
                                <CheckCircle className="text-green-400" size={20} />
                                <span className="text-gray-300">Expected: $500-$2,000/day</span>
                            </div>
                        </div>
                        <button
                            onClick={handleStart}
                            className="bg-[#00FF9D] hover:bg-[#00DD85] text-black font-bold py-4 px-8 rounded-lg text-lg transition-colors"
                        >
                            START EARNING NOW
                        </button>
                        <p className="text-sm text-gray-500">
                            Setup takes ~30 seconds • Gas fee: ~$5
                        </p>
                    </div>
                )}

                {step === 2 && (
                    <div className="text-center space-y-6">
                        <Wallet className="mx-auto text-blue-400 animate-pulse" size={80} />
                        <h2 className="text-3xl font-bold text-white">Connecting Wallet...</h2>
                        <p className="text-gray-400">Please approve the MetaMask connection</p>
                    </div>
                )}

                {step === 3 && (
                    <div className="text-center space-y-6">
                        <div className="relative">
                            <Rocket className="mx-auto text-purple-400 animate-bounce" size={80} />
                        </div>
                        <h2 className="text-3xl font-bold text-white">Deploying Your Engine...</h2>
                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6">
                            <div className="w-full bg-gray-700 rounded-full h-3 mb-4">
                                <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full animate-pulse" style={{ width: '75%' }}></div>
                            </div>
                            <div className="space-y-2 text-sm text-gray-400">
                                <p>✓ Smart contract compiled</p>
                                <p>✓ Modules configured</p>
                                <p className="text-white">⏳ Deploying to blockchain...</p>
                            </div>
                        </div>
                    </div>
                )}

                {step === 4 && (
                    <div className="text-center space-y-6">
                        <CheckCircle className="mx-auto text-green-400" size={80} />
                        <h2 className="text-3xl font-bold text-white">Engine Deployed!</h2>
                        <p className="text-gray-400">Starting in SIMULATION mode...</p>
                    </div>
                )}
            </div>
        </div>
    );
};
