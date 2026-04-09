import asyncio
import json
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.api.deps import get_merchant_tenant, redis_client
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.models.domain import Customer, Conversation, Message, Product, Order
from app.models.business import Business
from app.services.ai_engine import AIEngineService
import uuid

router = APIRouter()

async def check_rate_limit(key: str, limit: int, window: int):
    """Simple sliding window rate limit using Redis"""
    pipe = redis_client.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, window)
    results = await pipe.execute()

    current_count = results[0]
    if current_count > limit:
        raise HTTPException(status_code=429, detail="Too many requests for this business")


from app.services.chat_core import process_chat_core


@router.post("/message", response_model=ChatMessageResponse)
async def handle_message(
    request: Request,
    data: ChatMessageRequest,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    # Validate payload
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Empty hidden message")
        
    # Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    await check_rate_limit(f"rate_limit:chat:{business_id}:{client_ip}", 50, 60)

    ai_response, intent, msg_id, conv_id, smart_cards = await process_chat_core(
        db=db, business_id=business_id, customer_platform="web_admin",
        external_id=data.external_id, content=data.content
    )
    
    # Optional logic for smart_cards formatting inside admin
    if smart_cards:
        for c in smart_cards:
            ai_response = f"{ai_response}\n\n[SMART CARD: {c.get('product_name')} - {c.get('price')}]"

    return {
        "status": "ok", 
        "message_id": msg_id, 
        "conversation_id": conv_id,
        "ai_response": ai_response if ai_response else "A human agent will respond shortly.",
        "intent": intent
    }

@router.get("/stream/{conversation_id}")
async def stream_chat(
    request: Request,
    conversation_id: str,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    SSE stream endpoint demonstrating chunk format stability.
    """
    # [SECURITY FIX] Validate conversation_id strictly belongs to this business_id
    try:
        conv_uuid = uuid.UUID(conversation_id)
        result = await db.execute(select(Conversation).where(
            Conversation.id == conv_uuid, 
            Conversation.business_id == business_id
        ))
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=403, detail="Forbidden access to this conversation")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    async def event_generator():
        try:
            # Simulate generating tokens
            tokens = ["Hello", " ", "this", " ", "is", " ", "AI"]
            for token in tokens:
                if await request.is_disconnected():
                    break
                yield {
                    "event": "message",
                    "data": token
                }
                await asyncio.sleep(0.1)
                
            yield {"event": "done", "data": "[DONE]"}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())
