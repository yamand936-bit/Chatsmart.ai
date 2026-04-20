'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useTranslations, useLocale } from 'next-intl';
import dynamic from 'next/dynamic';
import { Skeleton } from '@/components/Skeleton';

const AdminCharts = dynamic(() => import('@/components/AdminCharts'), {
  ssr: false,
  loading: () => <Skeleton className="h-80 rounded-xl w-full" />,
});

const AdminHealthTab = dynamic(() => import('@/components/AdminHealthTab'), {
  ssr: false,
  loading: () => <Skeleton className="h-60" />,
});

const AdminMRRSummary = dynamic(() => import('@/components/AdminMRRSummary'), {
  ssr: false,
  loading: () => <div className="p-10 text-center"><Skeleton className="h-60" /></div>,
});


const Sparkline = ({ data }: { data: number[] }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data, 1);
  return (
    <div className="flex items-end gap-1 h-8 mt-2 opacity-80" aria-hidden="true">
      {data.map((val, i) => {
        const heightPct = Math.max(10, (val / max) * 100);
        return (
           <div 
             key={i} 
             className="w-full bg-slate-300 dark:bg-slate-600 rounded-t-sm transition-all hover:bg-slate-400" 
             style={{ height: `${heightPct}%` }}
             title={val.toString()}
           />
        );
      })}
    </div>
  );
};

const StatCard = ({ title, value, icon, trend }: { title: string; value: string | number; icon: string; trend?: number[] }) => (
  <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col hover:shadow-md transition">
     <div className="flex items-center gap-3 mb-2">
       <span className="text-2xl">{icon}</span>
       <span className="font-bold text-slate-800 text-sm tracking-wide bg-slate-100 px-2 py-0.5 rounded uppercase">{title}</span>
     </div>
     <div className="text-3xl font-black text-slate-900 mt-auto">{value}</div>
     {trend && <Sparkline data={trend} />}
  </div>
);

