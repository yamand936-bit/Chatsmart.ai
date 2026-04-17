import requests

def run_tests():
    print("Testing Missing Features Locally...")
    session = requests.Session()
    
    auth_res = session.post("http://localhost:8000/api/auth/login", data={"username": "admin@chatsmart.ai", "password": "admin123"})
    if auth_res.status_code != 200:
        print("Auth failed:", auth_res.text)
        return
        
    token = auth_res.json().get('access_token')
    headers = {'Cookie': f'access_token={token}'}
    
    print("\n[1] Testing Lifeline Monitor (Webhook Health in Metrics)...")
    m_res = session.get("http://localhost:8000/api/admin/metrics", headers=headers)
    metrics = m_res.json()
    webhook_rate = metrics.get("webhook_delivery_rate")
    print(f"-> Webhook Delivery Rate: {webhook_rate}%")
    if webhook_rate is not None:
        print("-> STATUS: PASS")
    else:
        print("-> STATUS: FAIL")

    print("\n[2] Testing Global Announcement Banner...")
    ann_post = session.post("http://localhost:8000/api/admin/system/announcement", json={"message": "🚨 CRITICAL SYSTEM UPDATE IN 5 MINS!"}, headers=headers)
    print("-> Admin POST /system/announcement:", ann_post.json())
    
    ann_get = session.get("http://localhost:8000/api/system/system/announcement")
    print("-> Public GET /system/announcement length:", len(ann_get.json()["message"]))
    if "CRITICAL SYSTEM UPDATE IN 5 MINS!" in ann_get.json()["message"]:
        print("-> STATUS: PASS")
    else:
        print("-> STATUS: FAIL")

    print("\n[3] Testing Last Active Column...")
    bz = session.get("http://localhost:8000/api/admin/businesses", headers=headers).json()
    data = bz.get("data", [])
    if data:
        has_last_active = 'last_active' in data[0]
        val = data[0].get('last_active')
        print(f"-> Found 'last_active' key: {has_last_active} (Value: {val})")
        if has_last_active:
            print("-> STATUS: PASS")
        else:
            print("-> STATUS: FAIL")
    else:
        print("-> Unverifiable (No businesses found)")

if __name__ == "__main__":
    run_tests()
