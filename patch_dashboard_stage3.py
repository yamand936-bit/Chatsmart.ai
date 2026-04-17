with open("frontend/src/app/app/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "import toast from 'react-hot-toast';",
    "import toast from 'react-hot-toast';\nimport { MetricCardSkeleton, Skeleton } from '@/components/Skeleton';"
)

old_loading = '  if (loading) {\n     return <div className="p-12 text-center text-slate-500 dark:text-slate-400 font-medium">جاري تحميل التحليلات المتقدمة...</div>;\n  }'

new_loading = """  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({length: 5}).map((_,i) => <MetricCardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-xl" />
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </div>
    );
  }"""

text = text.replace(old_loading, new_loading)

with open("frontend/src/app/app/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
