from fastapi import APIRouter, Depends
from app.api.deps import get_current_admin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.ai_usage_log import AIUsageLog

router = APIRouter()

@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    total_cost = await db.scalar(select(func.sum(AIUsageLog.cost)))
    total_tokens = await db.scalar(select(func.sum(AIUsageLog.total_tokens)))
    total_requests = await db.scalar(select(func.count(AIUsageLog.id)))

    return {
        "total_cost": total_cost or 0,
        "total_tokens": total_tokens or 0,
        "total_requests": total_requests or 0
    }

@router.get("/by-business")
async def by_business(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    result = await db.execute(
        select(
            AIUsageLog.business_id,
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
            func.sum(AIUsageLog.cost).label("total_cost")
        ).group_by(AIUsageLog.business_id)
        .limit(limit)
        .offset(offset)
    )
    # Convert result to a list of dicts for correct JSON serialization
    return [{"business_id": row[0], "total_tokens": row[1], "total_cost": row[2]} for row in result.all()]

@router.get("/by-provider")
async def by_provider(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    result = await db.execute(
        select(
            AIUsageLog.provider,
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
            func.sum(AIUsageLog.cost).label("total_cost")
        ).group_by(AIUsageLog.provider)
        .limit(limit)
        .offset(offset)
    )
    # Convert result to a list of dicts for correct JSON serialization
    return [{"provider": row[0], "total_tokens": row[1], "total_cost": row[2]} for row in result.all()]

from app.api.deps import get_merchant_tenant
from app.models.domain import Conversation, Message
from app.core.redis_client import redis_client
import uuid
import json
from datetime import datetime, timedelta, timezone

@router.get("/merchant/summary")
async def merchant_summary(business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    key = f'analytics:merchant:{business_id}'
    try:
        cached = await redis_client.get(key)
        if cached: 
            return json.loads(cached)
    except Exception:
        pass

    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
    
    # Total conversations
    c_res = await db.execute(
        select(Conversation.status, func.count(Conversation.id))
        .where(Conversation.business_id == business_id, Conversation.created_at >= thirty_days_ago)
        .group_by(Conversation.status)
    )
    c_counts = {r[0]: r[1] for r in c_res.all()}
    total_convs = sum(c_counts.values())
    bot_handled = c_counts.get("bot", 0)
    human_handled = c_counts.get("human", 0)

    avg_res = await db.scalar(
        select(func.avg(Message.response_time))
        .where(Message.business_id == business_id, Message.created_at >= thirty_days_ago)
    )
    avg_response_time_ms = round((avg_res or 0.0) * 1000, 2)
    
    int_res = await db.execute(
        select(Message.intent, func.count(Message.id))
        .where(Message.business_id == business_id, Message.created_at >= thirty_days_ago, Message.intent.is_not(None))
        .group_by(Message.intent)
        .order_by(func.count(Message.id).desc())
        .limit(5)
    )
    top_intents = [{"intent": r[0], "count": r[1]} for r in int_res.all()]
    
    flow_res = await db.scalar(
        select(func.count(Message.id))
        .where(Message.business_id == business_id, Message.created_at >= thirty_days_ago, Message.intent == "flow_match")
    )
    flow_match_count = flow_res or 0
    
    msg_day_res = await db.execute(
        select(func.date(Message.created_at), func.count(Message.id))
        .where(Message.business_id == business_id, Message.created_at >= thirty_days_ago)
        .group_by(func.date(Message.created_at))
        .order_by(func.date(Message.created_at).asc())
    )
    messages_per_day = [{"date": str(r[0]), "count": r[1]} for r in msg_day_res.all()]
    
    cost_res = await db.scalar(
        select(func.sum(AIUsageLog.cost))
        .where(AIUsageLog.business_id == str(business_id), AIUsageLog.created_at >= thirty_days_ago)
    )
    token_cost_total = round(cost_res or 0.0, 4)

    out = {
        "status": "ok",
        "total_conversations": total_convs,
        "bot_handled": bot_handled,
        "human_handled": human_handled,
        "avg_response_time_ms": avg_response_time_ms,
        "top_intents": top_intents,
        "messages_per_day": messages_per_day,
        "token_cost_total": token_cost_total,
        "flow_match_count": flow_match_count
    }
    
    try:
        await redis_client.setex(key, 300, json.dumps(out))
    except Exception:
        pass
    
    return out
