import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Skeleton } from '@/components/Skeleton';

export default function AdminMRRSummary() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get('/api/admin/mrr', { withCredentials: true })
      .then(res => {
        if (res.data?.status === 'ok') {
          setData(res.data);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 mb-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
          <Skeleton className="h-24 rounded-xl" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  const activeCount = data.total_businesses; 
  // We don't have separate active vs trial in the basic output right now unless computed,
  // but let's derive what we can or just show overall metrics.
  const mrr = data.total_mrr || 0;
  const churnRisks = data.churn_risks || [];

  return (
    <div className="space-y-6 mb-10 w-full">
      {/* Top Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total MRR</p>
          <p className="text-3xl font-bold text-slate-800 dark:text-slate-100 mt-1">${mrr.toLocaleString()}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Paying Businesses</p>
          <p className="text-3xl font-bold text-slate-800 dark:text-slate-100 mt-1">
            {data.by_plan?.filter((p: any) => p.plan !== 'free').reduce((acc: number, p: any) => acc + p.count, 0) || 0}
          </p>
        </div>
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total Businesses</p>
          <p className="text-3xl font-bold text-slate-800 dark:text-slate-100 mt-1">{activeCount}</p>
        </div>
        <div className={`p-5 rounded-2xl shadow-sm border ${churnRisks.length > 0 ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/50' : 'bg-white dark:bg-slate-800 border-slate-100 dark:border-slate-700'}`}>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Churn Risk (Usage >85%)</p>
          <div className="flex items-center gap-2 mt-1">
            <p className={`text-3xl font-bold ${churnRisks.length > 0 ? 'text-red-600 dark:text-red-400' : 'text-slate-800 dark:text-slate-100'}`}>
              {churnRisks.length}
            </p>
            {churnRisks.length > 0 && <span className="bg-red-600 text-white text-[10px] px-2 py-0.5 rounded-full uppercase font-bold animate-pulse">Action Needed</span>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        {/* By Plan Table */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50">
            <h4 className="font-semibold text-slate-800 dark:text-slate-100">Revenue by Plan</h4>
          </div>
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400">
              <tr>
                <th className="py-3 px-4 font-medium uppercase tracking-wider">Plan</th>
                <th className="py-3 px-4 font-medium uppercase tracking-wider">Subscribers</th>
                <th className="py-3 px-4 font-medium uppercase tracking-wider text-right">MRR</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
              {data.by_plan?.map((p: any) => (
                <tr key={p.plan}>
                  <td className="py-3 px-4 capitalize font-medium text-slate-700 dark:text-slate-300">{p.plan}</td>
                  <td className="py-3 px-4 text-slate-600 dark:text-slate-400">{p.count}</td>
                  <td className="py-3 px-4 text-slate-800 dark:text-slate-200 font-semibold text-right">${(p.mrr || 0).toLocaleString()}</td>
                </tr>
              ))}
              {(!data.by_plan || data.by_plan.length === 0) && (
                <tr><td colSpan={3} className="py-4 text-center text-slate-400">No data available</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Churn Risk Table */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
          <div className="p-4 border-b border-slate-100 dark:border-slate-700 bg-red-50/30 dark:bg-red-900/10">
            <h4 className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <span className="text-red-500">⚠️</span> Accounts at Risk
            </h4>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {churnRisks.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No high-risk accounts detected automatically.
              </div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 dark:text-slate-400 sticky top-0">
                  <tr>
                    <th className="py-3 px-4 font-medium uppercase tracking-wider">Business</th>
                    <th className="py-3 px-4 font-medium uppercase tracking-wider">Plan</th>
                    <th className="py-3 px-4 font-medium uppercase tracking-wider text-right">Usage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                  {churnRisks.map((r: any) => (
                    <tr key={r.id}>
                      <td className="py-3 px-4 font-medium text-slate-700 dark:text-slate-300">{r.name}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-[10px] rounded uppercase font-bold">{r.plan}</span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-semibold ${r.usage_pct > 95 ? 'text-red-600' : 'text-amber-500'}`}>
                          {r.usage_pct}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
