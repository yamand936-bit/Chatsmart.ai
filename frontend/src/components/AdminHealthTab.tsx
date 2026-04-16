import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Skeleton } from '@/components/Skeleton';
import { useTranslations } from 'next-intl';

export default function AdminHealthTab() {
  const tAdmin = useTranslations('admin');
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lastFetch, setLastFetch] = useState<Date | null>(null);
  const [secondsAgo, setSecondsAgo] = useState(0);

  const fetchHealth = async () => {
    try {
      const res = await axios.get('/api/admin/health', { withCredentials: true });
      if (res.data?.status === 'ok') {
        setHealthData(res.data.data);
        setLastFetch(new Date());
        setSecondsAgo(0);
      }
    } catch (err) {
      console.error('Failed to fetch health data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // 30 sec
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      if (lastFetch) {
        setSecondsAgo(Math.floor((new Date().getTime() - lastFetch.getTime()) / 1000));
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [lastFetch]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-32 rounded-xl" />)}
      </div>
    );
  }

  if (!healthData) {
    return <div className="text-center text-red-500 py-10 font-medium">Unable to load system health.</div>;
  }

  const getUsageColor = (value: number) => {
    if (value > 90) return 'text-red-600 dark:text-red-400 border-red-200 bg-red-50/50 dark:bg-red-900/20';
    if (value >= 70) return 'text-amber-600 dark:text-amber-400 border-amber-200 bg-amber-50/50 dark:bg-amber-900/20';
    return 'text-green-600 dark:text-green-400 border-green-200 bg-green-50/50 dark:bg-green-900/20';
  };

  const getStatusColor = (status: string) => {
    if (status === 'online') return 'text-green-600 dark:text-green-400 border-green-200 bg-green-50/50 dark:bg-green-900/20';
    return 'text-red-600 dark:text-red-400 border-red-200 bg-red-50/50 dark:bg-red-900/20';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100">System Health Overview</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">Last checked {secondsAgo} seconds ago</p>
        </div>
        <button 
          onClick={fetchHealth} 
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium transition cursor-pointer"
        >
          Refresh Now
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <div className={`p-5 rounded-2xl border ${getUsageColor(healthData.cpu_usage)} transition`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold uppercase tracking-wider opacity-80">CPU Usage</span>
            <span className="text-2xl">🖥️</span>
          </div>
          <div className="text-3xl font-black">{healthData.cpu_usage}%</div>
        </div>

        <div className={`p-5 rounded-2xl border ${getUsageColor(healthData.memory_usage)} transition`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold uppercase tracking-wider opacity-80">Memory (RAM)</span>
            <span className="text-2xl">🛠️</span>
          </div>
          <div className="text-3xl font-black">{healthData.memory_usage}%</div>
        </div>

        <div className={`p-5 rounded-2xl border ${getUsageColor(healthData.disk_usage)} transition`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold uppercase tracking-wider opacity-80">Disk Space</span>
            <span className="text-2xl">💽</span>
          </div>
          <div className="text-3xl font-black">{healthData.disk_usage}%</div>
        </div>

        <div className={`p-5 rounded-2xl border ${getStatusColor(healthData.redis_status)} transition`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold uppercase tracking-wider opacity-80">Redis Cache</span>
            <span className="text-2xl">⚡</span>
          </div>
          <div className="text-3xl font-black uppercase">{healthData.redis_status}</div>
        </div>

        <div className={`p-5 rounded-2xl border ${getStatusColor(healthData.db_status)} transition`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold uppercase tracking-wider opacity-80">PostgreSQL DB</span>
            <span className="text-2xl">🌐</span>
          </div>
          <div className="text-3xl font-black uppercase">{healthData.db_status}</div>
        </div>

      </div>
    </div>
  );
}
