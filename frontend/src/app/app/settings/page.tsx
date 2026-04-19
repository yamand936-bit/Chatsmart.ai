'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';
import dynamic from 'next/dynamic';

const VisualFlowBuilder = dynamic(() => import('@/components/VisualFlowBuilder'), { ssr: false });
export default function SettingsPage() {
    const t = useTranslations('settings');
    const tCommon = useTranslations('common');
    const [stats, setStats] = useState({ consumed_tokens: 0 });
    const [tone, setTone] = useState("Professional");
    
    // New Settings State
    const [knowledgeBase, setKnowledgeBase] = useState("");
    const [bankName, setBankName] = useState("");
    const [iban, setIban] = useState("");
    const [primaryColor, setPrimaryColor] = useState("#2563eb");
    const [logoUrl, setLogoUrl] = useState("");
    
    const [notificationEmail, setNotificationEmail] = useState("");
    const [notificationTelegram, setNotificationTelegram] = useState("");
    
    const [staffMembers, setStaffMembers] = useState("");
    
    const [telegramBotToken, setTelegramBotToken] = useState("");
    const [telegramWebhookSecret, setTelegramWebhookSecret] = useState("");
    const [activeFeatures, setActiveFeatures] = useState<string[]>([]);
    
    // Bot Flows
    const [botFlows, setBotFlows] = useState<any[]>([]);
    const [editingFlow, setEditingFlow] = useState<any | null>(null);
    const [showFlowForm, setShowFlowForm] = useState(false);
    
    const [updating, setUpdating] = useState(false);
    const limit = 10000; // Trial limit
    
    useEffect(() => {
        axios.get(`/api/merchant/stats`, { withCredentials: true })
        .then(res => setStats(res.data))
        .catch(console.error);
        
        axios.get(`/api/merchant/settings`, { withCredentials: true })
        .then(res => {
            const data = res.data.data;
            if (data.ai_tone) setTone(data.ai_tone);
            if (data.knowledge_base) setKnowledgeBase(data.knowledge_base);
            if (data.bank_details) {
                setBankName(data.bank_details.bank_name || "");
                setIban(data.bank_details.iban || "");
            }
            if (data.primary_color) setPrimaryColor(data.primary_color);
            if (data.logo_url) setLogoUrl(data.logo_url);
            if (data.notification_email) setNotificationEmail(data.notification_email);
            if (data.notification_telegram) setNotificationTelegram(data.notification_telegram);
            if (data.staff_members && data.staff_members.length > 0) {
                setStaffMembers(data.staff_members.join(", "));
            }
            
            // Set dynamic primary color for the document if valid
            if (data.primary_color) {
                document.documentElement.style.setProperty('--primary-color', data.primary_color);
            }
            if (data.active_features) {
                setActiveFeatures(data.active_features);
            }
        })
        .catch(console.error);
        
        axios.get(`/api/merchant/flows`, { withCredentials: true })
        .then(res => setBotFlows(res.data.data || []))
        .catch(console.error);
    }, []);

    const saveSettings = async () => {
        setUpdating(true);
        try {
            await axios.put(`/api/merchant/settings`, { 
                knowledge_base: knowledgeBase,
                bank_details: { bank_name: bankName, iban: iban },
                primary_color: primaryColor,
                logo_url: logoUrl,
                notification_email: notificationEmail,
                notification_telegram: notificationTelegram,
                staff_members: staffMembers ? staffMembers.split(",").map(s => s.trim()).filter(Boolean) : []
            }, { withCredentials: true });
            
            // Apply tone here as well if they modified it (we've left old PUT /api/merchant/tone active but can unify)
            await axios.put(`/api/merchant/tone`, { tone: tone }, { withCredentials: true });

            document.documentElement.style.setProperty('--primary-color', primaryColor);
            toast.success("تم الحفظ بنجاح / Settings saved");
        } catch (err) {
             toast.error("Error saving settings");
        } finally {
            setUpdating(false);
        }
    };

    const percentage = Math.min((stats.consumed_tokens / limit) * 100, 100).toFixed(1);
    const isNearingLimit = parseFloat(percentage) > 80;

    return (
        <div className="max-w-4xl mx-auto space-y-6 pb-20">
            <h2 className="text-2xl font-bold text-slate-800">{t('title')}</h2>

            {/* AI Personalization */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">{t('ai_tone')}</h3>
                <p className="text-slate-500 mb-4 text-sm">{t('ai_tone_desc')}</p>
                <select 
                   value={tone}
                   onChange={(e) => setTone(e.target.value)}
                   className="w-full md:w-1/2 rounded border-gray-300 shadow-sm p-3 bg-slate-50 focus:ring-blue-500 focus:border-blue-500 outline-none"
                >
                   <option value="Professional">{t('tone_professional')}</option>
                   <option value="Friendly">{t('tone_friendly')}</option>
                   <option value="Sales-driven">{t('tone_sales')}</option>
                </select>
            </div>

            {/* Knowledge Base */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100 mb-6">
                <h3 className="text-lg font-bold text-slate-800 mb-2">{t('kb_title')}</h3>
                <p className="text-slate-500 mb-4 text-sm">{t('kb_desc')}</p>
                
                <div className="flex gap-4">
                     <textarea 
                        rows={4}
                        value={knowledgeBase}
                        onChange={(e) => setKnowledgeBase(e.target.value)}
                        placeholder={t('kb_placeholder')}
                        className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 focus:ring-blue-500 focus:border-blue-500 outline-none resize-y"
                     ></textarea>
                </div>
                
                <div className="mt-4 flex flex-col md:flex-row md:items-center gap-4">
                     <input type="file" id="kb-file" className="hidden" accept=".txt,.pdf,.docx" onChange={async (e) => {
                          if (e.target.files && e.target.files[0]) {
                               const file = e.target.files[0];
                               const formData = new FormData();
                               formData.append('file', file);
                               const toastId = toast.loading("Processing file with AI...");
                               try {
                                    await axios.post(`/api/merchant/knowledge`, formData, { withCredentials: true });
                                    toast.success("File processed & learned successfully!", {id: toastId});
                                    setKnowledgeBase(prev => prev + `\n\n[System Alert: Document '${file.name}' has been embedded securely into the AI Knowledge Vector Base.]`);
                               } catch (err) {
                                    toast.error("Error processing file", {id: toastId});
                               }
                          }
                     }} />
                     <label htmlFor="kb-file" className="cursor-pointer bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded text-sm font-medium transition border border-slate-300 shadow-sm flex items-center justify-center gap-2">
                         <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
                         Upload File (PDF, DOCX, TXT)
                     </label>
                     <button onClick={async () => {
                         if (!knowledgeBase.trim()) return toast.error("Text is empty");
                         const formData = new FormData();
                         formData.append('text', knowledgeBase);
                         const toastId = toast.loading("Processing text with AI...");
                         try {
                              await axios.post(`/api/merchant/knowledge`, formData, { withCredentials: true });
                              toast.success("Knowledge Base ingested!", {id: toastId});
                              setKnowledgeBase("");
                         } catch (err) {
                              toast.error("Error ingesting text", {id: toastId});
                         }
                     }} className="bg-[var(--primary-color,#2563eb)] hover:opacity-90 text-white px-4 py-2 rounded text-sm font-medium transition shadow-sm">
                         Learn Text Source
                     </button>
                </div>
                <div className="mt-3 text-xs text-slate-500 flex items-center gap-2">
                   <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_5px_#22c55e]"></span>
                   Powered by Semantic Vector Search (pgvector)
                </div>
            </div>

            {/* Payment Details */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">{t('bank_title')}</h3>
                <p className="text-slate-500 mb-4 text-sm">{t('bank_desc')}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">{t('bank_name')}</label>
                        <input type="text" value={bankName} onChange={(e) => setBankName(e.target.value)} className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">{t('iban')}</label>
                        <input type="text" value={iban} onChange={(e) => setIban(e.target.value)} className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
                    </div>
                </div>
            </div>

            {/* Notifications */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">الإشعارات الذكية (Smart Notifications)</h3>
                <p className="text-slate-500 mb-4 text-sm">Receive alerts when a new order, appointment, or support request is generated by the AI.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Notification Email</label>
                        <input type="email" value={notificationEmail} onChange={(e) => setNotificationEmail(e.target.value)} placeholder="merchant@example.com" className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Notification Telegram Chat ID</label>
                        <input type="text" value={notificationTelegram} onChange={(e) => setNotificationTelegram(e.target.value)} placeholder="e.g. 12345678" className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
                        <p className="text-xs text-slate-400 mt-1">Start @userinfobot on Telegram to get your Chat ID.</p>
                    </div>
                </div>
            </div>

            {/* Staff Management */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">طاقم العمل (Staff & Doctors)</h3>
                <p className="text-slate-500 mb-4 text-sm">إذا كان لديك أكثر من موظف/طبيب، اكتب أسماءهم مفصولة بفاصلة. سيقوم الذكاء الاصطناعي بتخيير العميل بينهم عند الحجز ليتجنب التضارب.</p>
                <div>
                    <input type="text" value={staffMembers} onChange={(e) => setStaffMembers(e.target.value)} placeholder="مثال: د. يمان, د. خالد, د. سارة" className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
                </div>
            </div>

            {/* Bot Flows */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h3 className="text-lg font-bold text-slate-800">{t('botFlows')}</h3>
                        <p className="text-slate-500 text-sm">No-code keyword trigger bot responses</p>
                    </div>
                    <button onClick={() => { setEditingFlow({name: '', is_active: true, priority: 0, rules: [{trigger: '', match: 'contains', response: ''}]}); setShowFlowForm(true); }} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded text-sm font-medium transition">
                        + {t('newFlow')}
                    </button>
                </div>

                {showFlowForm && editingFlow && (
                    <div className="mb-6 h-[700px] rounded-2xl w-full relative">
                        <VisualFlowBuilder 
                            onClose={() => setShowFlowForm(false)} 
                            defaultUiState={editingFlow.flow_ui_state}
                            onSave={async (data: any) => {
                                try {
                                    const payload = {
                                        ...editingFlow,
                                        ...data,
                                        name: editingFlow.name || 'AI Flow ' + Math.floor(Math.random() * 1000),
                                        rules: editingFlow.rules || []
                                    };
                                    if(editingFlow.id) {
                                        await axios.put(`/api/merchant/flows/${editingFlow.id}`, payload, { withCredentials: true });
                                    } else {
                                        await axios.post(`/api/merchant/flows`, payload, { withCredentials: true });
                                    }
                                    toast.success(tCommon('save') || 'Saved successfully');
                                    setShowFlowForm(false);
                                    axios.get(`/api/merchant/flows`, { withCredentials: true }).then(res => setBotFlows(res.data.data));
                                } catch(e) { toast.error("Error saving flow"); }
                            }}
                        />
                    </div>
                )}

                <div className="space-y-2">
                    {botFlows.map(flow => (
                        <div key={flow.id} className="flex justify-between items-center p-3 border rounded-lg hover:bg-slate-50">
                            <div>
                                <div className="font-semibold text-slate-800">{flow.name}</div>
                                <div className="text-xs text-slate-500">{flow.rules.length} Rules • {flow.is_active ? <span className="text-green-600">Active</span> : <span className="text-red-500">Inactive</span>}</div>
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => { setEditingFlow(flow); setShowFlowForm(true); }} className="text-blue-600 hover:bg-blue-50 px-3 py-1 rounded text-sm border">{tCommon('edit')}</button>
                                <button onClick={async () => {
                                    if(confirm(tCommon('delete_confirm'))) {
                                        await axios.delete(`/api/merchant/flows/${flow.id}`, { withCredentials: true });
                                        setBotFlows(botFlows.filter(f => f.id !== flow.id));
                                    }
                                }} className="text-red-600 hover:bg-red-50 px-3 py-1 rounded text-sm border">{tCommon('delete')}</button>
                            </div>
                        </div>
                    ))}
                    {botFlows.length === 0 && <p className="text-sm text-slate-500 text-center py-4">No flows created yet.</p>}
                </div>
            </div>



            <div className="flex justify-end">
                <button 
                  onClick={saveSettings} 
                  disabled={updating}
                  className="bg-[var(--primary-color,#2563eb)] hover:opacity-90 text-white px-8 py-3 rounded-lg shadow font-medium transition"
                >
                  {updating ? t('saving_btn') : t('save_btn')}
                </button>
            </div>

            <div className="bg-white p-6 rounded-xl shadow border border-slate-100 mt-10">
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
            </div>
        </div>
    );
}
