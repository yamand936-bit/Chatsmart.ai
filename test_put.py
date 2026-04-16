import requests

def test_settings_update():
    session = requests.Session()
    session.post("https://smartchat-ai.org/api/auth/login", data={"username": "admin@chatsmart.ai", "password": "admin123"})
    
    payload = {
        "knowledge_base": "",
        "bank_details": {"bank_name": "", "iban": ""},
        "primary_color": "#2563eb",
        "logo_url": "",
        "notification_email": "",
        "notification_telegram": "12345:TEST",
        "staff_members": []
    }
    
    res = session.put("https://smartchat-ai.org/api/merchant/settings", json=payload)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)

test_settings_update()