export default function AdminDashboard() {
  const tAdmin = useTranslations('admin');
  const tSystem = useTranslations('system');
  const tCommon = useTranslations('common');
  
  const locale = useLocale();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  const [activeTab, setActiveTab] = useState<'overview' | 'merchants' | 'settings'>('overview');
  const [activeSettingsView, setActiveSettingsView] = useState<'general' | 'plans' | 'logs'>('general');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [systemSettings, setSystemSettings] = useState<any>({});
  
  const [name, setName] = useState('');
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [businessType, setBusinessType] = useState('retail');
  const [editingBusinessId, setEditingBusinessId] = useState<string | null>(null);
  
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState({ type: '', text: '' });
  const [savingSettings, setSavingSettings] = useState(false);
  
  const [maintenanceEnabled, setMaintenanceEnabled] = useState(false);
  const [selectedPlanBusinessId, setSelectedPlanBusinessId] = useState('');
  const [upgradeMsg, setUpgradeMsg] = useState({ type: '', text: '' });
  
  const [searchQuery, setSearchQuery] = useState('');
  const [planFilter, setPlanFilter] = useState('all');
  const [logSearch, setLogSearch] = useState('');
  
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkAction, setBulkAction] = useState('');
  const [bulkPlan, setBulkPlan] = useState('free');
  const [bulkCredits, setBulkCredits] = useState(0);

  const [selectedBusinessForSettings, setSelectedBusinessForSettings] = useState<any>(null);
  const [showLiveActivity, setShowLiveActivity] = useState(true);

  // Set up API client to automatically inject token
  const apiClient = axios.create({ baseURL: '', withCredentials: true });
  apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  useEffect(() => {
    const v = localStorage.getItem('hideLiveActivity');
    if (v === 'true') setShowLiveActivity(false);
    fetchData();
    const iv = setInterval(fetchData, 30000);
    return () => clearInterval(iv);
  }, []);

  const toggleActivity = (show: boolean) => {
    setShowLiveActivity(show);
    localStorage.setItem('hideLiveActivity', (!show).toString());
  };

  const fetchData = async () => {
    try {
      const [b, m, h, l, c] = await Promise.allSettled([
        apiClient.get('/api/admin/businesses'),
        apiClient.get('/api/admin/metrics'),
        apiClient.get('/api/admin/health'),
        apiClient.get('/api/admin/logs?limit=50'),
        apiClient.get('/api/system/settings')
      ]);

      if (b.status === 'fulfilled') setBusinesses(b.value.data.data || []);
      if (m.status === 'fulfilled') setMetrics(m.value.data.data);
      if (h.status === 'fulfilled') setSystemHealth(h.value.data);
      if (l.status === 'fulfilled') setLogs(l.value.data.data || []);
      if (c.status === 'fulfilled') {
        setSystemSettings(c.value.data.config || {});
        setMaintenanceEnabled(c.value.data.config?.maintenance_mode || false);
      }
    } catch (err: any) {
      if (err.response?.status === 401 || err.response?.status === 403) {
         window.location.href = '/login';
      }
    }
  };

  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateMsg({ type: '', text: '' });
    
    try {
      if (editingBusinessId) {
        await apiClient.patch(`/api/admin/businesses/${editingBusinessId}`, { 
           name, 
           business_type: businessType, 
           owner_password: ownerPassword || undefined 
        });
        setCreateMsg({ type: 'success', text: 'Business updated successfully' });
      } else {
        await apiClient.post('/api/admin/businesses', { 
           name, 
           business_type: businessType, 
           owner_email: ownerEmail, 
           owner_password: ownerPassword 
        });
        setCreateMsg({ type: 'success', text: 'Business details processed. Syncing bot flows in background...' });
      }
      setTimeout(() => { setIsCreateModalOpen(false); fetchData(); }, 2000);
    } catch (err: any) {
      setCreateMsg({ type: 'error', text: err.response?.data?.detail || 'An error occurred' });
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteBusiness = async (id: string) => {
    if (!window.confirm("Are you sure you want to completely delete this business? All data will be lost.")) return;
    try {
      await apiClient.delete(`/api/admin/businesses/${id}`);
      setBusinesses(businesses.filter(b => b.id !== id));
    } catch (err) {
      console.error(err);
      alert("Failed to delete business");
    }
  };

  const resetForm = () => {
     setEditingBusinessId(null);
     setName('');
     setOwnerEmail('');
     setOwnerPassword('');
     setBusinessType('retail');
     setCreateMsg({ type: '', text: '' });
  };
  
  const handleEdit = (id: string) => {
     const b = businesses.find(x => x.id === id);
     if (b) {
        setEditingBusinessId(b.id);
        setName(b.name);
        setOwnerEmail(b.owner_email);
        setOwnerPassword('');
        setBusinessType(b.business_type || 'retail');
        setIsCreateModalOpen(true);
     }
  };

  const handleSaveSystemSettings = async () => {
    setSavingSettings(true);
    try {
      await apiClient.post('/api/admin/config', systemSettings);
      alert('Settings saved!');
    } catch (err) {
      console.error(err);
      alert('Failed to save settings');
    } finally {
      setSavingSettings(false);
    }
  };

  const handleToggleMaintenance = async () => {
     const newState = !maintenanceEnabled;
     const updated = { ...systemSettings, maintenance_mode: newState };
     setSystemSettings(updated);
     setMaintenanceEnabled(newState);
     try {
       await apiClient.post('/api/admin/config', updated);
     } catch(err) {
        // revert on fail
     }
  };

  const handleUpgrade = async (planName: string) => {
     if(!selectedPlanBusinessId) return;
     setCreating(true);
     try {
        await apiClient.post(`/api/admin/businesses/${selectedPlanBusinessId}/subscribe`, { plan: planName, business_id: selectedPlanBusinessId });
        setUpgradeMsg({ type: 'success', text: `Successfully upgraded to ${planName}` });
        fetchData();
     } catch (err: any) {
        setUpgradeMsg({ type: 'error', text: err.response?.data?.detail || 'Upgrade failed' });
     } finally {
        setCreating(false);
     }
  };

  const handleImpersonate = async (id: string) => {
      try {
          const res = await apiClient.post(`/api/admin/impersonate/${id}`);
          if(res.data.token) {
              localStorage.setItem('token', res.data.token);
              window.location.href = '/app';
          }
      } catch (err) {
          alert('Failed to impersonate');
      }
  };
  
  const toggleAll = (e: any) => {
      if (e.target.checked) setSelectedIds(businesses.map(b => b.id));
      else setSelectedIds([]);
  };

  const toggleSelection = (id: string) => {
      setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleBulkAction = async () => {
      if (!bulkAction || selectedIds.length === 0) return;
      if (!window.confirm(`Apply ${bulkAction} to ${selectedIds.length} merchants?`)) return;
      
      try {
         if (bulkAction === 'plan') {
            await Promise.all(selectedIds.map(id => apiClient.post(`/api/admin/businesses/${id}/subscribe`, { plan: bulkPlan, business_id: id })));
         } else if (bulkAction === 'credits') {
            await apiClient.post('/api/admin/businesses/batch/credits', { business_ids: selectedIds, credits: bulkCredits });
         }
         setSelectedIds([]);
         setBulkAction('');
         fetchData();
         alert('Bulk action completed!');
      } catch(err) {
         console.error(err);
         alert('Failed bulk action');
      }
  };

  const getStatusColor = (s: string) => {
     if (!s) return 'bg-slate-100 text-slate-800';
     const st = s.toLowerCase();
     if (st === 'active') return 'bg-green-100 text-green-700';
     if (st === 'trial') return 'bg-blue-100 text-blue-700';
     if (st === 'expired' || st === 'suspended') return 'bg-red-100 text-red-700';
     return 'bg-slate-100 text-slate-800';
  };

  const profitData = businesses.map((b) => {
      // Mocked calculation for MRR summary 
      let cost = (b.token_usage || 0) * 0.000015;
      let profit = 0;
      if (b.plan_name === 'pro') profit = 49 - cost;
      if (b.plan_name === 'enterprise') profit = 199 - cost;
      
      const res: any = {
         name: b.name,
         Cost: parseFloat(cost.toFixed(6)),
         Profit: parseFloat(profit.toFixed(2))
      };
      
      const tokenKey = tAdmin('economic.total_tokens') || 'Tokens';
      const expectKey = tAdmin('forecast.expected') || 'Expected Profit';
      
      res[tokenKey] = b.token_usage || 0;
      res[expectKey] = parseFloat((profit * 1.15).toFixed(2));
      
      return res;
  });

  return (
    <div className="flex bg-slate-50 dark:bg-slate-900 min-h-screen" dir={dir}>
      {/* LEFT SIDEBAR */}
      <aside className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col p-4 shadow-sm z-10 sticky top-0 h-screen">
        <div className="text-xl font-black text-indigo-600 mb-8 px-2 flex items-center gap-2">
           <div className="w-8 h-8 bg-indigo-600 text-white rounded-lg flex items-center justify-center">S</div>
           <span>Super Admin</span>
        </div>
        
        <nav className="flex flex-col gap-2 flex-1">
           <button onClick={() => setActiveTab('overview')} className={`flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition-all ${activeTab === 'overview' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm' : 'text-slate-600 hover:bg-slate-100'}`}>
              📊 {tAdmin('tabs.overview')}
           </button>
           <button onClick={() => setActiveTab('merchants')} className={`flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition-all ${activeTab === 'merchants' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm' : 'text-slate-600 hover:bg-slate-100'}`}>
              🏢 {tAdmin('tabs.merchants')}
           </button>
           <button onClick={() => setActiveTab('settings')} className={`flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition-all ${activeTab === 'settings' ? 'bg-indigo-50 text-indigo-700 border border-indigo-100 shadow-sm' : 'text-slate-600 hover:bg-slate-100'}`}>
              ⚙️ {tAdmin('tabs.settings')}
           </button>
        </nav>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 w-full max-w-7xl mx-auto p-8 overflow-y-auto">
        <div className="space-y-8 pb-20">
        
        {/* WORKSPACE: OVERVIEW & HEALTH */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">{tAdmin('workspaces.system_overview')}</h2>
            
            <div className="mb-6"><AdminHealthTab /></div>
            
            {/* Top Stat Cards */}
            {metrics && (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <StatCard title={tAdmin('stats.total_businesses')} value={metrics.total_businesses || 0} icon="🏢" trend={metrics.sparklines?.businesses} />
                <StatCard title={tAdmin('stats.active_businesses')} value={metrics.active_businesses || 0} icon="🟢" trend={metrics.sparklines?.businesses} />
                <StatCard title={tAdmin('stats.total_orders')} value={metrics.total_orders || 0} icon="📦" />
                <StatCard title={tAdmin('stats.total_tokens_used')} value={metrics.total_tokens_used || 0} icon="🪙" trend={metrics.sparklines?.tokens} />
                <StatCard title="MRR" value={`$${metrics.mrr || 0}`} icon="💰" />
                <StatCard title="Requests/Day" value={metrics.ai_requests_today || 0} icon="⚡" trend={metrics.sparklines?.requests} />
              </div>
            )}
            
            {/* Charts */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
               <h3 className="text-lg font-semibold mb-4 text-slate-800">{tAdmin('workspaces.api_usage_trends')}</h3>
               <AdminCharts profitData={profitData} businesses={businesses} tAdmin={tAdmin as any} />
            </div>
          </div>
        )}

        {/* WORKSPACE: MERCHANTS */}
        {activeTab === 'merchants' && (
           <div className="space-y-6">
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-slate-200">
               <h2 className="text-xl font-bold text-slate-800">{tAdmin('workspaces.merchant_directory')}</h2>
               <button onClick={() => { resetForm(); setIsCreateModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-semibold shadow-sm transition">
                  + {tAdmin('workspaces.add_merchant')}
               </button>
            </div>
            
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-3 w-full bg-white p-3 rounded-xl shadow-sm border border-slate-200">
                 <input type="text" placeholder="Search name or email..." className="border border-slate-300 rounded-lg px-3 py-2 text-sm w-64 focus:ring-2 outline-none" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
                 <select className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white" value={planFilter} onChange={e => setPlanFilter(e.target.value)}>
                   <option value="all">All Plans</option>
                   <option value="free">Free</option>
                   <option value="starter">Starter</option>
                   <option value="pro">Pro</option>
                   <option value="enterprise">Enterprise</option>
                 </select>
                 
               {selectedIds.length > 0 && (
                <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 px-3 py-1.5 rounded-lg ml-auto">
                   <span className="text-sm font-semibold text-blue-700">{selectedIds.length} selected</span>
                   <select className="text-sm border border-slate-300 rounded-md px-2 py-1 bg-white" value={bulkAction} onChange={e => setBulkAction(e.target.value)}>
                      <option value="">-- Bulk Action --</option>
                      <option value="plan">Change Plan</option>
                      <option value="credits">Inject Credits</option>
                   </select>
                   {bulkAction === 'plan' && (
                      <select className="text-sm border border-slate-300 rounded-md px-2 py-1" value={bulkPlan} onChange={e => setBulkPlan(e.target.value)}>
                         <option value="free">Free</option>
                         <option value="pro">Pro</option>
                         <option value="enterprise">Enterprise</option>
                      </select>
                   )}
                   {bulkAction === 'credits' && (
                      <input type="number" placeholder="+500" className="w-24 text-sm border border-slate-300 rounded-md px-2 py-1 bg-white" value={bulkCredits} onChange={e => setBulkCredits(Number(e.target.value))} />
                   )}
                   <button onClick={handleBulkAction} className="bg-blue-600 text-white text-sm px-3 py-1 rounded-md font-medium hover:bg-blue-700">Apply</button>
                </div>
               )}
            </div>
            
            {/* Primary Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
               <table className="w-full text-start border-collapse text-sm">
                 <thead>
                   <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider text-[11px] font-bold">
                     <th className="py-3 px-4 text-start w-10"><input type="checkbox" onChange={toggleAll} checked={businesses.length > 0 && selectedIds.length === businesses.length} className="rounded" /></th>
                     <th className="py-3 px-4 text-start">{tAdmin('table.name_and_plan')}</th>
                     <th className="py-3 px-4 text-start">{tAdmin('table.owner_email')}</th>
                     <th className="py-3 px-4 text-start">MRR</th>
                     <th className="py-3 px-4 text-start">{tAdmin('table.credits_given')}</th>
                     <th className="py-3 px-4 text-start">{tAdmin('table.targeting')}</th>
                     <th className="py-3 px-4 text-center">Status</th>
                     <th className="py-3 px-4 text-end">{tAdmin('table.options')}</th>
                   </tr>
                 </thead>
                 <tbody className="divide-y divide-slate-100">
                   {businesses.filter(b => {
                      const matchSearch = !searchQuery || (b.name||'').toLowerCase().includes(searchQuery.toLowerCase()) || (b.owner_email||'').toLowerCase().includes(searchQuery.toLowerCase());
                      const matchPlan = planFilter === 'all' || b.plan_name === planFilter;
                      return matchSearch && matchPlan;
                   }).map((b) => (
                    <tr key={b.id} className="hover:bg-indigo-50/30 transition-colors group">
                       <td className="py-4 px-4"><input type="checkbox" checked={selectedIds.includes(b.id)} onChange={() => toggleSelection(b.id)} className="rounded" /></td>
                       <td className="py-4 px-4">
                         <div className="font-bold text-slate-800">{b.name}</div>
                         <div className="text-xs text-slate-500 uppercase font-medium mt-0.5">{b.plan_name || 'Free'}</div>
                       </td>
                       <td className="py-4 px-4 text-slate-600">{b.owner_email}</td>
                       <td className="py-4 px-4 font-semibold text-slate-800">${b.profit_margin > 0 ? b.profit_margin : 0}</td>
                       <td className="py-4 px-4 font-bold text-blue-600">{b.message_credits}</td>
                       <td className="py-4 px-4 text-lg" title="Connection">{b.features?.whatsapp || b.features?.telegram ? '🟢' : '🔴'}</td>
                       <td className="py-4 px-4 text-center">
                          <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider ${b.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                             {b.status.toUpperCase()}
                          </span>
                       </td>
                       <td className="py-4 px-4 text-end">
                         <div className="flex justify-end gap-2 rtl:flex-row-reverse opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => { handleImpersonate(b.id); }} className="text-slate-500 hover:text-green-600 transition border bg-white px-2 py-1 rounded shadow-sm text-xs" title="Login as Merchant">Login</button>
                            <button onClick={() => { handleEdit(b.id); }} className="text-slate-500 hover:text-blue-600 border bg-white transition px-2 py-1 rounded shadow-sm text-xs" title="Edit">Edit</button>
                            <button onClick={() => { handleDeleteBusiness(b.id); }} className="text-slate-500 hover:text-red-600 border bg-white transition px-2 py-1 rounded shadow-sm text-xs" title="Delete">🗑️</button>
                         </div>
                       </td>
                    </tr>
                   ))}
                 </tbody>
               </table>
               {businesses.filter(b => {
                      const matchSearch = !searchQuery || (b.name||'').toLowerCase().includes(searchQuery.toLowerCase()) || (b.owner_email||'').toLowerCase().includes(searchQuery.toLowerCase());
                      const matchPlan = planFilter === 'all' || b.plan_name === planFilter;
                      return matchSearch && matchPlan;
                   }).length === 0 && <div className="text-center py-10 text-slate-500">{tAdmin('table.no_businesses')}</div>}
            </div>
          </div>
        )}

        {/* WORKSPACE: SETTINGS & BILLING */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800">{tAdmin('workspaces.system_settings')}</h2>
            <div className="flex gap-2 bg-white p-1 rounded-lg shadow-sm border border-slate-200 w-max">
               <button onClick={()=>setActiveSettingsView('general')} className={`px-6 py-2 rounded-md font-medium text-sm transition ${activeSettingsView === 'general' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>{tAdmin('settings_nav.general')}</button>
               <button onClick={()=>setActiveSettingsView('plans')} className={`px-6 py-2 rounded-md font-medium text-sm transition ${activeSettingsView === 'plans' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>{tAdmin('settings_nav.subscription_plans')}</button>
               <button onClick={()=>setActiveSettingsView('logs')} className={`px-6 py-2 rounded-md font-medium text-sm transition ${activeSettingsView === 'logs' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>{tAdmin('settings_nav.error_logs')}</button>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 min-h-[400px]">
               {activeSettingsView === 'general' && (
                   <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                           <div>
                              <label className="block text-sm font-medium text-slate-700 mb-1">Platform Name</label>
                              <input className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings?.platform_name || ''} onChange={(e: any) => setSystemSettings({...systemSettings, platform_name: e.target.value})} />
                           </div>
                           <div>
                              <label className="block text-sm font-medium text-slate-700 mb-1">Support Phone</label>
                              <input className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings?.support_phone || ''} onChange={(e: any) => setSystemSettings({...systemSettings, support_phone: e.target.value})} placeholder="+1234567890" />
                           </div>
                           <div>
                              <label className="block text-sm font-medium text-slate-700 mb-1">AI Provider</label>
                              <select className="w-full border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 outline-none bg-white" value={systemSettings?.ai_provider || ''} onChange={(e: any) => setSystemSettings({...systemSettings, ai_provider: e.target.value})}>
                                <option value="openai">OpenAI (GPT-4)</option>
                                <option value="gemini">Google Gemini 1.5</option>
                              </select>
                           </div>
                      </div>

                      <div className="flex items-center justify-between border-b pb-4">
                         <div>
                            <h3 className="font-bold text-lg">{tAdmin('settings.maintenance_mode')}</h3>
                            <p className="text-sm text-slate-500">{tAdmin('settings.maintenance_desc')}</p>
                         </div>
                         <button onClick={handleToggleMaintenance} className={`px-4 py-2 rounded-lg font-bold text-white shadow-sm ${maintenanceEnabled ? 'bg-red-600' : 'bg-slate-400 hover:bg-slate-500'}`}>
                            {maintenanceEnabled ? tAdmin('settings.maintenance_is_on') : tAdmin('settings.turn_on_maintenance')}
                         </button>
                      </div>
                      <div className="flex justify-end pt-4"><button className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-bold" onClick={handleSaveSystemSettings}>{savingSettings ? tAdmin('settings.saving') : tAdmin('settings.save_settings')}</button></div>
                   </div>
               )}
               {activeSettingsView === 'plans' && (
                  <div className="space-y-8">
                    <div className="mb-4">
                      <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100">{tAdmin('plans.upgrades_title')}</h3>
                      <p className="text-slate-500 dark:text-slate-400 mb-6">{tAdmin('plans.subtitle') || 'Select a business and upgrade to a premium tier.'}</p>
                      <AdminMRRSummary />
                    </div>

                    {upgradeMsg.text && (
                      <div className={`p-4 rounded-xl text-sm font-medium ${upgradeMsg.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-600 border border-green-200'}`}>
                        {upgradeMsg.text}
                      </div>
                    )}

                    <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 max-w-xl">
                       <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('plans.select_placeholder')}</label>
                       <select 
                         className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 bg-white mb-4"
                         value={selectedPlanBusinessId} 
                         onChange={e => setSelectedPlanBusinessId(e.target.value)}
                         disabled={creating}
                       >
                         <option value="">{tAdmin('plans.select_placeholder')}</option>
                         {businesses.map(b => (
                           <option key={b.id} value={b.id}>{b.name} ({b.owner_email})</option>
                         ))}
                       </select>

                       <div className="flex gap-2">
                         <button onClick={() => handleUpgrade('free')} disabled={creating || !selectedPlanBusinessId} className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-800 py-2 rounded-lg font-bold">{tAdmin('plans.set_free') || 'Set Free'}</button>
                         <button onClick={() => handleUpgrade('pro')} disabled={creating || !selectedPlanBusinessId} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-bold">{tAdmin('plans.set_pro') || 'Set Pro'}</button>
                         <button onClick={() => handleUpgrade('enterprise')} disabled={creating || !selectedPlanBusinessId} className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-bold">{tAdmin('plans.set_enterprise') || 'Set Enterprise'}</button>
                       </div>
                    </div>
                  </div>
               )}
               {activeSettingsView === 'logs' && (
                  <div className="space-y-4">
                    <input type="text" placeholder={tAdmin('logs.filter_placeholder')} className="border border-slate-300 rounded-lg p-2 w-full max-w-md" value={logSearch} onChange={e => setLogSearch(e.target.value)} />
                    <div className="bg-slate-900 border border-slate-700 rounded-xl max-h-[600px] overflow-y-auto">
                        <table className="w-full text-slate-300 text-xs">
                           <tbody>
                             {logs.filter(l => (l.message||'').toLowerCase().includes(logSearch.toLowerCase())).map((l, i) => (
                                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800">
                                  <td className="p-3 w-32 font-mono text-slate-500">{new Date(l.timestamp).toLocaleString()}</td>
                                  <td className={`p-3 font-bold ${l.error_type==='error'?'text-red-400':l.error_type==='warning'?'text-yellow-400':'text-blue-400'}`}>{(l.error_type || 'error').toUpperCase()}</td>
                                  <td className="p-3 break-all">{l.message}</td>
                                </tr>
                             ))}
                             {logs.length === 0 && <tr><td colSpan={3} className="p-5 text-center text-slate-500">{tAdmin('logs.no_logs')}</td></tr>}
                           </tbody>
                        </table>
                    </div>
                  </div>
               )}
            </div>
          </div>
        )}
        </div>
      </main>
      {/* Live Activity Feed Sidebar */}
      {showLiveActivity && (
         <aside className="w-80 bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 flex flex-col p-4 shadow-sm h-screen sticky top-0 overflow-y-auto hidden xl:block">
           <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2 mt-4">
             <h3 className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
               <span className="relative flex h-3 w-3">
                 <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                 <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
               </span>
               Live Activity
             </h3>
             <div>
               <span className="text-xs text-slate-400 font-medium bg-slate-50 px-2 py-1 rounded">Auto-sync</span>
               <button onClick={() => toggleActivity(false)} className="text-xs ml-2 px-2 py-1 bg-slate-200 text-slate-600 rounded hover:bg-slate-300 transition">✖</button>
             </div>
           </div>
           
           <div className="space-y-4">
             {logs.length === 0 ? (
               <div className="text-center text-sm text-slate-500 py-4">No recent activity.</div>
             ) : (
               logs.slice(0, 15).map((log, idx) => (
                 <div key={idx} className="pb-3 border-b border-slate-50 last:border-0 last:pb-0">
                   <div className="flex items-start gap-2">
                     <span className="text-[16px] leading-none mt-0.5">{log.error_type === 'info' ? 'ℹ️' : log.error_type === 'warning' ? '⚠️' : '🔴'}</span>
                     <div>
                       <p className="text-sm font-medium text-slate-700 leading-snug">
                         <span className="font-bold">{log.business_name || 'System'}</span> 
                         <span className="text-slate-500 font-normal ml-1 line-clamp-2">{log.message}</span>
                       </p>
                       <p className="text-[10px] text-slate-400 mt-1 flex items-center gap-1 font-mono">
                          {new Date(log.timestamp).toLocaleTimeString()}
                       </p>
                     </div>
                   </div>
                 </div>
               ))
             )}
           </div>
         </aside>
      )}

      {/* Toggle Activity Button */}
      {!showLiveActivity && (
         <button onClick={() => toggleActivity(true)} className="fixed bottom-6 right-6 bg-slate-800 text-white px-4 py-3 rounded-full shadow-2xl hover:bg-slate-700 hover:scale-105 transition-all z-50 font-bold flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Activity Feed
         </button>
      )}

      {/* CREATE MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
              <div className="flex justify-between items-center p-6 border-b border-slate-100 sticky top-0 bg-white z-10">
                 <h2 className="text-xl font-bold text-slate-800">{editingBusinessId ? tAdmin('create.update_merchant') : tAdmin('create.add_new_merchant')}</h2>
                 <button onClick={() => setIsCreateModalOpen(false)} className="bg-slate-100 text-slate-500 w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-200 transition">✕</button>
              </div>
              <div className="p-6">
                 {/* Raw form goes here */}
                 <form onSubmit={handleCreateOrUpdate} className="space-y-6">
                    {createMsg.text && (
                      <div className={`p-4 rounded-xl flex items-center gap-3 font-medium ${createMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                        {createMsg.text}
                      </div>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.business_name')}</label>
                        <input required type="text" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none" value={name} onChange={e => setName(e.target.value)} disabled={creating} />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.business_type')}</label>
                        <select required className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none bg-white" value={businessType} onChange={e => setBusinessType(e.target.value)} disabled={creating}>
                          <option value="retail">Retail</option>
                          <option value="restaurant">Restaurant / Hotel</option>
                          <option value="services">Services / Real Estate</option>
                          <option value="medical">Medical / Clinic</option>
                        </select>
                      </div>
                      
                      {/* Only disable email if editing. Let password be updated if editing. */}
                      <div>
                         <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.owner_email')}</label>
                         <input required type="email" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 outline-none disabled:bg-slate-100" value={ownerEmail} onChange={e => setOwnerEmail(e.target.value)} disabled={creating || !!editingBusinessId} />
                      </div>
                      <div>
                         <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.owner_password')}</label>
                         <input required={!editingBusinessId} minLength={4} placeholder={editingBusinessId ? "**** (Leave blank to keep password)" : ""} type="password" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 outline-none" value={ownerPassword} onChange={e => setOwnerPassword(e.target.value)} disabled={creating} />
                      </div>
                    </div>
                    <div className="pt-6 border-t border-slate-100 flex justify-end">
                       <button type="submit" disabled={creating} className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold shadow-md hover:bg-indigo-700 disabled:opacity-50 transition">
                          {creating ? tAdmin('settings.saving') : (editingBusinessId ? tAdmin('create.update_merchant') : tAdmin('create.create_merchant'))}
                       </button>
                    </div>
                 </form>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
