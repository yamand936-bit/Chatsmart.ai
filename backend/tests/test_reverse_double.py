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
            "name": f"double_{uuid.uuid4().hex[:6]}",
            "owner_email": f"double_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        print("Creating business...")
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        
        client.cookies.clear()
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        merchant_cookie = client.cookies.get("access_token")

        # Test Turkish
        print("\n=== TR ===")
        chat_payload = {
            "customer_platform": "web",
            "external_id": "test_double_user",
            "content": "merhaba, nasılsın?"
        }
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        print("TURKISH RESPONSE:", res.json().get("ai_response"))

        # Test Arabic
        print("\n=== AR ===")
        chat_payload["content"] = "أريد حجز موعد"
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        print("ARABIC RESPONSE:", res.json().get("ai_response"))

        # Test Turkish again
        print("\n=== TR (Return) ===")
        chat_payload["content"] = "tamam, yarın saat 3 uygun mu?"
        res = await client.post(f"{BASE_URL}/chat/message", json=chat_payload, cookies={"access_token": merchant_cookie})
        data = res.json()
        print("TURKISH RESPONSE 2:", data.get("ai_response"))

if __name__ == "__main__":
    asyncio.run(main())
