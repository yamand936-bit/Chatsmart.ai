import asyncio
from app.db.session import async_session_maker
from sqlalchemy import select, func
from app.models.business import Business
from app.models.user import User
from app.models.domain import UsageLog

async def run():
    async with async_session_maker() as db:
        total = await db.scalar(select(func.count()).select_from(Business))
        print("Total businesses:", total)
        
        result = await db.execute(
            select(Business, func.max(User.email), func.sum(UsageLog.tokens_used))
            .join(User, Business.id == User.business_id)
            .outerjoin(UsageLog, Business.id == UsageLog.business_id)
            .where(User.role == "merchant")
            .group_by(Business.id)
            .order_by(Business.created_at.desc())
            .limit(50)
            .offset(0)
        )
        rows = result.all()
        print("Rows fetched:", len(rows))
        for b, e, t in rows:
            print(f" - {b.name} ({b.id}), owner: {e}")

if __name__ == "__main__":
    asyncio.run(run())
