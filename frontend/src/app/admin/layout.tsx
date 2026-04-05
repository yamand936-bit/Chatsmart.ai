'use client';
import RoleGuard from '@/components/RoleGuard';
import Link from 'next/link';
import LogoutButton from '@/components/LogoutButton';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import { useTranslations } from 'next-intl';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const t = useTranslations('admin');
  return (
    <RoleGuard requiredRole="admin">
      <div className="min-h-screen bg-slate-100 flex flex-col">
        <header className="bg-white shadow px-6 py-4 flex justify-between items-center text-slate-800">
          <h1 className="font-bold text-xl text-blue-600">{t('title')}</h1>
          <nav className="flex items-center gap-6">
            <LanguageSwitcher />
            <LogoutButton />
          </nav>
        </header>
        <main className="flex-1 p-6 text-slate-800">
          {children}
        </main>
      </div>
    </RoleGuard>
  );
}
