'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslations } from 'next-intl';
import toast from 'react-hot-toast';

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [formData, setFormData] = useState({ name: '', description: '', price: 0, image_url: '' });
  const [editingProduct, setEditingProduct] = useState<any>(null);
  const [editFormData, setEditFormData] = useState({ name: '', description: '', price: 0, image_url: '', is_active: true });
  
  // Sheet Sync State
  const [sheetUrl, setSheetUrl] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [uploading, setUploading] = useState(false);

  const t = useTranslations('products');
  const tCommon = useTranslations('common');

  useEffect(() => {
    fetchProducts();
    
    // Load Settings
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/settings`, { withCredentials: true })
        .then(res => {
            if (res.data.data && res.data.data.sheet_url) {
                setSheetUrl(res.data.data.sheet_url);
            }
            if (res.data.data && res.data.data.primary_color) {
                document.documentElement.style.setProperty('--primary-color', res.data.data.primary_color);
            }
        })
        .catch(console.error);
  }, []);

  const fetchProducts = async () => {
    try {
        const res = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true });
        setProducts(res.data.data || []);
    } catch (err) {
        console.error(err);
        toast.error('Failed to load products');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const loadingToast = toast.loading('...');
    try {
      await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, formData, { withCredentials: true });
      await fetchProducts();
      setFormData({ name: '', description: '', price: 0, image_url: '' });
      toast.success(tCommon('save'), { id: loadingToast });
    } catch(err) {
      console.error(err);
      toast.error('Error', { id: loadingToast });
    }
  };

  const handleSync = async () => {
      if (!sheetUrl) return toast.error("أدخل رابط الملف أولاً");
      setSyncing(true);
      const loadingToast = toast.loading('جاري جلب البيانات من الرابط...');
      
      try {
          // Save URL to settings first
          await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/settings`, { sheet_url: sheetUrl }, { withCredentials: true });
          
          // Trigger Sync
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/sync`, { sheet_url: sheetUrl }, { withCredentials: true });
          await fetchProducts();
          toast.success('تم التحديث والمزامنة بنجاح!', { id: loadingToast });
      } catch (err) {
          console.error(err);
          toast.error('حدث خطأ أثناء المزامنة عبر الرابط.', { id: loadingToast });
      } finally {
          setSyncing(false);
      }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setUploading(true);
      const loadingToast = toast.loading('جاري رفع وقراءة ملف الـ Excel...');
      
      const formData = new FormData();
      formData.append('file', file);

      try {
          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/upload`, formData, { 
              withCredentials: true,
              headers: { 'Content-Type': 'multipart/form-data' }
          });
          await fetchProducts();
          toast.success('تم رفع الملف وتحديث المنتجات بنجاح!', { id: loadingToast });
      } catch (err) {
          console.error(err);
          toast.error('حدث خطأ أثناء رفع الملف، تأكد أنه بصيغة XLSX أو CSV صالحة.', { id: loadingToast });
      } finally {
          setUploading(false);
          // clear input
          e.target.value = '';
      }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return;
    
    const loadingToast = toast.loading('...');
    try {
      await axios.delete(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/${id}`, { withCredentials: true });
      setProducts(products.filter(p => p.id !== id));
      toast.success(tCommon('save'), { id: loadingToast });
    } catch(err) {
      console.error(err);
      toast.error('Error', { id: loadingToast });
    }
  };

  const openEditModal = (product: any) => {
    setEditingProduct(product);
    setEditFormData({
        name: product.name,
        description: product.description || '',
        price: product.price,
        image_url: product.image_url || '',
        is_active: product.is_active
    });
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProduct) return;
    const loadingToast = toast.loading('...');
    try {
      const res = await axios.put(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/${editingProduct.id}`, editFormData, { withCredentials: true });
      setProducts(products.map(p => p.id === editingProduct.id ? res.data : p));
      setEditingProduct(null);
      toast.success(t('edit_success'), { id: loadingToast });
    } catch(err) {
      console.error(err);
      toast.error(t('edit_error'), { id: loadingToast });
    }
  };

  return (
    <div className="flex flex-col h-full gap-6 relative">
      <h2 className="text-2xl font-bold text-slate-800">{t('title')}</h2>
      
      <div className="bg-white p-6 rounded shadow border border-slate-100">
        <h3 className="font-semibold text-lg mb-4 text-slate-800">{t('addNew')}</h3>
        <form onSubmit={handleSubmit} className="flex gap-4 items-end flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('name')}</label>
            <input 
              type="text" required 
              value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}
              className="w-full border border-gray-300 p-2 rounded text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('description')}</label>
            <input 
              type="text" 
              value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})}
              className="w-full border border-gray-300 p-2 rounded text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="w-32">
            <label className="block text-sm font-medium mb-1 text-slate-700">{t('price')} ($)</label>
            <input 
              type="number" step="0.01" required 
              value={formData.price} onChange={e => setFormData({...formData, price: parseFloat(e.target.value)})}
              className="w-full border border-gray-300 p-2 rounded text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium mb-1 text-slate-700">URL (Optional)</label>
            <input 
              type="url" 
              placeholder="https://example.com/image.jpg"
              value={formData.image_url} onChange={e => setFormData({...formData, image_url: e.target.value})}
              className="w-full border border-gray-300 p-2 rounded text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <button type="submit" className="bg-[var(--primary-color,#2563eb)] text-white px-6 py-2 border border-transparent rounded hover:opacity-90 font-medium transition h-[42px]">
            {tCommon('add')}
          </button>
        </form>
      </div>

      {/* Sync Section Refactored For UI/UX */}
      <div className="bg-slate-50 p-8 rounded-xl border-2 border-dashed border-slate-300 relative shadow-sm my-4">
        <div className="absolute top-0 right-8 -mt-3.5 bg-slate-50 px-3 text-slate-500 font-bold tracking-wide">
             {t('sync_badge')}
        </div>
        
        <h3 className="font-bold text-xl mb-2 text-slate-800">{t('sync_title')}</h3>
        <p className="text-slate-500 mb-6 text-sm">{t('sync_desc')}</p>
        
        <div className="flex gap-4 mb-8">
            <a href={`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products/template-physical`} download className="bg-white hover:bg-slate-100 text-slate-700 px-5 py-3 border border-slate-200 shadow-sm rounded-lg font-bold transition flex items-center gap-2 w-full justify-center">
               <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
               {t('sync_download_physical')}
            </a>
        </div>

        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex gap-4 items-end flex-wrap">
              <div className="flex-1 min-w-[300px]">
                <label className="block text-sm font-bold mb-2 text-slate-700">{t('sync_upload_label')}</label>
                <input 
                  type="file" 
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="w-full border border-slate-200 p-2 rounded text-slate-800 bg-slate-50 focus:ring-2 focus:ring-blue-500 outline-none file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-[var(--primary-color,#2563eb)] file:text-white hover:file:bg-blue-700 cursor-pointer transition-all" 
                />
              </div>
            </div>

            <div className="flex justify-center my-6 opacity-30">
               <hr className="w-full border-slate-400" />
               <span className="px-4 text-xs font-bold text-slate-600 -mt-2 bg-white uppercase">{t('sync_or')}</span>
               <hr className="w-full border-slate-400" />
            </div>

            <div className="flex gap-4 items-end flex-wrap">
              <div className="flex-1 min-w-[300px]">
                <label className="block text-sm font-bold mb-2 text-slate-700">{t('sync_cloud_label')}</label>
                <input 
                  type="url" 
                  value={sheetUrl} onChange={e => setSheetUrl(e.target.value)}
                  placeholder="https://docs.google.com/spreadsheets/d/e/..."
                  className="w-full border border-slate-300 p-3 rounded-lg text-slate-800 bg-slate-50 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none" 
                />
              </div>
              <button onClick={handleSync} disabled={syncing} className="bg-green-600 text-white px-6 py-3 border border-transparent rounded-lg hover:bg-green-700 font-bold shadow-sm transition h-[48px] min-w-[150px]">
                {syncing ? t('sync_loading') : t('sync_button')}
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-3 flex items-center justify-start"><svg className="w-4 h-4 text-amber-500 inline ml-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd"></path></svg>{t('sync_note')}</p>
        </div>
      </div>

      {products.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-12 text-center border-2 border-dashed border-blue-100 flex flex-col items-center justify-center">
            <div className="w-16 h-16 bg-blue-50 text-[var(--primary-color,#2563eb)] rounded-full flex items-center justify-center mb-4">
               <svg fill="currentColor" viewBox="0 0 20 20" className="w-8 h-8"><path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path></svg>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">{t('empty_title')}</h3>
            <p className="text-slate-500 mb-6 max-w-md">{t('empty_desc')}</p>
        </div>
      ) : (
      <div className="bg-white rounded shadow overflow-x-auto border border-slate-200">
        <table className="w-full text-left border-collapse min-w-max" style={{ textAlign: 'start' }}>
          <thead>
            <tr className="border-b bg-slate-50">
              <th className="p-4 font-semibold text-slate-700 w-16">{t('image_col')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('name')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('description')}</th>
              <th className="p-4 font-semibold text-slate-700">{t('price')}</th>
              <th className="p-4 font-semibold text-slate-700 w-40 text-center">{tCommon('action')}</th>
            </tr>
          </thead>
          <tbody>
            {products.map(p => (
              <tr key={p.id} className="border-b hover:bg-slate-50">
                <td className="p-4">
                  {p.image_url ? (
                    <img src={p.image_url} alt={p.name} className="w-10 h-10 rounded object-cover border" />
                  ) : (
                    <div className="w-10 h-10 rounded bg-slate-200 border flex items-center justify-center text-slate-400 text-xs truncate p-1" title={t('no_image')}>{t('no_image')}</div>
                  )}
                </td>
                <td className="p-4 text-slate-800 font-medium">{p.name}</td>
                <td className="p-4 text-slate-600 text-sm max-w-[300px] truncate" title={p.description}>{p.description}</td>
                <td className="p-4 font-medium" style={{ color: 'var(--primary-color,#2563eb)' }}>${Number(p.price).toFixed(2)}</td>
                <td className="p-4 flex gap-2 justify-center">
                  <button onClick={() => openEditModal(p)} className="text-blue-500 hover:text-white hover:bg-[var(--primary-color,#2563eb)] px-3 py-1.5 rounded text-sm font-medium transition border border-transparent hover:border-[var(--primary-color,#2563eb)]">{tCommon('edit')}</button>
                  <button onClick={() => handleDelete(p.id)} className="text-red-500 hover:text-white hover:bg-red-500 px-3 py-1.5 rounded text-sm font-medium transition border border-transparent hover:border-red-600">{tCommon('delete')}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      )}

      {/* Edit Component Modal */}
      {editingProduct && (
        <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
           <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden">
              <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                 <h3 className="text-lg font-bold text-slate-800">{t('edit_product')}</h3>
                 <button onClick={() => setEditingProduct(null)} className="text-slate-400 hover:text-slate-600 text-xl font-bold">&times;</button>
              </div>
              <div className="p-6">
                <form onSubmit={handleEditSubmit} className="flex flex-col gap-4">
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('name')}</label>
                      <input 
                         type="text" required
                         value={editFormData.name}
                         onChange={e => setEditFormData({...editFormData, name: e.target.value})}
                         className="w-full border p-2 rounded focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none text-slate-800"
                      />
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('description')}</label>
                      <textarea
                         value={editFormData.description}
                         onChange={e => setEditFormData({...editFormData, description: e.target.value})}
                         className="w-full border p-2 rounded focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none min-h-[80px] text-slate-800"
                      />
                   </div>
                   <div className="flex gap-4">
                       <div className="w-1/3">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('price')} ($)</label>
                          <input 
                             type="number" step="0.01" min="0" required
                             value={editFormData.price}
                             onChange={e => setEditFormData({...editFormData, price: parseFloat(e.target.value)})}
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none text-slate-800"
                          />
                       </div>
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">URL</label>
                          <input 
                             type="url" 
                             value={editFormData.image_url}
                             onChange={e => setEditFormData({...editFormData, image_url: e.target.value})}
                             placeholder="https://..."
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-[var(--primary-color,#2563eb)] outline-none text-slate-800"
                          />
                       </div>
                   </div>
                   
                   <div className="flex gap-3 justify-end mt-4 pt-4 border-t border-slate-100">
                      <button type="button" onClick={() => setEditingProduct(null)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded font-medium">Cancel</button>
                      <button type="submit" className="px-4 py-2 bg-[var(--primary-color,#2563eb)] hover:opacity-90 text-white rounded font-medium shadow-sm transition">{tCommon('save')}</button>
                   </div>
                </form>
              </div>
           </div>
        </div>
      )}
    </div>
  );
}
