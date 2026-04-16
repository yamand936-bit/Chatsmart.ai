'use client';

import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'react-hot-toast';
import { Send, Tag as TagIcon, Sparkles } from 'lucide-react';
import axios from 'axios';

export default function CampaignsPage() {
  const t = useTranslations('campaigns');
  const [tag, setTag] = useState('');
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [audienceFilter, setAudienceFilter] = useState('all');

  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/templates`, { withCredentials: true })
      .then(res => {
         if (res.data?.data) setTemplates(res.data.data);
      })
      .catch(console.error);
  }, []);

  const handleLaunchCampaign = async () => {
    if (!tag.trim() || !instructions.trim()) {
      toast.error('الرجاء إدخال الوسم والتعليمات للتسويق');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/campaigns/send`, {
        tag: tag,
        instructions: instructions,
        template_id: selectedTemplate || null,
        audience_filter: audienceFilter
      }, { withCredentials: true });
      
      if (response.data?.status === 'success') {
        toast.success('تم جدولة الحملة بنجاح!');
        setTag('');
        setInstructions('');
      } else {
        toast.error('حدث خطأ أثناء إطلاق الحملة');
      }
    } catch (e: any) {
      const errorMessage = e.response?.data?.detail || e.message || 'حدث خطأ غير متوقع';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex items-center gap-3 mb-8">
        <Sparkles className="w-8 h-8 text-indigo-500" />
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
          {t('title')}
        </h1>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden relative">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full blur-3xl opacity-50 -mr-32 -mt-32 pointer-events-none"></div>

        <div className="p-8 relative z-10">
          <p className="text-slate-600 mb-8 max-w-2xl text-lg">
            {t('desc')}
          </p>

          <div className="space-y-6 max-w-2xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                 <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">Audience Filter</label>
                 <select value={audienceFilter} onChange={e => setAudienceFilter(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium bg-white">
                    <option value="all">All Registered Customers</option>
                    <option value="active_30d">Active (AI chat in last 30d)</option>
                    <option value="no_orders">No Orders Yet</option>
                 </select>
              </div>
              <div>
                 <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">WhatsApp Template</label>
                 <select value={selectedTemplate} onChange={e => setSelectedTemplate(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium bg-white">
                    <option value="">-- AI Freeform (Not WhatsApp) --</option>
                    {templates.map(t => (
                       <option key={t.id} value={t.id}>{t.name} ({t.language})</option>
                    ))}
                 </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <TagIcon className="w-4 h-4 text-slate-400" />
                {t('target_tag_label')}
              </label>
              <input
                type="text"
                placeholder={t('tag_placeholder')}
                value={tag}
                onChange={(e) => setTag(e.target.value)}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
              />
              <p className="text-xs text-slate-500 mt-2">
                {t('tag_desc')}
                <br/>
                <span className="font-semibold text-indigo-500 mt-1 inline-block">💡 اكتب &quot;all&quot; أو &quot;الكل&quot; لاستهداف جميع العملاء المسجلين.</span>
              </p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-slate-400" />
                {t('instructions_label')}
              </label>
              <textarea
                placeholder={t('instructions_placeholder')}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                rows={5}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-y font-medium leading-relaxed"
              ></textarea>
            </div>

            <button
              onClick={handleLaunchCampaign}
              disabled={loading}
              className="mt-4 bg-gradient-to-l from-indigo-600 to-purple-600 text-white font-bold py-3 px-8 rounded-xl flex items-center justify-center gap-2 hover:opacity-90 transition-opacity w-full md:w-auto shadow-lg shadow-indigo-200 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <Send className="w-5 h-5" />
              )}
              {loading ? t('launching_btn') : t('launch_btn')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
