import asyncio
import httpx
import uuid
import hmac
import hashlib
import json

BASE_URL = "http://localhost:8000/api"

async def test_whatsapp_interactive():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(">> 1. Authenticating Admin...")
        res = await client.post(f"{BASE_URL}/auth/login", data={"username": "admin@chatsmart.ai", "password": "password123"})
        client.cookies = res.cookies
        
        print(">> 2. Creating Business and Product...")
        b = await client.post(f"{BASE_URL}/admin/businesses", json={"name":"Store WhatsApp", "owner_email": f"wa_{uuid.uuid4().hex[:6]}@w.com", "owner_password":"123", "plan_name":"free", "business_type":"retail", "language":"ar"})
        b_id = b.json().get("business_id")
        
        imp_res = await client.post(f"{BASE_URL}/admin/impersonate/{b_id}")
        imp_token = imp_res.json().get("token")
        headers = {"Authorization": f"Bearer {imp_token}"}
        
        wa_config = {
            "app_secret": "mywasecret",
            "verify_token": "mywaverify",
            "access_token": "mywatoken",
            "phone_number_id": "123456789"
        }
        await client.post(f"{BASE_URL}/admin/businesses/{b_id}/features/whatsapp", json={"is_active": True, "config": wa_config}, cookies={"access_token": res.cookies.get("access_token")})
        
        # Create a product
        pA_res = await client.post(f"{BASE_URL}/merchant/products", json={"name": "WA_Prod", "price": 99.99, "image_url": "https://example.com/image.jpg", "description": "Test product"}, headers=headers)
        if pA_res.status_code != 200:
            print("Product failed:", pA_res.text)
        prod_id = pA_res.json().get("id")
        print(f"Product created: {prod_id}")
        
        print(">> 3. Ensuring WhatsApp Customer exists...")
        # Fire a normal text webhook to create the customer record
        wa_payload_text = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "123", "phone_number_id": "123456789"},
                        "contacts": [{"profile": {"name": "Test User"}, "wa_id": "987654321"}],
                        "messages": [{
                            "from": "987654321",
                            "id": f"wamid.{uuid.uuid4().hex}",
                            "timestamp": "1600000000",
                            "type": "text",
                            "text": {"body": "Hi, I want to buy WA_Prod"}
                        }]
                    }
                }]
            }]
        }
        
        body_bytes = json.dumps(wa_payload_text).encode('utf-8')
        sig = "sha256=" + hmac.new("mywasecret".encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
        
        await client.post(f"{BASE_URL}/integrations/whatsapp/{b_id}/webhook", content=body_bytes, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})
        await asyncio.sleep(2)
        
        print(">> 4. Simulating Interactive 'Buy Now' click...")
        wa_payload_interactive = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {"display_phone_number": "123", "phone_number_id": "123456789"},
                        "contacts": [{"profile": {"name": "Test User"}, "wa_id": "987654321"}],
                        "messages": [{
                            "from": "987654321",
                            "id": f"wamid.{uuid.uuid4().hex}",
                            "timestamp": "1600000001",
                            "type": "interactive",
                            "interactive": {
                                "type": "button_reply",
                                "button_reply": {
                                    "id": f"buy:{prod_id}",
                                    "title": "🛒 تأكيد الشراء"
                                }
                            }
                        }]
                    }
                }]
            }]
        }
        
        body_bytes = json.dumps(wa_payload_interactive).encode('utf-8')
        sig = "sha256=" + hmac.new("mywasecret".encode('utf-8'), body_bytes, hashlib.sha256).hexdigest()
        
        await client.post(f"{BASE_URL}/integrations/whatsapp/{b_id}/webhook", content=body_bytes, headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"})
        
        print(">> 5. Verifying Order Creation...")
        orders_req = await client.get(f"{BASE_URL}/merchant/stats", headers=headers)
        orders_today = orders_req.json().get("orders_today", 0)
        
        if orders_today > 0:
            print(f"✅ SUCCESS! Order was natively created for {prod_id}. Total Orders: {orders_today}")
        else:
            print("❌ FAILED! Order was not created via Interactive Message.")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_whatsapp_interactive())
