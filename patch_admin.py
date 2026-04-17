with open("frontend/src/app/admin/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'className="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex items-center justify-between hover:shadow-md transition"',
    'className="bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 flex items-center justify-between hover:shadow-md transition"'
)

text = text.replace(
    'className="text-slate-500 text-sm mb-1 font-medium"',
    'className="text-slate-500 dark:text-slate-400 text-sm mb-1 font-medium"'
)

text = text.replace(
    'className="text-2xl font-bold text-slate-800"',
    'className="text-2xl font-bold text-slate-800 dark:text-slate-100"'
)

text = text.replace(
    'className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 md:p-8 min-h-[500px] relative"',
    'className="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 p-6 md:p-8 min-h-[500px] relative"'
)

with open("frontend/src/app/admin/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
