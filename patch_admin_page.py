with open("frontend/src/app/admin/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

# 1. State for system health
state_declaration = """  const [logs, setLogs] = useState<any[]>([]);"""
new_state = """  const [logs, setLogs] = useState<any[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);"""
text = text.replace(state_declaration, new_state)

# 2. Fetch system health  
fetch_data = """    try {
      const metRes = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/metrics`, { withCredentials: true });
      if (metRes.data) {
        setMetrics(metRes.data);
      }
    } catch (error) {
      console.error("Failed to load metrics:", error);
    }"""
new_fetch_data = """    try {
      const metRes = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/metrics`, { withCredentials: true });
      if (metRes.data) {
        setMetrics(metRes.data);
      }
    } catch (error) {
      console.error("Failed to load metrics:", error);
    }
    
    try {
       const healthRes = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/admin/health`, { withCredentials: true });
       if (healthRes.data?.data) {
          setSystemHealth(healthRes.data.data);
       }
    } catch(e) {
       console.error("Failed to load health", e);
    }"""
text = text.replace(fetch_data, new_fetch_data)

# 3. Add MRR and Health UI
ui_to_replace = """      {/* Stats Section */}
      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard title={tAdmin('stats.total_businesses')} value={metrics.total_businesses || 0} icon="🏢" />
          <StatCard title={tAdmin('stats.active_businesses')} value={metrics.active_businesses || 0} icon="🟢" />
          <StatCard title={tAdmin('stats.total_orders')} value={metrics.total_orders || 0} icon="📦" />
          <StatCard title={tAdmin('stats.total_tokens_used')} value={metrics.total_tokens_used || 0} icon="🪙" />
          <StatCard title={tAdmin('stats.ai_requests_today')} value={metrics.ai_requests_today || 0} icon="🤖" />
        </div>
      )}"""

new_ui = """      {/* Stats Section */}
      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatCard title={tAdmin('stats.total_businesses')} value={metrics.total_businesses || 0} icon="🏢" />
          <StatCard title={tAdmin('stats.active_businesses')} value={metrics.active_businesses || 0} icon="🟢" />
          <StatCard title={tAdmin('stats.total_orders')} value={metrics.total_orders || 0} icon="📦" />
          <StatCard title={tAdmin('stats.total_tokens_used')} value={metrics.total_tokens_used || 0} icon="🪙" />
          <StatCard title={'MRR'} value={`$${metrics.mrr || 0}`} icon="💰" />
          <StatCard title={'Churn Rate'} value={`${metrics.churn_rate || '0.0'}%`} icon="📉" />
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
      )}"""
text = text.replace(ui_to_replace, new_ui)

with open("frontend/src/app/admin/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
