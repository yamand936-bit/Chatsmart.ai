import requests

def test():
    # Test WITHOUT cookie
    res1 = requests.get("https://smartchat-ai.org/api/auth/me")
    print("NO COOKIE:", res1.json())
    
    # Test WITH invalid cookie
    res2 = requests.get("https://smartchat-ai.org/api/auth/me", cookies={"access_token": "eyJhbxxxx"})
    print("INVALID COOKIE:", res2.json())

test()
