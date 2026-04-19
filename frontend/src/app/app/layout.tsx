'use client';
import RoleGuard from '@/components/RoleGuard';
import Link from 'next/link';
import LogoutButton from '@/components/LogoutButton';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { ThemeToggle } from '@/components/ThemeToggle';
import { NotificationBell } from '@/components/NotificationBell';
import MerchantStatsBar from '@/components/MerchantStatsBar';
import { useTranslations } from 'next-intl';
import { Toaster, toast } from 'react-hot-toast';
import { PlusCircle, MessageCircle, ShoppingCart } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import SidebarNav from '@/components/SidebarNav';

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
  const [announcement, setAnnouncement] = useState('');
  const router = require('next/navigation').useRouter();
  const pathname = require('next/navigation').usePathname();

  useEffect(() => {
    // Fetch business type for conditional routing
    axios.get(`/api/merchant/settings`, { withCredentials: true })
      .then(res => {
        if (res.data?.data) {
          if (res.data.data.business_type) setBusinessType(res.data.data.business_type);
          if (res.data.data.setup_complete === false && !pathname.includes('/app/onboarding')) {
              router.push('/app/onboarding');
          }
        }
      })
      .catch(() => {});

    axios.get(`/api/system/system/announcement`)
      .then(res => {
        if (res.data?.message) setAnnouncement(res.data.message);
      })
      .catch(() => {});
  }, [pathname, router]);



  return (
    <RoleGuard requiredRole="merchant">
      <div className="h-screen overflow-hidden bg-slate-50 dark:bg-slate-900 flex absolute inset-0 w-full text-slate-900 dark:text-slate-100">
        <Toaster position="top-center" reverseOrder={false} />
        
        {/* Left Sidebar */}
        <SidebarNav />

        {/* Main Content Scrollable Area */}
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {announcement && (
             <div className="bg-red-600 text-white text-center py-2 px-4 shadow font-bold text-sm z-50 sticky top-0 uppercase tracking-wide flex justify-center items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
                {announcement}
             </div>
          )}

          {/* Top Header App Bar */}
          <header className="bg-white/80 backdrop-blur-md dark:bg-slate-900/80 shadow-sm border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex justify-between items-center relative z-30 sticky top-0 print-hidden">
            <div className="flex items-center gap-3">
               <div className="hidden md:flex items-center gap-3">
                   <QuickActions tLayout={tLayout} />
                   <div className="bg-green-50 border border-green-200 px-3 py-1.5 rounded-full flex items-center gap-2" title="الربط مع WhatsApp نشط ويعمل بشكل طبيعي">
                       <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                       <span className="text-xs font-bold text-green-700">{tLayout('whatsapp_connected')}</span>
                   </div>
               </div>
            </div>
            
            <div className="flex items-center gap-2 print-hidden">
               <NotificationBell />
               <ThemeToggle />
               <LanguageSwitcher />
               <LogoutButton />
            </div>
          </header>

          {/* Global Merchant Stats Header */}
          <div className="z-20 print-hidden">
             <MerchantStatsBar />
          </div>

          {/* Page Content Constrained Wrapper */}
          <main className="flex-1 p-6 relative z-10 w-full max-w-7xl mx-auto">
            {children}
          </main>
        </div>
      </div>
    </RoleGuard>
  );
}
