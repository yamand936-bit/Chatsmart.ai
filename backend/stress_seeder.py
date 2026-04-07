import asyncio
import random
import uuid
import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure python can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_session_maker
from app.models.business import Business
from app.models.domain import Order, Product, Customer

async def seed_stress_data():
    async with async_session_maker() as db:
        res = await db.execute(select(Business).limit(1))
        business = res.scalar_one_or_none()
        
        if not business:
            print("No business found. Cannot stress test.")
            return
            
        print(f"Stress testing for Business: {business.name} (ID: {business.id})")
        
        p_res = await db.execute(select(Product).where(Product.business_id == business.id))
        products = p_res.scalars().all()
        
        if not products:
            print("No products found! Adding some dummy products first...")
            dummy_products = [
                Product(business_id=business.id, name="Wireless Headphones", price=99.99, is_active=True),
                Product(business_id=business.id, name="Smart Watch", price=199.50, is_active=True),
                Product(business_id=business.id, name="Mechanical Keyboard", price=120.00, is_active=True),
            ]
            db.add_all(dummy_products)
            await db.commit()
            products = dummy_products
            
        dummy_customer = Customer(
            business_id=business.id,
            platform="web_simulator",
            external_id=f"stress_{uuid.uuid4()}",
            name="Stress Tester"
        )
        db.add(dummy_customer)
        await db.commit()
        await db.refresh(dummy_customer)
        
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        new_orders = []
        
        for i in range(20):
            days_ago = random.randint(0, 6)
            random_date = today - timedelta(days=days_ago, hours=random.randint(1, 20), minutes=random.randint(0, 59))
            
            p = random.choice(products)
            qty = random.randint(1, 3)
            
            order = Order(
                id=uuid.uuid4(),
                business_id=business.id,
                customer_id=dummy_customer.id,
                status="pending",
                total_amount=p.price * qty,
                payload={
                    "product_name": p.name,
                    "quantity": qty,
                    "address": f"{random.randint(100, 999)} Stress Ave",
                    "phone": f"+1800555{random.randint(1000, 9999)}"
                }
            )
            order.created_at = random_date
            new_orders.append(order)
            
        db.add_all(new_orders)
        await db.commit()
        
        # Flush redis stats cache for analytics API
        from app.api.deps import redis_client
        await redis_client.delete(f"merchant:stats:{business.id}")
        await redis_client.delete(f"merchant:analytics:{business.id}")
        
        print("Successfully seeded 20 stress-test orders distributed across the last 7 days.")
        
if __name__ == "__main__":
    from sqlalchemy.future import select
    asyncio.run(seed_stress_data())
