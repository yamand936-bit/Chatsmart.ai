from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from typing import Any, Union

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

import uuid

def create_access_token(subject: Union[str, Any], role: str, business_id: str = None) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Generate unique JWT ID
    jti = str(uuid.uuid4())
    to_encode = {"exp": expire, "sub": str(subject), "role": role, "jti": jti}
    if business_id:
        to_encode["business_id"] = str(business_id)
        
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt
