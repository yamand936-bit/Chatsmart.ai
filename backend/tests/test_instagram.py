import asyncio
import httpx
import uuid
import hmac
import hashlib
import json

BASE_URL = "http://localhost:8000/api"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Logging in Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        admin_cookie = client.cookies.get("access_token")
        
        bus_payload = {
            "name": f"instab__{uuid.uuid4().hex[:6]}",
            "owner_email": f"ig_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload, cookies={"access_token": admin_cookie})
        if res.status_code >= 400:
            print("Failed to create business:", res.text)
            return
        b_id = res.json().get("business_id")
        print(f"Business Created: {b_id}")

        print("Enabling Instagram Feature...")
        feature_payload = {
            "is_active": True,
            "config": {
                "app_secret": "myigsecret", 
                "access_token": "myigtoken",
                "page_id": "IG_PAGE_123"
            }
        }
        f_res = await client.post(f"{BASE_URL}/admin/businesses/{b_id}/features/instagram", json=feature_payload, cookies={"access_token": admin_cookie})
        if f_res.status_code >= 400:
             print("Failed to enable feature:", f_res.text)

        print("\n=== Simulate Instagram Messaging ===\n")
        # Simulate Meta WhatsApp/Instagram Graph Payload
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "IG_PAGE_123",
                    "time": 1712312312,
                    "messaging": [
                        {
                            "sender": {"id": "ig_user_456"},
                            "recipient": {"id": "IG_PAGE_123"},
                            "timestamp": 1712312312,
                            "message": {
                                "mid": f"mid.{uuid.uuid4().hex}",
                                "text": "Can you tell me more about this?",
                                # Simulating an image
                                "attachments": [
                                    {
                                        "type": "image",
                                        "payload": {
                                            "url": "https://raw.githubusercontent.com/danielgatis/rembg/master/examples/car-1.jpg"
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        
        body_bytes = json.dumps(payload).encode('utf-8')
        
        # Meta's signature format: sha256=HMAC
        expected_hash = hmac.new("myigsecret".encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
        sig = f"sha256={expected_hash}"
        
        res = await client.post(
            f"{BASE_URL}/integrations/instagram/{b_id}/webhook",
            content=body_bytes,
            headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"}
        )
        print("WEBHOOK RESPONSE:", res.json())

if __name__ == "__main__":
    asyncio.run(main())
