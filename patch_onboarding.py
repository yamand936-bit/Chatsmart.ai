with open("frontend/src/app/app/onboarding/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
"""  // Step 2 State
  const [tgToken, setTgToken] = useState('');
  const [waPhone, setWaPhone] = useState('');""",
"""  // Step 2 State
  const [tgToken, setTgToken] = useState('');
  const [waPhone, setWaPhone] = useState('');
  const [waToken, setWaToken] = useState('');
  const [waSecret, setWaSecret] = useState('');"""
)

text = text.replace(
"""  const handleSaveStep2 = async () => {
      // Dummy save for mock, in reality calls features api
      setStep(3);
  };""",
"""  const handleSaveStep2 = async () => {
      try {
          if (tgToken) {
              await axios.post(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/merchant/features/telegram`, {
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
  };"""
)

text = text.replace(
"""                        <div className="border rounded-lg p-4 bg-slate-50 mt-4">
                            <h3 className="font-bold flex items-center gap-2"><MessageCircle size={18} className="text-green-500" />واتساب (WhatsApp)</h3>
                            <input value={waPhone} onChange={e=>setWaPhone(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Phone Number ID..." />
                        </div>""",
"""                        <div className="border rounded-lg p-4 bg-slate-50 mt-4">
                            <h3 className="font-bold flex items-center gap-2"><MessageCircle size={18} className="text-green-500" />واتساب (WhatsApp)</h3>
                            <input value={waPhone} onChange={e=>setWaPhone(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Phone Number ID..." />
                            <input value={waToken} onChange={e=>setWaToken(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="WhatsApp Access Token..." />
                            <input value={waSecret} onChange={e=>setWaSecret(e.target.value)} className="w-full border rounded p-2 mt-2 text-sm" placeholder="Meta App Secret..." />
                        </div>"""
)

with open("frontend/src/app/app/onboarding/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
