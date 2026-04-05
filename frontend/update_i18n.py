import json
import os

locales = ['ar', 'en', 'tr']

data_to_add = {
    'ar': {
        'products': {
            'edit_product': 'تعديل المنتج',
            'edit_success': 'تم تعديل المنتج بنجاح!',
            'edit_error': 'حدث خطأ أثناء التعديل.',
            'image_col': 'صورة',
            'no_image': 'بدون صورة',
            'empty_title': 'أضف منتجك الأول لتفعيل مبيعات الذكاء الاصطناعي',
            'empty_desc': 'لا توجد منتجات لعرضها. أضف منتجاتك هنا ليتمكن المساعد الذكي من اقتراحها وبيعها لعملائك ومشاركة صورها معهم تلقائياً.'
        },
        'orders': {
            'empty_title': 'في انتظار مبيعاتك الأولى!',
            'empty_desc': 'يمكنك تجربة المساعد الذكي ورؤية كيف يقوم المركز باستقبال الطلبات عوضاً عنك.',
            'try_chat': 'تجربة المحاكي الآن'
        },
        'common': {
            'edit': 'تعديل',
            'save': 'حفظ التعديلات'
        }
    },
    'en': {
        'products': {
            'edit_product': 'Edit Product',
            'edit_success': 'Product updated successfully!',
            'edit_error': 'Error updating product.',
            'image_col': 'Image',
            'no_image': 'No image',
            'empty_title': 'Add your first product to enable AI sales',
            'empty_desc': 'No products to display. Add your products here so the AI assistant can suggest and sell them to your customers.'
        },
        'orders': {
            'empty_title': 'Waiting for your first sales!',
            'empty_desc': 'You can try the AI assistant and see how it receives orders on your behalf.',
            'try_chat': 'Try Simulator Now'
        },
        'common': {
            'edit': 'Edit',
            'save': 'Save Changes'
        }
    },
    'tr': {
        'products': {
            'edit_product': 'Ürünü Düzenle',
            'edit_success': 'Ürün başarıyla güncellendi!',
            'edit_error': 'Ürün güncellenirken hata oluştu.',
            'image_col': 'Resim',
            'no_image': 'Resim Yok',
            'empty_title': 'Yapay zeka satışlarını etkinleştirmek için ilk ürününüzü ekleyin',
            'empty_desc': 'Gösterilecek ürün yok. Yapay zeka asistanının müşterilerinize önermesi ve satması için ürünlerinizi buraya ekleyin.'
        },
        'orders': {
            'empty_title': 'İlk satışlarınızı bekliyoruz!',
            'empty_desc': 'Yapay zeka asistanını deneyebilir ve siparişleri nasıl aldığını görebilirsiniz.',
            'try_chat': 'Simülatörü Şimdi Dene'
        },
        'common': {
            'edit': 'Düzenle',
            'save': 'Değişiklikleri Kaydet'
        }
    }
}

for loc in locales:
    file_path = f"C:/Users/yaman/.gemini/antigravity/playground/chatsmartai/frontend/messages/{loc}.json"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for root_key in ['products', 'orders', 'common']:
            if root_key not in data:
                data[root_key] = {}
            if root_key in data_to_add[loc]:
                for k, v in data_to_add[loc][root_key].items():
                    data[root_key][k] = v
                    
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
print("JSON Locales updated successfully via Python.")
