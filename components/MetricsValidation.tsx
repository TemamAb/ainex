import React, { useState, useEffect } from 'react';
import { RefreshCw, MousePointer, Hash, Clock, CheckCircle, XCircle } from 'lucide-react';

interface ValidationEvent {
    id: string;
    type: 'CLICK' | 'TRANSACTION' | 'API_CALL' | 'VALIDATION';
    timestamp: number;
    status: 'SUCCESS' | 'FAILED' | 'PENDING';
    details: string;
    hash: string;
}

interface MetricsValidationProps {
    events?: ValidationEvent[];
}

const MetricsValidation: React.FC<MetricsValidationProps> = ({ events = [] }) => {
    // No internal state for events, fully controlled by props
    // This ensures only REAL system events are displayed


    return (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Hash className="w-6 h-6 text-purple-400" />
                    <div>
                        <h2 className="text-xl font-bold text-white">Metrics Validation</h2>
                        <p className="text-sm text-slate-400">Real-time system event verification</p>
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                {events.map((event, index) => (
                    <div
                        key={event.id}
                        className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-3 flex items-center justify-between hover:border-slate-600 transition-colors animate-in fade-in slide-in-from-bottom-2"
                        style={{ animationDelay: `${index * 50}ms` }}
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                                <span className="text-xs font-mono text-slate-400">{index + 1}</span>
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${event.type === 'TRANSACTION' ? 'bg-green-500/20 text-green-400' :
                                        event.type === 'CLICK' ? 'bg-blue-500/20 text-blue-400' :
                                            event.type === 'API_CALL' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-purple-500/20 text-purple-400'
                                        }`}>
                                        {event.type}
                                    </span>
                                    <span className="text-sm text-slate-300 font-mono">{event.hash}</span>
                                </div>
                                <div className="text-xs text-slate-500 mt-1">{event.details}</div>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="text-right">
                                <div className={`text-xs font-bold flex items-center gap-1 justify-end ${event.status === 'SUCCESS' ? 'text-green-400' :
                                    event.status === 'FAILED' ? 'text-red-400' :
                                        'text-yellow-400'
                                    }`}>
                                    {event.status === 'SUCCESS' && <CheckCircle className="w-3 h-3" />}
                                    {event.status === 'FAILED' && <XCircle className="w-3 h-3" />}
                                    {event.status === 'PENDING' && <Clock className="w-3 h-3" />}
                                    {event.status}
                                </div>
                                <div className="text-[10px] text-slate-500 mt-0.5">
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default MetricsValidation;
