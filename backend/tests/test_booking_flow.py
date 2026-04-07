import asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Logging in Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        admin_cookie = client.cookies.get("access_token")
        
        bus_payload = {
            "name": f"booking_{uuid.uuid4().hex[:6]}",
            "owner_email": f"book_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        print("Creating business...")
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        b_data = res.json()
        
        client.cookies.clear()
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        merchant_cookie = client.cookies.get("access_token")

        # Create a service
        service_payload = {
            "name": "Consultation",
            "price": 100.0,
            "description": "Test service",
            "item_type": "service",
            "duration": 60,
            "is_active": True
        }
        res = await client.post(f"{BASE_URL}/merchant/products", json=service_payload, cookies={"access_token": merchant_cookie})

        # Test Turkish pricing
        print("\n=== Sending Turkish ===")
        chat_payload = {
            "customer_platform": "web",
            "external_id": "test_booking_user",
            "content": "fiyat soracağım"
        }
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        print("TURKISH RESPONSE:", res.json().get("ai_response"))

        # Test Arabic booking
        print("\n=== Sending Arabic ===")
        chat_payload["content"] = "tamam بدي"
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        data = res.json()
        print("ARABIC RESPONSE:", data.get("ai_response"))
        print("INTENT:", data.get("intent"))

if __name__ == "__main__":
    asyncio.run(main())
