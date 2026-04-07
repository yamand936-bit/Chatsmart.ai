'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';

export default function AdminAlerts() {
    const tAdmin = useTranslations('admin');
    const [alerts, setAlerts] = useState<any[]>([]);
    const [open, setOpen] = useState(false);

    useEffect(() => {
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 60000); // refresh every minute
        return () => clearInterval(interval);
    }, []);

    const fetchAlerts = async () => {
        try {
            const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/alerts`, { withCredentials: true });
            if (res.data && res.data.data) {
                setAlerts(res.data.data);
            }
        } catch (e) {
            console.error("Failed to load alerts", e);
        }
    };

    return (
        <div className="relative z-50">
            <button onClick={() => setOpen(!open)} className="relative p-2 rounded-full hover:bg-slate-100 transition focus:outline-none cursor-pointer">
                <span className="text-xl">🔔</span>
                {alerts.length > 0 && (
                    <span className="absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold leading-none text-white bg-red-600 rounded-full">{alerts.length}</span>
                )}
            </button>
            
            {open && (
                <div className="absolute right-0 rtl:-left-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-slate-100 overflow-hidden text-start">
                    <div className="p-3 border-b border-slate-100 bg-slate-50 font-bold text-slate-800">
                        {tAdmin('alerts.title')}
                    </div>
                    <div className="max-h-96 overflow-y-auto">
                        {alerts.length === 0 ? (
                            <div className="p-4 text-center text-sm text-slate-500">No new alerts</div>
                        ) : (
                            alerts.map(a => (
                                <div key={a.id} className="p-3 border-b border-slate-50 hover:bg-slate-50 flex flex-col gap-1 transition-colors">
                                    <div className="flex justify-between items-center">
                                       <span className={`text-xs font-bold uppercase rounded px-2 py-0.5 ${a.severity === 'critical' || a.severity === 'high' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}`}>
                                         {a.type === 'quota_warning' ? tAdmin('alerts.quota_warning') || 'Quota Warning' : a.type}
                                       </span>
                                       <span className="text-xs text-slate-400">{new Date(a.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="text-sm text-slate-700 py-1">{a.message}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
