import asyncio
import logging

logger = logging.getLogger(__name__)

def safe_create_task(coro, name: str = "Unknown Task"):
    """
    Creates an asyncio task and attaches a callback to catch unhandled exceptions,
    preventing silent event loop deaths.
    """
    task = asyncio.create_task(coro, name=name)
    
    def _handle_exception(t):
        try:
            t.result()
        except asyncio.CancelledError:
            pass  # Expected on shutdown
        except Exception as e:
            logger.error(f"Background Task '{name}' crashed: {e}", exc_info=True)
            
    task.add_done_callback(_handle_exception)
    return task
