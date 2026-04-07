'use client';
import { useAuthStore } from '@/store/useAuthStore';
import { useRouter } from 'next/navigation';

import { useTranslations } from 'next-intl';

export default function LogoutButton() {
  const logout = useAuthStore(state => state.logout);
  const router = useRouter();
  const t = useTranslations('layout');

  const handleLogout = async () => {
    await logout();
    router.replace('/login');
  };

  return (
    <button 
      onClick={handleLogout}
      className="text-slate-500 hover:text-red-500 font-medium transition"
    >
      {t('signOut') || 'Sign Out'}
    </button>
  );
}
