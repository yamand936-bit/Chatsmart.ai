import asyncio
import httpx
import uuid
import sys

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Logging in Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        admin_cookie = client.cookies.get("access_token")
        
        bus_payload = {
            "name": f"tele_{uuid.uuid4().hex[:6]}",
            "owner_email": f"tele_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        if res.status_code >= 400:
            print("Failed to create business:", res.text)
            return
        b_id = res.json().get("business_id")
        print(f"Business Created: {b_id}")

        print("\nConfiguring Telegram via Merchant Endpoint...")
        client.cookies.clear()
        
        # Login as merchant
        await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        
        # Test 1: Fake Validation
        print("Testing Fake Validation...")
        v_res = await client.post(f"{BASE_URL}/merchant/features/telegram", json={
            "bot_token": "invalid_1234",
            "webhook_secret": "mysecret",
            "action": "validate"
        })
        print("Validation Result (should fail):", v_res.json())
        
        # Test 2: Save anyway manually to test webhook
        s_res = await client.post(f"{BASE_URL}/merchant/features/telegram", json={
            "bot_token": "valid_mock_12345",
            "webhook_secret": "SUPERSAFESECRET",
            "action": "save"
        })
        print("\nForce Saved Feature:", s_res.json())

        print("\n=== Simulate Telegram Webhook ===")
        payload = {
            "update_id": 123456,
            "message": {
                "message_id": 1,
                "from": {"id": 999111, "is_bot": False, "first_name": "TestUser"},
                "chat": {"id": 999111, "type": "private"},
                "date": 1712312312,
                "text": "I want to buy a product"
            }
        }
        
        url = f"{BASE_URL}/integrations/telegram/{b_id}/webhook"

        print("\n[TEST A] Missing Secret Token (Should 401)")
        res1 = await client.post(url, json=payload)
        print("Response:", res1.status_code, res1.text)

        print("\n[TEST B] Invalid IP block header (Should 403)")
        res2 = await client.post(url, json=payload, headers={
             "X-Telegram-Bot-Api-Secret-Token": "SUPERSAFESECRET",
             "X-Forwarded-For": "8.8.8.8"
        })
        print("Response:", res2.status_code, res2.text)

        print("\n[TEST C] Valid Setup (Localhost proxy allowed)")
        res3 = await client.post(url, json=payload, headers={
             "X-Telegram-Bot-Api-Secret-Token": "SUPERSAFESECRET",
             "X-Forwarded-For": "testclient"
        })
        print("Response:", res3.status_code, res3.json() if res3.status_code == 200 else res3.text)


if __name__ == "__main__":
    asyncio.run(main())
