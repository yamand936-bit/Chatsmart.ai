'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslations, useLocale } from 'next-intl';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const [messages, setMessages] = useState<{role: 'user'|'ai', text: string}[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [products, setProducts] = useState<any[]>([]);

  // Order modal state
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderForm, setOrderForm] = useState({
    product_name: '',
    quantity: 1,
    customer_id: '',
    total_amount: 0,
    address: '',
    phone: ''
  });

  const t = useTranslations('chat');
  const tCommon = useTranslations('common');
  const locale = useLocale();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  useEffect(() => {
    // Fetch products to bind them to interactive cards
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true })
      .then(res => setProducts(res.data.data || []))
      .catch(console.error);
  }, []);

  const handleOpenOrderModal = async (product?: any) => {
    let guessedProduct = '';
    let defaultPrice = 0;
    if (product) {
        guessedProduct = product.name;
        defaultPrice = product.price;
    } else {
        const lastUserMessage = messages.slice().reverse().find(m => m.role === 'user');
        if (lastUserMessage) {
            const matched = products.find(p => lastUserMessage.text.toLowerCase().includes(p.name.toLowerCase()));
            if (matched) guessedProduct = matched.name;
        }
    }

    setOrderForm({
        product_name: guessedProduct,
        quantity: 1,
        customer_id: '',
        total_amount: defaultPrice,
        address: '',
        phone: ''
    });
    setShowOrderModal(true);
    
    if (messages.length > 0) {
        const loadingToast = toast.loading(t('extracting'));
        try {
            const lastMessages = messages.slice(-5).map(m => m.role + ": " + m.text);
            const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/extract-order`, { messages: lastMessages }, { withCredentials: true });
            
            if (res.data.status === "ok" && res.data.data) {
                setOrderForm(prev => ({
                    ...prev,
                    quantity: res.data.data.quantity || prev.quantity,
                    address: res.data.data.address || prev.address,
                    phone: res.data.data.phone || prev.phone
                }));
                toast.success(t('extracted_success'), { id: loadingToast });
            } else {
                toast.error(t('extraction_error'), { id: loadingToast });
            }
        } catch (err) {
            console.error(err);
            toast.error(t('extraction_error'), { id: loadingToast });
        }
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
          // If price is 0 and product exists, derive it
          let finalTotal = orderForm.total_amount;
          if (finalTotal === 0) {
              const p = products.find(prod => prod.name === orderForm.product_name);
              if (p) finalTotal = p.price * orderForm.quantity;
          }

          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/orders`, {
              product_name: orderForm.product_name,
              quantity: orderForm.quantity,
              customer_id: orderForm.customer_id || null,
              total_amount: finalTotal,
              address: orderForm.address,
              phone: orderForm.phone
          }, { withCredentials: true });
          
          setShowOrderModal(false);
          toast.success(t('order_success_toast'));
      } catch (err) {
          console.error(err);
          toast.error(t('order_error_toast'));
      }
  };

  const handleSend = async (e?: React.FormEvent, manualText?: string) => {
    if(e) e.preventDefault();
    const textToSend = manualText || input;
    if(!textToSend.trim() || limitReached) return;

    setMessages(prev => [...prev, {role: 'user', text: textToSend}]);
    if (!manualText) setInput('');
    setIsTyping(true);

    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/chat/message`, {
        customer_platform: "web_simulator",
        external_id: "demo_user",
        content: textToSend
      });
      
      const intentValue = res.data.intent;
      if (intentValue === "limit_reached") {
         setLimitReached(true);
      }
      
      setMessages(prev => [...prev, {
        role: 'ai', 
        text: intentValue === "limit_reached" ? t('limit_reached') : (res.data.ai_response || t('noResponse'))
      }]);
    } catch(err) {
      console.error(err);
      setMessages(prev => [...prev, {role: 'ai', text: tCommon('error')}]);
    } finally {
      setIsTyping(false);
    }
  };

  const renderMessageContent = (text: string, role: string) => {
      if (role === 'user') return text;

      // Smart Product Display Logic
      const matchedProducts = products.filter(p => text.toLowerCase().includes(p.name.toLowerCase()));

      return (
        <div className="flex flex-col gap-3">
          <span className="whitespace-pre-wrap">{text}</span>
          {matchedProducts.length > 0 && (
            <div className={`flex gap-2 flex-wrap ${dir === 'rtl' ? 'ml-auto' : 'mr-auto'} mt-2`}>
              {matchedProducts.map(p => (
                <div key={p.id} className="bg-white border border-blue-100 rounded-lg shadow-sm min-w-[200px] text-slate-800 text-sm overflow-hidden flex flex-col">
                   {p.image_url ? (
                      <img src={p.image_url} alt={p.name} className="w-full h-32 object-cover" />
                   ) : (
                      <div className="w-full h-24 bg-slate-100 flex items-center justify-center text-slate-400 text-xs">{t('no_product_image')}</div>
                   )}
                   <div className="p-3 flex-1 flex flex-col justify-between">
                       <div>
                           <div className="font-bold mb-1 text-slate-800">{p.name}</div>
                           <div className="text-blue-600 font-bold mb-3">${Number(p.price).toFixed(2)}</div>
                       </div>
                       <button 
                         onClick={() => handleOpenOrderModal(p)}
                         className="w-full bg-blue-50 border border-blue-200 hover:bg-blue-600 hover:text-white text-blue-700 py-1.5 rounded transition font-medium"
                       >
                         {t('order_now')}
                       </button>
                   </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
  };

  return (
    <div className="max-w-2xl mx-auto h-[80vh] flex flex-col bg-white rounded-xl shadow overflow-hidden relative" dir={dir}>
      <div className="bg-blue-600 text-white p-4 flex justify-between items-center" dir={dir}>
        <div>
          <h2 className="text-xl font-bold">{t('title')}</h2>
          <p className="text-sm opacity-80">{t('subtitle')}</p>
        </div>
        <button 
          onClick={() => handleOpenOrderModal()}
          className="bg-white text-blue-600 font-bold px-4 py-2 rounded shadow-sm hover:bg-blue-50 transition text-sm"
        >
          {t('convert_to_order_btn')}
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50" dir={dir}>
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20 p-8 border-2 border-dashed border-slate-200 rounded-xl">
            <div className="text-4xl mb-4 opacity-50">🤖</div>
            <p>{t('noMessages')}</p>
            <p className="text-sm opacity-70 mt-2">{t('cards_hint')}</p>
          </div>
        )}
        
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-3 rounded-2xl ${m.role === 'user' ? 'bg-blue-600 text-white rounded-br-none' : 'bg-white border text-slate-800 rounded-bl-none shadow-sm'}`}>
              {renderMessageContent(m.text, m.role)}
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white border text-slate-500 p-3 rounded-2xl rounded-bl-none shadow-sm text-sm italic">
              {t('typing')}
            </div>
          </div>
        )}
      </div>

      <div className="bg-white border-t p-4 flex flex-col gap-3" dir={dir}>
        
        {/* Quick Replies */}
        {!limitReached && (
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
            {[t('qr_prices'), t('qr_catalog'), t('qr_discounts'), t('qr_support')].map((qr, idx) => (
               <button 
                 key={idx}
                 onClick={() => handleSend(undefined, qr)}
                 disabled={isTyping}
                 className="bg-blue-50 border border-blue-200 text-blue-700 whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-semibold hover:bg-blue-100 transition disabled:opacity-50"
               >
                 {qr}
               </button>
            ))}
          </div>
        )}

        <form onSubmit={e => handleSend(e)} className="flex gap-2">
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={limitReached ? t('limit_reached') : t('typeMessage')}
            className={`flex-1 border text-slate-800 p-3 rounded-full focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 ${limitReached ? 'bg-red-50 border-red-200' : ''}`}
            disabled={isTyping || limitReached}
          />
          <button 
            type="submit" 
            disabled={isTyping || !input.trim() || limitReached}
            className="bg-blue-600 text-white px-6 py-2 rounded-full font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            {t('send')}
          </button>
        </form>
      </div>

      {/* Order Modal */}
      {showOrderModal && (
          <div className="absolute inset-0 bg-slate-800/50 flex items-center justify-center p-4 z-50">
             <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">{t('new_order_title')}</h3>
                <form onSubmit={handleCreateOrder} className="flex flex-col gap-4">
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('product_name')}</label>
                      <input 
                         type="text" required
                         value={orderForm.product_name}
                         onChange={e => setOrderForm({...orderForm, product_name: e.target.value})}
                         className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                   </div>
                   <div className="flex gap-4">
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('quantity')}</label>
                          <input 
                             type="number" min="1" required
                             value={orderForm.quantity}
                             onChange={e => setOrderForm({...orderForm, quantity: parseInt(e.target.value)})}
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                          />
                       </div>
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('total_price')}</label>
                          <input 
                             type="number" step="0.01" min="0" required
                             value={orderForm.total_amount}
                             onChange={e => setOrderForm({...orderForm, total_amount: parseFloat(e.target.value)})}
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                          />
                       </div>
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('customer_optional')}</label>
                      <input 
                         type="text" 
                         value={orderForm.customer_id}
                         onChange={e => setOrderForm({...orderForm, customer_id: e.target.value})}
                         placeholder={t('customer_placeholder')}
                         className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                      />
                   </div>
                   <div className="flex gap-4">
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('phone')}</label>
                          <input 
                             type="text" 
                             value={orderForm.phone}
                             onChange={e => setOrderForm({...orderForm, phone: e.target.value})}
                             placeholder={t('phone_placeholder')}
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                          />
                       </div>
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('address')}</label>
                          <input 
                             type="text" 
                             value={orderForm.address}
                             onChange={e => setOrderForm({...orderForm, address: e.target.value})}
                             placeholder={t('address_placeholder')}
                             className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                          />
                       </div>
                   </div>
                   
                   <div className="flex gap-3 justify-end mt-4 border-t pt-4">
                      <button type="button" onClick={() => setShowOrderModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded font-medium">{tCommon('cancel')}</button>
                      <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium">{t('save_order')}</button>
                   </div>
                </form>
             </div>
          </div>
      )}

    </div>
  );
}
