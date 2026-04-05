from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.core.config import settings
from app.api.deps import redis_client
from app.models.business import Business, BusinessFeature
from app.services.chat_core import process_chat_core
from typing import Optional
import httpx
import logging
import uuid
import hmac
import hashlib
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# =======================================================
# UTILITIES
# =======================================================

async def get_feature_config(db: AsyncSession, business_id: uuid.UUID, feature_type: str) -> dict:
    result = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.business_id == business_id,
            BusinessFeature.feature_type == feature_type,
            BusinessFeature.is_active == True
        )
    )
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=403, detail=f"Feature {feature_type} is not enabled for this business")
    return feature.config

def verify_meta_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """Verifies X-Hub-Signature-256 for Meta webhooks"""
    if not signature_header or not app_secret:
        return False
    
    expected_hash = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={expected_hash}"
    return hmac.compare_digest(expected_signature, signature_header)

async def transmit_telegram(bot_token: str, chat_id: str, text: str):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] Telegram Message to {chat_id}: {text}")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=10.0)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Telegram transmission failed: {e}")

async def transmit_meta_graph(phone_number_id: str, access_token: str, recipient_id: str, text: str):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] Meta Graph Message (wa_id/ig_id {recipient_id}): {text}")
        return
        
    # v20.0 Meta Graph API Standard
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp", # Will handle IG differently if needed, keeping simple here
        "to": recipient_id,
        "type": "text",
        "text": {"body": text}
    }
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, headers=headers, timeout=10.0)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"Meta graph transmission failed: {e}")


# =======================================================
# TELEGRAM
# =======================================================

@router.post("/telegram/{business_id}/webhook")
async def telegram_webhook(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    config = await get_feature_config(db, business_id, "telegram")
    
    # Telegram webhook secret is REQUIRED — reject if not configured.
    expected_secret = config.get("webhook_secret")
    if not expected_secret:
        raise HTTPException(
            status_code=500,
            detail="Telegram webhook_secret is not configured for this business",
        )
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header_secret != expected_secret:
        raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    body = await request.json()
    if "message" not in body:
        return {"status": "ignored"}
        
    message_data = body["message"]
    chat_id = str(message_data.get("chat", {}).get("id"))
    text_content = message_data.get("text", "")
    from_user = message_data.get("from", {})
    user_id = str(from_user.get("id"))
    
    if not chat_id or not text_content or not user_id:
        return {"status": "ignored"}

    msg_id = str(message_data.get("message_id", ""))
    if msg_id:
        dedup_key = f"msg:{business_id}:{chat_id}:{msg_id}"
        if await redis_client.get(dedup_key):
            return {"status": "duplicate"}
        await redis_client.setex(dedup_key, 86400, "1")

    logger.info(f"[TELEGRAM] msg from {user_id} for business {business_id}")

    try:
        ai_response, intent, _, _ = await process_chat_core(
            db=db, business_id=business_id, customer_platform="telegram",
            external_id=user_id, content=text_content
        )
        if ai_response:
            await transmit_telegram(config.get("bot_token", ""), chat_id, ai_response)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Telegram core logic fail: {e}")
        # Always return 200 so Telegram stops retrying
        return {"status": "error_handled"}


# =======================================================
# WHATSAPP (META)
# =======================================================

@router.get("/whatsapp/{business_id}/webhook")
async def whatsapp_webhook_verify(
    business_id: uuid.UUID, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Meta webhook challenge verification"""
    config = await get_feature_config(db, business_id, "whatsapp")
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == config.get("verify_token"):
        return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/{business_id}/webhook")
async def whatsapp_webhook_receive(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    config = await get_feature_config(db, business_id, "whatsapp")
    
    # WhatsApp app_secret is REQUIRED — reject if not configured.
    app_secret = config.get("app_secret")
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="WhatsApp app_secret is not configured for this business",
        )
    raw_body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, sig, app_secret):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")

    body = await request.json()

    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    if msg.get("type") == "text":
                        sender_wa_id = msg.get("from")
                        text_content = msg.get("text", {}).get("body", "")

                        if not sender_wa_id or not text_content.strip():
                            continue

                        msg_id = msg.get("id", "")
                        if msg_id:
                            dedup_key = f"msg:{business_id}:{msg_id}"
                            if await redis_client.get(dedup_key):
                                continue
                            await redis_client.setex(dedup_key, 86400, "1")

                        logger.info(f"[WHATSAPP] msg from {sender_wa_id} for business {business_id}")
                        
                        ai_response, intent, _, _ = await process_chat_core(
                            db=db, business_id=business_id, customer_platform="whatsapp",
                            external_id=sender_wa_id, content=text_content
                        )
                        
                        if ai_response:
                            await transmit_meta_graph(
                                phone_number_id=config.get("phone_number_id", ""),
                                access_token=config.get("access_token", ""),
                                recipient_id=sender_wa_id,
                                text=ai_response
                            )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"WhatsApp core logic fail: {e}")
        return {"status": "error_handled"}


# =======================================================
# INSTAGRAM (META)
# =======================================================

@router.get("/instagram/{business_id}/webhook")
async def instagram_webhook_verify(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    # Meta uses identical Graph validation as WhatsApp
    config = await get_feature_config(db, business_id, "instagram")
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == config.get("verify_token"):
        return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/instagram/{business_id}/webhook")
async def instagram_webhook_receive(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    config = await get_feature_config(db, business_id, "instagram")
    
    # Instagram app_secret is REQUIRED — reject if not configured.
    app_secret = config.get("app_secret")
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="Instagram app_secret is not configured for this business",
        )
    raw_body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, sig, app_secret):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")

    body = await request.json()
    try:
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                text_content = message.get("text", "")
                
                if sender_id and text_content:
                    msg_id = message.get("mid", "")
                    if msg_id:
                        dedup_key = f"msg:{business_id}:{msg_id}"
                        if await redis_client.get(dedup_key):
                            continue
                        await redis_client.setex(dedup_key, 86400, "1")

                    logger.info(f"[INSTAGRAM] msg from {sender_id} for business {business_id}")
                    
                    ai_response, intent, _, _ = await process_chat_core(
                        db=db, business_id=business_id, customer_platform="instagram",
                        external_id=sender_id, content=text_content
                    )
                    
                    if ai_response:
                        # Instagram uses slightly different send payload, handled simply here 
                        # using Graph v20.0 standard Page access
                        url = f"https://graph.facebook.com/v20.0/me/messages"
                        payload = {"recipient": {"id": sender_id}, "message": {"text": ai_response}}
                        headers = {"Authorization": f"Bearer {config.get('access_token', '')}", "Content-Type": "application/json"}
                        
                        if settings.INTEGRATIONS_MODE == "mock":
                            logger.info(f"[MOCK] Instagram Message to {sender_id}: {ai_response}")
                        else:
                            async with httpx.AsyncClient() as client:
                                res = await client.post(url, json=payload, headers=headers, timeout=10.0)
                                res.raise_for_status()

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Instagram core logic fail: {e}")
        return {"status": "error_handled"}
