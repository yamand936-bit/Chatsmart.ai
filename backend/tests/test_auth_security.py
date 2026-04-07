import asyncio
import httpx
import uuid
import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

BASE_URL = "http://localhost:8000/api"

async def test_auth_security():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(">> 1. Authenticating Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        client.cookies = res.cookies
        
        print(">> 2. Attacking /instagram/callback with raw business_id (C1 Fix Verification)...")
        # Attacker tries to inject a known business_id directly into the state parameter
        attacker_business_id = str(uuid.uuid4())
        attack_res = await client.get(
            f"{BASE_URL}/auth/instagram/callback",
            params={"state": attacker_business_id, "access_token": "malicious_token"}
        )
        
        print(f"Attack Response Status: {attack_res.status_code}")
        print(f"Attack Response Body: {attack_res.text}")
        
        if attack_res.status_code == 400:
            print("✅ SUCCESS: C1 Vulnerability Closed. Attack rejected.")
        else:
            print("❌ FAILED: C1 Vulnerability still open!")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_auth_security())
