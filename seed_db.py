import asyncio
import sys
import uuid
import datetime
import json
sys.path.append('/app')

from app.db.session import async_session_maker
from app.models.business import Business, BusinessFeature
from app.models.user import User
from app.models.domain import Product, Appointment, Customer
from app.models.bot_flow import BotFlow
from app.core.security import get_password_hash
from sqlalchemy import select, delete

async def clear_db(db):
    try:
        print('Wiping all businesses...')
        await db.execute(delete(Business))
        await db.commit()
    except Exception as e:
        print('Clear failed:', e)

async def create_retail(db):
    b1 = Business(
        id=uuid.uuid4(),
        name='LuxTime Watches & Wallets',
        business_type='retail',
        status='active',
        plan_name='pro',
        message_credits=10000,
        monthly_quota=10000,
        language='ar',
        ai_tone='Professional'
    )
    db.add(b1)
    await db.commit()
    await db.refresh(b1)
    
    u = User(id=uuid.uuid4(), email='admin@luxtime.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b1.id)
    db.add(u)
    
    # Add Products
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, name='Rolex Submariner Replica', description='ساعة يد فاخرة بجودة ممتازة', price=299.99, image_url='https://images.unsplash.com/photo-1523170335258-f5ed11844a49'))
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, name='Omega Speedmaster', description='ساعة أنيقة من التيتانيوم', price=499.00, image_url='https://images.unsplash.com/photo-1548690098-b80c32d431c9'))
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, name='Classic Leather Wallet', description='محفظة جلد طبيعي كلاسيكية', price=45.00, image_url='https://images.unsplash.com/photo-1627123424574-724758594e93'))
    
    # Feature
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b1.id, feature_type='telegram', config={'token': ''}, is_active=True))
    
    # Bot Flow
    flow = BotFlow(id=uuid.uuid4(), business_id=b1.id, name='Welcome Flow', is_active=True, rules=[{'condition': 'always', 'action': 'send_message', 'message': 'أهلاً بك في متجر الساعات والجزادين! كيف يمكننا مساعدتك؟'}])
    db.add(flow)
    await db.commit()

async def create_dental(db):
    b2 = Business(
        id=uuid.uuid4(),
        name='Smile Bright Dental Clinic',
        business_type='medical',
        status='active',
        plan_name='enterprise',
        message_credits=50000,
        monthly_quota=50000,
        language='ar',
        ai_tone='Empathetic'
    )
    db.add(b2)
    await db.commit()
    await db.refresh(b2)
    u = User(id=uuid.uuid4(), email='drsmith@smileclinic.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b2.id)
    db.add(u)
    
    db.add(Product(id=uuid.uuid4(), business_id=b2.id, item_type='service', name='General Checkup', description='فحص شامل للأسنان', price=50.0, duration=30))
    db.add(Product(id=uuid.uuid4(), business_id=b2.id, item_type='service', name='Teeth Whitening', description='تبييض الأسنان بالليزر', price=150.0, duration=60))
    
    c_dental = Customer(id=uuid.uuid4(), business_id=b2.id, platform='telegram', external_id='dummy_patient', name='مريض تجريبي', phone='+971501234567')
    db.add(c_dental)
    await db.commit()

    # Appointments (Instead of Staff model, we map staff details inside appointments)
    now = datetime.datetime.now()
    db.add(Appointment(id=uuid.uuid4(), business_id=b2.id, customer_id=c_dental.id, title='Consultation', start_time=now + datetime.timedelta(days=1), end_time=now + datetime.timedelta(days=1, minutes=30), staff_name='د. أحمد خليل', notes='كشفية عامة'))
    db.add(Appointment(id=uuid.uuid4(), business_id=b2.id, customer_id=c_dental.id, title='Root Canal', start_time=now + datetime.timedelta(days=2), end_time=now + datetime.timedelta(days=2, hours=1), staff_name='د. سارة عثمان', notes='عملية سحب عصب'))
    db.add(Appointment(id=uuid.uuid4(), business_id=b2.id, customer_id=c_dental.id, title='Whitening', start_time=now + datetime.timedelta(days=3), end_time=now + datetime.timedelta(days=3, minutes=45), staff_name='د. يوسف النجار', notes='تبييض أسنان'))
    
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b2.id, feature_type='telegram', config={'token': ''}, is_active=True))
    
    flow = BotFlow(id=uuid.uuid4(), business_id=b2.id, name='Dental Triage', is_active=True, rules=[{'condition': 'always', 'action': 'send_message', 'message': 'مرحباً، أنت تتواصل مع عيادة طب الأسنان. هل تود حجز موعد مع أحد أطبائنا؟'}])
    db.add(flow)
    await db.commit()

async def create_hotel(db):
    b3 = Business(
        id=uuid.uuid4(),
        name='Seaside Retreat Villa',
        business_type='services',
        status='active',
        plan_name='pro',
        message_credits=10000,
        monthly_quota=10000,
        language='ar',
        ai_tone='Friendly'
    )
    db.add(b3)
    await db.commit()
    await db.refresh(b3)
    u = User(id=uuid.uuid4(), email='manager@seasidehotel.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b3.id)
    db.add(u)
    
    # Products as Rooms
    db.add(Product(id=uuid.uuid4(), business_id=b3.id, name='Deluxe Ocean View Room', description='غرفة فاخرة مُطلة على البحر', price=150.00, image_url='https://images.unsplash.com/photo-1499955085172-a104c9463ece'))
    db.add(Product(id=uuid.uuid4(), business_id=b3.id, name='Standard Garden View', description='غرفة قياسية مُطلة على الحديقة', price=80.00, image_url='https://images.unsplash.com/photo-1566665797739-1674de7a421a'))
    db.add(Product(id=uuid.uuid4(), business_id=b3.id, name='Presidential Suite', description='جناح رئاسي فاخر للتجربة الأفضل', price=350.00, image_url='https://images.unsplash.com/photo-1582719478250-c89cae4dc85b'))
    
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b3.id, feature_type='telegram', config={'token': ''}, is_active=True))
    
    flow = BotFlow(id=uuid.uuid4(), business_id=b3.id, name='Hotel Concierge', is_active=True, rules=[{'condition': 'always', 'action': 'send_message', 'message': 'مرحباً في فندقنا الصغير على البحر! هل تود الاستفسار عن الغرف المتاحة أو الأسعار؟'}])
    db.add(flow)
    await db.commit()

async def main():
    async with async_session_maker() as db:
        await clear_db(db)
        await create_retail(db)
        await create_dental(db)
        await create_hotel(db)
        print('Wipe and Seed complete!')

asyncio.run(main())
