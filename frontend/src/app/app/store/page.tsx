'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import ProductsList from '@/components/store/ProductsList';
import OrdersList from '@/components/store/OrdersList';
import { Package, ShoppingCart } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function StoreRootPage() {
  const tLayout = useTranslations('layout');
  const t = useTranslations('merchant');
  const [activeTab, setActiveTab] = useState<'products' | 'orders'>('products');

  return (
    <div className="space-y-6 flex flex-col h-full">
       <div className="flex border-b border-slate-200 dark:border-slate-800">
           <button 
             onClick={() => setActiveTab('products')}
             className={cn("px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-all", activeTab === 'products' ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200')}
           >
             <Package size={18} /> {t('products')}
           </button>
           <button 
             onClick={() => setActiveTab('orders')}
             className={cn("px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-all", activeTab === 'orders' ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400' : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200')}
           >
             <ShoppingCart size={18} /> {t('orders')}
           </button>
       </div>

       <div className="flex-1 min-h-0">
          {activeTab === 'products' && <ProductsList />}
          {activeTab === 'orders' && <OrdersList />}
       </div>
    </div>
  );
}
