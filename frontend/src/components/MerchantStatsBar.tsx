'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';

export default function MerchantStatsBar() {
  const [stats, setStats] = useState({
    orders_today: 0,
    active_messages: 0,
    consumed_tokens: 0
  });

  const t = useTranslations('merchant');

  useEffect(() => {
    // Fetch stats
    axios.get(`/api/merchant/stats`, {
      withCredentials: true
    })
    .then(res => {
      if(res.data.status === 'ok') {
        setStats(res.data);
      }
    })
    .catch(console.error);

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      axios.get(`/api/merchant/stats`, { withCredentials: true })
        .then(res => { if(res.data.status === 'ok') setStats(res.data); })
        .catch(console.error);
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-blue-900 border-b border-blue-800 text-blue-50 py-2 px-6 sticky top-0 z-20 shadow-sm text-sm">
      <div className="flex items-center justify-center gap-12 font-medium">
        <div className="flex items-center gap-2">
          <span className="opacity-70">{t('stats_orders_today', { fallback: 'إجمالي طلبات اليوم:' })}</span>
          <span className="font-bold text-white bg-blue-800 px-2 py-0.5 rounded">{stats.orders_today}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="opacity-70">{t('stats_active_messages', { fallback: 'الرسائل النشطة:' })}</span>
          <span className="font-bold text-white bg-blue-800 px-2 py-0.5 rounded">{stats.active_messages}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="opacity-70">{t('stats_consumed_tokens', { fallback: 'التوكنز المستهلكة:' })}</span>
          <span className="font-bold text-white bg-blue-800 px-2 py-0.5 rounded">{stats.consumed_tokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
