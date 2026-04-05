import httpx

print("\n--- FRONTEND REQUEST TRACE ---")

# Send request WITHOUT cookies
with httpx.Client() as client:
    res = client.get("http://localhost:8000/api/auth/me")
    print(f"WITHOUT Cookies -> Expect 401. Got: {res.status_code}")

# Send request WITH cookies (Simulating step 2)
with httpx.Client() as client:
    res = client.post(
        "http://localhost:8000/api/auth/login",
        data={"username": "admin@chatsmart.ai", "password": "AdminUser123!"}
    )
    raw_set_cookie = res.headers.get("set-cookie")
    print(f"\nRAW Set-Cookie Header: {raw_set_cookie}")
    
    # Check attributes
    has_http_only = "HttpOnly" in raw_set_cookie if raw_set_cookie else False
    has_path = "Path=/" in raw_set_cookie if raw_set_cookie else False
    has_samesite = "SameSite=lax" in raw_set_cookie.lower() if raw_set_cookie else False
    has_secure = "Secure" in raw_set_cookie if raw_set_cookie else False
    print(f"HttpOnly: {has_http_only}")
    print(f"Path=/: {has_path}")
    print(f"SameSite=Lax: {has_samesite}")
    print(f"Secure: {has_secure}")
    
    me_res = client.get("http://localhost:8000/api/auth/me")
    print(f"Me Endpoint Status: {me_res.status_code}")
