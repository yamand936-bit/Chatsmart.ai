import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.db.session import async_session_maker
from app.models.user import User
from app.models.business import Business
from app.core.security import get_password_hash

async def seed_admin():
    async with async_session_maker() as session:
        email = "admin@chatsmart.ai"
        password = "admin"
        
        # Check if any admin exists
        stmt = select(User).where(User.role == "admin", User.email == email)
        result = await session.execute(stmt)
        existing_admin = result.scalars().first()
        
        if existing_admin:
            print("Admin already exists. Enforcing default testing password...")
            existing_admin.hashed_password = get_password_hash(password)
            await session.commit()
            print(f"email={email}")
            print(f"password={password}")
            return

        print("Creating default admin account...")
        
        # 1. Create Business
        business = Business(name="ChatSmart AI Core")
        session.add(business)
        await session.flush()  # to get the business.id
        
        # 2. Create Admin User
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            business_id=business.id
        )
        session.add(admin_user)
        
        await session.commit()
        
        print("SEEDED:")
        print(f"email={email}")
        print(f"password={password}")
        print(f"business_id={business.id}")

if __name__ == "__main__":
    asyncio.run(seed_admin())
