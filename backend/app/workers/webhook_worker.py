import json
import uuid
import logging
import asyncio
import httpx
from datetime import date
from sqlalchemy import select
from app.db.session import async_session_maker
from app.api.deps import redis_client
from app.services.chat_core import process_chat_core
from app.core.config import settings

logger = logging.getLogger(__name__)

async def transmit_meta_graph(phone_number_id, access_token, recipient_id, text=None, interactive_payload=None):
    from app.api.routers.integrations import transmit_meta_graph as orig_meta
    return await orig_meta(phone_number_id, access_token, recipient_id, text, interactive_payload)

async def transmit_tiktok_dm(access_token, recipient_id, text):
    from app.api.routers.integrations import transmit_tiktok_dm as orig_dm
    return await orig_dm(access_token, recipient_id, text)

async def transmit_tiktok_comment_reply(access_token, item_id, comment_id, text):
    from app.api.routers.integrations import transmit_tiktok_comment_reply as orig_cr
    return await orig_cr(access_token, item_id, comment_id, text)

async def _process_whatsapp(db, business_id, config, body):
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    msg_type = msg.get("type")
                    sender_wa_id = msg.get("from")
                    msg_id = msg.get("id", "")
                    
                    if not sender_wa_id or not msg_id:
                        continue
                        
                    dedup_key = f"msg:{business_id}:{msg_id}"
                    if await redis_client.get(dedup_key):
                        continue
                    await redis_client.setex(dedup_key, 86400, "1")

                    text_content = ""
                    media_url = None
                    media_b64 = None
                    
                    if msg_type == "text":
                        text_content = msg.get("text", {}).get("body", "")
                        
                    elif msg_type == "audio" or msg_type == "voice":
                        from app.services.media_processor import download_whatsapp_media, transcribe_audio
                        audio_info = msg.get(msg_type, {})
                        media_id = audio_info.get("id")
                        if media_id:
                            try:
                                audio_bytes = await download_whatsapp_media(media_id, config.get("access_token"))
                                transcript = await transcribe_audio(audio_bytes)
                                text_content = transcript
                                media_url = f"whatsapp_audio_id:{media_id}"
                            except Exception as e:
                                logger.error(f"WhatsApp audio processing failed: {e}")
                                continue
                                
                    elif msg_type == "image":
                        from app.services.media_processor import download_whatsapp_media, encode_image_base64
                        image_info = msg.get("image", {})
                        media_id = image_info.get("id")
                        mime_type = image_info.get("mime_type", "image/jpeg")
                        if media_id:
                            try:
                                image_bytes = await download_whatsapp_media(media_id, config.get("access_token"))
                                media_b64 = encode_image_base64(image_bytes, mime_type)
                                text_content = image_info.get("caption", "User sent an image.")
                                media_url = f"whatsapp_image_id:{media_id}"
                            except Exception as e:
                                logger.error(f"WhatsApp image processing failed: {e}")
                                continue
                                
                    elif msg_type == "interactive":
                        interactive_data = msg.get("interactive", {})
                        if interactive_data.get("type") == "button_reply":
                            button_id = interactive_data.get("button_reply", {}).get("id", "")
                            if button_id.startswith("buy:"):
                                prod_id_str = button_id.split(":")[1]
                                try:
                                    from app.models.domain import Customer, Order, Product
                                    from sqlalchemy import select
                                    result = await db.execute(select(Customer).where(
                                        Customer.business_id == business_id,
                                        Customer.platform == "whatsapp",
                                        Customer.external_id == sender_wa_id
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
                                            logger.info(f"Order created natively via WhatsApp Interactive for {sender_wa_id}")
                                            await transmit_meta_graph(
                                                phone_number_id=config.get("phone_number_id", ""),
                                                access_token=config.get("access_token", ""),
                                                recipient_id=sender_wa_id,
                                                text=f"✅ تم استلام طلبك للمنتج: *{product.name}*\nالحالة: قيد المراجعة (Pending). سنقوم بالتواصل معك قريباً!"
                                            )
                                except Exception as e:
                                    logger.error(f"WhatsApp Interactive Order failed: {e}")
                                continue
                    
                    if not text_content.strip() and not media_b64:
                        continue

                    logger.info(f"[WHATSAPP] msg from {sender_wa_id} for business {business_id}")
                    
                    ai_response, intent, _, _, smart_cards = await process_chat_core(
                        db=db, business_id=business_id, customer_platform="whatsapp",
                        external_id=sender_wa_id, content=text_content,
                        media_url=media_url, media_b64=media_b64
                    )
                    
                    if intent == "human_handoff_active":
                        return {"status": "ok"}
                    
                    if ai_response or smart_cards:
                        displayText = ai_response or ""
                                
                        # 1. Send the text part first
                        if displayText.strip():
                            await transmit_meta_graph(
                                phone_number_id=config.get("phone_number_id", ""),
                                access_token=config.get("access_token", ""),
                                recipient_id=sender_wa_id,
                                text=displayText.strip()
                            )
                            
                        # 2. Send Media & Button Messages for each smart card
                        for card in smart_cards:
                            if card.get("product_id") and card.get("image_url") and card.get("image_url") != "URL":
                                card_payload = {
                                    "type": "button",
                                    "header": {
                                        "type": "image",
                                        "image": {
                                            "link": card.get("image_url")  # In production, must be public URL
                                        }
                                    },
                                    "body": {
                                        "text": f"*{card.get('product_name')}*\nPrice: {card.get('price')}"
                                    },
                                    "action": {
                                        "buttons": [
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": f"buy:{card.get('product_id')}",
                                                    "title": "🛒 تأكيد الشراء"
                                                }
                                            }
                                        ]
                                    }
                                }
                                await transmit_meta_graph(
                                    phone_number_id=config.get("phone_number_id", ""),
                                    access_token=config.get("access_token", ""),
                                    recipient_id=sender_wa_id,
                                    interactive_payload=card_payload
                                )
        pass
    except Exception as e:
        logger.error(f"WhatsApp core logic fail: {e}")
        pass

