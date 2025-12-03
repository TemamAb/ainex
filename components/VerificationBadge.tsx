import React from 'react';
import { CheckCircle, XCircle, Clock, ExternalLink } from 'lucide-react';
import { VerificationStatus } from '../services/blockchainValidator';
import { generateVerificationLink } from '../services/etherscanService';

interface VerificationBadgeProps {
    status: VerificationStatus;
    txHash?: string;
    chain?: 'ethereum' | 'arbitrum' | 'base';
    blockNumber?: number;
    size?: 'sm' | 'md';
}

const VerificationBadge: React.FC<VerificationBadgeProps> = ({
    status,
    txHash,
    chain = 'ethereum',
    blockNumber,
    size = 'sm'
}) => {
    const getStatusConfig = () => {
        switch (status) {
            case 'VERIFIED':
                return {
                    icon: <CheckCircle className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
                    text: 'VERIFIED',
                    bgColor: 'bg-emerald-900/30',
                    borderColor: 'border-emerald-500/30',
                    textColor: 'text-emerald-400'
                };
            case 'PENDING':
                return {
                    icon: <Clock className={`${size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} animate-spin`} />,
                    text: 'PENDING',
                    bgColor: 'bg-yellow-900/30',
                    borderColor: 'border-yellow-500/30',
                    textColor: 'text-yellow-400'
                };
            case 'FAILED':
                return {
                    icon: <XCircle className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
                    text: 'FAILED',
                    bgColor: 'bg-red-900/30',
                    borderColor: 'border-red-500/30',
                    textColor: 'text-red-400'
                };
            case 'UNVERIFIED':
            default:
                return {
                    icon: <Clock className={size === 'sm' ? 'w-3 h-3' : 'w-4 h-4'} />,
                    text: 'UNVERIFIED',
                    bgColor: 'bg-slate-700/50',
                    borderColor: 'border-slate-600',
                    textColor: 'text-slate-400'
                };
        }
    };

    const config = getStatusConfig();
    const explorerLink = txHash ? generateVerificationLink(txHash, chain) : null;

    return (
        <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 px-2 py-1 ${config.bgColor} border ${config.borderColor} rounded`}>
                <span className={config.textColor}>{config.icon}</span>
                <span className={`text-xs font-light ${config.textColor}`}>{config.text}</span>
            </div>

            {explorerLink && status === 'VERIFIED' && (
                <a
                    href={explorerLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs font-light text-blue-400 hover:text-blue-300 transition-colors"
                    title="View on blockchain explorer"
                >
                    <ExternalLink className="w-3 h-3" />
                </a>
            )}

            {blockNumber && (
                <span className="text-xs font-light text-slate-500">
                    #{blockNumber}
                </span>
            )}
        </div>
    );
};

export default VerificationBadge;
