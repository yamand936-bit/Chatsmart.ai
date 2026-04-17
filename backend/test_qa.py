import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
import os
import sys

from sqlalchemy.future import select
from sqlalchemy import func, text

from dotenv import load_dotenv
load_dotenv()

# Setup path so we can import 'app' module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.api.deps import redis_client
from app.db.session import async_session_maker as async_session
from app.models.business import Business
from app.models.user import User
from app.models.domain import UsageLog
from app.core.security import get_password_hash

async def run_tests():
    print("Starting QA Protocol...")
    transport = ASGITransport(app=app)
    
    # SETUP MOCK DB DATA
    async with async_session() as db:
        # Create an admin user if not exists
        res = await db.execute(select(User).where(User.email == "admin@chatsmart.ai"))
        admin_user = res.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                id=uuid.uuid4(),
                email="admin@chatsmart.ai",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)
        else:
            admin_user.hashed_password = get_password_hash("admin123")
            
        # Create 4 test merchants
        created_merchants = []
        for i in range(4):
            res = await db.execute(select(User).where(User.email == f"merchant{i}@test.com"))
            merchant_user = res.scalar_one_or_none()
            if not merchant_user:
                b = Business(id=uuid.uuid4(), name=f"Test Biz {i}")
                db.add(b)
                merchant_user = User(
                    id=uuid.uuid4(),
                    email=f"merchant{i}@test.com",
                    hashed_password=get_password_hash("password123"),
                    role="merchant",
                    business_id=b.id
                )
                db.add(merchant_user)
                created_merchants.append(merchant_user)
            else:
                created_merchants.append(merchant_user)
        await db.commit()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Kill-Switch Test (Maintenance Mode)
        print("\n--- 1. Kill-Switch Test (Maintenance Mode) ---")
        await redis_client.set("system:maintenance", "1")
        
        # Login Merchant
        m_resp = await client.post("/api/auth/login", data={"username": "merchant0@test.com", "password": "password123"})
        merchant_status = m_resp.status_code
        print(f"Merchant Login Status: {merchant_status} (Expected 503)")
        
        # Login Admin
        a_resp = await client.post("/api/auth/login", data={"username": "admin@chatsmart.ai", "password": "admin123"})
        admin_status = a_resp.status_code
        print(f"Admin Login Status: {admin_status} (Expected 200)")
        admin_token = a_resp.json().get("access_token") if admin_status == 200 else None
        
        await redis_client.delete("system:maintenance")
        
        if merchant_status == 503 and admin_status == 200:
            print("=> TEST 1: PASS")
        else:
            print("=> TEST 1: FAIL")
            
        # 2. Burn Rate Test (Unit Economics Validation)
        print("\n--- 2. Burn Rate Test (Unit Economics) ---")
        biz_id_for_burn = created_merchants[0].business_id
        async with async_session() as db:
            # Inject huge token usage
            import datetime
            today = datetime.date.today()
            # Clear old logs
            from sqlalchemy import delete
            await db.execute(delete(UsageLog).where(UsageLog.business_id == biz_id_for_burn))
            log = UsageLog(
                id=uuid.uuid4(),
                business_id=biz_id_for_burn,
                date_logged=today,
                request_count=1000,
                tokens_used=10000000 # 10 Million Tokens -> ~$50 cost
            )
            db.add(log)
            # Ensure merchant is on free plan ($0 MRR)
            b_res = await db.execute(select(Business).where(Business.id == biz_id_for_burn))
            b = b_res.scalar_one()
            b.plan_name = "free"
            await db.commit()
            
        # Call GET /businesses
        biz_resp = await client.get("/api/admin/businesses", headers={"Cookie": f"access_token={admin_token}"})
        businesses_data = biz_resp.json().get("data", [])
        target_b = next((x for x in businesses_data if x["id"] == str(biz_id_for_burn)), None)
        
        print(f"Calculated MRR: ${target_b['mrr']}")
        print(f"Calculated API Cost: ${target_b['api_cost']}")
        print(f"Profit Margin: ${target_b['profit_margin']}")
        
        if target_b and target_b["profit_margin"] < 0:
            print("=> TEST 2: PASS")
        else:
            print("=> TEST 2: FAIL")
            
            
        # 3. Blast Radius Test (Batch Operations Safety)
        print("\n--- 3. Blast Radius Test (Batch Operations Safety) ---")
        # Ensure all merchants on free plan
        async with async_session() as db:
            await db.execute(text("UPDATE businesses SET plan_name = 'free'"))
            await db.commit()
            
        target_ids = [str(created_merchants[0].business_id), str(created_merchants[1].business_id)]
        
        batch_resp = await client.post("/api/admin/businesses/batch/plan", 
            json={"business_ids": target_ids, "new_plan": "enterprise"},
            headers={"Cookie": f"access_token={admin_token}"}
        )
        print(f"Batch Plan Update Status: {batch_resp.status_code}")
        
        # Verify
        biz_resp2 = await client.get("/api/admin/businesses", headers={"Cookie": f"access_token={admin_token}"})
        final_data = biz_resp2.json().get("data", [])
        
        enterprise_count = sum(1 for b in final_data if b["plan_name"] == "enterprise")
        other_plans_count = sum(1 for b in final_data if b["plan_name"] == "free")
        
        print(f"Total Enterprise plans: {enterprise_count} (Expected 2)")
        print(f"Total Free plans: {other_plans_count} (Expected total-2)")
        
        is_safe = True
        for b in final_data:
            if b["id"] in target_ids:
                if b["plan_name"] != "enterprise": is_safe = False
            else:
                if b["plan_name"] == "enterprise": is_safe = False
                
        if enterprise_count == 2 and is_safe:
            print("=> TEST 3: PASS")
        else:
            print("=> TEST 3: FAIL")

if __name__ == "__main__":
    asyncio.run(run_tests())
