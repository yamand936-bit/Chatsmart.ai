import asyncio
import secrets
import string
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import async_session_maker
from app.models.user import User
from app.models.business import Business
from app.core.security import get_password_hash

async def seed_admin():
    async with async_session_maker() as session:
        # Check if any admin exists
        stmt = select(User).where(User.role == "admin")
        result = await session.execute(stmt)
        existing_admin = result.scalars().first()
        
        if existing_admin:
            print("SEEDED:")
            print("Status=Admin already exists. Safely skipping.")
            return

        # Generate credentials
        email = "admin@chatsmart.ai"
        
        # Generate strong random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for i in range(16))
        
        # 1. Create Business
        business = Business(name="ChatSmart AI Core")
        session.add(business)
        await session.flush()  # to get the business.id generated securely
        
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
        print("api_key=N/A (Schema uses JWT)")

if __name__ == "__main__":
    asyncio.run(seed_admin())
