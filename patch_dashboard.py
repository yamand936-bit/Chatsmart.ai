with open("frontend/src/app/app/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("text-2xl font-bold text-slate-800", "text-2xl font-bold text-slate-800 dark:text-slate-100")
text = text.replace("bg-white p-4 rounded-xl shadow-sm border border-slate-100", "bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700")
text = text.replace("text-slate-500 text-sm font-medium", "text-slate-500 dark:text-slate-400 text-sm font-medium")
text = text.replace("bg-slate-100 rounded", "bg-slate-100 dark:bg-slate-700 rounded")
text = text.replace("bg-white p-6 rounded-xl shadow border border-slate-100", "bg-white dark:bg-slate-800 p-6 rounded-xl shadow border border-slate-100 dark:border-slate-700")
text = text.replace("font-semibold text-lg text-slate-800", "font-semibold text-lg text-slate-800 dark:text-slate-100")
text = text.replace("text-slate-700 font-medium", "text-slate-700 dark:text-slate-300 font-medium")
text = text.replace("text-slate-500 font-medium", "text-slate-500 dark:text-slate-400 font-medium")

with open("frontend/src/app/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
