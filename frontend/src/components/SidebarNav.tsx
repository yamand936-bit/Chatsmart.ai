'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { 
  LayoutDashboard, 
  MessageSquareDiff, 
  Users, 
  Store, 
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { useState, useEffect } from 'react';

export default function SidebarNav() {
  const tLayout = useTranslations('layout');
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // Auto-collapse on small screens
  useEffect(() => {
    const checkScreen = () => {
      if (window.innerWidth < 1024) {
        setCollapsed(true);
      }
    };
    checkScreen();
    window.addEventListener('resize', checkScreen);
    return () => window.removeEventListener('resize', checkScreen);
  }, []);

  const navItems = [
    {
      title: tLayout('overview'),
      href: '/app',
      icon: LayoutDashboard,
      activePattern: /^\/app\/?$/
    },
    {
      title: tLayout('inbox_ai'),
      href: '/app/chat',
      icon: MessageSquareDiff,
      activePattern: /^\/app\/chat/
    },
    {
      title: tLayout('crm_sales'),
      href: '/app/crm',
      icon: Users,
      activePattern: /^\/app\/crm/
    },
    {
      title: tLayout('ecommerce'),
      href: '/app/store',
      icon: Store,
      activePattern: /^\/app\/store/
    },
    {
      title: tLayout('settings_integrations'),
      href: '/app/settings',
      icon: Settings,
      activePattern: /^\/app\/settings/
    }
  ];

  return (
    <aside 
      className={cn(
        "relative flex flex-col bg-white dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 transition-all duration-300 ease-in-out shrink-0 z-40 print-hidden min-h-screen",
        collapsed ? "w-20" : "w-64"
      )}
    >
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800">
        {!collapsed && (
          <span className="font-bold text-xl text-slate-800 dark:text-slate-100 truncate">
            {tLayout('settings_integrations').includes('Ayarlar') ? 'ChatSmart' : 'ChatSmart AI'}
          </span>
        )}
        <button 
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "p-1.5 rounded-md text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition",
            collapsed && "mx-auto"
          )}
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-6 px-3 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.activePattern.test(pathname);
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.title : undefined}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-all group",
                isActive 
                  ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" 
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100",
                collapsed && "justify-center px-0"
              )}
            >
              <Icon size={22} className={cn("shrink-0", isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-500 group-hover:text-slate-700")} />
              {!collapsed && (
                 <span className="truncate">{item.title}</span>
              )}
            </Link>
          );
        })}
      </nav>
      
      {/* Bottom Area: User Info / Logout could go here in future */}
    </aside>
  );
}
