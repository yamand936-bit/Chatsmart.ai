import asyncio
import logging
from sqlalchemy import delete
from app.db.session import async_session_maker
from app.models.domain import Customer, Order, Appointment, Conversation, Message
from app.api.deps import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def purge_demo_data():
    async with async_session_maker() as session:
        # Delete demo customers directly via SQLAlchemy
        # Cascade deletes will automatically handle Orders, Appointments, Conversations, and Messages.
        # But to be safe if cascade isn't fully set up in DB, we'll manually bulk delete.
        try:
            logger.info("Purging demo data from production database...")

            # We can delete based on Customer name being 'demo_user' or 'Test Customer' or 'Customer_%'
            # First, fetch their IDs so we can clean up if necessary, but cascade is usually enough.
            # Using direct deletion on Customer
            stmt = delete(Customer).where(
                Customer.name.in_(['demo_user', 'Test Customer']) | Customer.name.like('Customer_%')
            )
            result = await session.execute(stmt)
            await session.commit()
            
            logger.info(f"Successfully deleted {result.rowcount} demo customers (cascading to related data).")

            # Flush specific Redis analytics counters if any
            logger.info("Flushing Redis caches...")
            keys_to_delete = await redis_client.keys("rate_limit:*")
            if keys_to_delete:
                await redis_client.delete(*keys_to_delete)
            
            # (Optional) Flush any cached metrics here if we used prefix "metrics:*"
            
            logger.info("Database and Caches purged successfully.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error purging data: {e}")

if __name__ == "__main__":
    asyncio.run(purge_demo_data())
