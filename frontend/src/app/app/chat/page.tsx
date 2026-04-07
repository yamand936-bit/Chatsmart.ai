'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTranslations, useLocale } from 'next-intl';
import toast from 'react-hot-toast';

export default function ChatPage() {
  const [messages, setMessages] = useState<{role: 'user'|'ai'|'assistant', text: string}[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [limitReached, setLimitReached] = useState(false);
  const [products, setProducts] = useState<any[]>([]);
  
  // Inbox State
  const [conversations, setConversations] = useState<any[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null);

  // Order modal state
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderForm, setOrderForm] = useState({
    product_name: '', quantity: 1, customer_id: '', total_amount: 0, address: '', phone: ''
  });

  const t = useTranslations('chat');
  const tCommon = useTranslations('common');
  const locale = useLocale();
  const dir = locale === 'ar' ? 'rtl' : 'ltr';

  useEffect(() => {
    axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/products`, { withCredentials: true })
      .then(res => setProducts(res.data.data || [])).catch(console.error);
      
    fetchConversations();
  }, []);

  const fetchConversations = () => {
     axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/conversations`, { withCredentials: true })
      .then(res => setConversations(res.data.data || [])).catch(console.error);
  };

  const loadConversationMessages = (id: string) => {
     setSelectedConversation(id);
     setIsTyping(true);
     axios.get(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/conversations/${id}/messages`, { withCredentials: true })
      .then(res => {
          setMessages(res.data.data || []);
      })
      .catch(console.error)
      .finally(() => setIsTyping(false));
  };

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

    setOrderForm({ product_name: guessedProduct, quantity: 1, customer_id: '', total_amount: defaultPrice, address: '', phone: '' });
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
            toast.error(t('extraction_error'), { id: loadingToast });
        }
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
          let finalTotal = orderForm.total_amount;
          if (finalTotal === 0) {
              const p = products.find(prod => prod.name === orderForm.product_name);
              if (p) finalTotal = p.price * orderForm.quantity;
          }

          await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/merchant/orders`, {
              ...orderForm, total_amount: finalTotal, customer_id: orderForm.customer_id || null
          }, { withCredentials: true });
          
          setShowOrderModal(false);
          toast.success(t('order_success_toast'));
      } catch (err) {
          toast.error(t('order_error_toast'));
      }
  };

  const handleSend = async (e?: React.FormEvent, manualText?: string) => {
    if(e) e.preventDefault();
    const textToSend = manualText || input;
    if(!textToSend.trim() || limitReached) return;
    
    if(selectedConversation) {
        toast("لا يمكن الإرسال حالياً إلا في وضع المحاكي.", { icon: '⚠️' });
        return;
    }

    setMessages(prev => [...prev, {role: 'user', text: textToSend}]);
    if (!manualText) setInput('');
    setIsTyping(true);

    try {
      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/api/chat/message`, {
        customer_platform: "web_simulator",
        external_id: "demo_user",
        content: textToSend
      });
      
      if (res.data.intent === "limit_reached") setLimitReached(true);
      
      setMessages(prev => [...prev, {
        role: 'assistant', 
        text: res.data.intent === "limit_reached" ? t('limit_reached') : (res.data.ai_response || t('noResponse'))
      }]);
      fetchConversations();
    } catch(err) {
      setMessages(prev => [...prev, {role: 'assistant', text: tCommon('error')}]);
    } finally {
      setIsTyping(false);
    }
  };

  const renderMessageContent = (text: string, role: string) => {
      if (role === 'user') return text;
      
      let displayText = text;
      let smartCards = [];
      
      // Parse JSON from codeblocks if exists
      const codeBlockRegex = /```json\n([\s\S]*?)\n```/g;
      let match;
      while ((match = codeBlockRegex.exec(text)) !== null) {
          try {
              smartCards.push(JSON.parse(match[1]));
              displayText = displayText.replace(match[0], ''); // Remove JSON block from visual text
          } catch(e) {}
      }

      const matchedProducts = products.filter(p => displayText.toLowerCase().includes(p.name.toLowerCase()));

      return (
        <div className="flex flex-col gap-3">
          <span className="whitespace-pre-wrap">{displayText}</span>
          
          {/* Render Explicit AI Smart Cards (JSON generated) */}
          {smartCards.length > 0 && (
            <div className={`flex gap-3 flex-wrap ${dir === 'rtl' ? 'ml-auto' : 'mr-auto'} mt-2`}>
              {smartCards.map((card, idx) => (
                <div key={idx} className="bg-gradient-to-b from-slate-50 to-white border border-indigo-100 rounded-xl shadow-md min-w-[220px] max-w-[280px] overflow-hidden flex flex-col hover:shadow-lg transition">
                   {card.image_url && card.image_url !== "URL" ? (
                      <img src={card.image_url} alt={card.product_name} className="w-full h-36 object-cover border-b border-slate-100" />
                   ) : (
                      <div className="w-full h-28 bg-indigo-50 flex items-center justify-center text-indigo-300 text-xs font-medium">✨ منتج مميز</div>
                   )}
                   <div className="p-4 flex-1 flex flex-col justify-between">
                       <div>
                           <div className="font-bold text-slate-900 mb-1 leading-tight">{card.product_name}</div>
                           <div className="text-indigo-600 font-extrabold mb-4">{card.price}</div>
                       </div>
                       <button onClick={() => {
                           const matched = products.find(p => p.name.includes(card.product_name));
                           if (matched) handleOpenOrderModal(matched);
                       }} className="w-full shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded-lg transition font-bold text-sm tracking-wide">
                         {t('cards.buy_now', {fallback: 'شراء الآن'})}
                       </button>
                   </div>
                </div>
              ))}
            </div>
          )}

          {/* Render Implicit Mentions Backwards compatibility */}
          {smartCards.length === 0 && matchedProducts.length > 0 && (
            <div className={`flex gap-2 flex-wrap ${dir === 'rtl' ? 'ml-auto' : 'mr-auto'} mt-2`}>
              {matchedProducts.map(p => (
                <div key={p.id} className="bg-white border border-blue-100 rounded-lg shadow-sm min-w-[200px] text-slate-800 text-sm overflow-hidden flex flex-col">
                   {p.image_url ? (
                      <img src={p.image_url} alt={p.name} className="w-full h-32 object-cover" />
                   ) : (
                      <div className="w-full h-24 bg-slate-100 flex items-center justify-center text-slate-400 text-xs">{t('no_image', {fallback: 'بدون صورة'})}</div>
                   )}
                   <div className="p-3 flex-1 flex flex-col justify-between">
                       <div>
                           <div className="font-bold mb-1 text-slate-800">{p.name}</div>
                           <div className="text-blue-600 font-bold mb-3">${Number(p.price).toFixed(2)}</div>
                       </div>
                       <button onClick={() => handleOpenOrderModal(p)} className="w-full bg-[var(--primary-color,#2563eb)] hover:opacity-90 text-white py-1.5 rounded transition font-medium">
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

  const getPriorityBadge = (priority: string) => {
      switch(priority) {
          case 'Hot': return <span className="bg-red-100 text-red-700 font-bold px-2 py-0.5 rounded text-xs ring-1 ring-red-200">🔥 Hot</span>;
          case 'Warm': return <span className="bg-amber-100 text-amber-700 font-bold px-2 py-0.5 rounded text-xs ring-1 ring-amber-200">✨ Warm</span>;
          case 'Cold': return <span className="bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded text-xs ring-1 ring-blue-200">❄️ Cold</span>;
          default: return <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs ring-1 ring-slate-200">جديد</span>;
      }
  };

  return (
    <div className="max-w-6xl mx-auto h-[80vh] flex bg-white rounded-xl shadow overflow-hidden relative border border-slate-200" dir={dir}>
      
      {/* Sidebar: Conversations List */}
      <div className="w-1/3 border-l bg-slate-50 flex flex-col h-full border-slate-200 shadow-inner overflow-hidden">
         <div className="p-4 bg-white border-b border-slate-200">
            <h3 className="font-bold text-slate-800 text-lg">{t('inbox_title')}</h3>
            <p className="text-xs text-slate-500">{t('inbox_desc')}</p>
         </div>
         <div className="flex-1 overflow-y-auto w-full">
            <button 
               onClick={() => { setSelectedConversation(null); setMessages([]); }}
               className={`w-full text-start p-4 border-b border-slate-200 hover:bg-slate-100 transition ${!selectedConversation ? 'bg-blue-50 border-l-4 border-l-[var(--primary-color,#2563eb)]' : ''}`}
            >
               <div className="font-bold text-slate-800 flex justify-between items-center">
                  <span>{t('simulator_title')}</span>
                  <span className="bg-slate-200 text-slate-700 text-xs px-2 py-1 rounded">{t('simulator_badge')}</span>
               </div>
               <p className="text-xs text-slate-500 mt-1 truncate">{t('simulator_desc')}</p>
            </button>
            
            {conversations.map(c => (
                <button 
                  key={c.id}
                  onClick={() => loadConversationMessages(c.id)}
                  className={`w-full text-start p-5 border-b border-slate-200 hover:bg-slate-100 transition flex flex-col gap-2 ${selectedConversation === c.id ? 'bg-blue-50 border-r-4 border-r-[var(--primary-color,#2563eb)] border-l-0' : ''}`}
                >
                   <div className="flex justify-between items-start w-full gap-2">
                       <span className="font-bold text-slate-800 font-mono text-[15px]" dir="ltr">{c.customer_phone}</span>
                       <div className="shrink-0">{getPriorityBadge(c.lead_priority)}</div>
                   </div>
                   <div className="text-sm text-slate-500 flex justify-between w-full">
                       <span className="truncate max-w-[70%] text-slate-600">{c.last_message || '...'}</span>
                       <span className="opacity-70 uppercase truncate text-xs font-semibold">{c.platform}</span>
                   </div>
                   {c.tags && c.tags.length > 0 && (
                     <div className="flex gap-1 flex-wrap w-full mt-1">
                       {c.tags.slice(0, 2).map((t: string, idx: number) => (
                         <span key={idx} className="bg-indigo-50 border border-indigo-100 text-indigo-700 text-[10px] font-bold px-1.5 py-0.5 rounded truncate max-w-[120px]" title={t}>
                           🏷️ {t}
                         </span>
                       ))}
                       {c.tags.length > 2 && (
                         <span className="text-[10px] text-slate-400 self-center">+{c.tags.length - 2}</span>
                       )}
                     </div>
                   )}
                </button>
            ))}
         </div>
      </div>

      {/* Main Chat Area */}
      <div className="w-2/3 flex flex-col h-full bg-slate-50 relative pointer-events-auto z-10">
          <div className="bg-[var(--primary-color,#2563eb)] text-white p-4 flex justify-between items-center shadow-md relative z-10" dir={dir}>
            <div>
              <h2 className="text-xl font-bold">{selectedConversation ? "عرض المحادثة" : t('title')}</h2>
              <p className="text-sm opacity-80">{selectedConversation ? 'تتبع طلبات العميل' : t('subtitle')}</p>
            </div>
            <button onClick={() => handleOpenOrderModal()} className="bg-white text-[var(--primary-color,#2563eb)] font-bold px-4 py-2 rounded shadow-sm hover:opacity-90 transition text-sm">
              {t('convert_to_order_btn')}
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4" dir={dir}>
            {messages.length === 0 && (
              <div className="text-center text-slate-400 mt-20 p-8 border-2 border-dashed border-slate-200 rounded-xl bg-white shadow-sm">
                <div className="text-4xl mb-4 opacity-50">🤖</div>
                <p>{t('noMessages')}</p>
              </div>
            )}
            
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl ${m.role === 'user' ? 'bg-[var(--primary-color,#2563eb)] text-white rounded-br-none shadow-md' : 'bg-white border text-slate-800 rounded-bl-none shadow-sm'}`}>
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

          <div className="bg-white border-t p-4 flex flex-col gap-3 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] relative z-20" dir={dir}>
            {!limitReached && !selectedConversation && (
              <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
                {[t('qr_prices'), t('qr_catalog'), t('qr_discounts'), t('qr_support')].map((qr, idx) => (
                   <button 
                     key={idx} onClick={() => handleSend(undefined, qr)} disabled={isTyping}
                     className="bg-blue-50 border border-blue-200 text-blue-700 whitespace-nowrap px-4 py-1.5 rounded-full text-xs font-semibold hover:bg-blue-100 transition disabled:opacity-50"
                   >{qr}</button>
                ))}
              </div>
            )}

            <form onSubmit={e => handleSend(e)} className="flex gap-2">
              <input 
                type="text" value={input} onChange={e => setInput(e.target.value)}
                placeholder={selectedConversation ? 'هذه نافذة عرض فقط. لا يمكنك الرد محلياً حالياً.' : (limitReached ? t('limit_reached') : t('typeMessage'))}
                className={`flex-1 border text-slate-800 p-3 rounded-full focus:outline-none focus:border-[var(--primary-color,#2563eb)] focus:ring-1 focus:ring-[var(--primary-color,#2563eb)] ${limitReached ? 'bg-red-50 border-red-200' : ''}`}
                disabled={isTyping || limitReached || selectedConversation !== null}
              />
              <button 
                type="submit" 
                disabled={isTyping || !input.trim() || limitReached || selectedConversation !== null}
                className="bg-[var(--primary-color,#2563eb)] text-white px-6 py-2 rounded-full font-medium hover:opacity-90 disabled:opacity-50 transition"
              >
                {t('send')}
              </button>
            </form>
          </div>
      </div>

       {/* Order Modal */}
       {showOrderModal && (
          <div className="absolute inset-0 bg-slate-800/50 flex items-center justify-center p-4 z-50">
             <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
                <h3 className="text-xl font-bold text-slate-800 mb-4">{t('new_order_title')}</h3>
                <form onSubmit={handleCreateOrder} className="flex flex-col gap-4">
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('product_name')}</label>
                      <input type="text" required value={orderForm.product_name} onChange={e => setOrderForm({...orderForm, product_name: e.target.value})} className="w-full border p-2 rounded focus:ring-[var(--primary-color,#2563eb)] outline-none" />
                   </div>
                   <div className="flex gap-4">
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('quantity')}</label>
                          <input type="number" min="1" required value={orderForm.quantity} onChange={e => setOrderForm({...orderForm, quantity: parseInt(e.target.value)})} className="w-full border p-2 rounded outline-none flex-1 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)]" />
                       </div>
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('total_price')}</label>
                          <input type="number" step="0.01" min="0" required value={orderForm.total_amount} onChange={e => setOrderForm({...orderForm, total_amount: parseFloat(e.target.value)})} className="w-full border p-2 rounded outline-none flex-1 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)]" />
                       </div>
                   </div>
                   <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1">{t('customer_optional')}</label>
                      <input type="text" value={orderForm.customer_id} onChange={e => setOrderForm({...orderForm, customer_id: e.target.value})} placeholder={t('customer_placeholder')} className="w-full border p-2 rounded outline-none flex-1 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)]" />
                   </div>
                   <div className="flex gap-4">
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('phone')}</label>
                          <input type="text" value={orderForm.phone} onChange={e => setOrderForm({...orderForm, phone: e.target.value})} placeholder={t('phone_placeholder')} className="w-full border p-2 rounded outline-none flex-1 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)]" />
                       </div>
                       <div className="flex-1">
                          <label className="block text-sm font-medium text-slate-700 mb-1">{t('address')}</label>
                          <input type="text" value={orderForm.address} onChange={e => setOrderForm({...orderForm, address: e.target.value})} placeholder={t('address_placeholder')} className="w-full border p-2 rounded outline-none flex-1 focus:ring-2 focus:ring-[var(--primary-color,#2563eb)]" />
                       </div>
                   </div>
                   <div className="flex gap-3 justify-end mt-4 border-t pt-4">
                      <button type="button" onClick={() => setShowOrderModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded font-medium">{tCommon('cancel')}</button>
                      <button type="submit" className="px-4 py-2 bg-[var(--primary-color,#2563eb)] hover:opacity-90 text-white rounded font-medium">{t('save_order')}</button>
                   </div>
                </form>
             </div>
          </div>
      )}
    </div>
  );
}
