'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { Users, Phone, Mail, Globe, Search, PlusCircle, MoreHorizontal } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function CustomersPage() {
  const t = useTranslations('merchant'); 
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchCustomers();
  }, []);

  const fetchCustomers = () => {
    setLoading(true);
    axios.get('/api/merchant/customers')
      .then(res => {
         if (res.data.status === 'success') {
             setCustomers(res.data.data);
         }
      })
      .catch(err => {
         toast.error("Failed to fetch customers");
      })
      .finally(() => setLoading(false));
  };

  const filtered = customers.filter(c => 
      (c.name || '').toLowerCase().includes(search.toLowerCase()) || 
      (c.phone || '').includes(search) || 
      (c.email || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
       <div className="flex items-center justify-between">
           <div>
             <h1 className="text-2xl font-bold flex items-center gap-2"><Users className="text-blue-600" /> العملاء (Customers CRM)</h1>
             <p className="text-slate-500 mt-1">سجل العملاء التلقائي والبيانات المجمعة من رحلة المحادثة.</p>
           </div>
           
           <div className="relative">
              <input 
                 type="text" 
                 placeholder="بحث (اسم، هاتف...)" 
                 value={search}
                 onChange={(e) => setSearch(e.target.value)}
                 className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg w-64 focus:ring-2 focus:outline-none focus:ring-blue-500" 
              />
              <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
           </div>
       </div>

       {loading ? (
           <div className="py-20 flex justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>
       ) : (
           <div className="bg-white rounded-xl shadow border border-slate-200 overflow-hidden">
               <div className="overflow-x-auto">
                   <table className="w-full text-left border-collapse">
                      <thead>
                         <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-sm">
                             <th className="p-4 font-medium">الاسم</th>
                             <th className="p-4 font-medium">الهاتف</th>
                             <th className="p-4 font-medium">الإيميل</th>
                             <th className="p-4 font-medium">المنصة</th>
                             <th className="p-4 font-medium">بيانات إضافية (Custom)</th>
                             <th className="p-4 font-medium">تاريخ الإضافة</th>
                         </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-sm">
                          {filtered.length === 0 ? (
                              <tr><td colSpan={6} className="p-8 text-center text-slate-400">لا يوجد عملاء بعد.</td></tr>
                          ) : filtered.map(c => (
                              <tr key={c.id} className="hover:bg-slate-50/50 transition">
                                  <td className="p-4 font-medium text-slate-800">
                                      {c.name || <span className="text-slate-400 italic">Unknown</span>}
                                  </td>
                                  <td className="p-4 text-slate-600">
                                      {c.phone ? <div className="flex items-center gap-1"><Phone size={14} className="text-slate-400"/> <span dir="ltr">{c.phone}</span></div> : '-'}
                                  </td>
                                  <td className="p-4 text-slate-600">
                                      {c.email ? <div className="flex items-center gap-1"><Mail size={14} className="text-slate-400"/> {c.email}</div> : '-'}
                                  </td>
                                  <td className="p-4">
                                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                                        c.platform === 'whatsapp' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                                      }`}>
                                         {c.platform}
                                      </span>
                                  </td>
                                  <td className="p-4">
                                      {Object.keys(c.custom_fields || {}).length > 0 ? (
                                         <div className="flex gap-1 flex-wrap max-w-xs">
                                             {Object.entries(c.custom_fields).slice(0, 2).map(([k,v]) => (
                                                 <span key={k} className="bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-md max-w-full truncate" title={String(v)}>
                                                    <b>{k}:</b> {String(v)}
                                                 </span>
                                             ))}
                                             {Object.keys(c.custom_fields).length > 2 && (
                                                <span className="bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-md cursor-pointer hover:bg-slate-200" title={JSON.stringify(c.custom_fields)}>+{Object.keys(c.custom_fields).length - 2}</span>
                                             )}
                                         </div>
                                      ) : <span className="text-slate-300">-</span>}
                                  </td>
                                  <td className="p-4 text-slate-500 whitespace-nowrap">
                                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : '-'}
                                  </td>
                              </tr>
                          ))}
                      </tbody>
                   </table>
               </div>
           </div>
       )}
    </div>
  );
}
