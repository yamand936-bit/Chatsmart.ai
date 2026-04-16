from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta, timezone
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.business import Business
from app.models.domain import Order, UsageLog, Message, SystemErrorLog
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
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
    
    res = await db.execute(select(Business.plan_name, func.count(Business.id)).group_by(Business.plan_name))
    plan_counts = res.all()
    
    mrr = 0
    churn_rate = 2.5 # Mock churn rate
    plan_distribution = {}
    
    for plan, count in plan_counts:
        plan_str = str(plan).lower()
        if plan_str == "free":
            pass
        elif plan_str == "starter":
            mrr += count * 49
        elif plan_str == "pro":
            mrr += count * 99
        elif plan_str == "enterprise":
            mrr += count * 299
        
        plan_distribution[plan_str] = count

    return {
        "status": "ok", 
        "total_businesses": total_businesses, 
        "active_businesses": active_businesses,
        "total_orders": total_orders,
        "total_tokens_used": total_tokens,
        "ai_requests_today": requests_today,
        "mrr": mrr,
        "churn_rate": churn_rate,
        "plan_distribution": plan_distribution
    }

@router.get("/businesses_test")
async def get_businesses_test(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    total = await db.scalar(select(func.count()).select_from(Business))
    
    avg_resp_subquery = (
        select(Message.business_id, func.avg(Message.response_time).label("avg_resp_time"))
        .where(Message.sender_type == "assistant")
        .group_by(Message.business_id)
        .subquery()
    )

    result = await db.execute(
        select(Business, func.max(User.email), func.sum(UsageLog.tokens_used), avg_resp_subquery.c.avg_resp_time)
        .join(User, Business.id == User.business_id)
        .outerjoin(UsageLog, Business.id == UsageLog.business_id)
        .outerjoin(avg_resp_subquery, Business.id == avg_resp_subquery.c.business_id)
        .where(User.role == "merchant")
        .group_by(Business.id, avg_resp_subquery.c.avg_resp_time)
        .order_by(Business.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    data = []
    for b, e, t_used, avg_time in rows:
        data.append({
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "status": b.status,
            "token_limit": b.token_limit,
            "monthly_quota": b.monthly_quota,
            "token_usage": t_used or 0,
            "plan_name": b.plan_name,
            "created_at": b.created_at,
            "owner_email": e,
            "avg_response_time": float(avg_time) if avg_time else 0.0
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
    
    avg_resp_subquery = (
        select(Message.business_id, func.avg(Message.response_time).label("avg_resp_time"))
        .where(Message.sender_type == "assistant")
        .group_by(Message.business_id)
        .subquery()
    )

    result = await db.execute(
        select(Business, func.max(User.email), func.sum(UsageLog.tokens_used), avg_resp_subquery.c.avg_resp_time)
        .join(User, Business.id == User.business_id)
        .outerjoin(UsageLog, Business.id == UsageLog.business_id)
        .outerjoin(avg_resp_subquery, Business.id == avg_resp_subquery.c.business_id)
        .where(User.role == "merchant")
        .group_by(Business.id, avg_resp_subquery.c.avg_resp_time)
        .order_by(Business.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.all()
    data = []
    for b, e, t_used, avg_time in rows:
        data.append({
            "id": b.id,
            "name": b.name,
            "business_type": b.business_type,
            "status": b.status,
            "token_limit": b.token_limit,
            "monthly_quota": b.monthly_quota,
            "token_usage": t_used or 0,
            "plan_name": b.plan_name,
            "created_at": b.created_at,
            "owner_email": e,
            "avg_response_time": float(avg_time) if avg_time else 0.0
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

@router.post("/impersonate/{business_id}")
async def impersonate_merchant(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    merchant_user_result = await db.execute(select(User).where(User.business_id == business_id, User.role == "merchant"))
    merchant_user = merchant_user_result.scalars().first()
    
    if not merchant_user:
        raise HTTPException(status_code=404, detail="No merchant user found for this business")
        
    access_token = create_access_token(
        subject=str(merchant_user.id),
        role="merchant",
        business_id=str(merchant_user.business_id)
    )
    return {"status": "ok", "token": access_token}

@router.get("/logs")
async def get_system_logs(limit: int = 100, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    from app.models.domain import SystemErrorLog
    result = await db.execute(
        select(SystemErrorLog, Business.name)
        .outerjoin(Business, SystemErrorLog.business_id == Business.id)
        .order_by(SystemErrorLog.timestamp.desc())
        .limit(limit)
    )
    rows = result.all()
    data = []
    for log, b_name in rows:
        data.append({
            "id": str(log.id),
            "business_name": b_name or "System",
            "error_type": log.error_type,
            "message": log.message,
            "timestamp": log.timestamp.isoformat()
        })
    return {"status": "ok", "data": data}


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    alerts = []
    
    # 1. Quota Usage >= 90%
    businesses_res = await db.execute(
        select(Business, func.sum(UsageLog.tokens_used))
        .outerjoin(UsageLog, Business.id == UsageLog.business_id)
        .group_by(Business.id)
    )
    for b, used in businesses_res.all():
        used = used or 0
        limit = b.token_limit or 100000
        if limit > 0 and used >= limit * 0.9:
            alerts.append({
                "id": str(uuid.uuid4()),
                "type": "quota_warning",
                "message": f"Business '{b.name}' has reached {(used/limit)*100:.1f}% of quota.",
                "business_id": str(b.id),
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
    # 2. > 5 Errors in the last hour
    one_hour_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    errors_res = await db.execute(
        select(Business, func.count(SystemErrorLog.id))
        .join(SystemErrorLog, Business.id == SystemErrorLog.business_id)
        .where(SystemErrorLog.timestamp >= one_hour_ago)
        .group_by(Business.id)
        .having(func.count(SystemErrorLog.id) >= 5)
    )
    for b, count in errors_res.all():
         alerts.append({
             "id": str(uuid.uuid4()),
             "type": "error_surge",
             "message": f"Business '{b.name}' has {count} errors in the last hour.",
             "business_id": str(b.id),
             "severity": "critical",
             "timestamp": datetime.now(timezone.utc).isoformat()
         })
         
    # 3. New businesses created in the last 24 hours
    one_day_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
    new_b_res = await db.execute(
        select(Business).where(Business.created_at >= one_day_ago)
    )
    for b in new_b_res.scalars().all():
         alerts.append({
             "id": str(uuid.uuid4()),
             "type": "new_tenant",
             "message": f"New business registered: '{b.name}'.",
             "business_id": str(b.id),
             "severity": "info",
             "timestamp": b.created_at.isoformat()
         })
         
    # sort alerts by timestamp desc
    alerts.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"status": "ok", "data": alerts}


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

class ValidateTelegramRequest(BaseModel):
    bot_token: str

@router.post("/businesses/{business_id}/features/telegram/validate")
async def validate_telegram_token(business_id: uuid.UUID, data: ValidateTelegramRequest, db: AsyncSession = Depends(get_db)):
    """Verifies a Telegram bot token via Telegram's getMe API"""
    url = f"https://api.telegram.org/bot{data.bot_token}/getMe"
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, timeout=5.0)
            if res.status_code == 200:
                bot_data = res.json()
                if bot_data.get("ok"):
                    return {"status": "success", "message": "Valid Token", "bot_username": bot_data["result"].get("username")}
            return {"status": "error", "message": "Invalid Bot Token"}
        except Exception as e:
            return {"status": "error", "message": "Failed to connect to Telegram"}

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
    
    if feature_type not in ["whatsapp", "telegram", "instagram", "tiktok"]:
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

import os
import psutil
from app.api.deps import redis_client

@router.get("/health")
async def system_health(admin: dict = Depends(get_current_admin)):
    """System health metrics for Admin dashboard."""
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        memory_usage = mem.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
    except Exception:
        cpu_usage = 0
        memory_usage = 0
        disk_usage = 0

    try:
        await redis_client.ping()
        redis_status = "online"
    except Exception:
        redis_status = "offline"

    return {
        "status": "ok",
        "data": {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "redis_status": redis_status,
            "db_status": "online" # handled by middleware usually, if here it's online
        }
    }
