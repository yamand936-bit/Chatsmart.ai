'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { Save, RefreshCw, Key, MessageSquare, AlertCircle } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function IntegrationsPage() {
  const t = useTranslations('merchant'); // basic fallback
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [businessId, setBusinessId] = useState<string>('');
  const [waConfig, setWaConfig] = useState({
    access_token: '',
    phone_number_id: '',
    app_secret: '',
    business_account_id: '',
    verify_token: ''
  });

  useEffect(() => {
    // 1. Get Settings (to find the current business_id if needed, though backend uses cookie)
    axios.get('/api/merchant/settings')
      .then(res => {
         setBusinessId(res.data.data.id);
      })
      .catch(err => {
         toast.error("Failed to load business profile");
      });

    // 2. Load WhatsApp Config
    axios.get('/api/merchant/features/whatsapp')
      .then(res => {
         if (res.data.status === 'success' && res.data.data) {
           setWaConfig(prev => ({ ...prev, ...res.data.data }));
         }
      })
      .catch(err => {
         // Might mean it's not setup yet, but our backend auto-creates it now.
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
       await axios.post('/api/merchant/features/whatsapp', {
          access_token: waConfig.access_token,
          phone_number_id: waConfig.phone_number_id,
          app_secret: waConfig.app_secret,
          business_account_id: waConfig.business_account_id
       });
       toast.success("WhatsApp configuration saved securely");
    } catch (err: any) {
       toast.error(err.response?.data?.message || "Failed to save configuration");
    } finally {
       setSaving(false);
    }
  };

  const webhookUrl = businessId ? `${window.location.protocol}//${window.location.host}/api/integrations/whatsapp/${businessId}/webhook` : 'Loading...';

  return (
    <div className="max-w-4xl mx-auto space-y-6">
       <div>
         <h1 className="text-2xl font-bold">التكاملات (Integrations)</h1>
         <p className="text-slate-500">قم بربط قنوات التواصل المختلفة مثل WhatsApp لتفعيل البوت الذكي عليها.</p>
       </div>

       {loading ? (
         <div className="flex justify-center p-12"><RefreshCw className="animate-spin text-blue-600" /></div>
       ) : (
         <div className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden">
            <div className="bg-green-600 px-6 py-4 flex items-center justify-between text-white">
                <div className="flex items-center gap-3">
                   <MessageSquare size={24} />
                   <h2 className="text-xl font-bold">WhatsApp Cloud API</h2>
                </div>
                <span className="text-sm bg-green-700 px-2 py-1 rounded">Meta v20.0 Standard</span>
            </div>
            
            <form onSubmit={handleSave} className="p-6 space-y-6">
                
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg flex items-start gap-3">
                   <AlertCircle className="text-blue-600 shrink-0 mt-0.5" />
                   <div>
                       <h4 className="font-semibold text-blue-900 text-sm">كيفية الربط (Webhook Params)</h4>
                       <p className="text-sm text-blue-800 mt-1">
                           انسخ هذه البيانات والصقها في واجهة مطوري ميتا (Meta Developer Console) لإنشاء نقطة الاتصال الواردة:
                       </p>
                       <div className="mt-3 space-y-2">
                           <div>
                                <span className="text-xs font-bold text-slate-500 uppercase">Callback URL</span>
                                <input readOnly type="text" value={webhookUrl} className="w-full mt-1 p-2 bg-white border border-blue-200 rounded text-sm font-mono text-slate-600 select-all focus:outline-none" />
                           </div>
                           <div>
                                <span className="text-xs font-bold text-slate-500 uppercase">Verify Token</span>
                                <div className="relative">
                                    <input readOnly type="text" value={waConfig.verify_token} className="w-full mt-1 p-2 bg-white border border-blue-200 rounded text-sm font-mono text-slate-600 select-all pr-12 focus:outline-none" />
                                    <Key className="absolute right-3 top-3 text-slate-400" size={16} />
                                </div>
                           </div>
                       </div>
                   </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Access Token (Permanent)</label>
                        <input required type="password" value={waConfig.access_token} onChange={(e) => setWaConfig({...waConfig, access_token: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none border-slate-300 focus:ring-green-500" placeholder="EA..."/>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Phone Number ID</label>
                        <input required type="text" value={waConfig.phone_number_id} onChange={(e) => setWaConfig({...waConfig, phone_number_id: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none border-slate-300 focus:ring-green-500" placeholder="1234567890" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">App Secret</label>
                        <input required type="password" value={waConfig.app_secret} onChange={(e) => setWaConfig({...waConfig, app_secret: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none border-slate-300 focus:ring-green-500" placeholder="Meta App Secret for Signature validation" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Business Account ID (Optional)</label>
                        <input type="text" value={waConfig.business_account_id} onChange={(e) => setWaConfig({...waConfig, business_account_id: e.target.value})} className="w-full p-2 border rounded focus:ring-2 outline-none border-slate-300" placeholder="WABA ID" />
                    </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-slate-100">
                    <button disabled={saving} type="submit" className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2 transition disabled:opacity-50">
                        {saving ? <RefreshCw className="animate-spin" size={18} /> : <Save size={18} />}
                        حفظ بيانات التكامل
                    </button>
                </div>
            </form>
         </div>
       )}
    </div>
  );
}
