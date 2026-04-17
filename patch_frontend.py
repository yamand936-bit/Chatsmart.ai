import os, re

def patch_admin_page():
    path = r'frontend/src/app/admin/page.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()

    # 1. Lifeline Monitor (Webhook Health)
    if 'Webhook Health' not in code:
        code = code.replace(
            '''<StatCard title={'Requests/Day'} value={metrics.ai_requests_today || 0} icon="⚡" \n               trend={metrics.sparklines?.requests} />''',
            '''<StatCard title={'Requests/Day'} value={metrics.ai_requests_today || 0} icon="⚡" \n               trend={metrics.sparklines?.requests} />\n            <StatCard title={'Webhook Health'} value={`${metrics.webhook_delivery_rate !== undefined ? metrics.webhook_delivery_rate : 100}%`} icon="❤️‍🩹" />'''
        )

    # 2. Announcement Banner inputs in Settings
    if 'announcementInput' not in code:
        code = code.replace(
            '''</button>\n            </div>''',
            '''</button>\n                <div className="mt-6 border-t border-red-300 pt-4">\n                  <h4 className="flex items-center gap-2 font-bold text-red-800 mb-2">📢 Global Announcement Banner</h4>\n                  <input type="text" id="announcementInput" className="w-full border p-2 rounded mb-2 text-black bg-white" placeholder="e.g. System upgrade in 5 minutes!..." />\n                  <button onClick={() => { const val = (document.getElementById('announcementInput') as HTMLInputElement).value; axios.post('/api/admin/system/announcement', {message: val}, {withCredentials: true}).then(()=>alert('Broadcasted!')).catch(()=>alert('Failed')); }} className="px-4 py-2 bg-red-600 text-white rounded font-bold hover:bg-red-700 block">\n                    Broadcast Banner\n                  </button>\n                </div>\n            </div>'''
        )

    # 3. Last Active Column - Header
    # Assuming there's a th with "Email" or similar
    if '>Last Active</th>' not in code:
        code = re.sub(
            r'(<th[^>]*>.*?Owner Email|صاحب المتجر|Email.*?</th\s*>)',
            r'\1\n                      <th className="py-4 px-2 font-semibold">Last Active</th>',
            code, count=1, flags=re.IGNORECASE | re.DOTALL
        )
    # 3. Last Active Column - Row
    if 'b.last_active' not in code:
        code = code.replace(
            '''<td className="py-4 px-2 text-slate-600">{b.owner_email}</td>''',
            '''<td className="py-4 px-2 text-slate-600">{b.owner_email}</td>\n                      <td className="py-4 px-2 text-slate-500 text-xs">{b.last_active ? new Date(b.last_active).toLocaleString() : 'Never'}</td>'''
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

def patch_layout():
    path = r'frontend/src/app/app/layout.tsx'
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()

    # Add announcement state
    if 'const [announcement' not in code:
        code = code.replace(
            'const [businessType, setBusinessType] = useState(\'retail\');',
            'const [businessType, setBusinessType] = useState(\'retail\');\n  const [announcement, setAnnouncement] = useState(\'\');'
        )

    # Add axios fetch for announcement
    if '/api/system/announcement' not in code:
        code = code.replace(
            '.catch(() => {});',
            '.catch(() => {});\n\n    axios.get(`/api/system/announcement`)\n      .then(res => {\n        if (res.data?.message) setAnnouncement(res.data.message);\n      })\n      .catch(() => {});'
        )

    # Add the JSX banner
    if '{announcement &&' not in code:
        code = code.replace(
            '<Toaster position="top-center" reverseOrder={false} />',
            '<Toaster position="top-center" reverseOrder={false} />\n        {announcement && (\n           <div className="bg-red-600 text-white text-center py-2 px-4 shadow font-bold text-sm z-50 sticky top-0 uppercase tracking-wide flex justify-center items-center gap-2">\n              <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>\n              {announcement}\n           </div>\n        )}'
        )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(code)

patch_admin_page()
patch_layout()
print("Frontend patched")
