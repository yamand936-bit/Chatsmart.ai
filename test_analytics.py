import requests

BASE_URL = "http://localhost:8000/api"

# 1. Login as Admin
login_data = {"username": "admin@chatsmart.ai", "password": "password123"}
res = requests.post(f"{BASE_URL}/auth/login", data=login_data)
if res.status_code != 200:
    print("Failed to login Admin:", res.text)
    exit(1)

cookies = {"access_token": res.cookies.get("access_token")}

# 2. Fetch Analytics
print("\n--- Analytics Overview ---")
overview_res = requests.get(f"{BASE_URL}/analytics/overview", cookies=cookies)
print(overview_res.json())

print("\n--- Analytics by Business ---")
business_res = requests.get(f"{BASE_URL}/analytics/by-business", cookies=cookies)
print(business_res.json())

print("\n--- Analytics by Provider ---")
provider_res = requests.get(f"{BASE_URL}/analytics/by-provider", cookies=cookies)
print(provider_res.json())
