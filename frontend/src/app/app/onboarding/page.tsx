'use client';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { CheckCircle2, Store, MessageCircle, Package, Bot } from 'lucide-react';

export default function OnboardingWizard() {
  const [step, setStep] = useState(1);
  const router = useRouter();
  
  // Step 1 State
  const [bName, setBName] = useState('');
  const [bType, setBType] = useState('retail');
  const [bLang, setBLang] = useState('ar');

  // Step 2 State
  const [tgToken, setTgToken] = useState('');
  const [waPhone, setWaPhone] = useState('');
  const [waToken, setWaToken] = useState('');
  const [waSecret, setWaSecret] = useState('');
  
  // Step 3 State
  const [pName, setPName] = useState('My First Item');
  const [pPrice, setPPrice] = useState('100.0');
  
  const handleSaveStep1 = async () => {
    if (!bName) return toast.error('أدخل اسم المتجر');
    try {
      await axios.put(`/api/merchant/settings`, {
          name: bName, business_type: bType, language: bLang
      }, { withCredentials: true });
      toast.success('تم الحفظ');
      setStep(2);
    } catch { toast.error('خطأ في الحفظ'); }
  };

  const handleSaveStep2 = async () => {
      try {
          if (tgToken) {
              await axios.post(`/api/merchant/features/telegram`, {
                  bot_token: tgToken, webhook_secret: "onboarding_default", action: "save"
              }, { withCredentials: true });
          }
          if (waPhone || waToken || waSecret) {
              localStorage.setItem('waPhone', waPhone);
              localStorage.setItem('waToken', waToken);
              localStorage.setItem('waSecret', waSecret);
              toast.success('Your WhatsApp credentials have been saved. Complete the webhook setup in Settings > Integrations after onboarding.');
          }
          setStep(3);
      } catch (e) {
          toast.error('Failed to save channel details');
          setStep(3);
      }
  };
  
  const handleSaveStep3 = async () => {
      try {
        await axios.post(`/api/merchant/products`, {
            name: pName, price: parseFloat(pPrice), item_type: bType === 'retail' ? 'product' : 'service'
        }, { withCredentials: true });
        toast.success('تمت الإضافة');
      } catch {}
      setStep(4);
  };

  const completeSetup = async () => {
      try {
        await axios.put(`/api/merchant/settings`, {
          setup_complete: true
        }, { withCredentials: true });
        toast.success('مرحباً بك في لوحة التحكم!');
        router.push('/app');
      } catch { toast.error('حدث خطأ'); }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-slate-100/95 backdrop-blur-sm overflow-y-auto w-full h-full" dir="rtl">
      <div className="max-w-2xl mx-auto my-12 bg-white rounded-2xl shadow-2xl border overflow-hidden">
        <div className="bg-slate-900 text-white p-8 pb-12 flex justify-between items-center">
             <div>
                <h1 className="text-2xl font-bold">إعداد حسابك الذكي</h1>
                <p className="text-slate-400 mt-2">عزز مبيعاتك وأتمت عملياتك في خطوات بسيطة</p>
             </div>
             <Bot size={64} className="text-blue-500 opacity-20" />
        </div>
        
        <div className="p-8 -mt-8">
            <div className="bg-white rounded-xl shadow-sm border p-6">
                
                {/* Steps indicator */}
                <div className="flex justify-between mb-8 overflow-hidden">
                    {[
                        {num: 1, icon: <Store size={18}/>, label: 'الأساسيات'},
                        {num: 2, icon: <MessageCircle size={18}/>, label: 'الربط'},
                        {num: 3, icon: <Package size={18}/>, label: 'المنتجات'},
                        {num: 4, icon: <CheckCircle2 size={18}/>, label: 'الاطلاق'}
                    ].map(s => (
                        <div key={s.num} className={`flex flex-col items-center flex-1 ${step >= s.num ? 'text-blue-600' : 'text-slate-400'}`}>
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 border-2 ${step >= s.num ? 'bg-blue-50 border-blue-600' : 'bg-slate-50 border-slate-200'}`}>
                                {step > s.num ? <CheckCircle2 size={20} /> : s.icon}
                            </div>
                            <span className="text-xs font-bold">{s.label}</span>
                        </div>
                    ))}
                </div>

                {/* Step 1 */}
                {step === 1 && (
                    <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
                        <h2 className="font-bold text-xl text-slate-800">تفاصيل المتجر الأساسية</h2>
                        <div>
                            <label className="block text-sm font-medium mb-1">اسم المتجر / النشاط</label>
                            <input value={bName} onChange={e=>setBName(e.target.value)} className="w-full border rounded-lg p-3" placeholder="مثال: عبايات الأناقة..." />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">نوع النشاط</label>
                                <select value={bType} onChange={e=>setBType(e.target.value)} className="w-full border rounded-lg p-3">
                                    <option value="retail">متاجر إلكترونية (E-commerce)</option>
                                    <option value="hotel">فنادق وضيافة (Hotels)</option>
                                    <option value="clinic">عيادات ومراكز طبية (Clinics)</option>
                                    <option value="real_estate">عقارات (Real Estate)</option>
                                    <option value="booking">حجوزات وخدمات عامة (Services)</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">لغة البوت الأساسية</label>
                                <select value={bLang} onChange={e=>setBLang(e.target.value)} className="w-full border rounded-lg p-3">
                                    <option value="ar">العربية</option>
                                    <option value="en">الإنجليزية</option>
                                    <option value="tr">التركية</option>
                                </select>
                            </div>
                        </div>
                        <button onClick={handleSaveStep1} className="w-full bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700 mt-4">حفظ والمتابعة</button>
                    </div>
                )}

                {/* Step 2 */}
                {step === 2 && (
                    <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
                        <h2 className="font-bold text-xl text-slate-800">ربط قنوات التواصل</h2>
                        <p className="text-sm text-slate-500 mb-4">يمكنك تجاوز هذه الخطوة والقيام بها لاحقاً من الإعدادات</p>
                        
                        <div className="border rounded-lg p-4 bg-slate-50">
                            <h3 className="font-bold flex items-center gap-2"><MessageCircle size={18} className="text-sky-500" />تيليغرام (Telegram)</h3>
                            <input value={tgToken} onChange={e=>setTgToken(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Bot Token..." />
                        </div>
                        <div className="border rounded-lg p-4 bg-slate-50 mt-4">
                            <h3 className="font-bold flex items-center gap-2"><MessageCircle size={18} className="text-green-500" />واتساب (WhatsApp)</h3>
                            <input value={waPhone} onChange={e=>setWaPhone(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Phone Number ID..." />
                            <input value={waToken} onChange={e=>setWaToken(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="WhatsApp Access Token..." />
                            <input value={waSecret} onChange={e=>setWaSecret(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Meta App Secret..." />
                        </div>

                        <div className="flex gap-2 mt-6">
                            <button onClick={handleSaveStep2} className="flex-1 bg-green-600 text-white font-bold py-3 rounded-lg hover:bg-green-700">تفعيل القنوات</button>
                            <button onClick={()=>setStep(3)} className="bg-slate-200 text-slate-700 font-bold py-3 px-6 rounded-lg hover:bg-slate-300">تخطي</button>
                        </div>
                    </div>
                )}

                {/* Step 3 */}
                {step === 3 && (
                    <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
                        <h2 className="font-bold text-xl text-slate-800">أضف منتجك الأول لتفعيل ذكاء المبيعات</h2>
                        <div>
                            <label className="block text-sm font-medium mb-1">اسم المنتج / الخدمة</label>
                            <input value={pName} onChange={e=>setPName(e.target.value)} className="w-full border rounded-lg p-3" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium mb-1">السعر</label>
                            <input value={pPrice} onChange={e=>setPPrice(e.target.value)} type="number" className="w-full border rounded-lg p-3" />
                        </div>
                        
                        <div className="flex gap-2 mt-6">
                            <button onClick={handleSaveStep3} className="flex-1 bg-blue-600 text-white font-bold py-3 rounded-lg hover:bg-blue-700">إضافة المنتج</button>
                            <button onClick={()=>setStep(4)} className="bg-slate-200 text-slate-700 font-bold py-3 px-6 rounded-lg hover:bg-slate-300">تخطي</button>
                        </div>
                    </div>
                )}

                {/* Step 4 */}
                {step === 4 && (
                    <div className="space-y-4 text-center animate-in fade-in zoom-in-95 duration-300 py-6">
                        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            <CheckCircle2 size={40} />
                        </div>
                        <h2 className="font-bold text-2xl text-slate-800">اكتمل التجهيز!</h2>
                        <p className="text-slate-500 mb-6">ذكاءك الاصطناعي جاهز للرد على استفسارات عملائك وزيادة مبيعاتك.</p>
                        
                        <button onClick={completeSetup} className="w-full bg-slate-900 text-white font-bold py-3 rounded-lg hover:bg-slate-800 shadow-md">
                            الدخول للوحة التحكم
                        </button>
                    </div>
                )}
                
            </div>
        </div>
      </div>
    </div>
  );
}
