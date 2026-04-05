import requests

API_URL = "http://localhost:8000/api"

print("--- Testing Context ---")
print("1. Logging in...")

session = requests.Session()
login_data = {
    "username": "admin@chatsmart.ai",
    "password": "AdminUser123!"
}
res = session.post(f"{API_URL}/auth/login", data=login_data)
print(f"Login Status: {res.status_code}")
print(f"Login Response: {res.text}")
print(f"Cookies Set: {session.cookies.get_dict()}")

if res.status_code == 200:
    print("\n2. Fetching /me...")
    me_res = session.get(f"{API_URL}/auth/me")
    print(f"Me Status: {me_res.status_code}")
    print(f"Me Response: {me_res.text}")
else:
    print("\nLogin failed. Can't test /me.")
