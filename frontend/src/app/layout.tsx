import type { Metadata } from "next";
import "./globals.css";
import HydrationGuard from "@/components/HydrationGuard";
import { cookies } from "next/headers";
import { NextIntlClientProvider } from "next-intl";
import { ThemeProvider } from "@/components/ThemeProvider";

export const metadata: Metadata = {
  title: "ChatSmart AI",
  description: "Next Generation AI Managed CRM",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = cookies();
  const locale = cookieStore.get('NEXT_LOCALE')?.value || 'en';
  
  let messages;
  try {
    messages = (await import(`../../messages/${locale}.json`)).default;
  } catch (error) {
    messages = (await import(`../../messages/en.json`)).default;
  }

  const isRtl = locale === 'ar';

  return (
    <html lang={locale} dir={isRtl ? 'rtl' : 'ltr'}>
      <body className={`antialiased font-sans flex flex-col min-h-screen ${isRtl ? 'text-right' : 'text-left'}`}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <HydrationGuard>
            <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
              {children}
            </ThemeProvider>
          </HydrationGuard>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
