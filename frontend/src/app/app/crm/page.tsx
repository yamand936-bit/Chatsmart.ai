'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import CustomersList from '@/components/crm/CustomersList';
import KanbanBoard from '@/components/crm/KanbanBoard';
import { Users, KanbanSquare } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function CRMRootPage() {
  const t = useTranslations('layout');
  const [activeTab, setActiveTab] = useState<'list' | 'board'>('list');

  return (
    <div className="space-y-6 flex flex-col h-full">
       <div className="flex border-b border-slate-200 dark:border-slate-800">
           <button 
             onClick={() => setActiveTab('list')}
             className={cn("px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-all", activeTab === 'list' ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200')}
           >
             <Users size={18} /> {t('customers_list', { fallback: 'سجل العملاء' })}
           </button>
           <button 
             onClick={() => setActiveTab('board')}
             className={cn("px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-all", activeTab === 'board' ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200')}
           >
             <KanbanSquare size={18} /> {t('crm_pipeline', { fallback: 'مسار المبيعات' })}
           </button>
       </div>

       <div className="flex-1 min-h-0">
          {activeTab === 'list' && <CustomersList />}
          {activeTab === 'board' && <KanbanBoard />}
       </div>
    </div>
  );
}
