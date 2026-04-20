import sys
sys.path.append('/app')
import asyncio
from app.db.session import async_session_maker
from app.models.user import User
from sqlalchemy import select
from app.core.security import create_access_token

async def run():
    async with async_session_maker() as db:
        res = await db.execute(select(User).where(User.email == 'admin@chatsmart.ai'))
        admin = res.scalar_one_or_none()
        if admin:
            token = create_access_token(admin)
            print('Token:', token)

asyncio.run(run())
