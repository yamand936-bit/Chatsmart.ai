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



const Sparkline = ({ data }: { data: number[] }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data, 1);
  return (
    <div className="flex items-end h-[18px] gap-0.5 mt-3">
      {data.map((val, i) => (
        <div key={i} className="flex-1 bg-blue-100 rounded-sm transition-all hover:bg-blue-400 group-hover:bg-blue-200" title={val.toString()} style={{ height: `${Math.max((val / max) * 100, 10)}%` }}></div>
      ))}
    </div>
  );
};

const StatCard = ({ title, value, icon, trend }: { title: string, value: string | number, icon: string, trend?: number[] }) => (
  <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition group overflow-hidden relative">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-slate-500 dark:text-slate-400 text-sm mb-1 font-medium">{title}</p>
        <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">{value}</p>
      </div>
      <div className="text-3xl bg-blue-50 w-12 h-12 flex items-center justify-center rounded-lg">{icon}</div>
    </div>
    {trend && trend.length > 0 && <Sparkline data={trend} />}
  </div>
);

export default function AdminDashboard() {
  const tAdmin = useTranslations('admin');
  const tCommon = useTranslations('common');
  const tSystem = useTranslations('system');
  const locale = useLocale();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  const [businesses, setBusinesses] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [logSearch, setLogSearch] = useState('');
  const [activeTab, setActiveTab] = useState<'overview' | 'merchants' | 'settings'>('overview');
  const [activeSettingsView, setActiveSettingsView] = useState<'general' | 'plans' | 'logs'>('general');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  // Filtering & Batch
  const [searchQuery, setSearchQuery] = useState('');
  const [planFilter, setPlanFilter] = useState('all');
  const [usageGtFilter, setUsageGtFilter] = useState<number | ''>('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkAction, setBulkAction] = useState('');
  const [bulkPlan, setBulkPlan] = useState('pro');
  const [bulkTokens, setBulkTokens] = useState(100000);
  const [bulkCredits, setBulkCredits] = useState(500);

  // New States for Edit / Settings Modal
  const [editingBusinessId, setEditingBusinessId] = useState<string | null>(null);
  const [selectedBusinessForSettings, setSelectedBusinessForSettings] = useState<any>(null);

  // System Settings State
  const [systemSettings, setSystemSettings] = useState<any>({});
  const [savingSettings, setSavingSettings] = useState(false);

  // Form State
  const [name, setName] = useState('');
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerPassword, setOwnerPassword] = useState('');
  const [businessType, setBusinessType] = useState('retail');
  const [creating, setCreating] = useState(false);
  const [createMsg, setCreateMsg] = useState({ type: '', text: '' });

  // Feature Configs
  const [enTg, setEnTg] = useState(false);
  const [tgToken, setTgToken] = useState('');
  const [tgWebhook, setTgWebhook] = useState('');

  const [enWa, setEnWa] = useState(false);
  const [waPhone, setWaPhone] = useState('');
  const [waToken, setWaToken] = useState('');
  const [waAppSecret, setWaAppSecret] = useState('');

  useEffect(() => {
    fetchBusinesses();
  }, [searchQuery, planFilter, usageGtFilter]);

  useEffect(() => {
    console.log("AdminDashboard mounted: Initializing SSE/Polling");
    fetchData(); // initial fetch for metrics and logs
    
    // Auto-refresh metrics and feeds every 30 seconds
    const intervalId = setInterval(() => {
       console.log("Auto-refreshing dashboard data...");
       fetchData();
    }, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  const fetchBusinesses = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (planFilter && planFilter !== 'all') params.append('plan', planFilter);
      if (usageGtFilter !== '') params.append('usage_gt', String(usageGtFilter));

      const bizRes = await axios.get(`/api/admin/businesses?${params.toString()}`, { withCredentials: true });
      if (bizRes.data && bizRes.data.data) {
        setBusinesses(bizRes.data.data);
      } else {
        setBusinesses([]);
      }
    } catch (error) {
      console.error("Failed to load businesses:", error);
    }
  };

  const fetchData = async () => {
    fetchBusinesses();
    
    try {
      const logsRes = await axios.get(`/api/admin/logs?limit=15`, { withCredentials: true });
      if (logsRes.data && logsRes.data.data) {
        setLogs(logsRes.data.data);
      }
    } catch (error) {
      console.warn("Failed to load logs:", error);
    }

    try {
      const metRes = await axios.get(`/api/admin/metrics`, { withCredentials: true });
      if (metRes.data) {
        setMetrics(metRes.data);
      }
    } catch (error) {
      console.error("Failed to load metrics:", error);
    }
    
    try {
       const healthRes = await axios.get(`/api/admin/health`, { withCredentials: true });
       if (healthRes.data?.data) {
          setSystemHealth(healthRes.data.data);
       }
    } catch(e) {
       console.error("Failed to load health", e);
    }

    try {
      const settingsRes = await axios.get(`/api/system/settings`, { withCredentials: true });
      if (settingsRes.data && settingsRes.data.data) {
        setSystemSettings(settingsRes.data.data);
      } else if (settingsRes.data) {
        setSystemSettings(settingsRes.data);
      }
    } catch (error) {
      console.warn("Settings failed to load:", error);
    }
  };

  const resetForm = () => {
    setName('');
    setOwnerEmail('');
    setOwnerPassword('');
    setBusinessType('retail');
    setEnTg(false);
    setTgToken('');
    setTgWebhook('');
    setEnWa(false);
    setWaPhone('');
    setWaToken('');
    setWaAppSecret('');
    setEditingBusinessId(null);
    setCreateMsg({ type: '', text: '' });
  };

  const handleTabChange = (tab: any) => {
    setActiveTab(tab);
    if (tab !== 'create') {
      resetForm();
    }
  };

  const handleBulkAction = async () => {
    if (selectedIds.length === 0) return alert('Select businesses first');
    if (!bulkAction) return alert('Select an action');

    if (!window.confirm(`Are you sure you want to apply this action to ${selectedIds.length} businesses?`)) return;

    try {
      setCreating(true);
      if (bulkAction === 'plan') {
         await axios.post('/api/admin/businesses/batch/plan', { business_ids: selectedIds, new_plan: bulkPlan }, { withCredentials: true });
      } else if (bulkAction === 'tokens') {
         await axios.post('/api/admin/businesses/batch/tokens', { business_ids: selectedIds, token_limit: bulkTokens }, { withCredentials: true });
      } else if (bulkAction === 'credits') {
         await axios.post('/api/admin/businesses/batch/credits', { business_ids: selectedIds, credits_to_add: bulkCredits }, { withCredentials: true });
      }
      setCreateMsg({ type: 'success', text: 'Batch action completed successfully.' });
      setSelectedIds([]);
      fetchBusinesses();
    } catch (e) {
      alert('Batch action failed.');
    } finally {
      setCreating(false);
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const toggleAll = () => {
    if (selectedIds.length === businesses.length) setSelectedIds([]);
    else setSelectedIds(businesses.map(b => b.id));
  };

  const handleSaveSystemSettings = async () => {
    setSavingSettings(true);
    try {
      await axios.post(`/api/system/settings`, { settings: systemSettings }, { withCredentials: true });
      alert(tSystem('saved') || "Saved successfully");
    } catch (e) {
      console.error(e);
      alert("Failed to save settings.");
    }
    setSavingSettings(false);
  };

  const [maintenanceEnabled, setMaintenanceEnabled] = useState(false);

  const handleToggleMaintenance = async () => {
    if (!window.confirm("Are you sure you want to toggle Maintenance Mode? When enabled, merchants will not be able to log in.")) return;
    try {
      const res = await axios.post('/api/admin/system/maintenance', { enabled: !maintenanceEnabled }, { withCredentials: true });
      if (res.data.status === 'ok') {
         setMaintenanceEnabled(res.data.maintenance_enabled);
         alert(`Maintenance mode is now ${res.data.maintenance_enabled ? 'ON' : 'OFF'}`);
      }
    } catch (e) {
      alert('Failed to toggle maintenance mode');
    }
  };

  const [selectedPlanBusinessId, setSelectedPlanBusinessId] = useState<string>('');
  const [upgradeMsg, setUpgradeMsg] = useState({ type: '', text: '' });

  const handleUpgrade = async (plan: string) => {
    
    if (!selectedPlanBusinessId) {
      alert(tAdmin('plans.select_business_first') || 'Select a business first');
      return;
    }
    
    try {
      setCreating(true);
      const res = await axios.post(`/api/admin/subscribe`, {
        business_id: selectedPlanBusinessId,
        plan: plan
      }, { withCredentials: true });
      
      // Optimistic update so UI instantly changes to "Pro" or "Enterprise" without waiting/caching
      setBusinesses(prev => prev.map(b => 
        b.id === selectedPlanBusinessId 
        ? { ...b, plan_name: plan, token_limit: plan === 'free' ? 10000 : plan === 'pro' ? 100000 : -1 }
        : b
      ));
      
      setUpgradeMsg({ type: 'success', text: res.data.message || "Plan updated successfully" });
      setTimeout(() => setUpgradeMsg({ type: '', text: '' }), 5000);
      
      fetchData(); // Refreshes the local dashboard data in background
      
    } catch (e: any) {
      console.error(e);
      setUpgradeMsg({ type: 'error', text: e?.response?.data?.detail || 'Error upgrading plan' });
      setTimeout(() => setUpgradeMsg({ type: '', text: '' }), 5000);
    } finally {
      setCreating(false);
    }
  };


  const handleCreateOrUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setCreateMsg({ type: '', text: '' });
    try {
      let targetBusinessId = editingBusinessId;

      if (editingBusinessId) {
        // Update Business (PUT)
        await axios.put(`/api/admin/businesses/${editingBusinessId}`, {
          name,
          business_type: businessType
        }, { withCredentials: true });
        
        setCreateMsg({ type: 'success', text: tAdmin('table.update_success') || tCommon('success') });
      } else {
        // Create Business (POST)
        const res = await axios.post(`/api/admin/businesses`, {
          name,
          owner_email: ownerEmail,
          owner_password: ownerPassword,
          business_type: businessType
        }, { withCredentials: true });

        targetBusinessId = res.data.business_id;
        setCreateMsg({ type: 'success', text: tAdmin('create.success') || tCommon('success') });
      }

      // Configure Telegram
      if (enTg) {
        await axios.post(`/api/admin/businesses/${targetBusinessId}/features/telegram`, {
          is_active: true,
          config: { bot_token: tgToken, webhook_secret: tgWebhook }
        }, { withCredentials: true });
      } else if (editingBusinessId) {
        await axios.post(`/api/admin/businesses/${targetBusinessId}/features/telegram`, {
          is_active: false,
          config: {}
        }, { withCredentials: true });
      }

      // Configure WhatsApp
      if (enWa) {
        await axios.post(`/api/admin/businesses/${targetBusinessId}/features/whatsapp`, {
          is_active: true,
          config: { phone_number_id: waPhone, access_token: waToken, app_secret: waAppSecret }
        }, { withCredentials: true });
      } else if (editingBusinessId) {
        await axios.post(`/api/admin/businesses/${targetBusinessId}/features/whatsapp`, {
          is_active: false,
          config: {}
        }, { withCredentials: true });
      }

      await fetchData();
      setIsCreateModalOpen(false);
      resetForm();

    } catch (err: any) {
      setCreateMsg({ type: 'error', text: err?.response?.data?.detail || tCommon('error') });
    } finally {
      setCreating(false);
    }
  };

  const handleEdit = async (id: string) => {
    console.log('handleEdit function started for ID:', id);
    setCreateMsg({ type: '', text: '' });
    try {
      const url = `/api/admin/businesses/${id}`;
      console.log('Executing GET request to:', url);
      const res = await axios.get(url, { withCredentials: true });
      console.log('GET /businesses/{id} Response:', res.data);
      const b = res.data.data;
      setName(b.name || '');
      setBusinessType(b.business_type || 'retail');
      
      const features = b.features || {};
      if (features.telegram) {
        setEnTg(true);
        setTgToken(features.telegram.bot_token || '');
        setTgWebhook(features.telegram.webhook_secret || '');
      } else {
        setEnTg(false);
        setTgToken('');
        setTgWebhook('');
      }

      if (features.whatsapp) {
        setEnWa(true);
        setWaPhone(features.whatsapp.phone_number_id || '');
        setWaToken(features.whatsapp.access_token || '');
        setWaAppSecret(features.whatsapp.app_secret || '');
      } else {
        setEnWa(false);
        setWaPhone('');
        setWaToken('');
        setWaAppSecret('');
      }

      setEditingBusinessId(b.id);
      setIsCreateModalOpen(true);
    } catch (error: any) {
      console.error('Failed to fetch business details', error?.response?.data || error);
      alert('Failed to fetch business details');
    }
  };



  const handleToggleStatus = async (id: string, currentStatus: string) => {
    console.log('handleToggleStatus function started for ID:', id, 'Current Status:', currentStatus);
    const isInactive = currentStatus === 'inactive';
    const confirmMessage = isInactive ? (tAdmin('table.confirm_enable') || 'Confirm enable') : (tAdmin('table.confirm_disable') || 'Confirm disable');
    if (!window.confirm(confirmMessage)) {
      console.log('Status toggle canceled by user');
      return;
    }
    
    try {
      console.log('Executing PATCH request to status endpoint');
      setBusinesses(prev => prev.map(b => b.id === id ? { ...b, status: isInactive ? 'active' : 'inactive' } : b)); // Optimistic UI
      const res = await axios.patch(`/api/admin/businesses/${id}/status`, {
        status: isInactive ? 'active' : 'inactive'
      }, { withCredentials: true });
      console.log('PATCH response:', res.data);
      fetchData();
    } catch (error: any) {
      console.error('Failed to update status', error?.response?.data || error);
      fetchData(); // Rollback on failure
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700 border-green-200';
      case 'inactive': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const handleImpersonate = async (businessId: string) => {
    const newWindow = window.open('', '_blank');
    if (!newWindow) {
      alert("Please allow popups to use the Impersonate feature.");
      return;
    }
    newWindow.document.write('<div style="font-family:sans-serif;text-align:center;margin-top:20%;"><h2>Redirecting securely to Merchant Dashboard...</h2></div>');
    
    try {
       const res = await axios.post(`/api/admin/impersonate/${businessId}`, {}, {withCredentials: true});
       const token = res.data.token;
       newWindow.location.href = `/app?impersonate_token=${token}`;
    } catch(err) {
       console.error("Failed to impersonate", err);
       newWindow.close();
       alert("Failed to impersonate merchant. See console for details.");
    }
  };

  const getPlanCostPer1k = (planName: string) => {
    if(planName === 'enterprise') return 0.015;
    if(planName === 'pro') return 0.002;
    return 0.0015; // free
  };

  const getPlanBasePrice = (planName: string) => {
    if(planName === 'enterprise') return 199;
    if(planName === 'pro') return 49;
    return 0; // free
  };

  const profitData = businesses.map((b) => {
      const usage = b.token_usage || 0;
      const plan = b.plan_name || 'free';
      const cost = (usage / 1000) * getPlanCostPer1k(plan);
      const profit = getPlanBasePrice(plan) - cost;
      
      const res: any = {
         name: b.name,
         Cost: parseFloat(cost.toFixed(6)),
         Profit: parseFloat(profit.toFixed(2))
      };
      
      const tokenKey = tAdmin('economic.total_tokens') || 'Tokens';
      const expectKey = tAdmin('forecast.expected') || 'Expected Profit';
      
      res[tokenKey] = usage;
      res[expectKey] = parseFloat((profit * 1.15).toFixed(2));
      
      return res;
  });

  // Force AST recompilation to invalidate Next.js corrupted cache
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
            
            {/* Health Bar Wrapper */}
            {systemHealth && (
                <div className="flex flex-wrap gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                   <div className="flex flex-col">
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">CPU</span>
                      <span className={`text-lg font-bold ${systemHealth.cpu_usage > 80 ? 'text-red-500' : 'text-green-600'}`}>{systemHealth.cpu_usage}%</span>
                   </div>
                   <div className="w-px bg-slate-200 mx-2"></div>
                   <div className="flex flex-col">
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Memory</span>
                      <span className={`text-lg font-bold ${systemHealth.memory_usage > 80 ? 'text-red-500' : 'text-blue-600'}`}>{systemHealth.memory_usage}%</span>
                   </div>
                    <div className="w-px bg-slate-200 mx-2"></div>
                   <div className="flex flex-col">
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Disk</span>
                      <span className={`text-lg font-bold ${systemHealth.disk_usage > 80 ? 'text-red-500' : 'text-slate-600'}`}>{systemHealth.disk_usage}%</span>
                   </div>
                    <div className="w-px bg-slate-200 mx-2"></div>
                   <div className="flex flex-col">
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Redis</span>
                      <span className={`text-lg font-bold ${systemHealth.redis_status === 'online' ? 'text-green-600' : 'text-red-600'}`}>{systemHealth.redis_status.toUpperCase()}</span>
                   </div>
                    <div className="w-px bg-slate-200 mx-2"></div>
                   <div className="flex flex-col">
                      <span className="text-xs text-slate-500 uppercase tracking-wider font-bold">Database</span>
                      <span className={`text-lg font-bold ${systemHealth.db_status === 'online' ? 'text-green-600' : 'text-red-600'}`}>{systemHealth.db_status.toUpperCase()}</span>
                   </div>
                </div>
            )}
            
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
                   {businesses.map((b) => (
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
                         </div>
                       </td>
                    </tr>
                   ))}
                 </tbody>
               </table>
               {businesses.length === 0 && <div className="text-center py-10 text-slate-500">{tAdmin('table.no_businesses')}</div>}
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
                   <div>
                      <h3 className="font-bold text-xl mb-4">{tAdmin('plans.upgrades_title')}</h3>
                      <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 max-w-lg space-y-4">
                        <select className="w-full border p-2 rounded-lg border-slate-300 bg-white" value={selectedPlanBusinessId} onChange={e => setSelectedPlanBusinessId(e.target.value)}>
                           <option value="">{tAdmin('plans.select_placeholder')}</option>
                           {businesses.map(b => <option key={b.id} value={b.id}>{b.name} ({b.owner_email})</option>)}
                        </select>
                        <div className="flex gap-2">
                           <button onClick={() => handleUpgrade('free')} disabled={creating} className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-800 py-2 rounded-lg font-bold">{tAdmin('plans.set_free')}</button>
                           <button onClick={() => handleUpgrade('pro')} disabled={creating} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-bold">{tAdmin('plans.set_pro')}</button>
                           <button onClick={() => handleUpgrade('enterprise')} disabled={creating} className="flex-1 bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg font-bold">{tAdmin('plans.set_enterprise')}</button>
                        </div>
                        {upgradeMsg.text && (
                          <div className={`p-3 rounded-lg text-sm font-semibold mt-2 ${upgradeMsg.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                             {upgradeMsg.text}
                          </div>
                        )}
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
                                  <td className={`p-3 font-bold ${l.level==='error'?'text-red-400':l.level==='warning'?'text-yellow-400':'text-blue-400'}`}>{l.level.toUpperCase()}</td>
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

      {/* CREATE MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
           <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto flex flex-col">
              <div className="flex justify-between items-center p-6 border-b border-slate-100 sticky top-0 bg-white z-10">
                 <h2 className="text-xl font-bold text-slate-800">{editingBusinessId ? tAdmin('create.update_merchant') : tAdmin('create.add_new_merchant')}</h2>
                 <button onClick={() => setIsCreateModalOpen(false)} className="bg-slate-100 text-slate-500 w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-200">X</button>
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
                      {!editingBusinessId && (
                        <>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.owner_email')}</label>
                            <input required type="email" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 outline-none" value={ownerEmail} onChange={e => setOwnerEmail(e.target.value)} disabled={creating} />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.owner_password')}</label>
                            <input required type="password" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 outline-none" value={ownerPassword} onChange={e => setOwnerPassword(e.target.value)} disabled={creating} />
                          </div>
                        </>
                      )}
                    </div>
                    <div className="pt-6 border-t border-slate-100 flex justify-end">
                       <button type="submit" disabled={creating} className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-bold shadow-md hover:bg-indigo-700 disabled:opacity-50">
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
