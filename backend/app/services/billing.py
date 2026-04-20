from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import logging

logger = logging.getLogger(__name__)

async def reserve_credit(db: AsyncSession, business_id: uuid.UUID) -> bool:
    """
    Atomically decreases message credits by 1 if credits are > 0.
    Returns True if successfully reserved, False if out of credits.
    """
    query = text("""
        UPDATE businesses 
        SET message_credits = message_credits - 1 
        WHERE id = :business_id AND message_credits > 0 
        RETURNING message_credits
    """)
    result = await db.execute(query, {"business_id": str(business_id)})
    row = result.fetchone()
    
    # Needs explicit commit to persist the lock decrement
    await db.commit()
    
    return row is not None

async def refund_credit(db: AsyncSession, business_id: uuid.UUID) -> None:
    """
    Refunds a credit in the event of an LLM timeout or system error during a reserved flow.
    """
    query = text("""
        UPDATE businesses 
        SET message_credits = message_credits + 1 
        WHERE id = :business_id
    """)
    await db.execute(query, {"business_id": str(business_id)})
    await db.commit()
    logger.info(f"Refunded 1 credit to business {business_id} due to LLM failure.")
