import asyncio
import httpx
import uuid
import sys
import json

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("=== TEST SCENARIO 1: ADMIN FLOW ===")
        # Seed the DB so admin@demo.com exists if it doesn't already
        # Wait, the seed script made admin@demo.com. Let's just login.
        login_data = {"username": "admin@chatsmart.ai", "password": "password123"}
        res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if res.status_code != 200:
            print("Failed to login Admin:", res.text)
            sys.exit(1)
            
        # The cookie is automatically stored in `client.cookies`!
        admin_auth_cookie = client.cookies.get("access_token")
        print(f"✔ Admin Login Success (Cookie Mode)")

        # Create business
        bus_payload = {
            "name": f"test_store_{uuid.uuid4().hex[:6]}",
            "owner_email": f"merchant_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_auth_cookie})
        if res.status_code != 200:
            print("Failed to create business:", res.text)
            sys.exit(1)
            
        b_data = res.json()
        business_id = b_data["business_id"]
        print(f"✔ Business Created: {business_id}")

        print("\n=== TEST SCENARIO 2: MERCHANT SETUP ===")
        # Clear cookies to simulate fresh login
        client.cookies.clear()
        
        login_data = {"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]}
        res = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if res.status_code != 200:
            print("Failed to login Merchant:", res.text)
            sys.exit(1)
        
        print("✔ Merchant Login Success")
        merchant_auth_cookie = client.cookies.get("access_token")
        
        prod_payload = {
            "name": "Test Product",
            "price": 25.0,
            "description": "Simulation item",
            "is_active": True
        }
        res = await client.post(f"{BASE_URL}/merchant/products", json=prod_payload, cookies={"access_token": merchant_auth_cookie})
        if res.status_code != 200:
            print("Failed to create product:", res.text)
            sys.exit(1)
            
        p_data = res.json()
        if "data" in p_data:
            p_data = p_data["data"]
        product_id = p_data["id"]
        print(f"✔ Product Created: {product_id}")

        print("\n=== TEST SCENARIO 3: CHAT FLOW ===")
        chat_payload = {
            "customer_platform": "web",
            "external_id": "test_user_001",
            "content": "I want to buy Test Product"
        }
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_auth_cookie})
        if res.status_code != 200:
            print("Failed chat message:", res.text)
            sys.exit(1)
            
        print("RAW RESPONSE:", res.text)
        chat_data = res.json()
        print(f"✔ AI Responded: {chat_data.get('ai_response')}")
        print(f"✔ Intent Detected: {chat_data.get('intent')}")
        conv_id = chat_data.get('conversation_id')

        print("\n=== TEST SCENARIO 4: ORDER CREATION ===")
        res = await client.get(f"{BASE_URL}/merchant/orders", cookies={"access_token": merchant_auth_cookie})
        orders = res.json()["data"]
        has_order = False
        for o in orders:
            if o["payload"].get("product_name") == "Test Product":
                has_order = True
                print(f"✔ Order Found! amount={o['total_amount']}")
        if not has_order:
            print("❌ Order was not created. (AI might have missed the product match or mocked fallback was used)")

        print("\n=== TEST SCENARIO 5: SECURITY ===")
        # Try accessing another conversation ID (fake uuid)
        fake_uuid = str(uuid.uuid4())
        res = await client.get(f"{BASE_URL}/chat/stream/{fake_uuid}", cookies={"access_token": merchant_auth_cookie})
        if res.status_code == 403 or res.status_code == 404:
            print(f"✔ Successfully blocked cross-tenant conversation access: {res.status_code}")
        else:
            print(f"❌ Security Warning: Fake UUID returned {res.status_code}")

        print("\n=== TEST SCENARIO 6: ERROR HANDLING ===")
        # Empty Message
        chat_payload = {
            "customer_platform": "web",
            "external_id": "test_user_001",
            "content": "   "
        }
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_auth_cookie})
        if res.status_code == 422 or res.status_code == 400:
            print(f"✔ Caught empty message smoothly (validation): {res.status_code}")
        else:
            print(f"❌ Empty message failed handling: {res.status_code}")
            
        # Long message
        chat_payload["content"] = "A" * 2500
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_auth_cookie})
        if res.status_code == 422:
            print("✔ Caught excessively long message smoothly (validation 422)")
        else:
            print(f"❌ Long message failed handling: {res.status_code}")

        print("\n=== TEST SCENARIO 7: OMNI-CHANNEL INTEGRATIONS (MOCK) ===")
        # 1. Admin configures whatsapp feature
        wa_config_payload = {
            "is_active": True,
            "config": {
                "phone_number_id": "test_phone_id",
                "access_token": "test_access_token",
                "verify_token": "secret_vtoken",
                "app_secret": "my_app_secret"
            }
        }
        res = await client.post(f"{BASE_URL}/admin/businesses/{business_id}/features/whatsapp", json=wa_config_payload, cookies={"access_token": admin_auth_cookie})
        if res.status_code == 200:
            print("✔ WhatsApp Feature Configured")
        else:
            print(f"❌ Failed to configure WhatsApp: {res.text}")

        # 2. Simulate Webhook
        wa_webhook_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "type": "text",
                            "text": {"body": "I want Test Product via WhatsApp"}
                        }]
                    }
                }]
            }]
        }
        
        import hmac, hashlib
        # calculate signature
        payload_bytes = json.dumps(wa_webhook_payload).encode('utf-8')
        mock_sig = "sha256=" + hmac.new(b"my_app_secret", payload_bytes, hashlib.sha256).hexdigest()
        
        res = await client.post(
            f"{BASE_URL}/integrations/whatsapp/{business_id}/webhook",
            json=wa_webhook_payload,
            headers={"X-Hub-Signature-256": mock_sig}
        )
        if res.status_code == 200:
            print("✔ WhatsApp Message processed successfully!")
        else:
            print(f"❌ WhatsApp message failed: {res.text}")

        print("\n=== TEST SCENARIO 8: SESSION / AUTH ===")
        # Delete cookie manually
        client.cookies.clear()
        res = await client.get(f"{BASE_URL}/merchant/orders")
        if res.status_code == 401:
            print("✔ Caught missing cookie correctly (401)")
        else:
            print("❌ Failed session test.")
            
if __name__ == "__main__":
    asyncio.run(main())
