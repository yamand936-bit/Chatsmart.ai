import asyncio
import httpx
import uuid
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

BASE_URL = "http://localhost:8000/api"

async def test_cross_tenant():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(">> 1. Authenticating Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        client.cookies = res.cookies
        
        print(">> 2. Creating Business A and Business B...")
        bA = await client.post(f"{BASE_URL}/admin/businesses", json={"name":"Store A", "owner_email":f"a{uuid.uuid4().hex[:6]}@a.com", "owner_password":"123", "plan_name":"free", "business_type":"retail", "language":"ar"}, cookies={"access_token": res.cookies.get("access_token")})
        bB = await client.post(f"{BASE_URL}/admin/businesses", json={"name":"Store B", "owner_email":f"b{uuid.uuid4().hex[:6]}@b.com", "owner_password":"123", "plan_name":"free", "business_type":"retail", "language":"ar"}, cookies={"access_token": res.cookies.get("access_token")})
        id_A = bA.json().get("business_id")
        id_B = bB.json().get("business_id")
        
        print(f"Business A: {id_A}, Business B: {id_B}")
        
        print(">> 3. Impersonating Business B and creating a product...")
        await client.post(f"{BASE_URL}/admin/impersonate/{id_B}", cookies={"access_token": res.cookies.get("access_token")})
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tf.write(b"mock image")
            tf.flush()
            with open(tf.name, "rb") as f:
                prod = await client.post(f"{BASE_URL}/merchant/products", data={"name": "Tenant B Product", "price": "100.0"}, files={"image": f})
        os.remove(tf.name)
        prod_id_B = prod.json().get("id")
        print(f"Product from Business B created: {prod_id_B}")
        
        print(">> 4. Attacking Telegram Webhook of Business A with Product B (C2 Fix Verification)...")
        # Ensure telegram feature is active for Business A first
        await client.post(f"{BASE_URL}/admin/impersonate/{id_A}", cookies={"access_token": res.cookies.get("access_token")})
        await client.post(f"{BASE_URL}/merchant/features/telegram", json={"action": "save", "bot_token": "mock_bot", "webhook_secret": "mock_sec"})
        
        tg_cb_payload = {
            "callback_query": {
                "id": "query_1",
                "from": {"id": 123456},
                "message": {"message_id": 2, "chat": {"id": 123456}},
                "data": f"buy:{prod_id_B}"
            }
        }
        cb_res = await client.post(
            f"{BASE_URL}/integrations/telegram/{id_A}/webhook",
            json=tg_cb_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "mock_sec", "X-Forwarded-For": "127.0.0.1"}
        )
        print(f"Webhook executed: {cb_res.status_code}")
        
        print(">> 5. Verifying Order wasn't created in Business A...")
        db_res = await client.get(f"{BASE_URL}/merchant/dashboard")
        orders = db_res.json().get("recent_orders", [])
        
        if len(orders) == 0:
            print("✅ SUCCESS: C2 Vulnerability Closed. Cross-tenant product fetch was prevented.")
        else:
            print(f"❌ FAILED: C2 Vulnerability Open! Found order: {orders[0]}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_cross_tenant())
