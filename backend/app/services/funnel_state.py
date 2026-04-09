import json
import logging
from typing import Optional
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

class FunnelStateService:
    CACHE_EXPIRY = 86400  # 24 hours

    @staticmethod
    async def get_state(conversation_id: str) -> dict:
        if not redis_client:
            return {}
        try:
            raw_state = await redis_client.get(f"sales_funnel:{conversation_id}")
            if raw_state:
                return json.loads(raw_state)
            return {}
        except Exception as e:
            logger.error(f"Error reading funnel state: {e}")
            return {}

    @staticmethod
    async def update_state(conversation_id: str, new_data: dict) -> dict:
        if not redis_client:
            return {}
        try:
            current_state = await FunnelStateService.get_state(conversation_id)
            
            # Update only non-empty fields to prevent overwriting with None
            for key, value in new_data.items():
                if value:  
                    current_state[key] = value

            await redis_client.setex(
                f"sales_funnel:{conversation_id}",
                FunnelStateService.CACHE_EXPIRY,
                json.dumps(current_state)
            )
            return current_state
        except Exception as e:
            logger.error(f"Error updating funnel state: {e}")
            return new_data

    @staticmethod
    async def clear_state(conversation_id: str):
        if not redis_client:
            return
        try:
            await redis_client.delete(f"sales_funnel:{conversation_id}")
        except Exception as e:
            logger.error(f"Error clearing funnel state: {e}")
