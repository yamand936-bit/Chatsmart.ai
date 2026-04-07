'use client';
import RoleGuard from '@/components/RoleGuard';
import Link from 'next/link';
import LogoutButton from '@/components/LogoutButton';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';
import MerchantStatsBar from '@/components/MerchantStatsBar';
import { useTranslations } from 'next-intl';
import { Toaster, toast } from 'react-hot-toast';
import { PlusCircle, MessageCircle, ShoppingCart } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import axios from 'axios';

function QuickActions({ tLayout }: { tLayout: any }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [ref]);

  return (
    <div className="relative" ref={ref}>
       <button onClick={() => setOpen(!open)} className="bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 transition shadow-sm">
          <PlusCircle size={20} />
       </button>
       {open && (
         <div className="absolute top-10 right-0 md:left-0 bg-white shadow-xl rounded-lg border w-48 py-2 z-50">
            <Link href="/app/products" onClick={() => setOpen(false)} className="flex items-center gap-2 px-4 py-2 hover:bg-slate-50 text-slate-700 text-sm font-medium">
               <PlusCircle size={16} /> {tLayout('quick_add_product', { fallback: 'إضافة منتج جديد' })}
            </Link>
            <Link href="/app/chat" onClick={() => setOpen(false)} className="flex items-center gap-2 px-4 py-2 hover:bg-slate-50 text-slate-700 text-sm font-medium">
               <MessageCircle size={16} /> {tLayout('quick_open_chat', { fallback: 'فتح محاكي الدردشة' })}
            </Link>
            <Link href="/app/orders" onClick={() => setOpen(false)} className="flex items-center gap-2 px-4 py-2 hover:bg-slate-50 text-slate-700 text-sm font-medium">
               <ShoppingCart size={16} /> {tLayout('quick_view_orders', { fallback: 'عرض آخر الطلبات' })}
            </Link>
         </div>
       )}
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const t = useTranslations('merchant');
  const tLayout = useTranslations('layout');
  const [businessType, setBusinessType] = useState('retail');

  useEffect(() => {
    // Fetch business type for conditional routing
    axios.get(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/merchant/settings`, { withCredentials: true })
      .then(res => {
        if (res.data?.data?.business_type) {
          setBusinessType(res.data.data.business_type);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
     // Mock New Message Notification (Simulate a live WhatsApp message after 3 seconds)
     const timer = setTimeout(() => {
        toast.custom((tCustom) => (
          <div className={`${tCustom.visible ? 'animate-enter' : 'animate-leave'} max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5 relative`} style={{ direction: 'rtl' }}>
            <div className="flex-1 w-0 p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 pt-0.5">
                  <span className="text-3xl">💬</span>
                </div>
                <div className="mr-3 flex-1">
                  <p className="text-sm font-bold text-slate-900">رسالة جديدة من WhatsApp!</p>
                  <p className="mt-1 text-sm text-slate-500">عميل جديد يستفسر عن المبيعات.</p>
                </div>
              </div>
            </div>
            <div className="flex border-r border-slate-200">
              <Link
                href="/app/chat"
                onClick={() => toast.dismiss(tCustom.id)}
                className="w-full border border-transparent rounded-none rounded-l-lg p-4 flex items-center justify-center text-sm font-bold text-green-600 hover:text-green-500 focus:outline-none"
              >
                عرض
              </Link>
            </div>
            <button onClick={() => toast.dismiss(tCustom.id)} className="absolute top-1 left-1 text-slate-400 hover:text-slate-600">×</button>
          </div>
        ), { duration: 6000, position: 'bottom-right' });
     }, 3000);

     return () => clearTimeout(timer);
  }, []);

  return (
    <RoleGuard requiredRole="merchant">
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Toaster position="top-center" reverseOrder={false} />
        <header className="bg-[var(--primary-color,#1e293b)] shadow px-6 py-4 flex justify-between items-center text-white relative z-30">
          <div className="flex items-center gap-3">
             <h1 className="font-bold text-xl text-white print-hidden">{t('title')}</h1>
             <div className="hidden md:flex items-center gap-3 print-hidden">
                 <QuickActions tLayout={tLayout} />
                 <div className="bg-green-50 border border-green-200 px-3 py-1.5 rounded-full flex items-center gap-2" title="الربط مع WhatsApp نشط ويعمل بشكل طبيعي">
                     <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                     <span className="text-xs font-bold text-green-700">{tLayout('whatsapp_connected')}</span>
                 </div>
             </div>
          </div>
          <nav className="flex items-center gap-4 md:gap-6 print-hidden">
            <Link href="/app" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('overview') || 'Overview'}</Link>
            <Link href="/app/products" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('products')}</Link>
            <Link href="/app/orders" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('orders')}</Link>
            {businessType === 'booking' && (
              <Link href="/app/calendar" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('calendar', { fallback: 'التقويم المشروط' })}</Link>
            )}
            <Link href="/app/chat" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('chat')}</Link>
            <Link href="/app/campaigns" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('campaigns', { fallback: 'الحملات الذكية' })}</Link>
            <Link href="/app/settings" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{tLayout('settings', { fallback: 'الإعدادات' })}</Link>
            <div className="border-l h-6 mx-1 md:mx-2 border-slate-300"></div>
            <div className="flex items-center gap-2">
               <ThemeToggle />
               <LanguageSwitcher />
               <LogoutButton />
            </div>
          </nav>
        </header>

        {/* Global Merchant Stats Header */}
        <div className="sticky top-0 z-20 print-hidden">
           <MerchantStatsBar />
        </div>

        <main className="flex-1 p-6 text-slate-800 relative z-10">
          {children}
        </main>
      </div>
    </RoleGuard>
  );
}
