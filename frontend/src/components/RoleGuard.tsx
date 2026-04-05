'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';

export default function RoleGuard({ children, requiredRole }: { children: React.ReactNode, requiredRole: 'admin' | 'merchant' }) {
  const { user, isHydrated } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isHydrated) {
      if (!user) {
        router.replace('/login');
      } else if (user.role !== requiredRole) {
        if (user.role === 'admin') router.replace('/admin');
        else if (user.role === 'merchant') router.replace('/app');
      }
    }
  }, [user, isHydrated, requiredRole, router, pathname]);

  if (!isHydrated || !user || user.role !== requiredRole) {
    return null; // Prevents render flash
  }

  return <>{children}</>;
}
