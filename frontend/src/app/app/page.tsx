'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';
import dynamic from 'next/dynamic';
const SalesTrendChart = dynamic(() => import('@/components/DynamicCharts').then(m => m.SalesTrendChart), { ssr: false, loading: () => <Skeleton className="h-full w-full" /> });
const PlatformDistributionChart = dynamic(() => import('@/components/DynamicCharts').then(m => m.PlatformDistributionChart), { ssr: false, loading: () => <Skeleton className="h-full w-full" /> });
import { MetricCardSkeleton, Skeleton } from '@/components/Skeleton';

export default function MerchantDashboard() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
     sales_trend: [],
     platform_distribution: []
  });
  const [advData, setAdvData] = useState<any>(null);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');
  
    const tDash = useTranslations('dashboard');

  useEffect(() => {
    setLoading(true);
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/analytics?period=${period}`, { withCredentials: true })
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

    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/merchant/summary?period=${period}`, { withCredentials: true })
    .then(res => setAdvData(res.data.data ? res.data.data : res.data))
    .catch(console.error);
  }, [period]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({length: 5}).map((_,i) => <MetricCardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-xl" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </div>
    );
  }

  const revenueEstimate = (data as any).total_revenue || 0;
  const roiValue = advData?.token_cost_total > 0
    ? ((revenueEstimate - advData.token_cost_total) / advData.token_cost_total) * 100
    : 0;

  return (
    <div className="space-y-6">
       <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{tDash('performance_overview', { fallback: 'نظرة عامة على الأداء' })}</h2>
          <button onClick={() => window.print()} className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg shadow-sm font-medium transition text-sm print-hidden hidden md:block">
              {tDash('export_pdf', { fallback: 'تصدير التقرير (PDF)' })}
          </button>
       </div>

       <div className="flex gap-2 mb-4">
         {(['7d','30d','90d'] as const).map(p => (
           <button key={p} onClick={() => setPeriod(p)}
             className={`px-3 py-1 rounded text-sm font-medium transition ${period === p ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200'}`}>
             {p === '7d' ? tDash('period_7d', {fallback: '7 days'}) : p === '30d' ? tDash('period_30d', {fallback: '30 days'}) : tDash('period_90d', {fallback: '90 days'})}
           </button>
         ))}
       </div>

       {advData && (
           <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('totalConversations', {fallback: 'Total Conversations'})}</div>
                   <div className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">{advData.total_conversations}</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('botHandled', {fallback: 'Bot Handled'})}</div>
                   <div className="text-2xl font-bold text-green-600 mt-2">{advData.bot_handled}</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('humanHandled', {fallback: 'Human Handled'})}</div>
                   <div className="text-2xl font-bold text-amber-500 mt-2">{advData.human_handled}</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('avgResponseTime', {fallback: 'Avg Response Time'})}</div>
                   <div className="text-2xl font-bold text-blue-600 mt-2">{advData.avg_response_time_ms} ms</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between col-span-2 md:col-span-1">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('tokenCost', {fallback: 'Token Cost (30d)'})}</div>
                   <div className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">${advData.token_cost_total}</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                 <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('roi', {fallback: 'AI ROI'})}</div>
                 <div className={`text-2xl font-bold mt-2 ${roiValue >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                   {roiValue >= 0 ? '+' : ''}{roiValue.toFixed(0)}%
                 </div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between col-span-2 md:col-span-3">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('topIntents', {fallback: 'Top AI Intents'})}</div>
                   <div className="flex flex-wrap gap-2 mt-2">
                       {advData.top_intents?.map((ti: any, i: number) => (
                           <span key={i} className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-sm text-slate-700 dark:text-slate-300 font-medium">
                               {ti.intent}: {ti.count}
                           </span>
                       ))}
                   </div>
               </div>
           </div>
       )}

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow border border-slate-100 dark:border-slate-700">
             <h3 className="font-semibold text-lg text-slate-800 dark:text-slate-100 mb-6">{tDash('orders_last_7_days', { fallback: 'معدل الطلبات في آخر 7 أيام' })}</h3>
             <div className="h-80" dir="ltr">
                <SalesTrendChart data={data.sales_trend} tDash={tDash} />
             </div>
          </div>

          <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow border border-slate-100 dark:border-slate-700">
             <h3 className="font-semibold text-lg text-slate-800 dark:text-slate-100 mb-6">{tDash('messages_distribution', { fallback: 'توزيع الرسائل حسب القناة' })}</h3>
             {data.platform_distribution.length > 0 ? (
                 <div className="h-80" dir="ltr">
                    <PlatformDistributionChart data={data.platform_distribution} tDash={tDash} />
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
