import json
import os

locales = ['ar', 'en', 'tr']

data_to_add = {
    'ar': {
        'chat': {
            'extracting': "يتم استخراج بيانات العميل بالذكاء الاصطناعي...",
            'extracted_success': "تم تعبئة البيانات بذكاء!",
            'extraction_error': "حدث خطأ في استخراج البيانات. نرجو إدخالها يدوياً.",
            'convert_to_order_btn': "+ تحويل لطلب",
            'order_success_toast': "تم تحويل الطلب وتسجيله بنجاح في النظام!",
            'order_error_toast': "حدث خطأ أثناء إنشاء الطلب.",
            'no_product_image': "صورة المنتج غير متوفرة",
            'order_now': "اطلب الآن",
            'cards_hint': "ستظهر بطاقات المنتجات تلقائياً إذا قام الذكاء الاصطناعي بذكرها.",
            'new_order_title': "إنشاء طلب جديد",
            'product_name': "اسم المنتج",
            'quantity': "الكمية",
            'total_price': "السعر الإجمالي ($)",
            'customer_optional': "اسم العميل (اختياري)",
            'customer_placeholder': "مثال: يمان",
            'phone': "رقم الهاتف",
            'phone_placeholder': "+966xxxxxxxxx",
            'address': "العنوان",
            'address_placeholder': "الرياض - حي النرجس",
            'save_order': "حفظ الطلب",
            'qr_prices': "سؤال عن الأسعار",
            'qr_catalog': "أريد عرض الكتالوج",
            'qr_discounts': "هل يوجد خصومات؟",
            'qr_support': "أريد التحدث مع خدمة العملاء"
        },
        'merchant': {
            'orders_count': "{count, plural, =0 {لا توجد طلبات} one {# طلب} two {# طلبين} few {# طلبات} many {# طلباً} other {# طلب}}"
        },
        'settings': {
            'title': "إعدادات المتجر",
            'token_usage': "استهلاك التوكنز",
            'used_of_limit': "من {limit}",
            'free_tier': "باقة مجانية",
            'warning': "تنبيه هام",
            'warning_desc': "لقد استهلكت أكثر من 80% من الباقة الخاصة بك. يرجى الترقية الآن لضمان عدم توقف خدمات الذكاء الاصطناعي لعملائك.",
            'upgrade_btn': "ترقية الباقة الآن",
            'ai_tone': "تخصيص نبرة المساعد الذكي",
            'ai_tone_desc': "اختر أسلوب المحادثة الذي تفضله لمساعدك الذكي عند حديثه مع عملائك.",
            'tone_professional': "الاحترافية (Professional)",
            'tone_friendly': "الودودة (Friendly)",
            'tone_sales': "المبيعات القوية (Sales-driven)",
            'tone_updating': "جاري تحديث النبرة...",
            'tone_updated': "تم تحديث النبرة بنجاح!"
        },
        'layout': {
            'whatsapp_connected': "واتساب: متصل 🟢",
            'whatsapp_disconnected': "واتساب: غير متصل 🔴",
            'pdf_export': "تصدير التقرير (PDF)"
        }
    },
    'en': {
        'chat': {
            'extracting': "Extracting customer data via AI...",
            'extracted_success': "Data smartly filled!",
            'extraction_error': "Data extraction failed. Please enter manually.",
            'convert_to_order_btn': "+ Convert to Order",
            'order_success_toast': "Order converted and saved successfully!",
            'order_error_toast': "Error occurred while creating order.",
            'no_product_image': "Product image unavailable",
            'order_now': "Order Now",
            'cards_hint': "Product cards will dynamically appear if mentioned by AI.",
            'new_order_title': "Create New Order",
            'product_name': "Product Name",
            'quantity': "Quantity",
            'total_price': "Total Price ($)",
            'customer_optional': "Customer Name (Optional)",
            'customer_placeholder': "e.g. John Doe",
            'phone': "Phone Number",
            'phone_placeholder': "+1xxxxxxx",
            'address': "Address",
            'address_placeholder': "New York, 5th Ave",
            'save_order': "Save Order",
            'qr_prices': "Ask about prices",
            'qr_catalog': "Show catalog",
            'qr_discounts': "Any discounts?",
            'qr_support': "Talk to customer support"
        },
        'merchant': {
            'orders_count': "{count, plural, =0 {No orders} one {# order} other {# orders}}"
        },
        'settings': {
            'title': "Store Settings",
            'token_usage': "Token Usage",
            'used_of_limit': "of {limit}",
            'free_tier': "Free Tier",
            'warning': "Urgent Warning",
            'warning_desc': "You have consumed over 80% of your limit. Please upgrade your plan now down to avoid disruptions.",
            'upgrade_btn': "Upgrade Now",
            'ai_tone': "AI Assistant Persona",
            'ai_tone_desc': "Select the conversational tone for your AI assistant when talking to customers.",
            'tone_professional': "Professional",
            'tone_friendly': "Friendly",
            'tone_sales': "Sales-driven",
            'tone_updating': "Updating tone...",
            'tone_updated': "Tone updated successfully!"
        },
        'layout': {
            'whatsapp_connected': "WhatsApp: Connected 🟢",
            'whatsapp_disconnected': "WhatsApp: Disconnected 🔴",
            'pdf_export': "Export Report (PDF)"
        }
    },
    'tr': {
        'chat': {
            'extracting': "Yapay zeka müşteri verilerini çıkarıyor...",
            'extracted_success': "Veriler akıllıca dolduruldu!",
            'extraction_error': "Veri çıkarma başarısız. Lütfen manuel girin.",
            'convert_to_order_btn': "+ Siparişe Dönüştür",
            'order_success_toast': "Sipariş dönüştürüldü ve kaydedildi!",
            'order_error_toast': "Sipariş oluşturulurken hata oluştu.",
            'no_product_image': "Ürün resmi yok",
            'order_now': "Şimdi Sipariş Ver",
            'cards_hint': "Yapay zeka üründen bahsederse kartlar otomatik çıkar.",
            'new_order_title': "Yeni Sipariş Oluştur",
            'product_name': "Ürün Adı",
            'quantity': "Miktar",
            'total_price': "Toplam Fiyat ($)",
            'customer_optional': "Müşteri Adı (İsteğe bağlı)",
            'customer_placeholder': "örn. Ahmet Yılmaz",
            'phone': "Telefon",
            'phone_placeholder': "+90xxxxxxx",
            'address': "Adres",
            'address_placeholder': "İstanbul, Kadıköy",
            'save_order': "Siparişi Kaydet",
            'qr_prices': "Fiyat sor",
            'qr_catalog': "Katalog göster",
            'qr_discounts': "İndirim var mı?",
            'qr_support': "Müşteri hizmetlerine bağlan"
        },
        'merchant': {
            'orders_count': "{count, plural, =0 {Sipariş yok} one {# sipariş} other {# sipariş}}"
        },
        'settings': {
            'title': "Mağaza Ayarları",
            'token_usage': "Token Kullanımı",
            'used_of_limit': "{limit} tokenden",
            'free_tier': "Ücretsiz Plan",
            'warning': "Önemli Uyarı",
            'warning_desc': "Limitinizin %80'ini aştınız. Kesintileri önlemek için planınızı yükseltin.",
            'upgrade_btn': "Şimdi Yükselt",
            'ai_tone': "Yapay Zeka Tonu",
            'ai_tone_desc': "Yapay zeka asistanınızın konuşma tarzını seçin.",
            'tone_professional': "Profesyonel",
            'tone_friendly': "Arkadaşça",
            'tone_sales': "Satış odaklı",
            'tone_updating': "Ton güncelleniyor...",
            'tone_updated': "Ton başarıyla güncellendi!"
        },
        'layout': {
            'whatsapp_connected': "WhatsApp: Bağlı 🟢",
            'whatsapp_disconnected': "WhatsApp: Bağlantı yok 🔴",
            'pdf_export': "Raporu İndir (PDF)"
        }
    }
}

for loc in locales:
    file_path = f"C:/Users/yaman/.gemini/antigravity/playground/chatsmartai/frontend/messages/{loc}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for root_key in ['chat', 'merchant', 'settings', 'layout']:
            if root_key not in data:
                data[root_key] = {}
            if root_key in data_to_add[loc]:
                for k, v in data_to_add[loc][root_key].items():
                    data[root_key][k] = v
                    
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
print("JSON Locales updated successfully via Python.")
