'use client';

import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import { useTranslations } from 'next-intl';

export default function CalendarPage() {
  const t = useTranslations('merchant');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEvents = async () => {
    try {
      const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments`, { withCredentials: true });
      if (res.data.status === 'ok') {
        setEvents(res.data.data);
      }
    } catch (err) {
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleEventDrop = async (info: any) => {
    const { event } = info;
    try {
      await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments/${event.id}`, {
        start_time: event.start.toISOString(),
        end_time: event.end ? event.end.toISOString() : event.start.toISOString(),
      }, { withCredentials: true });
      toast.success('Appointment rescheduled successfully!');
    } catch (err) {
      toast.error('Failed to reschedule appointment');
      info.revert();
    }
  };

  const [sheetUrl, setSheetUrl] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [uploading, setUploading] = useState(false);

  const handleSync = async () => {
      if (!sheetUrl) return toast.error(t('enter_link'));
      setSyncing(true);
      const loadingToast = toast.loading('...');
      
      try {
          await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/settings`, { sheet_url: sheetUrl }, { withCredentials: true });
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments/sync`, { sheet_url: sheetUrl }, { withCredentials: true });
          await fetchEvents();
          toast.success(t('sync_success'), { id: loadingToast });
      } catch (err) {
          toast.error(t('sync_error'), { id: loadingToast });
      } finally {
          setSyncing(false);
      }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setUploading(true);
      const loadingToast = toast.loading('...');
      
      const formData = new FormData();
      formData.append('file', file);

      try {
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments/upload`, formData, { 
              withCredentials: true,
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          await fetchEvents();
          toast.success(t('sync_success'), { id: loadingToast });
      } catch (err) {
          console.error(err);
          toast.error(t('sync_error'), { id: loadingToast });
      } finally {
          setUploading(false);
          e.target.value = '';
      }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading calendar...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 h-full flex flex-col gap-6">
      <div className="mb-2">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
          {t('calendar') || 'AI Calendar'}
        </h1>
        <p className="text-slate-500 mt-2">{t('calendar_desc', { fallback: 'Manage your bookings visually. Drag and drop appointments to reschedule them.' })}</p>
      </div>

      {/* Sync Section */}
      <div className="bg-slate-50 p-6 rounded-xl border-2 border-dashed border-slate-300 relative shadow-sm">
        <div className="absolute top-0 right-6 -mt-3.5 bg-slate-50 px-3 text-slate-500 font-bold tracking-wide">
             {t('sync_badge', { fallback: 'المزامنة الذكية' })}
        </div>
        
        <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-end">
            <div className="flex-1 w-full">
                <p className="font-bold mb-3 text-slate-800">{t('sync_upload_label', { fallback: '1. رفع ملف المواعيد (Excel)' })}</p>
                <div className="flex flex-wrap gap-3 w-full">
                    <a href={`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments/template`} download className="bg-white hover:bg-slate-100 text-slate-700 px-4 py-2 border border-slate-200 shadow-sm rounded-lg font-bold transition flex items-center justify-center min-w-[200px] shrink-0">
                       <svg className="w-5 h-5 text-[var(--primary-color,#2563eb)] mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                       {t('sync_download_booking', { fallback: 'تحميل نموذج المواعيد' })}
                    </a>
                    <a href={`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/appointments/export`} download className="bg-indigo-50 hover:bg-indigo-100 text-indigo-700 px-4 py-2 border border-indigo-200 shadow-sm rounded-lg font-bold transition flex items-center justify-center min-w-[200px] shrink-0">
                       <svg className="w-5 h-5 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                       {t('sync_export_appointments', { fallback: 'تصدير المواعيد الحالية (Excel)' })}
                    </a>
                    <input 
                      type="file" 
                      accept=".xlsx,.xls,.csv"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      className="w-full border border-slate-200 p-2 rounded-lg text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-[var(--primary-color,#2563eb)] file:text-white hover:file:bg-blue-700 cursor-pointer transition-all mt-2" 
                    />
                </div>
            </div>

            <div className="w-full lg:w-px lg:h-16 lg:bg-slate-300 mx-2 hidden lg:block"></div>

            <div className="flex-1 w-full">
               <p className="font-bold mb-3 text-slate-800">{t('sync_cloud_label', { fallback: '2. مزامنة رابط Google Sheets' })}</p>
               <div className="flex gap-3">
                 <input 
                   type="url" 
                   value={sheetUrl} onChange={e => setSheetUrl(e.target.value)}
                   placeholder="https://docs.google.com/spreadsheets/d/e/..."
                   className="w-full border border-slate-300 p-2 rounded-lg text-slate-800 bg-slate-50 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none" 
                 />
                 <button onClick={handleSync} disabled={syncing} className="bg-green-600 text-white px-6 py-2 border border-transparent rounded-lg hover:bg-green-700 font-bold shadow-sm transition min-w-[120px]">
                   {syncing ? '...' : t('sync_button', { fallback: 'مزامنة الآن' })}
                 </button>
               </div>
            </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[700px]">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
          }}
          editable={true}
          selectable={true}
          selectMirror={true}
          dayMaxEvents={true}
          events={events}
          eventDrop={handleEventDrop}
          eventResize={handleEventDrop}
          height="100%"
        />
      </div>
    </div>
  );
}
