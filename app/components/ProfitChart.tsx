import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { X } from 'lucide-react';

interface ProfitChartProps {
    currentProfit: number;
    theoreticalMax: number;
    onClose: () => void;
}

export const ProfitChart = ({ currentProfit, theoreticalMax, onClose }: ProfitChartProps) => {
    // Generate 90-day projection data
    const data = [];
    let accumulated = currentProfit;
    // Assume a compounding growth based on current performance
    // If we are capturing X per block, extrapolate to days
    // 1 Day = ~7200 blocks. 
    // Let's assume 'currentProfit' passed here is a "Daily Run Rate" for visualization purposes
    // or we calculate a run rate.

    const dailyRunRate = Math.max(0.05, currentProfit * 7200); // Mock run rate if profit is low/zero

    for (let i = 0; i <= 90; i++) {
        // Compound slightly
        accumulated += dailyRunRate * (1 + (i * 0.001));
        data.push({
            day: `Day ${i}`,
            profit: accumulated,
            baseline: i * dailyRunRate // Linear baseline
        });
    }

    return (
        <div className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#111217] border border-[#22252b] w-full max-w-4xl rounded-lg shadow-2xl overflow-hidden">
                <div className="flex justify-between items-center p-6 border-b border-[#22252b]">
                    <div>
                        <h2 className="text-2xl font-bold text-white">90-Day Wealth Projection</h2>
                        <p className="text-gray-400 text-sm">AI Compounding Trajectory based on current efficiency</p>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#00FF9D" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#00FF9D" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#22252b" />
                            <XAxis dataKey="day" stroke="#666" tick={{ fontSize: 12 }} interval={14} />
                            <YAxis stroke="#666" tick={{ fontSize: 12 }} unit=" ETH" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#181b1f', borderColor: '#22252b', color: '#fff' }}
                                itemStyle={{ color: '#00FF9D' }}
                            />
                            <Area
                                type="monotone"
                                dataKey="profit"
                                stroke="#00FF9D"
                                strokeWidth={2}
                                fillOpacity={1}
                                fill="url(#colorProfit)"
                                name="Projected Wealth"
                            />
                            <Line
                                type="monotone"
                                dataKey="baseline"
                                stroke="#5794F2"
                                strokeDasharray="5 5"
                                dot={false}
                                name="Linear Baseline"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="bg-[#181b1f] p-6 flex justify-between items-center">
                    <div>
                        <div className="text-gray-500 text-xs uppercase tracking-wider">Projected 90-Day Total</div>
                        <div className="text-3xl font-bold text-[#00FF9D]">{data[90].profit.toFixed(2)} ETH</div>
                    </div>
                    <div className="text-right">
                        <div className="text-gray-500 text-xs uppercase tracking-wider">Growth Factor</div>
                        <div className="text-xl font-bold text-white">{(data[90].profit / (data[0].profit || 1)).toFixed(1)}x</div>
                    </div>
                </div>
            </div>
        </div>
    );
};
