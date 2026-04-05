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
