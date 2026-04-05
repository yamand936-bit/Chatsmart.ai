import asyncio
from app.db.session import async_session_maker
from app.models.user import User
from app.core.security import get_password_hash

async def seed():
    async with async_session_maker() as session:
        # Check if admin already exists
        from sqlalchemy.future import select
        result = await session.execute(select(User).where(User.email == "admin@chatsmart.ai"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            admin = User(
                email="admin@chatsmart.ai",
                hashed_password=get_password_hash("password123"),
                role="admin"
            )
            session.add(admin)
            await session.commit()
            print("Admin user 'admin@chatsmart.ai' created successfully with password 'password123'")
        else:
            print("Admin user already exists")

if __name__ == "__main__":
    asyncio.run(seed())
