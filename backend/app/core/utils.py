import asyncio
import logging

logger = logging.getLogger(__name__)

def safe_create_task(coro, name: str = "UnknownTask"):
    """
    Safely executes an asyncio background task by wrapping it in a try-except block.
    Prevents unhandled exceptions from silently dying or bubbling up and crashing the event loop.
    """
    async def wrapper():
        try:
            await coro
        except asyncio.CancelledError:
            logger.info(f"Task {name} was cancelled.")
        except Exception as e:
            logger.error(f"Background generic task '{name}' failed with error: {e}", exc_info=True)
            # You can also plug in global notifications here if critical.

    return asyncio.create_task(wrapper(), name=name)
