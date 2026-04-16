'use client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

export function SalesTrendChart({ data, tDash }: { data: any, tDash: any }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.5} />
        <XAxis dataKey="date" tick={{fontSize: 12}} />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip 
          formatter={(value: any, name: string) => name === tDash('revenue', { fallback: 'الأرباح ($)' }) ? `${Number(value).toFixed(2)}` : value}
          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
        />
        <Legend />
        <Line yAxisId="left" type="monotone" dataKey="orders" name={tDash('orders_count', { fallback: 'عدد الطلبات' })} stroke="#2563eb" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
        <Line yAxisId="right" type="monotone" dataKey="revenue" name={tDash('revenue', { fallback: 'الأرباح ($)' })} stroke="#10b981" strokeWidth={3} />
      </LineChart>
    </ResponsiveContainer>
  );
}

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#6366f1'];

export function PlatformDistributionChart({ data, tDash }: { data: any, tDash: any }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.5} vertical={false} />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
        <Legend />
        <Bar dataKey="value" name={tDash('messages_count', { fallback: 'عدد الرسائل' })} radius={[4, 4, 0, 0]} maxBarSize={60}>
          {data.map((entry: any, index: number) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
