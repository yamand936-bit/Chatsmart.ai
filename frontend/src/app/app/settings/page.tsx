'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';

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

            {/* Branding */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">{t('brand_title')}</h3>
                <p className="text-slate-500 mb-4 text-sm">{t('brand_desc')}</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">{t('primary_color')}</label>
                        <div className="flex items-center gap-3">
                           <input type="color" value={primaryColor} onChange={(e) => setPrimaryColor(e.target.value)} className="w-12 h-12 p-1 rounded border-gray-300 cursor-pointer" />
                           <span className="text-slate-600 font-mono text-sm">{primaryColor}</span>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">{t('logo_url')}</label>
                        <input type="text" value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} placeholder="https://example.com/logo.png" className="w-full rounded border-gray-300 shadow-sm p-3 bg-slate-50 outline-none" />
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
                    <div className="mb-6 p-4 border rounded-lg bg-indigo-50 border-indigo-100">
                        <div className="flex justify-between items-center mb-3">
                            <h4 className="font-bold text-slate-800">{editingFlow.id ? tCommon('edit') : t('newFlow')}</h4>
                            <button onClick={() => setShowFlowForm(false)} className="text-slate-500 hover:text-slate-700">✕</button>
                        </div>
                        <div className="flex gap-4 mb-4">
                            <div className="flex-1">
                                <label className="block text-xs font-semibold text-slate-700 mb-1">{t('flowName')}</label>
                                <input type="text" value={editingFlow.name} onChange={e => setEditingFlow({...editingFlow, name: e.target.value})} className="w-full rounded border p-2 text-sm outline-none focus:border-indigo-500" />
                            </div>
                            <div className="flex items-center gap-2 mt-5">
                                <input type="checkbox" checked={editingFlow.is_active} onChange={e => setEditingFlow({...editingFlow, is_active: e.target.checked})} className="w-4 h-4 cursor-pointer" />
                                <label className="text-sm font-medium text-slate-700">Active</label>
                            </div>
                        </div>
                        
                        <div className="space-y-3 mb-4">
                            <label className="block text-xs font-semibold text-slate-700">{t('flowRules')}</label>
                            {editingFlow.rules.map((rule: any, idx: number) => (
                                <div key={idx} className="flex flex-col md:flex-row gap-2 bg-white p-3 rounded border shadow-sm items-start md:items-center">
                                    <div className="flex-1">
                                        <input type="text" placeholder={t('triggerKeyword')} value={rule.trigger} onChange={e => {
                                            const newR = [...editingFlow.rules]; newR[idx].trigger = e.target.value; setEditingFlow({...editingFlow, rules: newR});
                                        }} className="w-full rounded border border-slate-200 p-2 text-sm outline-none" />
                                    </div>
                                    <div className="shrink-0">
                                        <select value={rule.match} onChange={e => {
                                            const newR = [...editingFlow.rules]; newR[idx].match = e.target.value; setEditingFlow({...editingFlow, rules: newR});
                                        }} className="rounded border border-slate-200 p-2 text-sm outline-none bg-slate-50">
                                            <option value="contains">Contains</option>
                                            <option value="exact">Exact Match</option>
                                            <option value="starts_with">Starts With</option>
                                        </select>
                                    </div>
                                    <div className="flex-1">
                                        <textarea placeholder={t('responseText')} value={rule.response} onChange={e => {
                                            const newR = [...editingFlow.rules]; newR[idx].response = e.target.value; setEditingFlow({...editingFlow, rules: newR});
                                        }} className="w-full rounded border border-slate-200 p-2 text-sm outline-none h-[38px] resize-none" />
                                    </div>
                                    <button onClick={() => {
                                        const newR = [...editingFlow.rules]; newR.splice(idx, 1); setEditingFlow({...editingFlow, rules: newR});
                                    }} className="text-red-500 hover:bg-red-50 p-2 rounded">
                                        ✕
                                    </button>
                                </div>
                            ))}
                            <button onClick={() => setEditingFlow({...editingFlow, rules: [...editingFlow.rules, {trigger: '', match: 'contains', response: ''}]})} className="text-indigo-600 text-sm font-medium hover:underline">
                                + {t('addRule')}
                            </button>
                        </div>

                        <div className="flex justify-end">
                            <button onClick={async () => {
                                try {
                                    if(editingFlow.id) {
                                        await axios.put(`/api/merchant/flows/${editingFlow.id}`, editingFlow, { withCredentials: true });
                                    } else {
                                        await axios.post(`/api/merchant/flows`, editingFlow, { withCredentials: true });
                                    }
                                    toast.success(t('saved'));
                                    setShowFlowForm(false);
                                    axios.get(`/api/merchant/flows`, { withCredentials: true }).then(res => setBotFlows(res.data.data));
                                } catch(e) { toast.error("Error saving flow"); }
                            }} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded text-sm font-medium transition">
                                {t('saveFlow')}
                            </button>
                        </div>
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

            {/* Integrations */}
            <div className="bg-white p-6 rounded-xl shadow border border-slate-100">
                <h3 className="text-lg font-bold text-slate-800 mb-2">Integrations</h3>
                <p className="text-slate-500 mb-4 text-sm">Connect external channels to AI Sales Assistant.</p>
                <div className="flex flex-col gap-4">
                    
                    <div className="flex flex-col md:flex-row md:items-center justify-between p-4 border rounded-lg bg-slate-50 gap-4">
                        <div className="flex items-center gap-3">
                            <div className="text-pink-600 bg-pink-100 p-2 rounded-full hidden md:block">
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                    <path fillRule="evenodd" d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772A4.902 4.902 0 015.45 2.525c.636-.247 1.363-.416 2.428-.465C8.901 2.013 9.256 2 11.685 2h.63zm-.081 1.802h-.468c-2.456 0-2.784.011-3.807.058-.975.045-1.504.207-1.857.344-.467.182-.8.398-1.15.748-.35.35-.566.683-.748 1.15-.137.353-.3.882-.344 1.857-.047 1.023-.058 1.351-.058 3.807v.468c0 2.456.011 2.784.058 3.807.045.975.207 1.504.344 1.857.182.466.399.8.748 1.15.35.35.683.566 1.15.748.353.137.882.3 1.857.344 1.054.048 1.37.058 4.041.058h.08c2.597 0 2.917-.01 3.96-.058.976-.045 1.505-.207 1.858-.344.466-.182.8-.398 1.15-.748.35-.35.566-.683.748-1.15.137-.353.3-.882.344-1.857.048-1.055.058-1.37.058-4.041v-.08c0-2.597-.01-2.917-.058-3.96-.045-.976-.207-1.505-.344-1.858a3.097 3.097 0 00-.748-1.15 3.098 3.098 0 00-1.15-.748c-.353-.137-.882-.3-1.857-.344-1.023-.047-1.351-.058-3.807-.058zM12 6.865a5.135 5.135 0 110 10.27 5.135 5.135 0 010-10.27zm0 1.802a3.333 3.333 0 100 6.666 3.333 3.333 0 000-6.666zm5.338-3.205a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h4 className="font-semibold text-slate-800">Instagram Direct</h4>
                                    {activeFeatures.includes('instagram') && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">Connected</span>}
                                </div>
                                <p className="text-xs text-slate-500">Enable AI for Instagram messages & story replies</p>
                            </div>
                        </div>
                        <div className="shrink-0 flex items-center">
                            {!activeFeatures.includes('instagram') ? (
                                <button 
                                    onClick={async () => {
                                        try {
                                            const res = await axios.get(`/api/auth/instagram/login`, { withCredentials: true });
                                            window.open(res.data.url, '_blank', 'width=600,height=700');
                                        } catch (e) {
                                            toast.error("Failed to initialize Instagram connect");
                                        }
                                    }}
                                    className="text-sm font-medium border border-slate-300 hover:bg-slate-100 px-4 py-2 rounded transition text-slate-700">
                                    Connect Instagram
                                </button>
                            ) : (
                                <button className="text-sm font-medium border border-red-300 text-red-600 hover:bg-red-50 px-4 py-2 rounded transition">
                                    Disconnect
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-col md:flex-row md:items-center justify-between p-4 border rounded-lg bg-slate-50 gap-4">
                        <div className="flex items-center gap-3">
                            <div className="text-black bg-gray-200 p-2 rounded-full hidden md:block">
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                    <path d="M19.53 7.15c-2.34-.1-4.24-1.8-4.52-4.06H11.8v14.1c0 2.22-1.9 4-4.13 4a4.14 4.14 0 01-4-4.3c0-2.22 1.6-3.9 3.8-4h.34v3.1a.99.99 0 00-.34-.05c-.56 0-1.02.48-1.02 1.1s.46 1.12 1.02 1.12 1.07-.48 1.07-1.12v-14h3.2c.16 2.5 1.96 4.6 4.3 4.9.04.01.2.03.24.03v3.13z"/>
                                </svg>
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h4 className="font-semibold text-slate-800">TikTok Business</h4>
                                    {activeFeatures.includes('tiktok') && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">Connected</span>}
                                </div>
                                <p className="text-xs text-slate-500">Enable AI for TikTok direct messages & video comments</p>
                            </div>
                        </div>
                        <div className="shrink-0 flex items-center">
                            {!activeFeatures.includes('tiktok') ? (
                                <button 
                                    onClick={async () => {
                                        try {
                                            const res = await axios.get(`/api/auth/tiktok/login`, { withCredentials: true });
                                            window.open(res.data.url, '_blank', 'width=600,height=700');
                                        } catch (e) {
                                            toast.error("Failed to initialize TikTok connect");
                                        }
                                    }}
                                    className="text-sm font-medium border border-slate-300 hover:bg-slate-100 px-4 py-2 rounded transition text-slate-700">
                                    Connect TikTok
                                </button>
                            ) : (
                                <button className="text-sm font-medium border border-red-300 text-red-600 hover:bg-red-50 px-4 py-2 rounded transition">
                                    Disconnect
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-slate-50">
                        <div className="flex items-center gap-3">
                            <div className="text-blue-500 bg-blue-100 p-2 rounded-full hidden md:block">
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                     <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.96-.65-.34-1.01.24-1.61.15-.15 2.71-2.48 2.76-2.7.01-.03.01-.14-.08-.19-.09-.05-.2.02-.28.05-.33.14-2.88 1.83-3.6 2.31-.69.45-1.31.67-1.93.66-.75-.02-2.18-.42-3.24-.77-.87-.29-1.57-.44-1.51-.93.03-.25.38-.51 1.03-.78 4.04-1.76 6.74-2.92 8.09-3.48 3.85-1.6 4.64-1.88 5.17-1.89.12 0 .37.03.5.15.11.1.15.24.16.37-.01.12-.01.26-.03.35z"/>
                                </svg>
                            </div>
                            <div>
                                <div className="flex items-center gap-2">
                                    <h4 className="font-semibold text-slate-800">Telegram Bot</h4>
                                    {activeFeatures.includes('telegram') && <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">Connected</span>}
                                </div>
                                <p className="text-xs text-slate-500">Provide your Bot Token to instantly configure Telegram messaging</p>
                            </div>
                        </div>
                        {!activeFeatures.includes('telegram') ? (
                            <div className="flex flex-col md:flex-row gap-2 mt-2">
                                 <input type="text" value={telegramBotToken} onChange={e => setTelegramBotToken(e.target.value)} placeholder="Bot Token (e.g. 1234:ABC)" className="flex-1 rounded border-gray-300 p-2 text-sm outline-none" />
                                 <input type="text" value={telegramWebhookSecret} onChange={e => setTelegramWebhookSecret(e.target.value)} placeholder="Webhook Secret Phrase" className="w-48 rounded border-gray-300 p-2 text-sm outline-none" />
                                 <button
                                     onClick={async () => {
                                          if (!telegramBotToken || !telegramWebhookSecret) return toast.error("Please fill both Token and Secret");
                                          try {
                                              const res = await axios.post(`/api/merchant/features/telegram`, {
                                                   bot_token: telegramBotToken,
                                                   webhook_secret: telegramWebhookSecret,
                                                   action: 'validate'
                                              }, { withCredentials: true });
                                              
                                              if (res.data.status === 'success') {
                                                   toast.success(`Connected to: @${res.data.bot_username}`);
                                                   // Save it for real
                                                   await axios.post(`/api/merchant/features/telegram`, {
                                                        bot_token: telegramBotToken,
                                                        webhook_secret: telegramWebhookSecret,
                                                        action: 'save'
                                                   }, { withCredentials: true });
                                                   setActiveFeatures([...activeFeatures, 'telegram']);
                                              } else {
                                                   toast.error(res.data.message || "Failed validating token");
                                              }
                                          } catch (e) {
                                              toast.error("Failed to configure Telegram");
                                          }
                                     }}
                                     className="bg-blue-600 text-white font-medium px-4 py-2 rounded shadow hover:bg-blue-700 transition shrink-0"
                                 >
                                     Verify & Connect
                                 </button>
                            </div>
                        ) : (
                            <div className="mt-2 text-sm text-green-700 bg-green-50 p-3 rounded border border-green-200">
                                Telegram Webhook is securely attached to your business profile. To modify or reset, please contact support.
                            </div>
                        )}
                    </div>
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
