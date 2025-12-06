import React from 'react';
import { CheckCircle, Loader2, Circle } from 'lucide-react';
import { ActivationStep } from '../services/activationService';

interface ActivationOverlayProps {
    title: string;
    steps: ActivationStep[];
    isVisible: boolean;
}

const ActivationOverlay: React.FC<ActivationOverlayProps> = ({ title, steps, isVisible }) => {
    if (!isVisible) return null;

    return (
        <div className="absolute inset-0 z-50 bg-[#0b0c0e]/95 flex flex-col items-center justify-center p-8 backdrop-blur-sm">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-lg p-6 shadow-2xl">
                <h2 className="text-xl font-bold text-white mb-6 text-center animate-pulse">{title}</h2>

                <div className="space-y-4">
                    {steps.map((step) => (
                        <div key={step.id} className="flex items-center gap-4 p-3 rounded bg-slate-800/50 border border-slate-700/50">
                            <div className="flex-shrink-0">
                                {step.status === 'COMPLETED' && <CheckCircle className="w-5 h-5 text-emerald-500" />}
                                {step.status === 'IN_PROGRESS' && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                                {step.status === 'PENDING' && <Circle className="w-5 h-5 text-slate-600" />}
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className={`text-sm font-medium ${step.status === 'IN_PROGRESS' ? 'text-blue-400' :
                                        step.status === 'COMPLETED' ? 'text-emerald-400' : 'text-slate-400'
                                    }`}>
                                    {step.label}
                                </div>
                                {step.status !== 'PENDING' && step.details && (
                                    <div className="text-xs text-slate-500 mt-0.5 truncate">
                                        {step.details}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-6 text-center text-xs text-slate-600">
                    System Handshake in Progress... Please Wait.
                </div>
            </div>
        </div>
    );
};

export default ActivationOverlay;
