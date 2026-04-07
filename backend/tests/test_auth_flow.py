import asyncio
import httpx
import uuid
from urllib.parse import urlparse, parse_qs

BASE_URL = "http://localhost:8000/api"

async def test_tiktok_pkce_flow():
    async with httpx.AsyncClient() as client:
        # 1. Admin login to create business
        await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        
        bus_payload = {
            "name": f"auth_test_{uuid.uuid4().hex[:6]}",
            "owner_email": f"auth_{uuid.uuid4().hex[:6]}@test.com",
            "owner_password": "secure123"
        }
        res = await client.post(f"{BASE_URL}/admin/businesses", json=bus_payload)
        b_id = res.json().get("business_id")
        print(f"Created Test Business: {b_id}")

        # 2. Login as the merchant
        client.cookies.clear()
        await client.post(f"{BASE_URL}/auth/login", data={"username": bus_payload["owner_email"], "password": bus_payload["owner_password"]})
        
        # 3. Hit /tiktok/login to get URL and trigger PKCE state creation
        print("\n--- TikTok Login Redirect ---")
        login_res = await client.get(f"{BASE_URL}/auth/tiktok/login")
        data = login_res.json()
        print("Response:", data)
        
        url = data.get("url")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        print("\nExtracted OAuth Params sent to TikTok:")
        print(f"  state (business_id): {params.get('state')[0]}")
        print(f"  code_challenge: {params.get('code_challenge')[0]}")
        print(f"  code_challenge_method: {params.get('code_challenge_method')[0]}")
        
        # 4. Simulate the TikTok Callback (TikTok redirects the user back with '?code=...')
        print("\n--- Simulating Callback from TikTok ---")
        state = params.get('state')[0]
        cb_res = await client.get(f"{BASE_URL}/auth/tiktok/callback?code=fake_tiktok_auth_code_123&state={state}")
        
        print("Callback Response Status:", cb_res.status_code)
        print("Callback Response JSON/Text:", cb_res.text)

if __name__ == "__main__":
    asyncio.run(test_tiktok_pkce_flow())
