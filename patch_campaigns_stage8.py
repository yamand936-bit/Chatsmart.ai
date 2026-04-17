with open("frontend/src/app/app/campaigns/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

import_react = "import React, { useState } from 'react';"
new_import_react = "import React, { useState, useEffect } from 'react';"
text = text.replace(import_react, new_import_react)

state_vars = """  const [tag, setTag] = useState('');
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);"""
new_state_vars = """  const [tag, setTag] = useState('');
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
  }, []);"""
text = text.replace(state_vars, new_state_vars)

api_call = """      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/campaigns/send`, {
        tag: tag,
        instructions: instructions
      }, { withCredentials: true });"""
new_api_call = """      const response = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/campaigns/send`, {
        tag: tag,
        instructions: instructions,
        template_id: selectedTemplate || null,
        audience_filter: audienceFilter
      }, { withCredentials: true });"""
text = text.replace(api_call, new_api_call)

template_dropdown = """            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
                <TagIcon className="w-4 h-4 text-slate-400" />
                {t('target_tag_label')}
              </label>"""
new_template_dropdown = """            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
              </label>"""
text = text.replace(template_dropdown, new_template_dropdown)

with open("frontend/src/app/app/campaigns/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
