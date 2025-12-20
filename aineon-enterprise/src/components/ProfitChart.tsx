import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ProfitData } from '../types';

interface ProfitChartProps {
  profitData: ProfitData | null;
}

const ProfitChart: React.FC<ProfitChartProps> = ({ profitData }) => {
  // Mock data for chart (in real app, this would come from API)
  const chartData = [
    { time: '09:00', profit: 1200 },
    { time: '10:00', profit: 1500 },
    { time: '11:00', profit: 1800 },
    { time: '12:00', profit: 2200 },
    { time: '13:00', profit: 2500 },
    { time: '14:00', profit: 2800 },
    { time: '15:00', profit: 3100 },
    { time: '16:00', profit: 3500 },
  ];

  return (
    <div className="bg-gray-800/50 rounded-xl p-6 border border-gray-700 h-full">
      <h2 className="text-xl font-bold mb-6">Profit Trend</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
            <XAxis dataKey="time" stroke="#888" />
            <YAxis stroke="#888" tickFormatter={(value) => `$${value}`} />
            <Tooltip 
              formatter={(value) => [`$${value}`, 'Profit']}
              labelStyle={{ color: '#fff' }}
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
            />
            <Line 
              type="monotone" 
              dataKey="profit" 
              stroke="#0ea5e9" 
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-sm text-gray-400">
        Real-time profit tracking with 5-minute intervals
      </div>
    </div>
  );
};

export default ProfitChart;
