'use client';

import React, { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { toast } from 'react-hot-toast';
import { Send, Tag as TagIcon, Sparkles, ArrowLeft } from 'lucide-react';
import axios from 'axios';
import Select from 'react-select';

export default function CampaignsPage() {
  const t = useTranslations('campaigns');
  
  // Step 1 State
  const [step, setStep] = useState(1);
  const [availableTags, setAvailableTags] = useState<{value: string, label: string}[]>([]);
  const [selectedTags, setSelectedTags] = useState<any[]>([]);
  const [instructions, setInstructions] = useState('');
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  
  // Preview State
  const [previewCount, setPreviewCount] = useState<number | null>(null);
  const [previewSample, setPreviewSample] = useState<string[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  
  // Submit State
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    // Load Templates
    axios.get('/api/merchant/templates', { withCredentials: true })
      .then(res => {
         if (res.data?.data) {
           // only show approved templates
           setTemplates(res.data.data.filter((t: any) => t.is_approved));
         }
      })
      .catch(console.error);

    // Load Tags
    axios.get('/api/merchant/customers/tags', { withCredentials: true })
      .then(res => {
         if (res.data?.data) {
           const opts = res.data.data.map((t: string) => ({ value: t, label: t }));
           opts.unshift({ value: 'all', label: 'All Customers (الكل)' });
           setAvailableTags(opts);
         }
      })
      .catch(console.error);
  }, []);

  // Debounced Preview call
  useEffect(() => {
    if (selectedTags.length === 0) {
      setPreviewCount(null);
      setPreviewSample([]);
      return;
    }
    
    setPreviewLoading(true);
    const timeout = setTimeout(() => {
      axios.post('/api/merchant/campaigns/preview', {
        tags: selectedTags.map(t => t.value)
      }, { withCredentials: true })
      .then(res => {
        if (res.data?.status === 'ok') {
          setPreviewCount(res.data.matched_count);
          setPreviewSample(res.data.sample_names);
        }
      })
      .catch(() => {
        toast.error('Failed to load audience preview');
      })
      .finally(() => setPreviewLoading(false));
    }, 400);

    return () => clearTimeout(timeout);
  }, [selectedTags]);

  const handlePreviewNext = () => {
    if (selectedTags.length === 0) {
      toast.error('Please select at least one tag or "All Customers"');
      return;
    }
    if (!instructions.trim()) {
      toast.error('Please enter instructions for the campaign');
      return;
    }
    setStep(2);
  };

  const handleConfirmSend = async () => {
    setSubmitting(true);
    try {
      // Create a comma separated string for the old endpoint payload format
      const tagStr = selectedTags.some(t => t.value === 'all') ? 'all' : selectedTags.map(t => t.value).join(',');
      
      const response = await axios.post(`/api/merchant/campaigns/send`, {
        tag: tagStr,
        instructions: instructions,
        template_id: selectedTemplate || null
      }, { withCredentials: true });
      
      if (response.data?.status === 'success') {
        toast.success(response.data.message || 'تم جدولة الحملة بنجاح!');
        setSelectedTags([]);
        setInstructions('');
        setSelectedTemplate('');
        setStep(1);
      } else {
        toast.error('حدث خطأ أثناء إطلاق الحملة');
      }
    } catch (e: any) {
      const errorMessage = e.response?.data?.detail || e.message || 'حدث خطأ غير متوقع';
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-8">
        <Sparkles className="w-8 h-8 text-indigo-500" />
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-purple-600">
          Smart Broadcast Builder
        </h1>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden relative min-h-[500px]">
        {/* Glow effect */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 dark:bg-indigo-900/20 rounded-full blur-3xl opacity-50 -mr-32 -mt-32 pointer-events-none"></div>

        <div className="p-6 md:p-8 relative z-10 w-full h-full flex flex-col">
          
          {step === 1 && (
            <div className="space-y-6 flex-grow animate-in fade-in zoom-in-95 duration-200">
              <p className="text-slate-600 dark:text-slate-400 text-lg mb-4">
                Build your audience using tags, define your marketing instructions, and preview before sending.
              </p>

              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                  <TagIcon className="w-4 h-4 text-slate-400" /> Target Audience Tags
                </label>
                <Select 
                  isMulti 
                  options={availableTags} 
                  value={selectedTags}
                  onChange={(val) => setSelectedTags(val as any)}
                  className="react-select-container text-slate-900"
                  classNamePrefix="react-select"
                  placeholder="Select tags..."
                />
                
                {previewLoading ? (
                  <p className="text-sm text-indigo-500 mt-2 animate-pulse">Calculating audience...</p>
                ) : previewCount !== null ? (
                  <div className="mt-3 p-3 rounded-xl bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-100 dark:border-indigo-800/50">
                    <p className="font-medium text-indigo-800 dark:text-indigo-200">
                      🎯 {previewCount} customers will receive this campaign.
                    </p>
                    {previewSample.length > 0 && (
                      <p className="text-xs text-indigo-600 dark:text-indigo-400 mt-1">
                        Examples: {previewSample.join(', ')} ...
                      </p>
                    )}
                  </div>
                ) : null}
              </div>

              <div>
                 <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">WhatsApp Template</label>
                 {templates.length === 0 ? (
                   <div className="text-sm p-3 border border-amber-200 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-xl">
                      No approved templates yet. Create one in Settings if targeting WhatsApp customers.
                   </div>
                 ) : (
                   <select value={selectedTemplate} onChange={e => setSelectedTemplate(e.target.value)} className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium bg-white dark:bg-slate-700 text-slate-900 dark:text-white">
                      <option value="">-- AI Freeform (Not recommended for WhatsApp &gt;24h) --</option>
                      {templates.map(t => (
                         <option key={t.id} value={t.id}>{t.name} ({t.language})</option>
                      ))}
                   </select>
                 )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-slate-400" />
                  {t('instructions_label', { fallback: 'AI Campaign Instructions' })}
                </label>
                <textarea
                  placeholder={t('instructions_placeholder', { fallback: 'e.g., Target customers with a 20% discount on winter shoes' })}
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all resize-y font-medium leading-relaxed bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
                ></textarea>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  onClick={handlePreviewNext}
                  disabled={previewLoading || selectedTags.length === 0 || !instructions.trim()}
                  className="bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900 font-bold py-3 px-8 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 flex gap-2 items-center"
                >
                  Preview & Send <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6 flex-grow animate-in slide-in-from-right-8 duration-300">
              <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                Confirm Campaign
              </h2>
              
              <div className="bg-slate-50 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Target Audience</p>
                    <p className="font-semibold text-slate-800 dark:text-slate-200 text-lg">
                      {previewCount} Customers
                    </p>
                    <p className="text-sm text-slate-500 mt-1 flex flex-wrap gap-1">
                      {selectedTags.map(t => <span key={t.value} className="bg-slate-200 dark:bg-slate-700 px-2 rounded-md">{t.label}</span>)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Template Selection</p>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                      {selectedTemplate 
                        ? templates.find(t => t.id === selectedTemplate)?.name || 'Unknown Template'
                        : 'AI Freeform'}
                    </p>
                  </div>
                </div>
                
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-2">AI Instructions</p>
                  <p className="text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 p-3 rounded-lg border border-slate-100 dark:border-slate-700">
                    {instructions}
                  </p>
                </div>
              </div>

              <div className="pt-6 flex justify-between items-center">
                <button 
                  onClick={() => setStep(1)} 
                  disabled={submitting}
                  className="text-slate-600 dark:text-slate-400 font-medium py-3 px-4 flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Edit
                </button>
                
                <button
                  onClick={handleConfirmSend}
                  disabled={submitting}
                  className="bg-indigo-600 text-white font-bold py-3 px-8 rounded-xl flex items-center justify-center gap-2 hover:bg-indigo-700 shadow-lg shadow-indigo-200 dark:shadow-indigo-900/20 transition disabled:opacity-50"
                >
                  {submitting ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                  {submitting ? 'Sending...' : 'Confirm & Launch Campaign'}
                </button>
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
