import asyncio
import sys
import os
sys.path.append('/app')
from app.db.session import async_session_maker
from app.models.business import Business
from app.models.user import User
from app.models.domain import UsageLog
from sqlalchemy import select, func

async def main():
    async with async_session_maker() as db:
        print('Starting query...')
        query = select(Business, func.max(User.email).label('owner_email'), func.sum(UsageLog.tokens_used).label('tokens_used'), func.max(UsageLog.date_logged).label('last_active'))
        query = query.join(User, Business.id == User.business_id, isouter=True)
        query = query.outerjoin(UsageLog, Business.id == UsageLog.business_id)
        query = query.where(User.role == 'merchant')
        query = query.group_by(Business.id)
        res = await db.execute(query)
        data = res.all()
        print('Total WITH WHERE merchant:', len(data))

asyncio.run(main())