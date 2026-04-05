'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';

export default function SettingsPage() {
    const [stats, setStats] = useState({ consumed_tokens: 0 });
    const limit = 10000; // Trial limit
    
    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/stats`, { withCredentials: true })
        .then(res => setStats(res.data))
        .catch(console.error);
    }, []);

    const percentage = Math.min((stats.consumed_tokens / limit) * 100, 100).toFixed(1);
    const isNearingLimit = parseFloat(percentage) > 80;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">الإعدادات والاشتراك</h2>
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
               <h3 className="text-lg font-bold text-slate-800 mb-6">الاستهلاك الحالي للذكاء الاصطناعي (الباقة المجانية Trial)</h3>
               <div className="w-full bg-slate-100 rounded-full h-4 mb-3 border">
                 <div className={`${isNearingLimit ? 'bg-red-500' : 'bg-blue-600'} h-full rounded-full transition-all duration-1000`} style={{ width: `${percentage}%` }}></div>
               </div>
               <div className="flex justify-between text-sm font-medium mb-8">
                   <span className="text-slate-600">تم استهلاك {stats.consumed_tokens} توكن</span>
                   <span className="text-slate-600">الحد الأقصى {limit} توكن</span>
               </div>
               
               {isNearingLimit && (
                   <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 border border-red-200">
                       <strong className="block mb-1">تنبيه المبيعات المستمرة:</strong>
                       لقد اقتربت من استنفاد باقة التوكنز المجانية. المساعد الذكي سيتوقف عن الرد على العملاء، يرجى الترقية للحفاظ على استمرارية الإيرادات.
                   </div>
               )}
               
               <button className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg shadow font-medium hover:opacity-90 transition">
                   الترقية للباقة الاحترافية بطريقة آمنة (Stripe)
               </button>
            </div>
        </div>
    );
}
