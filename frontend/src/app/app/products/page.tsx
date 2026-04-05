'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [formData, setFormData] = useState({ name: '', description: '', price: 0, image_url: '' });
  const t = useTranslations('products');
  const tCommon = useTranslations('common');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
        const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true });
        setProducts(res.data.data || []);
    } catch (err) {
        console.error(err);
        toast.error('فشل في جلب المنتجات. يرجى تحديث الصفحة.');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const loadingToast = toast.loading('جاري إضافة المنتج...');
    try {
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, formData, { withCredentials: true });
      await fetchProducts();
      setFormData({ name: '', description: '', price: 0, image_url: '' });
      toast.success('تم إضافة المنتج بنجاح', { id: loadingToast });
    } catch(err) {
      console.error(err);
      toast.error('حدث خطأ أثناء إضافة المنتج. تحقق من البيانات وحاول مجدداً.', { id: loadingToast });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('هل أنت متأكد من حذف هذا المنتج؟')) return;
    
    const loadingToast = toast.loading('جاري الحذف...');
    try {
      await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/${id}`, { withCredentials: true });
      setProducts(products.filter(p => p.id !== id));
      toast.success('تم حذف المنتج بنجاح', { id: loadingToast });
    } catch(err) {
      console.error(err);
      toast.error('حدث خطأ أثناء حذف المنتج.', { id: loadingToast });
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">{t('title')}</h2>
      
      <div className="bg-white p-6 rounded shadow mb-8">
        <h3 className="font-semibold text-lg mb-4 text-slate-800">{t('addNew')}</h3>
        <form onSubmit={handleSubmit} className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('name')}</label>
            <input 
              type="text" required 
              value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}
              className="w-full border p-2 rounded text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('description')}</label>
            <input 
              type="text" 
              value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full border p-2 rounded text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="w-32">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('price')} ($)</label>
            <input 
              type="number" step="0.01" required 
              value={formData.price} onChange={e => setFormData({...formData, price: parseFloat(e.target.value)})}
              className="w-full border p-2 rounded text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">رابط صورة المنتج (اختياري)</label>
            <input 
              type="url" 
              placeholder="https://example.com/image.jpg"
              value={formData.image_url} onChange={e => setFormData({...formData, image_url: e.target.value})}
              className="w-full border p-2 rounded text-slate-800 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <button type="submit" className="bg-blue-600 text-white px-6 py-2 border border-transparent rounded hover:bg-blue-700 font-medium transition h-[42px]">
            {tCommon('add')}
          </button>
        </form>
      </div>

      {products.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-12 text-center border-2 border-dashed border-blue-100 flex flex-col items-center justify-center">
            <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4">
               <svg fill="currentColor" viewBox="0 0 20 20" className="w-8 h-8"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">أضف منتجك الأول لتفعيل مبيعات الذكاء الاصطناعي</h3>
            <p className="text-slate-500 mb-6 max-w-md">لا توجد منتجات لعرضها. أضف منتجاتك هنا ليتمكن المساعد الذكي من اقتراحها وبيعها لعملائك ومشاركة صورها معهم تلقائياً.</p>
        </div>
      ) : (
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="w-full text-left border-collapse" style={{ textAlign: 'start' }}>
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="p-4 font-semibold text-slate-700 w-16">صورة</th>
              <th className="p-4 font-semibold text-slate-700">{t('name')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('description')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('price')}</th>
              <th className="p-4 font-semibold text-slate-700 w-24">{tCommon('action')}</th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.id} className="border-b hover:bg-slate-50">
                <td className="p-4">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="w-10 h-10 rounded object-cover border" />
                  ) : (
                    <div className="w-10 h-10 rounded bg-slate-200 border flex items-center justify-center text-slate-400 text-xs">بدون صورة</div>
                  )}
                </td>
                <td className="p-4 text-slate-800 font-medium">{p.name}</td>
                <td className="p-4 text-slate-600 text-sm max-w-[300px] truncate">{p.description}</td>
                <td className="p-4 font-medium text-blue-600">${p.price}</td>
                <td className="p-4">
                  <button onClick={() => handleDelete(p.id)} className="text-red-500 hover:text-white hover:bg-red-500 px-3 py-1 rounded text-sm font-medium transition">{tCommon('delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}
    </div>
  );
}
