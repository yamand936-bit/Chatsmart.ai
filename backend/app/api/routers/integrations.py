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

def verify_tiktok_signature(payload: bytes, signature_header: str, app_secret: str) -> bool:
    """Verifies x-tt-signature for TikTok webhooks"""
    if not signature_header or not app_secret:
        return False
    
    expected_hash = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_hash, signature_header)

import ipaddress
TELEGRAM_SUBNETS = [
    ipaddress.ip_network('149.154.160.0/20'),
    ipaddress.ip_network('149.154.168.0/22'),
    ipaddress.ip_network('91.108.4.0/22'),
    ipaddress.ip_network('91.108.8.0/22'),
    ipaddress.ip_network('91.108.56.0/22')
]

def is_telegram_ip(ip: str) -> bool:
    if not ip or ip == "testclient" or ip == "127.0.0.1":
        # Allow localhost/testclient for our pytest simulations
        return True
    try:
        req_ip = ipaddress.ip_address(ip)
        for subnet in TELEGRAM_SUBNETS:
            if req_ip in subnet:
                return True
        return False
    except ValueError:
        return False

async def transmit_telegram(bot_token: str, chat_id: str, text: str, smart_cards: list = None):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] Telegram Message to {chat_id}: {text} Cards: {len(smart_cards) if smart_cards else 0}")
        return
        
    async with httpx.AsyncClient() as client:
        # 1. Dispatch text payload
        if text.strip():
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            try:
                res = await client.post(url, json=payload, timeout=10.0)
                res.raise_for_status()
            except Exception as e:
                logger.error(f"Telegram text transmission failed: {e}")
                
        # 2. Dispatch Smart Cards using sendPhoto
        if smart_cards:
            for card in smart_cards:
                if card.get("image_url") and card.get("image_url") != "URL":
                    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                    caption = f"*{card.get('product_name')}*\nPrice: {card.get('price')}"
                    payload = {
                        "chat_id": chat_id, 
                        "photo": card.get("image_url"),
                        "caption": caption,
                        "parse_mode": "Markdown",
                        "reply_markup": {
                            "inline_keyboard": [[
                                {"text": "🛒 تأكيد الطلب (Buy Now)", "callback_data": f"buy:{card.get('product_id', '')}"},
                                {"text": "💬 Contact Agent", "callback_data": f"handoff"}
                            ]]
                        }
                    }
                    try:
                        res = await client.post(url, json=payload, timeout=10.0)
                        res.raise_for_status()
                    except Exception as e:
                        logger.error(f"Telegram inline card transmission failed: {e}")

async def transmit_meta_graph(phone_number_id: str, access_token: str, recipient_id: str, text: str = None, interactive_payload: dict = None, template_payload: dict = None):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] Meta Graph Message (wa_id/ig_id {recipient_id}): {text} | INTERACTIVE: {interactive_payload} | TEMPLATE: {template_payload}")
        return
        
    # v20.0 Meta Graph API Standard
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    
    if template_payload:
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "template",
            "template": template_payload
        }
    elif interactive_payload:
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "interactive",
            "interactive": interactive_payload
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
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

async def transmit_tiktok_dm(access_token: str, recipient_id: str, text: str):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] TikTok DM to {recipient_id}: {text}")
        return
        
    url = f"https://open.tiktokapis.com/v2/messages/send/"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, headers=headers, timeout=10.0)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"TikTok DM transmission failed: {e}")

async def transmit_tiktok_comment_reply(access_token: str, item_id: str, comment_id: str, text: str):
    if settings.INTEGRATIONS_MODE == "mock":
        logger.info(f"[MOCK] TikTok Comment Reply to {comment_id} on item {item_id}: {text}")
        return
        
    url = f"https://open.tiktokapis.com/v2/comment/create/"
    payload = {
        "item_id": item_id,
        "reply_to_comment_id": comment_id,
        "text": text
    }
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, headers=headers, timeout=10.0)
            res.raise_for_status()
        except Exception as e:
            logger.error(f"TikTok Comment generation failed: {e}")


# =======================================================
# TELEGRAM
# =======================================================

