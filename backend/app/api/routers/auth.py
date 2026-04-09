from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import PlainTextResponse
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
    # Strictly use SET NX EX logic to ensure expiry only happens on initial creation, preventing reset bypasses.
    await redis_client.set(key, 0, nx=True, ex=window)
    current_count = await redis_client.incr(key)
    if current_count > limit:
        minutes = getattr(window, "minutes", window // 60)
        raise HTTPException(status_code=429, detail=f"Too many requests. Please try again after {minutes} minutes.")

@router.post("/login")
async def login(response: Response, request: Request, data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Rate Limiting: 10 attempts / 2 minutes
    client_ip = request.client.host if request.client else "unknown"
    await check_rate_limit(f"rate_limit:login:{client_ip}", 10, 120)
    
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
    return {"status": "ok", "message": "Successfully logged in", "access_token": access_token}

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

from jose import jwt, JWTError

@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")

    try:
        # Decode without verifying expiration so we can renew an expired token
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            is_blacklisted = await redis_client.get(f"blacklist:{jti}")
            if is_blacklisted:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token blacklisted")
            # Blacklist old token immediately to prevent reuse
            await redis_client.setex(f"blacklist:{jti}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "true")

        # Create new token
        new_token = create_access_token(
            subject=payload.get("sub"),
            role=payload.get("role"),
            business_id=payload.get("business_id")
        )
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=settings.IS_PRODUCTION,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )
        return {"status": "ok", "message": "Token refreshed successfully"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.get("/instagram/login")
async def instagram_login_redirect(payload: TokenPayload = Depends(get_current_user_payload)):
    """Provides the URL for the frontend to redirect the user to Meta's OAuth screen"""
    client_id = settings.META_APP_ID if hasattr(settings, 'META_APP_ID') and settings.META_APP_ID else (settings.INSTAGRAM_APP_ID if hasattr(settings, 'INSTAGRAM_APP_ID') else "MOCK_APP_ID")
    redirect_uri = f"{settings.BACKEND_CORS_ORIGINS[0]}/api/auth/instagram/callback"
    
    import os, base64
    nonce = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    state = nonce
    
    await redis_client.setex(f"ig_state:{nonce}", 600, str(payload.business_id))
    
    oauth_url = (
        f"https://www.facebook.com/v20.0/dialog/oauth?"
        f"client_id={client_id}&"
        f"display=page&"
        f"extras={{\"setup\":{{\"channel\":\"IG_API\"}}}}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=token,config_id&"
        f"scope=instagram_basic,instagram_manage_messages,pages_manage_metadata&"
        f"state={state}"
    )
    return {"status": "ok", "url": oauth_url}

import httpx

@router.get("/instagram/callback")
async def instagram_oauth_callback(
    request: Request,
    code: str = None, 
    access_token: str = None, 
    state: str = None, 
    db: AsyncSession = Depends(get_db)):
    """
    Handles the redirect back from Meta.
    Meta's new 'Instagram Direct Login' uses implicit flow or standard code flow.
    We capture the generated token, store it via Admin internal routing or business updates.
    """
    if not state:
         return PlainTextResponse(content="Error: Invalid state parameter", status_code=400)
    
    # Validate CSRF state nonce
    stored_business_id = await redis_client.get(f"ig_state:{state}")
    if not stored_business_id:
         return PlainTextResponse(content="Error: Invalid or expired state parameter", status_code=400)
    
    # Consume the nonce to prevent replay attacks
    await redis_client.delete(f"ig_state:{state}")
    business_id_str = stored_business_id
    
    from app.models.business import BusinessFeature
    
    # If returned as a fragment or query param token
    final_token = access_token
    if not final_token and code:
        # If code flow is used, exchange code for Long Lived Token
        url = "https://graph.facebook.com/v20.0/oauth/access_token"
        params = {
            "client_id": settings.META_APP_ID if hasattr(settings, 'META_APP_ID') and settings.META_APP_ID else (settings.INSTAGRAM_APP_ID if hasattr(settings, 'INSTAGRAM_APP_ID') else "MOCK"),
            "redirect_uri": f"{settings.BACKEND_CORS_ORIGINS[0]}/api/auth/instagram/callback",
            "client_secret": settings.META_APP_SECRET if hasattr(settings, 'META_APP_SECRET') and settings.META_APP_SECRET else (settings.INSTAGRAM_APP_SECRET if hasattr(settings, 'INSTAGRAM_APP_SECRET') else "MOCK"),
            "code": code
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                final_token = res.json().get("access_token")

    if final_token:
        # Store in BusinessFeature
        import uuid
        result = await db.execute(
            select(BusinessFeature).where(
                BusinessFeature.business_id == uuid.UUID(business_id_str),
                BusinessFeature.feature_type == "instagram"
            )
        )
        feature = result.scalar_one_or_none()
        
        config = feature.config if feature else {}
        config["access_token"] = final_token
        # Typically we'd also call /me/accounts to get the page_id and link it, keeping it simple for the hook.
        
        if feature:
            feature.config = config
            feature.is_active = True
        else:
            feature = BusinessFeature(
                business_id=uuid.UUID(business_id_str),
                feature_type="instagram",
                is_active=True,
                config=config
            )
            db.add(feature)
        
        await db.commit()
        return {"status": "success", "message": "Instagram connected successfully. You can close this window."}
    
    return {"status": "error", "message": "Failed to authenticate"}

@router.get("/tiktok/login")
async def tiktok_login_redirect(payload: TokenPayload = Depends(get_current_user_payload)):
    """Provides the URL for the frontend to redirect the user to TikTok's OAuth screen"""
    client_key = settings.TIKTOK_CLIENT_KEY if hasattr(settings, 'TIKTOK_CLIENT_KEY') else "MOCK_TK_KEY"
    redirect_uri = f"{settings.BACKEND_CORS_ORIGINS[0]}/api/auth/tiktok/callback"
    state = str(payload.business_id) 
    
    import os, base64, hashlib
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    
    await redis_client.setex(f"tiktok_auth:{state}", 600, code_verifier)
    
    # TikTok OAuth v2 standard
    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/?"
        f"client_key={client_key}&"
        f"response_type=code&"
        f"scope=user.info.basic,message.send,comment.list,comment.create&"
        f"redirect_uri={redirect_uri}&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"
    )
    return {"status": "ok", "url": oauth_url}

@router.get("/tiktok/callback")
async def tiktok_oauth_callback(
    request: Request,
    code: str = None, 
    state: str = None, 
    db: AsyncSession = Depends(get_db)):
    """
    Handles redirect back from TikTok Auth.
    Exchanges code for access token via TikTok v2 api.
    """
    if not state or not code:
         return PlainTextResponse(content="Error: Invalid state or code parameter", status_code=400)
    
    from app.models.business import BusinessFeature
    final_token = None
    
    code_verifier = await redis_client.get(f"tiktok_auth:{state}") or ""
    
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": settings.TIKTOK_CLIENT_KEY if hasattr(settings, 'TIKTOK_CLIENT_KEY') else "MOCK",
        "client_secret": settings.TIKTOK_CLIENT_SECRET if hasattr(settings, 'TIKTOK_CLIENT_SECRET') else "MOCK",
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{settings.BACKEND_CORS_ORIGINS[0]}/api/auth/tiktok/callback",
        "code_verifier": code_verifier.decode('utf-8') if isinstance(code_verifier, bytes) else code_verifier
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if res.status_code == 200:
            final_token = res.json().get("access_token")

    if final_token:
        result = await db.execute(
            select(BusinessFeature).where(
                BusinessFeature.business_id == state,
                BusinessFeature.feature_type == "tiktok"
            )
        )
        feature = result.scalar_one_or_none()
        
        config = feature.config if feature else {}
        config["access_token"] = final_token
        
        if feature:
            feature.config = config
            feature.is_active = True
        else:
            feature = BusinessFeature(
                business_id=state,
                feature_type="tiktok",
                is_active=True,
                config=config
            )
            db.add(feature)
        await db.commit()
        return {"status": "success", "message": "TikTok connected successfully. You can close this window."}
        
    return {"status": "error", "message": "TikTok Auth Failed"}
