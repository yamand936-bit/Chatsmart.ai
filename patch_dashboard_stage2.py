import re

with open("frontend/src/app/app/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

# Step 2.1: remove t
text = text.replace("const t = useTranslations('merchant');\n", "")

# Step 2.2: Add period state
text = text.replace(
    "const [advData, setAdvData] = useState<any>(null);",
    "const [advData, setAdvData] = useState<any>(null);\n  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');"
)

# Replace useEffect to depend on period and update URLs.
# Note: we need to replace the URL inside useEffect.
old_use_effect = """  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/analytics`, { withCredentials: true })
    .then((res) => {
       if (res.data.status === 'ok') {
          setData(res.data);
       }
    })
    .catch(err => {
       console.error(err);
       toast.error("فشل في جلب التحليلات. حاول مجدداً.");
    })
    .finally(() => {
       setLoading(false);
    });

    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/merchant/summary`, { withCredentials: true })
    .then(res => setAdvData(res.data.data ? res.data.data : res.data))
    .catch(console.error);
  }, []);"""

new_use_effect = """  useEffect(() => {
    setLoading(true);
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/analytics?period=${period}`, { withCredentials: true })
    .then((res) => {
       if (res.data.status === 'ok') {
          setData(res.data);
       }
    })
    .catch(err => {
       console.error(err);
       toast.error("فشل في جلب التحليلات. حاول مجدداً.");
    })
    .finally(() => {
       setLoading(false);
    });

    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/analytics/merchant/summary?period=${period}`, { withCredentials: true })
    .then(res => setAdvData(res.data.data ? res.data.data : res.data))
    .catch(console.error);
  }, [period]);"""

text = text.replace(old_use_effect, new_use_effect)

# Step 2.3 & 2.4 Compute ROI and add UI
roi_compute = """  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#6366f1'];

  const revenueEstimate = (data as any).total_revenue || 0;
  const roiValue = advData?.token_cost_total > 0
    ? ((revenueEstimate - advData.token_cost_total) / advData.token_cost_total) * 100
    : 0;

  return ("""

text = text.replace("  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#6366f1'];\n\n  return (", roi_compute)

period_ui = """       <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{tDash('performance_overview', { fallback: 'نظرة عامة على الأداء' })}</h2>
          <button onClick={() => window.print()} className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg shadow-sm font-medium transition text-sm print-hidden hidden md:block">
              {tDash('export_pdf', { fallback: 'تصدير التقرير (PDF)' })}
          </button>
       </div>

       <div className="flex gap-2 mb-4">
         {(['7d','30d','90d'] as const).map(p => (
           <button key={p} onClick={() => setPeriod(p)}
             className={`px-3 py-1 rounded text-sm font-medium transition ${period === p ? 'bg-blue-600 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200'}`}>
             {p === '7d' ? tDash('period_7d', {fallback: '7 days'}) : p === '30d' ? tDash('period_30d', {fallback: '30 days'}) : tDash('period_90d', {fallback: '90 days'})}
           </button>
         ))}
       </div>"""

text = text.replace("""       <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{tDash('performance_overview', { fallback: 'نظرة عامة على الأداء' })}</h2>
          <button onClick={() => window.print()} className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg shadow-sm font-medium transition text-sm print-hidden hidden md:block">
              {tDash('export_pdf', { fallback: 'تصدير التقرير (PDF)' })}
          </button>
       </div>""", period_ui)

roi_card = """               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between col-span-2 md:col-span-1">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('tokenCost', {fallback: 'Token Cost (30d)'})}</div>
                   <div className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">${advData.token_cost_total}</div>
               </div>
               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between">
                 <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('roi', {fallback: 'AI ROI'})}</div>
                 <div className={`text-2xl font-bold mt-2 ${roiValue >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                   {roiValue >= 0 ? '+' : ''}{roiValue.toFixed(0)}%
                 </div>
               </div>"""

text = text.replace("""               <div className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col justify-between col-span-2 md:col-span-1">
                   <div className="text-slate-500 dark:text-slate-400 text-sm font-medium">{tDash('tokenCost', {fallback: 'Token Cost (30d)'})}</div>
                   <div className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">${advData.token_cost_total}</div>
               </div>""", roi_card)


with open("frontend/src/app/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
