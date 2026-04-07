import asyncio
import httpx
import uuid
import sys

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login admin to create business
        print("Logging in Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        admin_cookie = client.cookies.get("access_token")
        
        bus_payload = {
            "name": f"multilang_{uuid.uuid4().hex[:6]}",
            "owner_email": f"multi_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        print("Creating business...")
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        b_data = res.json()
        
        # Login Merchant
        client.cookies.clear()
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        merchant_cookie = client.cookies.get("access_token")

        # Test Turkish
        print("\n=== Sending Turkish ===")
        chat_payload = {
            "customer_platform": "web",
            "external_id": "test_multi_user",
            "content": "Merhaba!"
        }
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        print("TURKISH RESPONSE:", res.json().get("ai_response"))

        # Test Arabic
        print("\n=== Sending Arabic ===")
        chat_payload["content"] = "ما هي المنتجات التي تبيعها؟"
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        print("ARABIC RESPONSE:", res.json().get("ai_response"))

if __name__ == "__main__":
    asyncio.run(main())
