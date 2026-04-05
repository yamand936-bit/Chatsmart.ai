from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.orm import selectinload
from datetime import date
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.business import Business
from app.models.domain import Order, UsageLog
from app.models.user import User
from app.core.security import get_password_hash
from app.services.stripe_service import create_checkout_session
from app.config.plans import PLANS
from app.core.config import settings
from app.services.settings_service import SettingsService
import stripe
import uuid

router = APIRouter()

class CreateBusinessRequest(BaseModel):
    name: str
    owner_email: EmailStr
    owner_password: str
    business_type: str = "retail"

class UpdateBusinessRequest(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    status: Optional[str] = None

class UpdateBusinessStatusRequest(BaseModel):
    status: str

class SubscribeRequest(BaseModel):
    plan: str
    business_id: uuid.UUID



@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    """Admin-only global metrics endpoint."""
    total_businesses = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    active_businesses = (await db.execute(select(func.count(Business.id)).where(Business.status == "active"))).scalar() or 0
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    total_tokens = (await db.execute(select(func.sum(UsageLog.tokens_used)))).scalar() or 0
    requests_today = (await db.execute(select(func.sum(UsageLog.request_count)).where(UsageLog.date_logged == date.today()))).scalar() or 0
    
    return {
        "status": "ok", 
        "total_businesses": total_businesses, 
        "active_businesses": active_businesses,
        "total_orders": total_orders,
        "total_tokens_used": total_tokens,
        "ai_requests_today": requests_today
    }

@router.get("/businesses_test")
async def get_businesses_test(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    total = await db.scalar(select(func.count()).select_from(Business))
    result = await db.execute(
        select(Business, func.max(User.email), func.sum(UsageLog.tokens_used))
        .join(User, Business.id == User.business_id)
        .outerjoin(UsageLog, Business.id == UsageLog.business_id)
        .where(User.role == "merchant")
        .group_by(Business.id)
        .order_by(Business.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    data = []
    for b, e, t_used in rows:
        data.append({
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "status": b.status,
            "token_limit": b.token_limit,
            "monthly_quota": b.monthly_quota,
            "token_usage": t_used or 0,
            "created_at": b.created_at,
            "owner_email": e
        })
    return {"status": "ok", "data": data, "total": total}

@router.get("/businesses")
async def get_businesses(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    total = await db.scalar(select(func.count()).select_from(Business))
    result = await db.execute(
        select(Business, func.max(User.email), func.sum(UsageLog.tokens_used))
        .join(User, Business.id == User.business_id)
        .outerjoin(UsageLog, Business.id == UsageLog.business_id)
        .where(User.role == "merchant")
        .group_by(Business.id)
        .order_by(Business.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    data = []
    for b, e, t_used in rows:
        data.append({
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "status": b.status,
            "token_limit": b.token_limit,
            "monthly_quota": b.monthly_quota,
            "token_usage": t_used or 0,
            "created_at": b.created_at,
            "owner_email": e
        })
    return {"status": "ok", "data": data, "total": total}

@router.get("/businesses/{business_id}")
async def get_business(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    result = await db.execute(select(Business).options(selectinload(Business.features)).where(Business.id == business_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
        
    telegram = next((f for f in b.features if f.feature_type == "telegram"), None)
    whatsapp = next((f for f in b.features if f.feature_type == "whatsapp"), None)

    return {
        "status": "ok",
        "data": {
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "status": b.status,
            "token_limit": b.token_limit,
            "monthly_quota": b.monthly_quota,
            "created_at": b.created_at,
            "features": {
                "telegram": telegram.config if telegram and telegram.is_active else None,
                "whatsapp": whatsapp.config if whatsapp and whatsapp.is_active else None
            }
        }
    }

@router.put("/businesses/{business_id}")
async def update_business(business_id: uuid.UUID, data: UpdateBusinessRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
        
    if data.name is not None:
        b.name = data.name
    if data.business_type is not None:
        b.business_type = data.business_type
    if data.status is not None:
        b.status = data.status
        
    await db.commit()
    return {"status": "ok", "message": "Business updated successfully"}

@router.patch("/businesses/{business_id}/status")
async def update_business_status(business_id: uuid.UUID, data: UpdateBusinessStatusRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    b = result.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
        
    b.status = data.status
    await db.commit()
    return {"status": "ok", "message": f"Business status updated to {data.status}"}


@router.post("/businesses")
async def create_business(data: CreateBusinessRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    """Admin creates a new business/merchant."""
    result = await db.execute(select(User).where(User.email == data.owner_email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Owner email already registered")
        
    business = Business(name=data.name, business_type=data.business_type)
    db.add(business)
    await db.flush()
    
    merchant_user = User(
        email=data.owner_email,
        hashed_password=get_password_hash(data.owner_password),
        role="merchant",
        business_id=business.id
    )
    db.add(merchant_user)
    await db.commit()
    
    return {
        "status": "ok", 
        "business_id": str(business.id),
        "user_id": str(merchant_user.id)
    }

class FeatureConfigRequest(BaseModel):
    is_active: bool
    config: dict

@router.post("/businesses/{business_id}/features/{feature_type}")
async def configure_business_feature(
    business_id: uuid.UUID,
    feature_type: str,
    data: FeatureConfigRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Admin configures an integration feature (e.g., telegram, whatsapp, instagram) for a business."""
    from app.models.business import BusinessFeature
    
    if feature_type not in ["whatsapp", "telegram", "instagram"]:
        raise HTTPException(status_code=400, detail="Invalid feature_type")

    # Check if business exists
    b_res = await db.execute(select(Business).where(Business.id == business_id))
    if not b_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Business not found")

    result = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.business_id == business_id,
            BusinessFeature.feature_type == feature_type
        )
    )
    feature = result.scalar_one_or_none()
    
    if feature:
        feature.is_active = data.is_active
        feature.config = data.config
    else:
        feature = BusinessFeature(
            business_id=business_id,
            feature_type=feature_type,
            is_active=data.is_active,
            config=data.config
        )
        db.add(feature)
        
    await db.commit()
    return {"status": "ok", "message": f"Feature {feature_type} configured successfully."}

@router.post("/subscribe")
async def create_subscription_checkout(data: SubscribeRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    valid_plans = ["free", "pro", "enterprise"]
    if data.plan not in valid_plans:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
        
    result = await db.execute(select(Business).where(Business.id == data.business_id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
        
    token_limit_str = await SettingsService.get(db, f"{data.plan}_tokens")
    token_limit = int(token_limit_str) if token_limit_str else -1
    
    # If the retrieved token limit is extraordinarily high (representing infinity), we store -1 instead
    if token_limit >= 999999999:
        token_limit = -1
        
    business.plan_name = data.plan
    business.token_limit = token_limit
    business.subscription_status = "active"

    await db.commit()
    return {
        "status": "ok",
        "message": f"Upgraded to {data.plan} plan"
    }


from fastapi import Request

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type") if isinstance(event, dict) else event.type
    
    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        business_id_str = session.get("metadata", {}).get("business_id")
        plan_name = session.get("metadata", {}).get("plan")
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        
        if business_id_str and plan_name in PLANS:
            try:
                b_id = uuid.UUID(business_id_str)
                result = await db.execute(select(Business).where(Business.id == b_id))
                b = result.scalar_one_or_none()
                if b:
                    b.plan_name = plan_name
                    b.subscription_status = "active"
                    b.stripe_customer_id = customer_id
                    b.stripe_subscription_id = subscription_id
                    b.token_limit = PLANS[plan_name]["tokens"] or 999999999 # Use large int for unlimited
                    await db.commit()
            except Exception as e:
                print(f"Error handling checkout completed: {e}")
                
    elif event_type == "customer.subscription.deleted":
        subscription = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        sub_id = subscription.get("id")
        
        if sub_id:
            result = await db.execute(select(Business).where(Business.stripe_subscription_id == sub_id))
            b = result.scalar_one_or_none()
            if b:
                b.plan_name = "free"
                b.subscription_status = "canceled"
                b.stripe_subscription_id = None
                b.token_limit = PLANS["free"]["tokens"]
                await db.commit()
                
    return {"status": "success"}
