import asyncio
import httpx
import uuid
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

BASE_URL = "http://localhost:8000/api"

async def run_simulation():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Admin login to create business
        print(">> 1. Authenticating & Creating Business...")
        await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        
        bus_payload = {
            "name": f"omni_sim_{uuid.uuid4().hex[:6]}",
            "owner_email": f"merchant_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload)
        b_id = res.json().get("business_id")
        
        # 2. Login as merchant
        client.cookies.clear()
        login_res = await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        print(f"Merchant logged in: {login_res.status_code}")

        # 3. Create a test product
        print(">> 2. Creating Test Product in CRM...")
        prod_payload = {
            "name": "ساعة ذكية فاخرة",
            "description": "ساعة رياضية تتحمل الماء والغبار",
            "price": 250,
            "stock_quantity": 50,
            "item_type": "product"
        }
        res = await client.post(f"{BASE_URL}/merchant/products", json=prod_payload)
        product_id = res.json().get("id")
        print(f"Product created: {product_id}")

        # 4. Activate TikTok and Telegram
        # 4. Activate TikTok and Telegram via API
        print(">> 3. Activating Integrations via API...")
        # Since Telegram validates bot_token with Telegram natively via /getMe, we will mock it differently
        # Actually our local docker backend does reach out to Telegram unless INTEGRATIONS_MODE=mock
        # Let's hit the endpoints
        tt_feat = await client.post(f"{BASE_URL}/merchant/features/tiktok", json={"action": "save", "access_token": "mock_tt", "app_secret": "mock_secret"})
        
        # Telegram will fail verification if token is invalid, but for the sake of test we'll rely on our mock API behavior (if configured)
        tg_feat = await client.post(f"{BASE_URL}/merchant/features/telegram", json={"action": "save", "bot_token": "mock_bot", "webhook_secret": "mock_sec"})
        print(f"Features API responses TT:{tt_feat.status_code} TG:{tg_feat.status_code}")

        # 5. SIMULATE TIKTOK COMMENT
        print(">> 4. [TIKTOK] Simulating Customer Comment...")
        import hmac
        import hashlib
        import json
        
        tt_comment = {
            "event": "comment.create",
            "comment": {
                "author_id": "tt_user_99",
                "text": "بكم هذا المنتج؟",
                "comment_id": "cmt_123",
                "item_id": "vid_456"
            }
        }
        raw_body_bytes = json.dumps(tt_comment).encode('utf-8')
        mock_secret = "mock_secret"
        expected_hash = hmac.new(mock_secret.encode('utf-8'), raw_body_bytes, hashlib.sha256).hexdigest()

        tt_res = await client.post(
            f"{BASE_URL}/integrations/tiktok/{b_id}/webhook", 
            content=raw_body_bytes, 
            headers={"x-tt-signature": expected_hash, "Content-Type": "application/json", "X-Forwarded-For": "127.0.0.1"}
        )
        print(f"TikTok Webhook response: {tt_res.status_code} -> {tt_res.text}")

        # 6. SIMULATE TELEGRAM CHAT
        print(">> 5. [TELEGRAM] Simulating Customer Message...")
        tg_payload = {
            "message": {
                "message_id": 1,
                "from": {"id": 123456},
                "chat": {"id": 123456},
                "text": "أريد شراء الساعة الذكية الآن"
            }
        }
        tg_msg_res = await client.post(
            f"{BASE_URL}/integrations/telegram/{b_id}/webhook",
            json=tg_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "mock_sec", "X-Forwarded-For": "127.0.0.1"}
        )
        print(f"Telegram Msg Webhook response: {tg_msg_res.status_code} -> {tg_msg_res.text}")

        print("Waiting 3 seconds for AI to process...")
        await asyncio.sleep(3)

        # 7. SIMULATE TELEGRAM INLINE BUTTON CLICK (Order Confirmation)
        print(">> 6. [TELEGRAM] Simulating user clicking Buy button")
        tg_cb_payload = {
            "callback_query": {
                "id": "query_1",
                "from": {"id": 123456},
                "message": {"message_id": 2, "chat": {"id": 123456}},
                "data": f"buy:{product_id}"
            }
        }
        cb_res = await client.post(
            f"{BASE_URL}/integrations/telegram/{b_id}/webhook",
            json=tg_cb_payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "mock_sec", "X-Forwarded-For": "127.0.0.1"}
        )
        print(f"Callback Webhook response: {cb_res.status_code} -> {cb_res.text}")

        # 8. VERIFY ORDER IN DB
        print(">> 7. Verifying Order Creation in Database...")
        db_res = await client.get(f"{BASE_URL}/merchant/dashboard")
        data = db_res.json()
        orders = data.get("recent_orders", [])
        
        if len(orders) > 0:
             print(f"\n SUCCESS! Order was natively created across channels:")
             print(f"Order ID: {orders[0]['id']}")
             print(f"Status: {orders[0]['status']}")
             print(f"Amount: ${orders[0]['total_amount']}")
             print(f"Product: {orders[0]['payload'].get('product_name')}")
        else:
             print("\n FAILED! No orders found for business.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
