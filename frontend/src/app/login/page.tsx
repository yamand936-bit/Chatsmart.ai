'use client';

import { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const login = useAuthStore(state => state.login);
  const fetchMe = useAuthStore(state => state.fetchMe);
  const router = useRouter();
  const t = useTranslations('login');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const params = new URLSearchParams();
      params.append('username', email);
      params.append('password', password);

      const res = await axios.post(`/api/auth/login`, params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        withCredentials: true
      });
      if (res.data?.access_token) {
        sessionStorage.setItem('impersonate_token', res.data.access_token);
      }
      login();
      await fetchMe();
      
      const user = useAuthStore.getState().user;
      if (user?.role === 'admin') router.push('/admin');
      else router.push('/app');
      
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('failed'));
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-50 relative">
      <div className="absolute top-4 end-4">
        <LanguageSwitcher />
      </div>
      <form onSubmit={handleLogin} className="bg-white p-8 shadow-xl rounded-2xl w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-6 text-center text-slate-800">{t('title')}</h1>
        {error && <div className="bg-red-100 text-red-600 p-3 rounded mb-4 text-sm">{error}</div>}
        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-1">{t('email')}</label>
          <input 
            type="email" 
            className="w-full text-slate-800 bg-white border border-slate-300 p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-1">{t('password')}</label>
          <input 
            type="password" 
            className="w-full text-slate-800 bg-white border border-slate-300 p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="w-full bg-[var(--primary-color,#2563eb)] text-white p-2 flex items-center justify-center rounded-lg hover:opacity-90 font-medium transition shadow-sm">
          {t('signIn')}
        </button>
      </form>
    </div>
  );
}
