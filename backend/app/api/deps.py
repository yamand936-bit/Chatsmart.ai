from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.config import settings
from pydantic import BaseModel
import uuid
from redis.asyncio import Redis, ConnectionPool

# Redis client for token blacklisting and rate limiting
pool = ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True, max_connections=50)
redis_client = Redis(connection_pool=pool)

class TokenPayload(BaseModel):
    sub: str
    role: str
    business_id: str | None = None
    jti: str | None = None

async def get_current_user_payload(request: Request) -> TokenPayload:
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        
    def validate_token_sync(t):
        if not t: return None
        try:
            return jwt.decode(t, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None

    payload = validate_token_sync(token)

    # Fallback to cookie gracefully to prevent infinite front-end loops if Bearer token in state expires
    if not payload:
        cookie_token = request.cookies.get("access_token")
        if cookie_token and cookie_token != token:
            payload = validate_token_sync(cookie_token)
            token = cookie_token

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated or token expired",
        )

    token_data = TokenPayload(**payload)
    
    # Check if the token is blacklisted in Redis
    if token_data.jti:
        is_blacklisted = await redis_client.exists(f"blacklist:{token_data.jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
            
    return token_data

async def get_current_admin(payload: TokenPayload = Depends(get_current_user_payload)) -> TokenPayload:
    if payload.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return payload

async def get_merchant_tenant(payload: TokenPayload = Depends(get_current_user_payload)) -> uuid.UUID:
    """
    Core Multi-Tenancy Enforcement.
    Extracts the business_id from the authenticated user token context.
    If the user is not associated with a business or not a merchant, raises an error.
    """
    if payload.role != "merchant" or not payload.business_id:
        raise HTTPException(status_code=403, detail="Merchant business context missing or invalid role")
    return uuid.UUID(payload.business_id)
