import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
    errorInfo: ErrorInfo | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
        errorInfo: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error, errorInfo: null };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        this.setState({
            error,
            errorInfo,
        });
    }

    private handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null,
        });
        // Reload the page to reset state
        window.location.reload();
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-red-900/50 rounded-xl p-8 max-w-2xl w-full shadow-2xl">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-3 bg-red-950/30 rounded-full">
                                <AlertTriangle className="w-8 h-8 text-red-400" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-white">System Error Detected</h1>
                                <p className="text-slate-400 text-sm mt-1">The AiNex Engine encountered an unexpected error</p>
                            </div>
                        </div>

                        <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 mb-6">
                            <p className="text-red-400 font-mono text-sm mb-2">
                                {this.state.error?.toString()}
                            </p>
                            {this.state.errorInfo && (
                                <details className="mt-4">
                                    <summary className="text-slate-500 text-xs cursor-pointer hover:text-slate-300 transition-colors">
                                        Stack Trace (Click to expand)
                                    </summary>
                                    <pre className="text-slate-600 text-xs mt-2 overflow-auto max-h-64">
                                        {this.state.errorInfo.componentStack}
                                    </pre>
                                </details>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={this.handleReset}
                                className="flex-1 flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-3 px-6 rounded-lg transition-colors"
                            >
                                <RefreshCw className="w-5 h-5" />
                                Restart Engine
                            </button>
                            <button
                                onClick={() => window.location.href = '/'}
                                className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold py-3 px-6 rounded-lg transition-colors"
                            >
                                Return to Home
                            </button>
                        </div>

                        <div className="mt-6 pt-6 border-t border-slate-800">
                            <p className="text-slate-500 text-xs text-center">
                                If this error persists, please contact support with the error details above.
                            </p>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
