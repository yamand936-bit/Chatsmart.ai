'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import toast from 'react-hot-toast';

export default function MerchantDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
     sales_trend: [],
     platform_distribution: []
  });
  
  const t = useTranslations('merchant');
  const tDash = useTranslations('dashboard');

  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/analytics`, { withCredentials: true })
    .then((res) => {
       if (res.data.status === 'ok') {
          setData(res.data);
       }
    })
    .catch(err => {
       console.error(err);
       toast.error("فشل في جلب التحليلات. حاول مجدداً.");
    })
    .finally(() => {
       setLoading(false);
    });
  }, []);

  if (loading) {
     return <div className="p-12 text-center text-slate-500 font-medium">جاري تحميل التحليلات المتقدمة...</div>;
  }

  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#6366f1'];

  return (
    <div className="space-y-6">
       <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-800">{tDash('performance_overview', { fallback: 'نظرة عامة على الأداء' })}</h2>
          <button onClick={() => window.print()} className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg shadow-sm font-medium transition text-sm print-hidden hidden md:block">
              {tDash('export_pdf', { fallback: 'تصدير التقرير (PDF)' })}
          </button>
       </div>

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
             <h3 className="font-semibold text-lg text-slate-800 mb-6">{tDash('orders_last_7_days', { fallback: 'معدل الطلبات في آخر 7 أيام' })}</h3>
             <div className="h-80" dir="ltr">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.sales_trend} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
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
             </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
             <h3 className="font-semibold text-lg text-slate-800 mb-6">{tDash('messages_distribution', { fallback: 'توزيع الرسائل حسب القناة' })}</h3>
             {data.platform_distribution.length > 0 ? (
                 <div className="h-80" dir="ltr">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.platform_distribution} margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.5} vertical={false} />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend />
                        <Bar dataKey="value" name={tDash('messages_count', { fallback: 'عدد الرسائل' })} radius={[4, 4, 0, 0]} maxBarSize={60}>
                          {data.platform_distribution.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                 </div>
             ) : (
                <div className="h-80 flex items-center justify-center text-slate-400">
                    {tDash('no_messages_yet', { fallback: 'لا توجد رسائل مسجلة بعد.' })}
                </div>
             )}
          </div>
       </div>
    </div>
  );
}
