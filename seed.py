import asyncio
import sys
import uuid
import datetime
import json
sys.path.append('/app')
from app.db.session import async_session_maker
from app.models.business import Business, BusinessFeature
from app.models.user import User
from app.models.domain import Customer, Message, Conversation, TemplateMessage, UsageLog, Category, Product, Order, OrderItem, Appointment, Staff
from app.core.security import get_password_hash
from sqlalchemy import select, delete

async def clear_db(db):
    try:
        print('Wiping cleanly...')
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
        monthly_quota=10000
    )
    db.add(b1)
    await db.commit()
    await db.refresh(b1)
    
    u = User(id=uuid.uuid4(), email='retail@lxt.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b1.id)
    db.add(u)
    
    # Add Categories
    c1 = Category(id=uuid.uuid4(), business_id=b1.id, name='Luxury Watches')
    c2 = Category(id=uuid.uuid4(), business_id=b1.id, name='Leather Wallets')
    db.add(c1)
    db.add(c2)
    await db.commit()
    
    # Add Products
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, category_id=c1.id, name='Rolex Submariner Replica', description='High quality luxury watch', price=299.99, stock_quantity=15, image_url='https://images.unsplash.com/photo-1523170335258-f5ed11844a49'))
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, category_id=c1.id, name='Omega Speedmaster', description='Sleek titanium build', price=499.00, stock_quantity=5, image_url='https://images.unsplash.com/photo-1548690098-b80c32d431c9'))
    db.add(Product(id=uuid.uuid4(), business_id=b1.id, category_id=c2.id, name='Bifold Classic Wallet', description='Genuine Italian Leather', price=45.00, stock_quantity=100, image_url='https://images.unsplash.com/photo-1627123424574-724758594e93'))
    
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b1.id, feature_type='whatsapp', config={'token': ''}, is_active=True))
    await db.commit()

async def create_dental(db):
    b2 = Business(
        id=uuid.uuid4(),
        name='Smile Bright Dental',
        business_type='medical',
        status='active',
        plan_name='enterprise',
        message_credits=50000
    )
    db.add(b2)
    await db.commit()
    u = User(id=uuid.uuid4(), email='drsmith@smile.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b2.id)
    db.add(u)
    
    # Staff for dental
    db.add(Staff(id=uuid.uuid4(), business_id=b2.id, name='Dr. Sarah Jenkins', role='Orthodontist', calendar_id='doc1'))
    db.add(Staff(id=uuid.uuid4(), business_id=b2.id, name='Dr. Mark Williams', role='General Dentist', calendar_id='doc2'))
    db.add(Staff(id=uuid.uuid4(), business_id=b2.id, name='Dr. Emily Chen', role='Pediatric Dentist', calendar_id='doc3'))
    
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b2.id, feature_type='telegram', config={'token': ''}, is_active=True))
    await db.commit()

async def create_hotel(db):
    b3 = Business(
        id=uuid.uuid4(),
        name='Seaside Retreat Villa',
        business_type='services',
        status='active',
        plan_name='starter',
        message_credits=5000
    )
    db.add(b3)
    await db.commit()
    u = User(id=uuid.uuid4(), email='manager@seaside.com', hashed_password=get_password_hash('123456'), role='merchant', business_id=b3.id)
    db.add(u)
    
    # Products as Rooms
    c = Category(id=uuid.uuid4(), business_id=b3.id, name='Suites & Rooms')
    db.add(c)
    await db.commit()
    db.add(Product(id=uuid.uuid4(), business_id=b3.id, category_id=c.id, name='Deluxe Ocean View', description='Spacious room with balcony facing the beach', price=150.00, stock_quantity=10, image_url='https://images.unsplash.com/photo-1499955085172-a104c9463ece'))
    db.add(Product(id=uuid.uuid4(), business_id=b3.id, category_id=c.id, name='Standard Garden View', description='Quiet and cozy', price=80.00, stock_quantity=20, image_url='https://images.unsplash.com/photo-1566665797739-1674de7a421a'))
    
    db.add(BusinessFeature(id=uuid.uuid4(), business_id=b3.id, feature_type='telegram', config={'token': ''}, is_active=True))
    await db.commit()

async def main():
    async with async_session_maker() as db:
        await clear_db(db)
        await create_retail(db)
        await create_dental(db)
        await create_hotel(db)
        print('Seed complete!')

asyncio.run(main())