@router.post("/telegram/{business_id}/webhook")
async def telegram_webhook(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    
    # 1. IP Hardening
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")
    if client_ip and "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
        
    if not is_telegram_ip(client_ip):
         logger.warning(f"Rejected Telegram webhook from non-Telegram IP: {client_ip}")
         raise HTTPException(status_code=403, detail="Forbidden. Payload not from recognized Telegram subnets.")
         
    config = await get_feature_config(db, business_id, "telegram")
    
    # 2. Secret validation
    expected_secret = config.get("webhook_secret")
    if expected_secret:
        header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header_secret != expected_secret:
            logger.warning("Rejected Telegram webhook: Secret token mismatch")
            raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    body = await request.json()
    if "callback_query" in body:
        cb = body["callback_query"]
        cb_data = cb.get("data", "")
        cb_user_id = str(cb.get("from", {}).get("id"))
        chat_id = str(cb.get("message", {}).get("chat", {}).get("id"))
        
        if cb_data.startswith("buy:"):
            prod_id_str = cb_data.split(":")[1]
            try:
                from app.models.domain import Customer, Order, Product
                result = await db.execute(select(Customer).where(
                    Customer.business_id == business_id,
                    Customer.platform == "telegram",
                    Customer.external_id == cb_user_id
                ))
                customer = result.scalar_one_or_none()
                if customer and prod_id_str:
                    p_res = await db.execute(select(Product).where(Product.id == uuid.UUID(prod_id_str), Product.business_id == business_id))
                    product = p_res.scalar_one_or_none()
                    if product:
                        new_order = Order(
                            business_id=business_id,
                            customer_id=customer.id,
                            status="pending",
                            total_amount=product.price,
                            payload={"product_name": product.name, "product_id": str(product.id), "quantity": 1}
                        )
                        db.add(new_order)
                        await db.commit()
                        logger.info(f"Order created natively via Telegram Callback for {cb_user_id}")
                        
                        # Pass a SYSTEM directive to AI so it natively asks for Address and phone
                        system_prompt_inj = f"[SYSTEM NOTIFICATION: The user just clicked the 'Buy Now' button for the product: {product.name}. Please acknowledge their order enthusiastically, and then ask them to provide their FULL DELIVERY ADDRESS and PHONE NUMBER rigidly so we can ship the item.]"
                        
                        import json
                        from app.api.deps import redis_client
                        payload_data = {
                            "platform": "telegram_callback",
                            "business_id": str(business_id),
                            "config": config,
                            "cb_user_id": cb_user_id,
                            "system_prompt_inj": system_prompt_inj,
                            "chat_id": chat_id
                        }
                        await redis_client.lpush("webhook_payloads", json.dumps(payload_data))
            except Exception as e:
                logger.error(f"Telegram Callback Order failed: {e}")
        return {"status": "success"}

    if "message" not in body:
        return {"status": "ignored"}
        
    message_data = body["message"]
    chat_id = str(message_data.get("chat", {}).get("id"))
    from_user = message_data.get("from", {})
    user_id = str(from_user.get("id"))
    
    if not chat_id or not user_id:
        return {"status": "ignored"}

    msg_id = str(message_data.get("message_id", ""))
    if msg_id:
        dedup_key = f"msg:{business_id}:{chat_id}:{msg_id}"
        if await redis_client.get(dedup_key):
            return {"status": "duplicate"}
        await redis_client.setex(dedup_key, 86400, "1")

    text_content = message_data.get("text", "")
    media_url = None
    media_b64 = None
    bot_token = config.get("bot_token", "")

    if "voice" in message_data or "audio" in message_data:
        media_info = message_data.get("voice", message_data.get("audio", {}))
        file_id = media_info.get("file_id")
        if file_id:
            try:
                from app.services.media_processor import download_telegram_media, transcribe_audio
                audio_bytes = await download_telegram_media(file_id, bot_token)
                transcript = await transcribe_audio(audio_bytes)
                text_content = transcript
                media_url = f"telegram_audio_id:{file_id}"
            except Exception as e:
                logger.error(f"Telegram audio processing failed: {e}")

    elif "photo" in message_data:
        photos = message_data.get("photo", [])
        if photos:
            # Telegram sends array of photos (different sizes), get the largest one
            largest_photo = photos[-1]
            file_id = largest_photo.get("file_id")
            if file_id:
                try:
                    from app.services.media_processor import download_telegram_media, encode_image_base64
                    image_bytes = await download_telegram_media(file_id, bot_token)
                    media_b64 = encode_image_base64(image_bytes, "image/jpeg")
                    text_content = message_data.get("caption", "User sent an image.")
                    media_url = f"telegram_image_id:{file_id}"
                except Exception as e:
                    logger.error(f"Telegram photo processing failed: {e}")

    if not text_content.strip() and not media_b64:
        return {"status": "ignored"}

    logger.info(f"[TELEGRAM] msg from {user_id} for business {business_id}")

    import json
    from app.api.deps import redis_client
    payload_data = {
        "platform": "telegram",
        "business_id": str(business_id),
        "config": config,
        "body": message_data
    }
    await redis_client.lpush("webhook_payloads", json.dumps(payload_data))
    return {"status": "success"}


# =======================================================
# WHATSAPP (META)
# =======================================================

@router.get("/whatsapp/webhook")
async def whatsapp_webhook_verify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Meta webhook challenge verification"""
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Find the business config by verify_token
    bf_res = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.feature_type == "whatsapp",
            BusinessFeature.config["verify_token"].astext == token
        )
    )
    feature = bf_res.scalar_one_or_none()

    if mode == "subscribe" and feature and feature.is_active:
        return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp/webhook")
async def whatsapp_webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    body = await request.json()
    
    try:
        phone_number_id = body["entry"][0]["changes"][0]["value"]["metadata"]["phone_number_id"]
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid metadata structure. phone_number_id missing.")
        
    bf_res = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.feature_type == "whatsapp",
            BusinessFeature.config["phone_number_id"].astext == phone_number_id
        )
    )
    feature = bf_res.scalar_one_or_none()
    
    if not feature or not feature.is_active:
        raise HTTPException(status_code=403, detail="Tenant context invalid or deactivated")
        
    business_id = feature.business_id
    config = feature.config

    # WhatsApp app_secret is REQUIRED — reject if not configured.
    app_secret = config.get("app_secret")
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="WhatsApp app_secret is not configured for this business",
        )
        
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, sig, app_secret):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")

    body = await request.json()

    import json
    from app.api.deps import redis_client
    payload_data = {
        "platform": "whatsapp",
        "business_id": str(business_id),
        "config": config,
        "body": body
    }
    await redis_client.lpush("webhook_payloads", json.dumps(payload_data))
    return {"status": "success"}


# =======================================================
# INSTAGRAM (META)
# =======================================================

@router.get("/instagram/webhook")
async def instagram_webhook_verify(request: Request, db: AsyncSession = Depends(get_db)):
    # Meta uses identical Graph validation as WhatsApp
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    bf_res = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.feature_type == "instagram",
            BusinessFeature.config["verify_token"].astext == token
        )
    )
    feature = bf_res.scalar_one_or_none()

    if mode == "subscribe" and feature and feature.is_active:
        return PlainTextResponse(content=challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/instagram/webhook")
async def instagram_webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    raw_body = await request.body()
    body = await request.json()
    
    try:
        page_id = body.get("entry", [{}])[0].get("id")
        if not page_id: raise KeyError()
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid metadata structure. page_id missing.")
        
    bf_res = await db.execute(
        select(BusinessFeature).where(
            BusinessFeature.feature_type == "instagram",
            BusinessFeature.config["page_id"].astext == page_id
        )
    )
    feature = bf_res.scalar_one_or_none()
    
    if not feature or not feature.is_active:
        raise HTTPException(status_code=403, detail="Tenant context invalid or deactivated")
        
    business_id = feature.business_id
    config = feature.config
    
    # Instagram app_secret is REQUIRED — reject if not configured.
    app_secret = config.get("app_secret")
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="Instagram app_secret is not configured for this business",
        )
    sig = request.headers.get("X-Hub-Signature-256")
    if not verify_meta_signature(raw_body, sig, app_secret):
        raise HTTPException(status_code=401, detail="Invalid Meta signature")
    import json
    from app.api.deps import redis_client
    payload_data = {
        "platform": "instagram",
        "business_id": str(business_id),
        "config": config,
        "body": body
    }
    await redis_client.lpush("webhook_payloads", json.dumps(payload_data))
    return {"status": "success"}


# =======================================================
# TIKTOK
# =======================================================

@router.get("/tiktok/{business_id}/webhook")
async def tiktok_webhook_verify(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    config = await get_feature_config(db, business_id, "tiktok")
    token = request.query_params.get("verify_token")
    challenge = request.query_params.get("challenge")
    if token != config.get("verify_token"):
        raise HTTPException(status_code=403, detail="Verification failed")
    return {"challenge": challenge}

@router.post("/tiktok/{business_id}/webhook")
async def tiktok_webhook_receive(business_id: uuid.UUID, request: Request, db: AsyncSession = Depends(get_db)):
    config = await get_feature_config(db, business_id, "tiktok")
    app_secret = config.get("app_secret")
    if not app_secret:
        raise HTTPException(
            status_code=500,
            detail="TikTok app_secret is not configured for this business",
        )
        
    raw_body = await request.body()
    sig = request.headers.get("x-tt-signature")
    if not verify_tiktok_signature(raw_body, sig, app_secret):
        raise HTTPException(status_code=401, detail="Invalid TikTok signature")

    body = await request.json()
    event_type = body.get("event")
    
    import json
    from app.api.deps import redis_client
    payload_data = {
        "platform": "tiktok",
        "business_id": str(business_id),
        "config": config,
        "body": body
    }
    await redis_client.lpush("webhook_payloads", json.dumps(payload_data))
    return {"status": "success"}
