import asyncio
from sqlalchemy.future import select
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash

async def run():
    async with async_session_maker() as session:
        stmt = select(User).where(User.role == "admin")
        result = await session.execute(stmt)
        admin = result.scalars().first()
        if admin:
            admin.hashed_password = get_password_hash("AdminUser123!")
            await session.commit()
            print("RESET_SUCCESS", admin.email)

if __name__ == "__main__":
    asyncio.run(run())
