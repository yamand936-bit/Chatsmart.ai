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
  const [activeTab, setActiveTab] = useState<'businesses' | 'create' | 'usage' | 'plans' | 'health' | 'settings' | 'logs'>('businesses');

  // Filtering & Batch
  const [searchQuery, setSearchQuery] = useState('');
  const [planFilter, setPlanFilter] = useState('all');
  const [usageGtFilter, setUsageGtFilter] = useState<number | ''>('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [bulkAction, setBulkAction] = useState('');
  const [bulkPlan, setBulkPlan] = useState('pro');
  const [bulkTokens, setBulkTokens] = useState(100000);

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
      setActiveTab('businesses');
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
      setActiveTab('create');
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

  const profitData = businesses.map(b => {
      const usage = b.token_usage || 0;
      const plan = b.plan_name || 'free';
      const cost = (usage / 1000) * getPlanCostPer1k(plan);
      const profit = getPlanBasePrice(plan) - cost;
      return {
         name: b.name,
         [tAdmin('economic.total_tokens') || 'Tokens']: usage,
         Cost: parseFloat(cost.toFixed(6)),
         Profit: parseFloat(profit.toFixed(2)),
         [tAdmin('forecast.expected') || 'Expected Profit']: parseFloat((profit * 1.15).toFixed(2))
      };
  });

  return (
    <div className="flex gap-6" dir={dir}>
      {/* Main Content Area */}
      <div className="flex-1 space-y-6 min-w-0">
        {/* Stats Section */}
        {metrics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <StatCard title={tAdmin('stats.total_businesses')} value={metrics.total_businesses || 0} icon="🏢" 
               trend={metrics.sparklines?.businesses} />
            <StatCard title={tAdmin('stats.active_businesses')} value={metrics.active_businesses || 0} icon="🟢" 
               trend={metrics.sparklines?.businesses} />
            <StatCard title={tAdmin('stats.total_orders')} value={metrics.total_orders || 0} icon="📦" />
            <StatCard title={tAdmin('stats.total_tokens_used')} value={metrics.total_tokens_used || 0} icon="🪙" 
               trend={metrics.sparklines?.tokens} />
            <StatCard title={'MRR'} value={`$${metrics.mrr || 0}`} icon="💰" />
            <StatCard title={'Requests/Day'} value={metrics.ai_requests_today || 0} icon="⚡" 
               trend={metrics.sparklines?.requests} />
            <StatCard title={'Webhook Health'} value={`${metrics.webhook_delivery_rate !== undefined ? metrics.webhook_delivery_rate : 100}%`} icon="❤️‍🩹" />
          </div>
        )}
        
        {/* System Health Section */}
        {systemHealth && (
            <div className="flex flex-wrap gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 shadow-inner rtl:space-x-reverse">
               <div className="flex items-center gap-2">
                  <span className="text-xl">🖥️</span>
                  <span className="text-sm font-bold text-slate-700">CPU: <span className={systemHealth.cpu_usage > 80 ? 'text-red-500' : 'text-green-600'}>{systemHealth.cpu_usage}%</span></span>
               </div>
               <div className="w-px h-6 bg-slate-300 mx-2 hidden md:block"></div>
               <div className="flex items-center gap-2">
                  <span className="text-xl">🛠️</span>
                  <span className="text-sm font-bold text-slate-700">RAM: <span className={systemHealth.memory_usage > 80 ? 'text-red-500' : 'text-blue-600'}>{systemHealth.memory_usage}%</span></span>
               </div>
               <div className="w-px h-6 bg-slate-300 mx-2 hidden md:block"></div>
               <div className="flex items-center gap-2">
                  <span className="text-xl">💽</span>
                  <span className="text-sm font-bold text-slate-700">Disk: <span className={systemHealth.disk_usage > 80 ? 'text-red-500' : 'text-slate-600'}>{systemHealth.disk_usage}%</span></span>
               </div>
               <div className="w-px h-6 bg-slate-300 mx-2 hidden md:block"></div>
               <div className="flex items-center gap-2">
                  <span className="text-xl">⚡</span>
                  <span className="text-sm font-bold text-slate-700">Redis: <span className={systemHealth.redis_status === 'online' ? 'text-green-600' : 'text-red-600'}>{systemHealth.redis_status.toUpperCase()}</span></span>
               </div>
               <div className="w-px h-6 bg-slate-300 mx-2 hidden md:block"></div>
               <div className="flex items-center gap-2">
                  <span className="text-xl">🌐</span>
                  <span className="text-sm font-bold text-slate-700">DB: <span className={systemHealth.db_status === 'online' ? 'text-green-600' : 'text-red-600'}>{systemHealth.db_status.toUpperCase()}</span></span>
               </div>
            </div>
        )}
      
      {/* Plans Distribution (optional visual) */}
      {metrics?.plan_distribution && (
         <div className="flex gap-4">
            {Object.keys(metrics.plan_distribution).map(plan => (
               <div key={plan} className="bg-white py-1 px-3 border border-slate-200 rounded-full text-xs font-bold text-slate-600 shadow-sm capitalize">
                  {plan}: {metrics.plan_distribution[plan]}
               </div>
            ))}
         </div>
      )}

      {/* Tabs */}
      <div className="flex space-x-2 rtl:space-x-reverse bg-gray-100 p-1.5 rounded-xl w-max shadow-inner">
        {['businesses', 'create', 'usage', 'plans', 'health', 'settings', 'logs'].map((tab) => (
          <button
            key={tab}
            onClick={() => handleTabChange(tab)}
            className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 cursor-pointer flex-1 ${
              activeTab === tab ? 'bg-blue-600 text-white shadow-md' : 'text-slate-600 hover:bg-gray-200 hover:text-slate-900'
            }`}
          >
            {tab === 'create' && editingBusinessId ? (tAdmin('table.update') || 'Update') : tAdmin(`tabs.${tab}` as any)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 p-6 md:p-8 min-h-[500px] relative">
        
        {/* Businesses Tab */}
        {activeTab === 'businesses' && (
          <div className="space-y-4">
            {/* Filters & Bulk Actions Block */}
            <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
                 <input 
                   type="text" 
                   placeholder="Search name or email..." 
                   className="border border-slate-300 rounded-lg px-3 py-2 text-sm max-w-xs focus:ring-2 outline-none"
                   value={searchQuery}
                   onChange={e => setSearchQuery(e.target.value)}
                 />
                 <select 
                   className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
                   value={planFilter}
                   onChange={e => setPlanFilter(e.target.value)}
                 >
                   <option value="all">All Plans</option>
                   <option value="free">Free</option>
                   <option value="starter">Starter</option>
                   <option value="pro">Pro</option>
                   <option value="enterprise">Enterprise</option>
                 </select>
                 <select 
                   className="border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
                   value={usageGtFilter}
                   onChange={e => setUsageGtFilter(e.target.value === '' ? '' : Number(e.target.value))}
                 >
                   <option value="">Any Usage</option>
                   <option value="50">&gt; 50% Usage</option>
                   <option value="80">&gt; 80% Usage (Risk)</option>
                   <option value="95">&gt; 95% Usage (Critical)</option>
                 </select>
              </div>

              {selectedIds.length > 0 && (
              <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 p-2 rounded-lg">
                 <span className="text-sm font-semibold text-blue-700">{selectedIds.length} chosen</span>
                 <select 
                   className="text-sm border border-slate-300 rounded-md px-2 py-1 bg-white"
                   value={bulkAction}
                   onChange={e => setBulkAction(e.target.value)}
                 >
                    <option value="">-- Actions --</option>
                    <option value="plan">Change Plan</option>
                    <option value="tokens">Adjust Tokens</option>
                 </select>
                 {bulkAction === 'plan' && (
                    <select className="text-sm border border-slate-300 rounded-md px-2 py-1" value={bulkPlan} onChange={e => setBulkPlan(e.target.value)}>
                       <option value="free">Free</option>
                       <option value="pro">Pro</option>
                       <option value="enterprise">Enterprise</option>
                    </select>
                 )}
                 {bulkAction === 'tokens' && (
                    <input type="number" className="w-24 text-sm border border-slate-300 rounded-md px-2 py-1" value={bulkTokens} onChange={e => setBulkTokens(Number(e.target.value))} />
                 )}
                 <button onClick={handleBulkAction} className="bg-blue-600 text-white text-sm px-3 py-1 rounded-md hover:bg-blue-700">Apply</button>
              </div>
              )}
            </div>

            <div className="overflow-x-auto">
            {businesses.length === 0 ? (
               <div className="flex flex-col items-center justify-center py-20 text-slate-500 min-h-[300px]">
                 <div className="text-6xl mb-4">🏢</div>
                 <p className="text-xl font-medium text-slate-700 mb-6">{tAdmin('table.no_businesses')}</p>
                 <button 
                  onClick={() => handleTabChange('create')}
                  className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm cursor-pointer"
                 >
                   {tAdmin('tabs.create')}
                 </button>
               </div>
            ) : (
              <table className="w-full text-start border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 text-sm">
                    <th className="py-4 font-semibold px-2 text-start">
                      <input type="checkbox" onChange={toggleAll} checked={businesses.length > 0 && selectedIds.length === businesses.length} />
                    </th>
                      <th className="py-4 px-2 font-semibold">Last Active</th>
                    <th className="py-4 font-semibold px-2 text-start">{tAdmin('table.name')}</th>
                    <th className="py-4 font-semibold px-2 text-start">{tAdmin('table.owner_email')}</th>
                    <th className="py-4 font-semibold px-2 text-start">Profit Margin</th>
                    <th className="py-4 font-semibold px-2 text-start">{tAdmin('table.token_usage')}</th>
                    <th className="py-4 font-semibold px-2 text-start">{tAdmin('table.connection_status') || 'Connection Status'}</th>
                    <th className="py-4 font-semibold px-2 text-start">{tAdmin('table.status')}</th>
                    <th className="py-4 font-semibold px-2 text-end">{tCommon('actions')}</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {businesses.map((b) => {
                    const limit = b.token_limit || 100000;
                    const usage = b.token_usage || 0;
                    const percentage = Math.min((usage / limit) * 100, 100);
                    let pgColor = 'bg-green-500';
                    if (percentage >= 90) pgColor = 'bg-red-500';
                    else if (percentage >= 70) pgColor = 'bg-yellow-500';
                    
                    return (
                    <tr key={b.id} className="border-b border-slate-100 hover:bg-gray-50 transition-colors group">
                      <td className="py-4 px-2">
                         <input type="checkbox" checked={selectedIds.includes(b.id)} onChange={() => toggleSelection(b.id)} />
                      </td>
                      <td className="py-4 px-2 font-medium text-slate-800">
                        {b.name}
                        <div className="text-xs text-slate-500 font-normal mt-0.5 capitalize">{b.plan_name || 'Free'}</div>
                      </td>
                      <td className="py-4 px-2 text-slate-600">{b.owner_email}</td>
                      <td className="py-4 px-2 text-slate-500 text-xs">{b.last_active ? new Date(b.last_active).toLocaleString() : 'Never'}</td>
                      <td className="py-4 px-2">
                        <span className={`font-semibold ${b.profit_margin < 0 ? 'text-red-600' : 'text-green-600'}`}>
                          ${b.profit_margin}
                        </span>
                        <div className="text-[10px] text-slate-400">Cost: ${b.api_cost}</div>
                      </td>
                      <td className="py-4 px-2">
                         <div className="flex flex-col gap-1 w-32">
                           <span className="text-xs text-slate-500">{usage.toLocaleString()} / {limit.toLocaleString()}</span>
                           <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                             <div className={`h-1.5 rounded-full ${pgColor} transition-all duration-500`} style={{ width: `${percentage}%` }}></div>
                           </div>
                         </div>
                      </td>
                      <td className="py-4 px-2">
                         <span title="Connection Status">
                            {b.features?.whatsapp || b.features?.telegram ? '🟢' : '🔴'}
                         </span>
                      </td>
                      <td className="py-4 px-2">
                        <span className={`px-2.5 py-1 rounded-md text-xs font-medium border ${getStatusColor(b.status)}`}>
                          {b.status === 'active' ? (tAdmin('table.status_active') || 'Active') : (tAdmin('table.status_inactive') || 'Inactive')}
                        </span>
                      </td>
                      <td className="py-4 px-2 text-end">
                        <div className="flex justify-end gap-3 rtl:flex-row-reverse opacity-70 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => { handleImpersonate(b.id); }} className="text-slate-500 hover:text-green-600 transition-colors cursor-pointer text-base flex gap-1 items-center border border-slate-200 px-2 py-1 rounded-lg" title={tAdmin('table.impersonate') || 'Login as Merchant'}>
                             🔑 {tAdmin('table.impersonate') || 'Impersonate'}
                          </button>
                          <button onClick={() => { handleEdit(b.id); }} className="text-slate-500 hover:text-blue-600 transition-colors cursor-pointer text-base" title={tAdmin('table.edit') || 'Edit'}>✏️</button>
                          <button onClick={() => { setSelectedBusinessForSettings(b); }} className="text-slate-500 hover:text-blue-600 transition-colors cursor-pointer text-base" title={tAdmin('table.configure') || 'Configure'}>⚙️</button>
                          <button onClick={() => { handleToggleStatus(b.id, b.status); }} className="text-slate-500 hover:text-red-600 transition-colors cursor-pointer text-base" title={tAdmin('table.disable') || 'Disable'}>⛔</button>
                        </div>
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            )}
            </div>
          </div>
        )}

        {/* Create / Update Business Tab */}
        {activeTab === 'create' && (
          <form onSubmit={handleCreateOrUpdate} className="max-w-3xl space-y-8">
            
            {createMsg.text && (
              <div className={`p-4 rounded-xl flex items-center gap-3 font-medium ${createMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100' : 'bg-red-50 text-red-700 border border-red-100'}`}>
                <span className="text-xl">{createMsg.type === 'success' ? '✅' : '❌'}</span>
                {createMsg.text}
              </div>
            )}

            {/* Basic & Owner Info Section */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-slate-800 border-b pb-2">
                {editingBusinessId ? (tAdmin('table.update') || 'Update') : tAdmin('tabs.create')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.business_name')}</label>
                  <input required type="text" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" value={name} onChange={e => setName(e.target.value)} disabled={creating} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.business_type')}</label>
                  <select required className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow bg-white cursor-pointer" value={businessType} onChange={e => setBusinessType(e.target.value)} disabled={creating}>
                    <option value="retail">{tAdmin('create.type_retail')}</option>
                    <option value="restaurant">{tAdmin('create.type_restaurant')}</option>
                    <option value="services">{tAdmin('create.type_services')}</option>
                  </select>
                </div>
                {!editingBusinessId && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.email')}</label>
                      <input required type="email" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" value={ownerEmail} onChange={e => setOwnerEmail(e.target.value)} disabled={creating} />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">{tAdmin('create.password')}</label>
                      <input required type="password" className="w-full border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-shadow" value={ownerPassword} onChange={e => setOwnerPassword(e.target.value)} disabled={creating} />
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Integrations Section */}
            <div className="space-y-6 pt-4 cursor-pointer">
                <h3 className="text-lg font-semibold text-slate-800 border-b pb-2">{tAdmin('create.integrations_title')}</h3>
                
                {/* Telegram */}
                <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-200 transition-colors hover:border-blue-200">
                  <label className="flex items-center space-x-3 rtl:space-x-reverse cursor-pointer w-max">
                    <div className="relative flex items-center">
                      <input type="checkbox" checked={enTg} onChange={e => setEnTg(e.target.checked)} disabled={creating} className="w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500 cursor-pointer" />
                    </div>
                    <span className="font-semibold text-slate-700 flex items-center gap-2">
                      <span className="text-blue-500 font-normal">✈️</span> {tAdmin('create.telegram')}
                    </span>
                  </label>
                  
                  {enTg && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 transition-all">
                      <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">{tAdmin('create.bot_token')}</label>
                        <input type="text" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow" value={tgToken} onChange={e => setTgToken(e.target.value)} disabled={creating} />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">{tAdmin('create.webhook_secret')}</label>
                        <input type="text" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow" value={tgWebhook} onChange={e => setTgWebhook(e.target.value)} disabled={creating} />
                      </div>
                    </div>
                  )}
                </div>

                {/* WhatsApp */}
                <div className="bg-slate-50/50 p-5 rounded-2xl border border-slate-200 transition-colors hover:border-green-200">
                  <label className="flex items-center space-x-3 rtl:space-x-reverse cursor-pointer w-max">
                    <div className="relative flex items-center">
                      <input type="checkbox" checked={enWa} onChange={e => setEnWa(e.target.checked)} disabled={creating} className="w-5 h-5 rounded border-slate-300 text-green-600 focus:ring-green-500 cursor-pointer" />
                    </div>
                    <span className="font-semibold text-slate-700 flex items-center gap-2">
                      <span className="text-green-500 font-normal">💬</span> {tAdmin('create.whatsapp')}
                    </span>
                  </label>
                  {enWa && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5 transition-all">
                      <div>
                         <label className="block text-xs font-medium text-slate-500 mb-1">{tAdmin('create.phone_number_id')}</label>
                         <input type="text" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow" value={waPhone} onChange={e => setWaPhone(e.target.value)} disabled={creating} />
                      </div>
                      <div>
                         <label className="block text-xs font-medium text-slate-500 mb-1">{tAdmin('create.access_token')}</label>
                         <input type="text" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow" value={waToken} onChange={e => setWaToken(e.target.value)} disabled={creating} />
                      </div>
                      <div>
                         <label className="block text-xs font-medium text-slate-500 mb-1">{tAdmin('create.app_secret')}</label>
                         <input type="text" className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-shadow" value={waAppSecret} onChange={e => setWaAppSecret(e.target.value)} disabled={creating} />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            <div className="flex justify-end pt-6">
              <button 
                type="submit" 
                disabled={creating}
                className="bg-blue-600 text-white px-8 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center gap-2"
              >
                {creating && <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>}
                {creating ? tCommon('loading') : (editingBusinessId ? (tAdmin('table.update') || 'Update') : tCommon('submit'))}
              </button>
                <div className="mt-6 border-t border-red-300 pt-4">
                  <h4 className="flex items-center gap-2 font-bold text-red-800 mb-2">📢 Global Announcement Banner</h4>
                  <input type="text" id="announcementInput" className="w-full border p-2 rounded mb-2 text-black bg-white" placeholder="e.g. System upgrade in 5 minutes!..." />
                  <button onClick={() => { const val = (document.getElementById('announcementInput') as HTMLInputElement).value; axios.post('/api/admin/system/announcement', {message: val}, {withCredentials: true}).then(()=>alert('Broadcasted!')).catch(()=>alert('Failed')); }} className="px-4 py-2 bg-red-600 text-white rounded font-bold hover:bg-red-700 block">
                    Broadcast Banner
                  </button>
                </div>
            </div>
          </form>
        )}

        {/* Usage Tab */}
        {activeTab === 'usage' && (
          <div className="space-y-6">
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-slate-800">{tAdmin('usage.title')}</h3>
              <p className="text-slate-500">{tAdmin('usage.subtitle')}</p>
            </div>

            {businesses.length === 0 ? (
              <div className="p-10 text-center text-slate-500 bg-slate-50 rounded-2xl border border-slate-100">
                {tAdmin('table.no_businesses')}
              </div>
            ) : (
              <AdminCharts profitData={profitData} businesses={businesses} tAdmin={tAdmin} />
            )}
          </div>
        )}

        {/* Plans Tab */}
        {activeTab === 'plans' && (
          <div className="space-y-8">
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-100">{tAdmin('plans.title') || 'Subscription Plans'}</h3>
              <p className="text-slate-500 dark:text-slate-400 mb-6">{tAdmin('plans.subtitle') || 'Select a business and upgrade to a premium tier.'}</p>
              <AdminMRRSummary />
            </div>

            {upgradeMsg.text && (
              <div className={`p-4 rounded-xl text-sm font-medium ${upgradeMsg.type === 'error' ? 'bg-red-50 text-red-600 border border-red-200' : 'bg-green-50 text-green-600 border border-green-200'}`}>
                {upgradeMsg.text}
              </div>
            )}

            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200">
               <label className="block text-sm font-medium text-slate-700 mb-3">{tAdmin('plans.select_business_first') || 'Select Business'}</label>
               <select 
                 className="w-full md:w-1/2 border border-slate-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 bg-white"
                 value={selectedPlanBusinessId} 
                 onChange={e => setSelectedPlanBusinessId(e.target.value)}
                 disabled={creating}
               >
                 <option value="">{tAdmin('plans.select_placeholder') || '-- Choose Business --'}</option>
                 {businesses.map(b => (
                   <option key={b.id} value={b.id}>{b.name} ({tAdmin(`plans.${b.plan_name || 'free'}`) || b.plan_name})</option>
                 ))}
               </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
               {/* Free Plan */}
               <div className="bg-white border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
                  <h4 className="text-2xl font-bold text-slate-800 mb-2">{tAdmin('plans.free') || 'Free'}</h4>
                  <p className="text-4xl font-extrabold text-blue-600 mb-6">$0<span className="text-lg text-slate-400 font-normal">/mo</span></p>
                  <ul className="space-y-3 mb-8 text-slate-600 text-sm">
                     <li>✅ 10,000 Tokens</li>
                     <li>✅ Community Support</li>
                     <li>✅ Basic AI Sales</li>
                  </ul>
                  <button 
                    onClick={() => handleUpgrade('free')} disabled={creating || !selectedPlanBusinessId}
                    className="w-full bg-slate-100 text-slate-700 py-3 rounded-xl font-bold hover:bg-slate-200 disabled:opacity-50"
                  >
                     {tAdmin('plans.upgrade') || 'Downgrade to Free'}
                  </button>
               </div>

               {/* Pro Plan */}
               <div className="bg-gradient-to-b from-blue-50 to-white border border-blue-200 rounded-2xl p-6 shadow-[0_4px_20px_-4px_rgba(59,130,246,0.15)] relative transform md:-translate-y-2">
                  <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs font-bold px-3 py-1 rounded-bl-xl rounded-tr-xl">POPULAR</div>
                  <h4 className="text-2xl font-bold text-blue-800 mb-2">{tAdmin('plans.pro') || 'Pro'}</h4>
                  <p className="text-4xl font-extrabold text-blue-600 mb-6">$49<span className="text-lg text-slate-400 font-normal">/mo</span></p>
                  <ul className="space-y-3 mb-8 text-slate-700 text-sm font-medium">
                     <li>🔥 100,000 Tokens</li>
                     <li>🔥 Priority Support</li>
                     <li>🔥 Multi-channel Integration</li>
                  </ul>
                  <button 
                    onClick={() => handleUpgrade('pro')} disabled={creating || !selectedPlanBusinessId}
                    className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 shadow-md disabled:opacity-50 transition-colors"
                  >
                     {tAdmin('plans.upgrade') || 'Upgrade to Pro'}
                  </button>
               </div>

               {/* Enterprise Plan */}
               <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl text-white">
                  <h4 className="text-2xl font-bold text-white mb-2">{tAdmin('plans.enterprise') || 'Enterprise'}</h4>
                  <p className="text-4xl font-extrabold text-blue-400 mb-6">$199<span className="text-lg text-slate-400 font-normal">/mo</span></p>
                  <ul className="space-y-3 mb-8 text-slate-300 text-sm">
                     <li>🚀 Unlimited Tokens</li>
                     <li>🚀 Dedicated Account Manager</li>
                     <li>🚀 White-glove Onboarding</li>
                  </ul>
                  <button 
                    onClick={() => handleUpgrade('enterprise')} disabled={creating || !selectedPlanBusinessId}
                    className="w-full bg-slate-800 text-white py-3 rounded-xl font-bold hover:bg-slate-700 border border-slate-700 disabled:opacity-50 transition-colors"
                  >
                     {tAdmin('plans.upgrade') || 'Upgrade to Enterprise'}
                  </button>
               </div>
            </div>
          </div>
        )}

        {/* Health Tab */}
        {activeTab === 'health' && (
          <AdminHealthTab />
        )}

        {/* System Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="mb-4">
              <h3 className="text-xl font-semibold text-slate-800">System Configuration</h3>
              <p className="text-slate-500">Manage platform-wide settings such as AI providers, support phone, and plan quotas.</p>
            </div>
            
            <div className="bg-red-50 border border-red-200 rounded-xl p-5 mb-6">
               <h4 className="flex items-center gap-2 font-bold text-red-800 mb-2">
                 <span>⚠️</span> Emergency Actions
               </h4>
               <p className="text-sm text-red-700 mb-4">
                 Enable Maintenance Mode to block all merchant logins during updates or downtime. Admin access will remain active.
               </p>
               <button 
                 onClick={handleToggleMaintenance}
                 className={`px-4 py-2 font-bold rounded-lg transition-colors ${maintenanceEnabled ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-white text-red-600 border border-red-300 hover:bg-red-100'}`}
               >
                 {maintenanceEnabled ? 'Deactivate Maintenance Mode' : 'Activate Maintenance Mode'}
               </button>
                <div className="mt-6 border-t border-red-300 pt-4">
                  <h4 className="flex items-center gap-2 font-bold text-red-800 mb-2">📢 Global Announcement Banner</h4>
                  <input type="text" id="announcementInput" className="w-full border p-2 rounded mb-2 text-black bg-white" placeholder="e.g. System upgrade in 5 minutes!..." />
                  <button onClick={() => { const val = (document.getElementById('announcementInput') as HTMLInputElement).value; axios.post('/api/admin/system/announcement', {message: val}, {withCredentials: true}).then(()=>alert('Broadcasted!')).catch(()=>alert('Failed')); }} className="px-4 py-2 bg-red-600 text-white rounded font-bold hover:bg-red-700 block">
                    Broadcast Banner
                  </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="space-y-4">
                 <div>
                    <label className="block text-sm font-medium text-slate-700">{tSystem('platform_name') || 'Platform Name'}</label>
                    <input className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.platform_name || ''} onChange={(e: any) => setSystemSettings({...systemSettings, platform_name: e.target.value})} />
                 </div>
                 <div>
                    <label className="block text-sm font-medium text-slate-700">{tSystem('support_phone') || 'Support Phone'}</label>
                    <input className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.support_phone || ''} onChange={(e: any) => setSystemSettings({...systemSettings, support_phone: e.target.value})} placeholder="+1234567890" />
                 </div>
                 <div>
                    <label className="block text-sm font-medium text-slate-700">{tSystem('ai_provider') || 'AI Provider'}</label>
                    <select className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.ai_provider || ''} onChange={(e: any) => setSystemSettings({...systemSettings, ai_provider: e.target.value})}>
                      <option value="openai">OpenAI</option>
                      <option value="gemini">Google Gemini</option>
                    </select>
                 </div>
              </div>


              
              <div className="col-span-1 md:col-span-2 space-y-4 mt-4 border-t pt-6">
                 <h4 className="font-semibold text-slate-700 mb-2">Plan Token Limits (Infinity = 999999999)</h4>
                  <div className="grid grid-cols-3 gap-4">
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('free_tokens') || 'Free Plan Tokens'}</label>
                      <input type="number" className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.free_tokens || ''} onChange={(e: any) => setSystemSettings({...systemSettings, free_tokens: e.target.value})} />
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('pro_tokens') || 'Pro Plan Tokens'}</label>
                      <input type="number" className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.pro_tokens || ''} onChange={(e: any) => setSystemSettings({...systemSettings, pro_tokens: e.target.value})} />
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('enterprise_tokens') || 'Enterprise Tokens'}</label>
                      <input type="number" className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.enterprise_tokens || ''} onChange={(e: any) => setSystemSettings({...systemSettings, enterprise_tokens: e.target.value})} />
                   </div>
                 </div>
                 
                 <h4 className="font-semibold text-slate-700 mb-2 mt-6">Plan AI Models</h4>
                  <div className="grid grid-cols-3 gap-4">
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('free_model') || 'Free Model'}</label>
                      <select className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.free_model || ''} onChange={(e: any) => setSystemSettings({...systemSettings, free_model: e.target.value})}>
                        <option value="">Default</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      </select>
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('pro_model') || 'Pro Model'}</label>
                      <select className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.pro_model || ''} onChange={(e: any) => setSystemSettings({...systemSettings, pro_model: e.target.value})}>
                        <option value="">Default</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      </select>
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700">{tSystem('enterprise_model') || 'Enterprise Model'}</label>
                      <select className="w-full border border-slate-300 rounded-lg p-2.5 mt-1 focus:ring-2 focus:ring-blue-500 outline-none" value={systemSettings.enterprise_model || ''} onChange={(e: any) => setSystemSettings({...systemSettings, enterprise_model: e.target.value})}>
                        <option value="">Default</option>
                        <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                        <option value="gpt-4o-mini">GPT-4o Mini</option>
                        <option value="gpt-4o">GPT-4o</option>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                        <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                      </select>
                   </div>
                 </div>
              </div>

            </div>
            <div className="flex justify-end pt-4 border-t mt-6">
              <button 
                onClick={handleSaveSystemSettings}
                disabled={savingSettings}
                className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-bold hover:bg-blue-700 shadow-sm transition disabled:opacity-50"
              >
                {savingSettings ? 'Saving...' : (tSystem('save') || 'Save Settings')}
              </button>
                <div className="mt-6 border-t border-red-300 pt-4">
                  <h4 className="flex items-center gap-2 font-bold text-red-800 mb-2">📢 Global Announcement Banner</h4>
                  <input type="text" id="announcementInput" className="w-full border p-2 rounded mb-2 text-black bg-white" placeholder="e.g. System upgrade in 5 minutes!..." />
                  <button onClick={() => { const val = (document.getElementById('announcementInput') as HTMLInputElement).value; axios.post('/api/admin/system/announcement', {message: val}, {withCredentials: true}).then(()=>alert('Broadcasted!')).catch(()=>alert('Failed')); }} className="px-4 py-2 bg-red-600 text-white rounded font-bold hover:bg-red-700 block">
                    Broadcast Banner
                  </button>
                </div>
            </div>
          </div>
        )}

        {/* LOGS TAB */}
        {activeTab === 'logs' && (
          <div className="animate-fadeIn">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{tAdmin('logs.title') || 'Global Error Logs'}</h2>
            </div>
            <div className="bg-white border flex items-center p-2 rounded-xl mb-4 max-w-sm shadow-sm ring-1 ring-slate-100">
                <span className="text-xl mr-2 ml-2">🔍</span>
                <input 
                  type="text" 
                  value={logSearch} 
                  onChange={(e) => setLogSearch(e.target.value)} 
                  placeholder={tAdmin('logs.search_placeholder') || 'Search errors...'} 
                  className="w-full outline-none text-slate-700 bg-transparent text-sm p-1"
                />
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
               <div className="overflow-x-auto">
                 <table className="w-full min-w-[600px]">
                   <thead className="bg-slate-50 border-b border-slate-100 text-slate-500 text-sm">
                     <tr>
                       <th className="py-4 font-semibold px-4 text-start">{tAdmin('logs.timestamp') || 'Timestamp'}</th>
                       <th className="py-4 font-semibold px-2 text-start">{tAdmin('logs.business') || 'Business'}</th>
                       <th className="py-4 font-semibold px-2 text-start">{tAdmin('logs.error_type') || 'Error Type'}</th>
                       <th className="py-4 font-semibold px-4 text-start">{tAdmin('logs.message') || 'Message'}</th>
                     </tr>
                   </thead>
                   <tbody className="divide-y divide-slate-100">
                      {logs.filter(log => (log.business_name || '').toLowerCase().includes(logSearch.toLowerCase())).length === 0 ? (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-slate-500">{tAdmin('logs.no_logs') || 'No errors found.'}</td>
                        </tr>
                      ) : (
                        logs.filter(log => (log.business_name || '').toLowerCase().includes(logSearch.toLowerCase())).map((log, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                            <td className="py-4 px-4 whitespace-nowrap text-xs font-mono text-slate-500">
                               {new Date(log.timestamp).toLocaleString()}
                            </td>
                            <td className="py-4 px-2 font-medium text-slate-800">{log.business_name}</td>
                            <td className="py-4 px-2">
                               <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-bold rounded-md">
                                 {log.error_type}
                               </span>
                            </td>
                            <td className="py-4 px-4 text-sm text-slate-600 max-w-sm truncate" title={log.message}>
                               {log.message}
                            </td>
                          </tr>
                        ))
                      )}
                   </tbody>
                 </table>
               </div>
            </div>
          </div>
        )}

      </div>

      {/* Live Activity Feed Sidebar */}
      <div className="w-80 flex-shrink-0 space-y-4">
         <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 p-4 sticky top-6">
           <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-2">
             <h3 className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
               <span className="relative flex h-3 w-3">
                 <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                 <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
               </span>
               Live Activity
             </h3>
             <span className="text-xs text-slate-400 font-medium bg-slate-50 px-2 py-1 rounded">Auto-sync</span>
           </div>
           
           <div className="space-y-4 max-h-[800px] overflow-y-auto pr-1">
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
         </div>
      </div>

      {/* Settings Modal */}
      {selectedBusinessForSettings && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all" >
          <div className="bg-white rounded-2xl p-7 w-[400px] max-w-full shadow-2xl relative border border-slate-100">
             <button onClick={() => setSelectedBusinessForSettings(null)} className="absolute top-4 right-4 rtl:right-auto rtl:left-4 text-slate-400 hover:text-slate-600">✕</button>
             <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-xl font-bold">
                  {selectedBusinessForSettings.name.charAt(0).toUpperCase()}
                </div>
                <div>
                   <h3 className="text-lg font-bold text-slate-800">{selectedBusinessForSettings.name}</h3>
                   <p className="text-xs text-slate-500">{tAdmin('table.settings')}</p>
                </div>
             </div>

             <div className="space-y-4 text-sm bg-slate-50 p-4 rounded-xl border border-slate-100">
                <div className="flex justify-between border-b border-slate-200 pb-2">
                   <strong className="text-slate-600">{tAdmin('table.status')}:</strong> 
                   <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getStatusColor(selectedBusinessForSettings.status)}`}>
                     {selectedBusinessForSettings.status ? tAdmin(`table.status_${selectedBusinessForSettings.status}` as any) : tAdmin('table.status_unknown')}
                   </span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-2">
                   <strong className="text-slate-600">{tAdmin('table.business_type')}:</strong> 
                   <span className="text-slate-800 capitalize">
                      {selectedBusinessForSettings.business_type ? tAdmin(`create.type_${selectedBusinessForSettings.business_type}` as any) : '-'}
                   </span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-2">
                   <strong className="text-slate-600">{tAdmin('create.token_limit')}:</strong> 
                   <span className="text-slate-800">{selectedBusinessForSettings.token_limit ? selectedBusinessForSettings.token_limit.toLocaleString() : '∞'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-2">
                   <strong className="text-slate-600">{tAdmin('table.token_usage')}:</strong> 
                   <span className="text-slate-800">{selectedBusinessForSettings.token_usage ? selectedBusinessForSettings.token_usage.toLocaleString() : '0'}</span>
                </div>
                <div className="flex justify-between pb-1">
                   <strong className="text-slate-600">{tAdmin('create.monthly_quota')}:</strong> 
                   <span className="text-slate-800">{selectedBusinessForSettings.monthly_quota ? selectedBusinessForSettings.monthly_quota.toLocaleString() : 'N/A'}</span>
                </div>
             </div>
             
             <button onClick={() => setSelectedBusinessForSettings(null)} className="w-full bg-slate-100 text-slate-700 font-medium py-3 rounded-xl mt-6 hover:bg-slate-200 transition-colors shadow-sm cursor-pointer border border-slate-200">
               {tAdmin('table.close')}
             </button>
          </div>
        </div>
      )}
    </div>
  );
}