async def _process_instagram(db, business_id, config, body):
    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    msg_type = msg.get("type")
                    sender_wa_id = msg.get("from")
                    msg_id = msg.get("id", "")
                    
                    if not sender_wa_id or not msg_id:
                        continue
                        
                    dedup_key = f"msg:{business_id}:{msg_id}"
                    if await redis_client.get(dedup_key):
                        continue
                    await redis_client.setex(dedup_key, 86400, "1")

                    text_content = ""
                    media_url = None
                    media_b64 = None
                    
                    if msg_type == "text":
                        text_content = msg.get("text", {}).get("body", "")
                        
                    elif msg_type == "audio" or msg_type == "voice":
                        from app.services.media_processor import download_whatsapp_media, transcribe_audio
                        audio_info = msg.get(msg_type, {})
                        media_id = audio_info.get("id")
                        if media_id:
                            try:
                                audio_bytes = await download_whatsapp_media(media_id, config.get("access_token"))
                                transcript = await transcribe_audio(audio_bytes)
                                text_content = transcript
                                media_url = f"whatsapp_audio_id:{media_id}"
                            except Exception as e:
                                logger.error(f"WhatsApp audio processing failed: {e}")
                                continue
                                
                    elif msg_type == "image":
                        from app.services.media_processor import download_whatsapp_media, encode_image_base64
                        image_info = msg.get("image", {})
                        media_id = image_info.get("id")
                        mime_type = image_info.get("mime_type", "image/jpeg")
                        if media_id:
                            try:
                                image_bytes = await download_whatsapp_media(media_id, config.get("access_token"))
                                media_b64 = encode_image_base64(image_bytes, mime_type)
                                text_content = image_info.get("caption", "User sent an image.")
                                media_url = f"whatsapp_image_id:{media_id}"
                            except Exception as e:
                                logger.error(f"WhatsApp image processing failed: {e}")
                                continue
                                
                    elif msg_type == "interactive":
                        interactive_data = msg.get("interactive", {})
                        if interactive_data.get("type") == "button_reply":
                            button_id = interactive_data.get("button_reply", {}).get("id", "")
                            if button_id.startswith("buy:"):
                                prod_id_str = button_id.split(":")[1]
                                try:
                                    from app.models.domain import Customer, Order, Product
                                    from sqlalchemy import select
                                    result = await db.execute(select(Customer).where(
                                        Customer.business_id == business_id,
                                        Customer.platform == "whatsapp",
                                        Customer.external_id == sender_wa_id
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
                                            logger.info(f"Order created natively via WhatsApp Interactive for {sender_wa_id}")
                                            await transmit_meta_graph(
                                                phone_number_id=config.get("phone_number_id", ""),
                                                access_token=config.get("access_token", ""),
                                                recipient_id=sender_wa_id,
                                                text=f"✅ تم استلام طلبك للمنتج: *{product.name}*\nالحالة: قيد المراجعة (Pending). سنقوم بالتواصل معك قريباً!"
                                            )
                                except Exception as e:
                                    logger.error(f"WhatsApp Interactive Order failed: {e}")
                                continue
                    
                    if not text_content.strip() and not media_b64:
                        continue

                    logger.info(f"[WHATSAPP] msg from {sender_wa_id} for business {business_id}")
                    
                    ai_response, intent, _, _, smart_cards = await process_chat_core(
                        db=db, business_id=business_id, customer_platform="whatsapp",
                        external_id=sender_wa_id, content=text_content,
                        media_url=media_url, media_b64=media_b64
                    )
                    
                    if intent == "human_handoff_active":
                        return {"status": "ok"}
                    
                    if ai_response or smart_cards:
                        displayText = ai_response or ""
                                
                        # 1. Send the text part first
                        if displayText.strip():
                            await transmit_meta_graph(
                                phone_number_id=config.get("phone_number_id", ""),
                                access_token=config.get("access_token", ""),
                                recipient_id=sender_wa_id,
                                text=displayText.strip()
                            )
                            
                        # 2. Send Media & Button Messages for each smart card
                        for card in smart_cards:
                            if card.get("product_id") and card.get("image_url") and card.get("image_url") != "URL":
                                card_payload = {
                                    "type": "button",
                                    "header": {
                                        "type": "image",
                                        "image": {
                                            "link": card.get("image_url")  # In production, must be public URL
                                        }
                                    },
                                    "body": {
                                        "text": f"*{card.get('product_name')}*\nPrice: {card.get('price')}"
                                    },
                                    "action": {
                                        "buttons": [
                                            {
                                                "type": "reply",
                                                "reply": {
                                                    "id": f"buy:{card.get('product_id')}",
                                                    "title": "🛒 تأكيد الشراء"
                                                }
                                            }
                                        ]
                                    }
                                }
                                await transmit_meta_graph(
                                    phone_number_id=config.get("phone_number_id", ""),
                                    access_token=config.get("access_token", ""),
                                    recipient_id=sender_wa_id,
                                    interactive_payload=card_payload
                                )
        pass
    except Exception as e:
        logger.error(f"WhatsApp core logic fail: {e}")
        pass


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
    try:
        for entry in body.get("entry", []):
            page_id = entry.get("id")
            if page_id != config.get("page_id"):
                continue
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                text_content = message.get("text", "")
                
                media_b64 = None
                media_url = None
                attachments = message.get("attachments", [])
                
                for att in attachments:
                    att_type = att.get("type")
                    if att_type in ["image", "video"]: # We treat video frames similarly, but IG vision mainly supports images here
                        url = att.get("payload", {}).get("url")
                        if url:
                            try:
                                from app.services.media_processor import download_instagram_media, encode_image_base64
                                image_bytes = await download_instagram_media(url)
                                media_b64 = encode_image_base64(image_bytes, "image/jpeg")
                                media_url = f"ig_media_url:{url}"
                                break # Only process first media for AI vision
                            except Exception as e:
                                logger.error(f"Failed to process IG media: {e}")
                
                if sender_id:
                    msg_id = message.get("mid", "")
                    if msg_id:
                        dedup_key = f"msg:{business_id}:{msg_id}"
                        if await redis_client.get(dedup_key):
                            continue
                        await redis_client.setex(dedup_key, 86400, "1")

                if not text_content.strip() and not media_b64:
                    continue

                logger.info(f"[INSTAGRAM] msg from {sender_id} for business {business_id}")
                
                ai_response, intent, _, _, smart_cards = await process_chat_core(
                    db=db, business_id=business_id, customer_platform="instagram",
                    external_id=sender_id, content=text_content,
                    media_url=media_url, media_b64=media_b64
                )
                
                if intent == "human_handoff_active":
                    return {"status": "ok"}
                
                if ai_response or smart_cards:
                    # Instagram uses slightly different send payload, handled simply here 
                    # using Graph v20.0 standard Page access
                    url = f"https://graph.facebook.com/v20.0/me/messages"
                    
                    resp_text = ai_response or ""
                    if smart_cards:
                        for c in smart_cards:
                            product_link = c.get("product_url") or ""
                            if product_link:
                                resp_text += f"\n{c.get('product_name')}: {product_link}"
                    
                    payload = {"recipient": {"id": sender_id}, "message": {"text": resp_text}}
                    headers = {"Authorization": f"Bearer {config.get('access_token', '')}", "Content-Type": "application/json"}
                    
                    if settings.INTEGRATIONS_MODE == "mock":
                        logger.info(f"[MOCK] Instagram Message to {sender_id}: {resp_text}")
                    else:
                        async with httpx.AsyncClient() as client:
                            res = await client.post(url, json=payload, headers=headers, timeout=10.0)
                            res.raise_for_status()

        pass
    except Exception as e:
        logger.error(f"Instagram core logic fail: {e}")
        pass

async def _process_tiktok(db, business_id, config, body):
    try:
        # Handling Direct Messages
        if event_type == "message.receive":
            message_info = body.get("message", {})
            sender_id = message_info.get("sender_id")
            text_content = message_info.get("text", "")
            msg_id = message_info.get("message_id", "")
            
            if sender_id and text_content and msg_id:
                dedup_key = f"msg:{business_id}:{msg_id}"
                if await redis_client.get(dedup_key):
                    return {"status": "duplicate"}
                await redis_client.setex(dedup_key, 86400, "1")

                logger.info(f"[TIKTOK] DM from {sender_id} for business {business_id}")
                ai_response, intent, _, _, smart_cards = await process_chat_core(
                    db=db, business_id=business_id, customer_platform="tiktok",
                    external_id=sender_id, content=text_content
                )
                
                if ai_response or smart_cards:
                    resp_text = ai_response or ""
                    if smart_cards:
                        for c in smart_cards:
                            resp_text += f"\nLink to {c.get('product_name')}: reply with buy:{c.get('product_id')}"
                    await transmit_tiktok_dm(config.get("access_token", ""), sender_id, resp_text)

        # Handling Video Comments
        elif event_type == "comment.create":
            comment_info = body.get("comment", {})
            sender_id = comment_info.get("author_id")
            text_content = comment_info.get("text", "")
            comment_id = comment_info.get("comment_id", "")
            item_id = comment_info.get("item_id", "") # Video ID
            
            if sender_id and text_content and comment_id:
                dedup_key = f"comment:{business_id}:{comment_id}"
                if await redis_client.get(dedup_key):
                    return {"status": "duplicate"}
                await redis_client.setex(dedup_key, 86400, "1")

                logger.info(f"[TIKTOK] Comment from {sender_id} for business {business_id}")
                
                # We prefix the content with [COMMENT] so process_chat_core can catch it
                special_payload = f"[COMMENT:{item_id}:{comment_id}] {text_content}"
                
                ai_response, intent, _, _, _ = await process_chat_core(
                    db=db, business_id=business_id, customer_platform="tiktok",
                    external_id=sender_id, content=special_payload
                )
                
                if ai_response:
                    try:
                        import json
                        response_data = json.loads(ai_response)
                        public_reply = response_data.get("public_reply")
                        private_dm = response_data.get("private_dm")
                        
                        if public_reply:
                            await transmit_tiktok_comment_reply(config.get("access_token", ""), item_id, comment_id, public_reply)
                        if private_dm:
                            await transmit_tiktok_dm(config.get("access_token", ""), sender_id, private_dm)
                    except Exception as e:
                        # Fallback if AI didn't format as JSON
                        await transmit_tiktok_comment_reply(config.get("access_token", ""), item_id, comment_id, ai_response)

        pass
    except Exception as e:
        logger.error(f"TikTok core logic fail: {e}")
        pass

async def transmit_telegram_wrapper(bot_token, chat_id, text, smart_cards=None):
    from app.api.routers.integrations import transmit_telegram
    return await transmit_telegram(bot_token, chat_id, text, smart_cards)

async def _process_telegram(db, business_id, config, body):
    try:
        chat_id = body.get("chat", {}).get("id")
        user_id = str(body.get("from", {}).get("id"))
        text_content = body.get("text", "")
        
        media_b64, media_url = None, None # Add media processing later

        if not text_content.strip() and not media_b64:
            return

        logger.info(f"[TELEGRAM] msg from {user_id} for business {business_id}")

        ai_response, intent, _, _, smart_cards = await process_chat_core(
            db=db, business_id=business_id, customer_platform="telegram",
            external_id=user_id, content=text_content,
            media_url=media_url, media_b64=media_b64
        )
        if intent == "human_handoff_active":
            return
        if ai_response or smart_cards:
            await transmit_telegram_wrapper(config.get("bot_token", ""), chat_id, ai_response or "", smart_cards=smart_cards)
    except Exception as e:
        logger.error(f"Telegram worker logic fail: {e}", exc_info=True)

async def _process_telegram_callback(db, business_id, config, payload_data):
    try:
        cb_user_id = payload_data.get("cb_user_id")
        system_prompt_inj = payload_data.get("system_prompt_inj")
        chat_id = payload_data.get("chat_id")
        
        ai_resp, intent, _, _, sc = await process_chat_core(
            db=db, business_id=business_id, customer_platform="telegram",
            external_id=cb_user_id, content=system_prompt_inj,
            media_url=None, media_b64=None
        )
        if ai_resp or sc:
            await transmit_telegram_wrapper(config.get("bot_token", ""), chat_id, ai_resp or "", smart_cards=sc)
    except Exception as e:
        logger.error(f"Telegram worker cb logic fail: {e}")

async def webhook_consumer_loop():
    logger.info("Webhook consumer loop started and waiting for events...")
    while True:
        try:
            result = await redis_client.blpop("webhook_payloads", timeout=0)
            if not result:
                continue
            
            queue_name, payload_bytes = result
            payload_data = json.loads(payload_bytes)
            
            platform = payload_data.get("platform")
            business_id = uuid.UUID(payload_data.get("business_id"))
            config = payload_data.get("config", {})
            body = payload_data.get("body", {})
            
            # Spin up a dedicated DB session per background task
            async with async_session_maker() as db:
                if platform == "whatsapp":
                    await _process_whatsapp(db, business_id, config, body)
                elif platform == "instagram":
                    await _process_instagram(db, business_id, config, body)
                elif platform == "tiktok":
                    await _process_tiktok(db, business_id, config, body)
                elif platform == "telegram":
                    await _process_telegram(db, business_id, config, body)
                elif platform == "telegram_callback":
                    await _process_telegram_callback(db, business_id, config, payload_data)
                    
        except asyncio.CancelledError:
            logger.info("Webhook consumer gracefully stopped.")
            break
        except Exception as e:
            logger.error(f"Webhook consumer processing error: {e}", exc_info=True)
            await asyncio.sleep(1) # Prevent hot loop crash
