'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const t = useTranslations('orders');

  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/orders`, { withCredentials: true })
      .then(res => setOrders(res.data.data || []))
      .catch(console.error);
  }, []);

  return (
    <div className="flex flex-col h-full gap-6">
      <h2 className="text-2xl font-bold text-slate-800">{t('title')}</h2>
      
      {orders.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-12 text-center border-2 border-dashed border-blue-100 flex flex-col items-center justify-center mt-2">
            <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4">
               <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-8 h-8"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">{t('empty_title')}</h3>
            <p className="text-slate-500 mb-6 max-w-md">{t('empty_desc')}</p>
            <a href="/app/chat" className="bg-blue-600 text-white px-6 py-2 rounded-full font-medium hover:bg-blue-700 transition">{t('try_chat')}</a>
        </div>
      ) : (
      <div className="bg-white rounded shadow overflow-x-auto border border-slate-200">
        <table className="w-full text-left border-collapse min-w-max" style={{ textAlign: 'start' }}>
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="p-4 font-semibold text-slate-700">{t('orderId')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('product')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('quantity')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('amount')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('status')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('date')}</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(o => (
              <tr key={o.id} className="border-b hover:bg-slate-50">
                <td className="p-4 text-slate-600 text-sm font-mono truncate max-w-[100px]" title={o.id}>{o.id}</td>
                <td className="p-4 text-slate-800 font-medium">{o.payload?.product_name || 'N/A'}</td>
                <td className="p-4 text-slate-800">{o.payload?.quantity || 1}</td>
                <td className="p-4 font-medium text-green-600">${Number(o.total_amount).toFixed(2)}</td>
                <td className="p-4 text-slate-800">
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs uppercase font-bold tracking-wider">
                    {o.status}
                  </span>
                </td>
                <td className="p-4 text-slate-600 text-sm">{new Date(o.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}
    </div>
  );
}
