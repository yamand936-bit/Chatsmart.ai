import React from 'react';
import { ComposedChart, BarChart, Bar, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface AdminChartsProps {
  profitData: any[];
  businesses: any[];
  tAdmin: (key: string) => string;
}

export default function AdminCharts({ profitData, businesses, tAdmin }: AdminChartsProps) {
  return (
    <div className="grid gap-6">
      <div className="h-80 w-full bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <h4 className="text-lg font-bold text-slate-700 mb-4">{tAdmin('economic.profit') || 'Economic Profit/Cost ($)'}</h4>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={profitData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="Profit" fill="#10b981" name={tAdmin('economic.profit') || 'Profit'} radius={[4, 4, 0, 0]} />
            <Bar dataKey="Cost" fill="#ef4444" name={tAdmin('economic.cost') || 'Cost'} radius={[4, 4, 0, 0]} />
            <Line type="monotone" dataKey={tAdmin('forecast.expected') || 'Expected Profit'} stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {businesses.map((biz) => {
        const quota = biz.monthly_quota || 10000;
        const usage = biz.token_usage || 0;
        const percentage = Math.min((usage / quota) * 100, 100);
        
        let progressColor = 'bg-blue-500';
        if (percentage >= 90) progressColor = 'bg-red-500';
        else if (percentage >= 75) progressColor = 'bg-yellow-500';

        return (
          <div key={biz.id} className="bg-slate-50/50 p-5 rounded-2xl border border-slate-200">
            <div className="flex justify-between items-center mb-3 text-sm">
              <span className="font-semibold text-slate-800">{biz.name}</span>
              <span className="text-slate-500">
                <strong className="text-slate-700">{usage.toLocaleString()}</strong> / {quota.toLocaleString()} Tokens
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
              <div className={`h-2.5 rounded-full ${progressColor} transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
