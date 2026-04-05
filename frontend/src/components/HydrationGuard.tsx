'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/store/useAuthStore';

export default function HydrationGuard({ children }: { children: React.ReactNode }) {
  const { isHydrated, fetchMe } = useAuthStore();

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  if (!isHydrated) {
    return <div className="flex items-center justify-center min-h-screen text-slate-800 font-bold">Loading System...</div>;
  }

  return <>{children}</>;
}
