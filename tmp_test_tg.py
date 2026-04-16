import httpx
try:
    url = "https://api.telegram.org/botAAHJzN73UpY4Jh-8VwxB9bKFh_r5oNuUCGw:8712864523/getMe"
    res = httpx.get(url, timeout=5.0)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Exception happened: {str(e)}")
