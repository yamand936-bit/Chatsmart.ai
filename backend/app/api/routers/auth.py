from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user_payload, TokenPayload, redis_client
from app.schemas.auth import UserOut
from app.core.config import settings

router = APIRouter()

async def check_rate_limit(key: str, limit: int, window: int):
    """Simple sliding window rate limit using Redis"""
    pipe = redis_client.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, window)
    results = await pipe.execute()

    current_count = results[0]
    if current_count > limit:
        raise HTTPException(status_code=429, detail="Too many requests")

@router.post("/login")
async def login(response: Response, request: Request, data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Rate Limiting: 5 attempts / 15 minutes
    client_ip = request.client.host if request.client else "unknown"
    await check_rate_limit(f"rate_limit:login:{client_ip}", 5, 900)
    
    result = await db.execute(select(User).where(User.email == data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        
    access_token = create_access_token(
        subject=str(user.id),
        role=user.role,
        business_id=str(user.business_id) if user.business_id else None
    )
    
    # Store token in HTTP-Only Cookie.
    # secure=True only in production — allows local HTTP dev without TLS.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.IS_PRODUCTION,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return {"status": "ok", "message": "Successfully logged in"}

@router.post("/logout")
async def logout(response: Response, payload: TokenPayload = Depends(get_current_user_payload)):
    if payload.jti:
        # Blacklist the JTI in Redis for the remaining token lifetime.
        await redis_client.setex(
            f"blacklist:{payload.jti}",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "true",
        )
        
    response.delete_cookie("access_token", path="/")
    return {"status": "ok", "message": "Successfully logged out"}

@router.get("/me", response_model=UserOut)
async def get_me(payload: TokenPayload = Depends(get_current_user_payload), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
