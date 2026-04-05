'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';

export default function SettingsPage() {
    const t = useTranslations('settings');
    const [stats, setStats] = useState({ consumed_tokens: 0 });
    const [tone, setTone] = useState("Professional");
    const [updating, setUpdating] = useState(false);
    const limit = 10000; // Trial limit
    
    useEffect(() => {
        axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/stats`, { withCredentials: true })
        .then(res => setStats(res.data))
        .catch(console.error);
    }, []);

    const updateTone = async (newTone: string) => {
        setUpdating(true);
        try {
            await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/tone`, { tone: newTone }, { withCredentials: true });
            setTone(newTone);
            toast.success(t('tone_updated'));
        } catch (err) {
             toast.error("Error setting tone");
        } finally {
            setUpdating(false);
        }
    };

    const percentage = Math.min((stats.consumed_tokens / limit) * 100, 100).toFixed(1);
    const isNearingLimit = parseFloat(percentage) > 80;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">{t('title')}</h2>

            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">{t('ai_tone')}</h3>
                <p className="text-slate-500 mb-4 text-sm">{t('ai_tone_desc')}</p>
                
                <select 
                   value={tone}
                   onChange={(e) => updateTone(e.target.value)}
                   disabled={updating}
                   className="w-full md:w-1/2 rounded border-gray-300 shadow-sm p-3 mb-4 bg-slate-50 focus:ring-blue-500 focus:border-blue-500 outline-none"
                >
                   <option value="Professional">{t('tone_professional')}</option>
                   <option value="Friendly">{t('tone_friendly')}</option>
                   <option value="Sales-driven">{t('tone_sales')}</option>
                </select>
                {updating && <span className="text-sm text-blue-500 mx-3">{t('tone_updating')}</span>}
            </div>

            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
               <h3 className="text-lg font-bold text-slate-800 mb-6">{t('token_usage')} ({t('free_tier')})</h3>
               <div className="w-full bg-slate-100 rounded-full h-4 mb-3 border">
                 <div className={`${isNearingLimit ? 'bg-red-500' : 'bg-blue-600'} h-full rounded-full transition-all duration-1000`} style={{ width: `${percentage}%` }}></div>
               </div>
               <div className="flex justify-between text-sm font-medium mb-8">
                   <span className="text-slate-600">{stats.consumed_tokens} {t('used_of_limit', { limit })}</span>
               </div>
               
               {isNearingLimit && (
                   <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6 border border-red-200">
                       <strong className="block mb-1">{t('warning')}:</strong>
                       {t('warning_desc')}
                   </div>
               )}
               
               <button className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg shadow font-medium hover:opacity-90 transition">
                   {t('upgrade_btn')}
               </button>
            </div>
        </div>
    );
}
