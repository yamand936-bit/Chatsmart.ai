with open("frontend/src/app/app/layout.tsx", "r", encoding="utf-8") as f:
    text = f.read()

old_nav = "<Link href=\"/app/chat\" className=\"hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100\">{t('chat')}</Link>"
new_nav = """<Link href="/app/chat" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{t('chat')}</Link>
            <Link href="/app/kanban" className="hover:text-blue-200 font-medium transition text-sm md:text-base opacity-90 hover:opacity-100">{'CRM Funnel'}</Link>"""

text = text.replace(old_nav, new_nav)

with open("frontend/src/app/app/layout.tsx", "w", encoding="utf-8") as f:
    f.write(text)
