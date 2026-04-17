with open("backend/app/api/routers/merchant.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("from fastapi import APIRouter", "from fastapi import APIRouter, Request")

stream_endpoint = """
import asyncio
from sse_starlette.sse import EventSourceResponse

@router.get("/stream")
async def sse_merchant_stream(
    request: Request,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
):
    channel_name = f"merchant:{business_id}:events"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel_name)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                # Non-blocking get_message
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                if message is not None and message['type'] == 'message':
                    yield {
                        "event": "message",
                        "data": message['data'].decode('utf-8') if isinstance(message['data'], bytes) else str(message['data'])
                    }
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"SSE Error: {e}")
        finally:
            await pubsub.unsubscribe(channel_name)
            await pubsub.close()

    return EventSourceResponse(event_generator())
"""

if "def sse_merchant_stream" not in text:
    text += stream_endpoint

with open("backend/app/api/routers/merchant.py", "w", encoding="utf-8") as f:
    f.write(text)
