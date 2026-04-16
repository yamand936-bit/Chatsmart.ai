from jose import jwt
from datetime import datetime, timedelta, timezone

# Emulate their code exactly
expire = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=60)
to_encode = {"exp": expire, "sub": "test", "role": "admin", "jti": "foo"}

secret = "test_secret"
token = jwt.encode(to_encode, secret, algorithm="HS256")

print("Encoded token:", token)

try:
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    print("Decoded payload:", payload)
except Exception as e:
    print("Decode error:", type(e), e)
