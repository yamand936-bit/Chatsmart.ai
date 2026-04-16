import requests

def test_login():
    login_payload = {
        "username": "admin@chatsmart.ai",
        "password": "admin123456"
    }
    
    res1 = requests.post("https://smartchat-ai.org/api/auth/login", data=login_payload)
    print("STATUS:", res1.status_code)
    print("RESPONSE:", res1.text)
    
test_login()
