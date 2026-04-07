import asyncio
import httpx
import uuid
import hmac
import hashlib

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Logging in Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        admin_cookie = client.cookies.get("access_token")
        
        bus_payload = {
            "name": f"tiktok_{uuid.uuid4().hex[:6]}",
            "owner_email": f"tiktok_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        if res.status_code >= 400:
            print("Failed to create business:", res.text)
            return
        b_id = res.json().get("business_id")
        print(f"Business Created: {b_id}")

        client.cookies.clear()
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        merchant_cookie = client.cookies.get("access_token")

        print("Enabling TikTok Feature...")
        feature_payload = {
            "is_active": True,
            "config": {"app_secret": "mysecret", "access_token": "mytoken"}
        }
        f_res = await client.post(f"{BASE_URL}/admin/businesses/{b_id}/features/tiktok", json=feature_payload, cookies={"access_token": admin_cookie})
        if f_res.status_code >= 400:
             print("Failed to enable feature:", f_res.text)

        print("\n=== Simulate TikTok Comment ===")
        import json
        payload = {
            "event": "comment.create",
            "comment": {
                "author_id": "tiktok_user123",
                "text": "How much is this?",
                "comment_id": f"comment_{uuid.uuid4().hex[:5]}",
                "item_id": "video_999"
            }
        }
        
        body_bytes = json.dumps(payload).encode('utf-8')
        sig = hmac.new("mysecret".encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
        
        res = await client.post(
            f"{BASE_URL}/integrations/tiktok/{b_id}/webhook",
            content=body_bytes,
            headers={"x-tt-signature": sig, "Content-Type": "application/json"}
        )
        print("WEBHOOK RESPONSE:", res.json())

if __name__ == "__main__":
    asyncio.run(main())
