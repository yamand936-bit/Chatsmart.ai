import asyncio
import datetime
import random
import uuid
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.session import async_session_maker
from app.models.user import User
from app.models.business import Business
from app.models.domain import Product, Appointment
from app.core.security import get_password_hash

async def seed_demos():
    async with async_session_maker() as db:
        password_hashed = get_password_hash("demo123")

        # Define Demo accounts
        demos = [
            {
                "email": "retail@demo.com",
                "name": "Luxury Timepieces & Leather",
                "type": "retail",
                "tone": "Sales-driven",
                "bank": {"iban": "SA123456789", "bank_name": "Al Rajhi Bank", "currency": "SAR"},
                "kb": "نحن متجر متخصص في بيع الساعات الفاخرة والمحافظ الجلدية. \nسياسة الاسترجاع: خلال 14 يوم من تاريخ الشراء بشرط عدم الاستخدام.\nالتوصيل: مجاني لجميع المناطق خلال 2-3 أيام عمل.\nتعليمات لك كبائع ذكاء اصطناعي: كن حماسياً وتشجيعياً جداً، ركز على أناقة المنتج وجودته، وإذا طلب العميل ساعة اقترح عليه محفظة تليق بها. دائماً حاول إتمام البيع مباشرة واطلب بيانات الشحن.",
                "item_type": "product",
                "items": [
                    {"name": f"ساعة رولكس كلاسيك - إصدار محدود {i}", "price": 450.0 + (i*10), "desc": "ساعة فاخرة مقاومة للماء مع ضمان سنتين.", "stock": 5} for i in range(1, 13)
                ] + [
                    {"name": f"محفظة جلد طبيعي إيطالي {i}", "price": 50.0 + (i*5), "desc": "محفظة رجالية أنيقة تتسع لـ 10 بطاقات.", "stock": 10} for i in range(1, 14)
                ]
            },
            {
                "email": "dental@demo.com",
                "name": "SmileCare Clinic - عيادة سمايل كير للأسنان",
                "type": "services",
                "tone": "Professional",
                "bank": {"iban": "", "bank_name": "Cash/Card at Clinic", "currency": "USD"},
                "kb": "نحن عيادة أسنان متخصصة. الأطباء المتاحون: د. أحمد، د. سارة، د. خالد.\nساعات العمل: من 10 صباحاً حتى 8 مساءً يومياً عدا الجمعة.\nسياسة العيادة: يتم تأكيد الموعد مبدئياً ويجب الحضور قبل 15 دقيقة. لا توجد رسوم على الإلغاء قبل 24 ساعة.\nتعليمات مساعد الذكاء الاصطناعي: كن لطيفاً ومهنياً جداً. اسأل المريض عن نوع الألم أو الخدمة التي يحتاجها، ثم اعرض عليه أقرب وقت متاح وقم بجدولة الموعد مباشرة.",
                "item_type": "service",
                "items": [
                    {"name": "خلع ضرس / سن (Tooth Extraction)", "price": 20.0, "desc": "خلع آمن بدون ألم مع تخدير موضعي.", "duration": 30},
                    {"name": "تلبيس أسنان زيركون", "price": 50.0, "desc": "تركيبة زيركون ألمانية عالية الجودة.", "duration": 60},
                    {"name": "تنظيف الجير وتلميع الأسنان", "price": 15.0, "desc": "إزالة الرواسب الجيرية وتلميع المينا.", "duration": 30},
                    {"name": "حشوة تجميلية للأسنان الأمامية", "price": 30.0, "desc": "حشوة ليزر مطابقة للون السن الطبيعي.", "duration": 45},
                    {"name": "تبييض الأسنان بالليزر (الجلسة)", "price": 70.0, "desc": "تبييض سريع وآمن بتقنية زووم.", "duration": 60},
                    {"name": "تقويم الأسنان (دفعة أولى)", "price": 200.0, "desc": "تركيب أقواس التقويم وبدء الخطة العلاجية.", "duration": 90},
                    {"name": "علاج عصب جذور", "price": 80.0, "desc": "بواسطة أحدث الأجهزة الروتاري لمنع الألم.", "duration": 60},
                    {"name": "استشارة طبية مجانية", "price": 0.0, "desc": "فحص طبي مبدئي وتصوير أشعة إن لزم الأمر.", "duration": 15},
                ]
            },
            {
                "email": "hotel@demo.com",
                "name": "Blue Waves Boutique Hotel - فندق أمواج",
                "type": "services",
                "tone": "Friendly",
                "bank": {"iban": "TR987654321", "bank_name": "Garanti Bank", "currency": "USD"},
                "kb": "أهلاً بك في فندق أمواج الصغير المطل على البحر.\nمعلومات الفندق: يقع الفندق على الشاطئ مباشرة. تسجيل الدخول الساعة 2 مساءً، والخروج الساعة 12 ظهراً.\nالإفطار مجاني لجميع النزلاء.\nسياسة الإلغاء: استرداد كامل إذا تم الإلغاء قبل 72 ساعة.\nشروط: لا يُسمح باصطحاب الحيوانات الأليفة.\nتعليمات لك كبائع ذكاء اصطناعي: تحدث بلهجة مرحبة ودافئة جداً كأنك تستقبل ضيفاً في منزلك. اسألهم عن تواريخ إقامتهم وعدد الأشخاص وبناء عليه رشح الغرفة المناسبة.",
                "item_type": "service",
                "items": [
                    {"name": "غرفة مفردة قياسية (مع إفطار)", "price": 80.0, "desc": "غرفة مريحة لشخص واحد.", "duration": 1440},
                    {"name": "غرفة مزدوجة إطلالة على الحديقة", "price": 120.0, "desc": "مثالية للأزواج، تتسع لشخصين.", "duration": 1440},
                    {"name": "غرفة مزدوجة إطلالة مباشرة على البحر", "price": 150.0, "desc": "إطلالة بانورامية رائعة مع شرفة خاصة.", "duration": 1440},
                    {"name": "جناح عائلي 1 غرفة وصالة", "price": 250.0, "desc": "يتسع حتى 4 أشخاص، مطبخ صغير.", "duration": 1440},
                    {"name": "فيلا شاطئية بمسابح خاصة", "price": 400.0, "desc": "خصوصية تامة، مثالية للعرسان.", "duration": 1440},
                ]
            }
        ]

        from datetime import date, timedelta
        current_date_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        start_of_month = current_date_utc.replace(day=1, hour=0, minute=0, second=0)
        
        # Determine number of days in the current month
        next_month = start_of_month.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        total_days = last_day_of_month.day
        
        for demo in demos:
            # 1. Check or Create User
            u_res = await db.execute(select(User).where(User.email == demo["email"]))
            user = u_res.scalar_one_or_none()
            if not user:
                user = User(
                    email=demo["email"],
                    hashed_password=password_hashed
                )
                db.add(user)
                await db.flush() # get id
            
            # 2. Check or Create Business
            b_res = await db.execute(select(Business).where(Business.name == demo["name"]))
            business = b_res.scalar_one_or_none()
            if not business:
                business = Business(
                    name=demo["name"],
                    business_type=demo["type"],
                    ai_tone=demo["tone"],
                    knowledge_base=demo["kb"],
                    bank_details=demo["bank"],
                    status="active",
                    plan_name="pro"
                )
                db.add(business)
                await db.flush()
                
                # Assign user to this business
                user.business_id = business.id
                db.add(user)
                await db.flush()
                
            # Clear existing items to avoid duplicates on bad runs
            await db.execute(Product.__table__.delete().where(Product.business_id == business.id))
            
            # Add Items
            for idx, item in enumerate(demo["items"]):
                images = [
                    "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
                    "https://images.unsplash.com/photo-1546868871-7041f2a55e12",
                    "https://images.unsplash.com/photo-1622434641406-a158123450f9"
                ]
                img = images[idx % len(images)] if demo["item_type"] == "product" else None
                p = Product(
                    business_id=business.id,
                    name=item["name"],
                    item_type=demo["item_type"],
                    price=item["price"],
                    description=item["desc"],
                    stock=item.get("stock", 0),
                    duration=item.get("duration"),
                    is_active=True,
                    image_url=img
                )
                db.add(p)

            # Generate 40% appointments for Dental
            if "Dental" in demo["name"]:
                await db.execute(Appointment.__table__.delete().where(Appointment.business_id == business.id))
                
                # 40% of standard 8 slots a day x total days (approx roughly 3 appointments per day)
                for day_offset in range(total_days):
                    dt = start_of_month + timedelta(days=day_offset)
                    if dt.weekday() == 4: # Skip Fridays
                        continue
                        
                    # Let's say 4 appointments per active day
                    for hour in [10, 12, 14, 16]:
                        if random.random() < 0.40: # 40% chance to book
                            # Mock Customer
                            from app.models.domain import Customer
                            c_id = uuid.uuid4()
                            cust = Customer(
                                id=c_id,
                                business_id=business.id,
                                platform="system",
                                external_id=f"seed_{c_id}",
                                name=f"Mocker {random.randint(100, 999)}",
                                phone=f"+96650000{random.randint(1000, 9999)}"
                            )
                            db.add(cust)
                            await db.flush()
                            
                            start_t = dt.replace(hour=hour)
                            end_t = start_t + timedelta(minutes=45)
                            appt = Appointment(
                                business_id=business.id,
                                customer_id=cust.id,
                                title=f"Dental Service - Dr. {random.choice(['Ahmed', 'Sara', 'Khalid'])}",
                                start_time=start_t,
                                end_time=end_t,
                                status="confirmed",
                                notes="Seeded booked appointment"
                            )
                            db.add(appt)
                            
            await db.commit()
            print(f"✅ Seeded {demo['name']} successfully.")

if __name__ == "__main__":
    asyncio.run(seed_demos())
