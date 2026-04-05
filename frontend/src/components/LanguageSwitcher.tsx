'use client';
import { useState, useEffect } from 'react';

export default function LanguageSwitcher() {
  const [currentLocale, setCurrentLocale] = useState('en');

  useEffect(() => {
    const match = document.cookie.match(new RegExp('(^| )NEXT_LOCALE=([^;]+)'));
    if (match) setCurrentLocale(match[2]);
  }, []);

  const switchLanguage = (locale: string) => {
    document.cookie = `NEXT_LOCALE=${locale}; path=/; max-age=31536000; SameSite=Lax`;
    setCurrentLocale(locale);
    window.location.reload();
  };

  return (
    <div className="flex gap-1 items-center text-xs font-medium border rounded-md p-1 bg-white shadow-sm" style={{ direction: 'ltr' }}>
      <button 
        onClick={() => switchLanguage('en')} 
        className={`px-2 py-1 rounded transition-colors ${currentLocale === 'en' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
      >
        EN
      </button>
      <button 
        onClick={() => switchLanguage('ar')} 
        className={`px-2 py-1 rounded transition-colors ${currentLocale === 'ar' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
      >
        AR
      </button>
      <button 
        onClick={() => switchLanguage('tr')} 
        className={`px-2 py-1 rounded transition-colors ${currentLocale === 'tr' ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
      >
        TR
      </button>
    </div>
  );
}
