with open("frontend/src/app/app/layout.tsx", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    "import { ThemeToggle } from '@/components/ThemeToggle';",
    "import { ThemeToggle } from '@/components/ThemeToggle';\nimport { NotificationBell } from '@/components/NotificationBell';"
)

mock_toast = """  useEffect(() => {
     // Mock New Message Notification (Simulate a live WhatsApp message after 3 seconds)
     const timer = setTimeout(() => {
        toast.custom((tCustom) => (
          <div className={`${tCustom.visible ? 'animate-enter' : 'animate-leave'} max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto flex ring-1 ring-black ring-opacity-5 relative`} style={{ direction: 'rtl' }}>
            <div className="flex-1 w-0 p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 pt-0.5">
                  <span className="text-3xl">💬</span>
                </div>
                <div className="mr-3 flex-1">
                  <p className="text-sm font-bold text-slate-900">رسالة جديدة من WhatsApp!</p>
                  <p className="mt-1 text-sm text-slate-500">عميل جديد يستفسر عن المبيعات.</p>
                </div>
              </div>
            </div>
            <div className="flex border-r border-slate-200">
              <Link
                href="/app/chat"
                onClick={() => toast.dismiss(tCustom.id)}
                className="w-full border border-transparent rounded-none rounded-l-lg p-4 flex items-center justify-center text-sm font-bold text-green-600 hover:text-green-500 focus:outline-none"
              >
                عرض
              </Link>
            </div>
            <button onClick={() => toast.dismiss(tCustom.id)} className="absolute top-1 left-1 text-slate-400 hover:text-slate-600">×</button>
          </div>
        ), { duration: 6000, position: 'bottom-right' });
     }, 3000);

     return () => clearTimeout(timer);
  }, []);"""

text = text.replace(mock_toast, "")

old_nav_tools = """            <div className="flex items-center gap-2">
               <ThemeToggle />
               <LanguageSwitcher />
               <LogoutButton />
            </div>"""
new_nav_tools = """            <div className="flex items-center gap-2">
               <NotificationBell />
               <ThemeToggle />
               <LanguageSwitcher />
               <LogoutButton />
            </div>"""

text = text.replace(old_nav_tools, new_nav_tools)

with open("frontend/src/app/app/layout.tsx", "w", encoding="utf-8") as f:
    f.write(text)
