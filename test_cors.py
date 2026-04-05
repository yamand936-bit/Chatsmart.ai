import httpx
res = httpx.post(
    "http://localhost:8000/api/auth/login",
    data={"username": "admin@chatsmart.ai", "password": "AdminUser123!"},
    headers={"Origin": "http://localhost:3000"}
)
print("Response Status:", res.status_code)
print("Response CORS Headers:", {k: v for k, v in res.headers.items() if "access-control" in k.lower()})
