import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle, ExternalLink, Shield, Download } from 'lucide-react';
import { VerificationStatus, validateLiveModeAuthenticity, generateVerificationReport } from '../services/blockchainValidator';
import { generateVerificationLink } from '../services/etherscanService';

interface LiveModeValidatorProps {
    isLive: boolean;
    recentTransactions: Array<{ id: string; txHash: string; profit: number; status: string }>;
    chain: 'ethereum' | 'arbitrum' | 'base';
}

const LiveModeValidator: React.FC<LiveModeValidatorProps> = ({ isLive, recentTransactions, chain }) => {
    const [validationStatus, setValidationStatus] = useState<{
        isGenuineLive: boolean;
        verifiedCount: number;
        totalCount: number;
        verificationRate: number;
    }>({
        isGenuineLive: false,
        verifiedCount: 0,
        totalCount: 0,
        verificationRate: 0
    });

    const [isValidating, setIsValidating] = useState(false);
    const [lastValidation, setLastValidation] = useState<number>(0);

    // Validate LIVE mode authenticity
    useEffect(() => {
        if (!isLive || recentTransactions.length === 0) {
            setValidationStatus({
                isGenuineLive: false,
                verifiedCount: 0,
                totalCount: 0,
                verificationRate: 0
            });
            return;
        }

        const validateMode = async () => {
            setIsValidating(true);
            try {
                const txHashes = recentTransactions
                    .filter(t => t.txHash && t.txHash.startsWith('0x'))
                    .map(t => t.txHash)
                    .slice(0, 10); // Validate last 10 transactions

                if (txHashes.length === 0) {
                    // No valid tx hashes - likely simulation mode or waiting for first trade
                    setValidationStatus({
                        isGenuineLive: false,
                        verifiedCount: 0,
                        totalCount: 0,
                        verificationRate: 0
                    });
                    setLastValidation(Date.now());
                    setIsValidating(false);
                    return;
                }

                // Check if these are simulated/fake transactions
                // Real tx hashes are 66 characters (0x + 64 hex chars)
                const realTxHashes = txHashes.filter(hash => hash.length === 66);

                if (realTxHashes.length === 0) {
                    // All transactions are simulated (short fake hashes)
                    setValidationStatus({
                        isGenuineLive: false,
                        verifiedCount: 0,
                        totalCount: txHashes.length,
                        verificationRate: 0
                    });
                    setLastValidation(Date.now());
                    setIsValidating(false);
                    return;
                }

                // Verify real blockchain transactions
                const result = await validateLiveModeAuthenticity(realTxHashes, chain);
                setValidationStatus(result);
                setLastValidation(Date.now());
            } catch (error) {
                console.error('Validation failed:', error);
                setValidationStatus({
                    isGenuineLive: false,
                    verifiedCount: 0,
                    totalCount: recentTransactions.length,
                    verificationRate: 0
                });
            } finally {
                setIsValidating(false);
            }
        };

        // Validate every 30 seconds
        validateMode();
        const interval = setInterval(validateMode, 30000);
        return () => clearInterval(interval);
    }, [isLive, recentTransactions, chain]);

    const handleExportReport = async () => {
        try {
            const report = await generateVerificationReport(recentTransactions, chain);
            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `verification-report-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Failed to export report:', error);
        }
    };

    const getStatusBadge = () => {
        if (!isLive) {
            return (
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                    <span className="text-xs font-light text-white">SIMULATION MODE</span>
                </div>
            );
        }

        if (isValidating) {
            return (
                <div className="flex items-center gap-2 px-3 py-2 bg-blue-900/30 border border-blue-500/30 rounded-lg">
                    <Clock className="w-4 h-4 text-blue-400 animate-spin" />
                    <span className="text-xs font-light text-blue-400">VALIDATING...</span>
                </div>
            );
        }

        if (validationStatus.isGenuineLive) {
            return (
                <div className="flex items-center gap-2 px-3 py-2 bg-emerald-900/30 border border-emerald-500/30 rounded-lg">
                    <Shield className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-light text-emerald-400">BLOCKCHAIN VERIFIED</span>
                </div>
            );
        }

        // If we have transactions but they're not verified (simulated trades)
        if (validationStatus.totalCount > 0 && !validationStatus.isGenuineLive) {
            return (
                <div className="flex items-center gap-2 px-3 py-2 bg-amber-900/30 border border-amber-500/30 rounded-lg">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-light text-amber-400">DEMO MODE</span>
                </div>
            );
        }

        // No transactions yet - waiting for first trade
        return (
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="text-xs font-light text-slate-400">AWAITING TRADES</span>
            </div>
        );
    };

    if (!isLive) {
        return (
            <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        <div>
                            <div className="text-xs font-light text-white">Simulation Mode Active</div>
                            <div className="text-xs font-light text-slate-400">Transactions are not on-chain</div>
                        </div>
                    </div>
                    {getStatusBadge()}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-emerald-400" />
                    <div>
                        <div className="text-xs font-light text-white">Blockchain Verification</div>
                        <div className="text-xs font-light text-slate-400">
                            Third-party validated via Etherscan
                        </div>
                    </div>
                </div>
                {getStatusBadge()}
            </div>

            {/* Verification Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Verified</div>
                    <div className="text-sm font-light text-emerald-400">
                        {validationStatus.verifiedCount}/{validationStatus.totalCount}
                    </div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Success Rate</div>
                    <div className={`text-sm font-light ${validationStatus.verificationRate >= 80 ? 'text-emerald-400' : 'text-yellow-400'
                        }`}>
                        {validationStatus.verificationRate.toFixed(1)}%
                    </div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Last Check</div>
                    <div className="text-sm font-light text-slate-300">
                        {lastValidation ? new Date(lastValidation).toLocaleTimeString() : 'Never'}
                    </div>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-3 border border-slate-700">
                    <div className="text-xs font-light text-slate-400 mb-1">Chain</div>
                    <div className="text-sm font-light text-blue-400 capitalize">
                        {chain}
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
                <button
                    onClick={handleExportReport}
                    className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-xs font-light transition-colors"
                >
                    <Download className="w-3 h-3" />
                    Export Report
                </button>
                <a
                    href={generateVerificationLink(recentTransactions[0]?.txHash || '', chain)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-light transition-colors"
                >
                    <ExternalLink className="w-3 h-3" />
                    Verify on Etherscan
                </a>
            </div>

            {/* Warning if verification rate is low */}
            {validationStatus.verificationRate < 80 && validationStatus.totalCount > 0 && (
                <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                    <div className="flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5" />
                        <div>
                            <div className="text-xs font-light text-yellow-400 mb-1">Low Verification Rate</div>
                            <div className="text-xs font-light text-yellow-500/80">
                                Some transactions could not be verified on-chain. This may indicate network issues or pending confirmations.
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiveModeValidator;
