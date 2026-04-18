import uuid
import time
import json
import logging
logger = logging.getLogger(__name__)
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models.domain import Customer, Conversation, Message, Product, Order, UsageLog, Appointment, SystemErrorLog
from app.models.business import Business
from app.services.ai_engine import AIEngineService
from app.config.plans import PLANS
from app.services.settings_service import SettingsService
from app.models.ai_usage_log import AIUsageLog
from app.services.token_service import TokenService
from app.services.cost_service import CostService
from app.services.notification_service import NotificationService
from typing import Tuple, List, Dict
import re
import time

def detect_language(text: str) -> str:
    if not text:
        return "en"
    if re.search(r'(?i)[çğışöüÇĞİIŞÖÜ]|\b(merhaba|selam|nasılsın|iyi|evet|hayır|lütfen|teşekkür|ondan|istiyorum|sağol|tamam)\b', text):
        return "tr"
    if re.search(r'[\u0600-\u06FF\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        return "ar"
    return "en"


async def process_chat_core(
    db: AsyncSession,
    business_id: uuid.UUID,
    customer_platform: str,
    external_id: str,
    content: str,
    media_url: str = None,
    media_b64: str = None
) -> Tuple[str, str, str, str, List[Dict]]:
    """
    Core pipeline for processing incoming messages logic.
    Returns: (ai_response_text, intent_string, user_msg_id, conversation_id, smart_cards)
    """

    # ── 1. Find or create Customer (race-condition safe) ─────────────────────
    result = await db.execute(
        select(Customer).where(
            Customer.business_id == business_id,
            Customer.platform == customer_platform,
            Customer.external_id == external_id,
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        
        is_comment = False
        if content.startswith("[COMMENT:"):
            is_comment = True

        try:
            initial_tags = []
            if customer_platform == "tiktok":
                initial_tags.append("platform:tiktok")
            if is_comment:
                initial_tags.append("source:comment")
                
            customer = Customer(
                business_id=business_id,
                platform=customer_platform,
                external_id=external_id,
                tags=initial_tags
            )
            db.add(customer)
            await db.flush()
        except IntegrityError:
            # Concurrent request already created this customer — fetch it.
            await db.rollback()
            result = await db.execute(
                select(Customer).where(
                    Customer.business_id == business_id,
                    Customer.platform == customer_platform,
                    Customer.external_id == external_id,
                )
            )
            customer = result.scalar_one()

    # Ensure tags are dynamically updated for returning customers
    is_comment = content.startswith("[COMMENT:")
    tags_modified = False
    
    current_tags = list(customer.tags) if customer.tags else []
    if customer_platform == "tiktok" and "platform:tiktok" not in current_tags:
        current_tags.append("platform:tiktok")
        tags_modified = True
    if is_comment and "source:comment" not in current_tags:
        current_tags.append("source:comment")
        tags_modified = True
        
    if tags_modified:
        customer.tags = current_tags
        db.add(customer)
        await db.flush()

    # ── 2. Find most-recent Conversation (avoids MultipleResultsFound) ───────
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.business_id == business_id,
            Conversation.customer_id == customer.id,
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            business_id=business_id,
            customer_id=customer.id,
            status="bot",
        )
        db.add(conversation)
        await db.flush()

    # ── 3. Intercept Reset Commands ─────────────────────────────
    if content.strip().lower() in ["/start", "reset", "/reset", "تصفير"]:
        if conversation:
            from sqlalchemy import delete
            await db.execute(delete(Message).where(Message.conversation_id == conversation.id))
            
            from app.services.funnel_state import FunnelStateService
            await FunnelStateService.clear_state(str(conversation.id))
            
            conversation.status = "bot"
            db.add(conversation)
            await db.flush()
        
        return "🧹 تم تصفير المحادثة والذاكرة بنجاح! / Hafıza ve sohbet sıfırlandı!\n\nكيف يمكنني مساعدتك؟ / Size nasıl yardımcı olabilirim?", "none", str(uuid.uuid4()), str(conversation.id), []

    user_msg = Message(

        business_id=business_id,
        conversation_id=conversation.id,
        sender_type="user",
        content=content,
        media_url=media_url
    )
    db.add(user_msg)
    await db.flush()
    
    try:
        import json as _json
        from app.api.deps import redis_client
        event = _json.dumps({
            "type": "new_message",
            "conversation_id": str(conversation.id),
            "customer_phone": customer.external_id,
            "platform": customer.platform,
            "content": (content or "")[:120],
        })
        await redis_client.publish(f"merchant:{business_id}:events", event)
    except Exception as _pub_err:
        logger.warning(f"SSE publish failed (non-critical): {_pub_err}")

    # ── 4. Human-handoff guard — skip AI when an agent is active ─────────────
    if conversation.status == "human":
        await db.commit()
        return ("", "human_handoff_active", str(user_msg.id), str(conversation.id), [])

    # ── 5. Load business and active products ──────────────────────────────────
    b_res = await db.execute(select(Business).where(Business.id == business_id))
    business = b_res.scalar_one()

    # ── 5.1. Business status guard ────────────────────────────────────────────
    if business.status != "active":
        assistant_msg = Message(
            business_id=business_id,
            conversation_id=conversation.id,
            sender_type="assistant",
            content="This service is temporarily unavailable.",
        )
        db.add(assistant_msg)
        await db.commit()
        return ("This service is temporarily unavailable.", "business_disabled", str(user_msg.id), str(conversation.id), [])

    p_res = await db.execute(
        select(Product).where(
            Product.business_id == business_id,
            Product.is_active == True,
        ).limit(50)
    )
    products = p_res.scalars().all()

    # ── 5.5. Token Limit Enforcement (monthly) ───────────────────────────────
    start_of_month = date.today().replace(day=1)

    import json
    from app.api.deps import redis_client
    cache_key = f"token_usage:{business_id}:{start_of_month.isoformat()}"
    cached_tokens = await redis_client.get(cache_key)
    
    if cached_tokens:
        tokens_used = int(cached_tokens)
    else:
        u_res = await db.execute(
            select(func.sum(UsageLog.tokens_used)).where(
                UsageLog.business_id == business_id,
                UsageLog.date_logged >= start_of_month,
            )
        )
        tokens_used = u_res.scalar() or 0
        await redis_client.setex(cache_key, 60, str(tokens_used))

    plan_limit_str = await SettingsService.get(db, f"{business.plan_name}_tokens")
    plan_limit = int(plan_limit_str) if plan_limit_str else None

    if plan_limit is not None and tokens_used >= plan_limit:
        ai_msg_content = "Token limit reached"
        intent_value = "limit_reached"
        # Save Bot Message
        bot_msg = Message(
            business_id=business_id,
            conversation_id=conversation.id,
            sender_type="bot",
            content=ai_msg_content,
            intent=intent_value,
            model_used="none",
            token_count=0 
        )
        db.add(bot_msg)
        await db.commit()
        await db.refresh(user_msg)

        return ai_msg_content, intent_value, str(user_msg.id), str(conversation.id), []

    # ── 5.6. Evaluate State Machine & Flow Engine ──────────────────────────────
    from app.services.flow_engine import FlowEngine
    session_target = external_id if customer_platform == "telegram" else str(conversation.id)
    flow_res = await FlowEngine.evaluate_message(db, business_id, session_target, content)
    
    if flow_res["handled"] and not flow_res["ai_handoff"]:
        if flow_res["response"]:
            # Save Bot Message
            bot_msg = Message(
                business_id=business_id,
                conversation_id=conversation.id,
                sender_type="bot",
                content=flow_res["response"],
                intent=flow_res["intent"],
                model_used="bot_flow",
                token_count=0 
            )
            db.add(bot_msg)
            await db.commit()
            await db.refresh(user_msg)
            
            return flow_res["response"], flow_res["intent"], str(user_msg.id), str(conversation.id), []
        else:
            # E.g., wait_for_input capturing state implicitly without reply
            return "", flow_res["intent"], str(user_msg.id), str(conversation.id), []

    # ── 6. Call AI engine ─────────────────────────────────────────────────────
    detected_lang = detect_language(content)
    
    # ── 6.1 Tone Injection from Flow ──
    dynamic_tone = business.ai_tone
    if flow_res["ai_handoff"] and flow_res["ai_tone"]:
        dynamic_tone = flow_res["ai_tone"]
    
    from app.services.funnel_state import FunnelStateService
    current_funnel_state = await FunnelStateService.get_state(str(conversation.id))
    from app.api.deps import redis_client
    crm_vars = await redis_client.hgetall(f"crm_vars:{conversation.id}")
    if isinstance(crm_vars, dict) and crm_vars:
        crm_vars = {k.decode('utf-8') if isinstance(k, bytes) else k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in crm_vars.items()}
    else:
        crm_vars = {}
        
    ai_engine = AIEngineService(
        business_id=str(business.id),
        business_type=business.business_type, 
        products=products, 
        funnel_state=current_funnel_state,
        language=detected_lang,
        ai_tone=dynamic_tone,
        ai_instructions=flow_res.get("ai_instructions", ""),
        flow_vars=crm_vars,
        knowledge_base=business.knowledge_base,
        bank_details=business.bank_details,
        is_tiktok_comment=is_comment,
        platform=customer_platform,
        customer_name=customer.name,
        customer_phone=customer.phone,
        staff_members=business.staff_members
    )

    provider = "unknown"
    model = "unknown"

    resp_time = None
    smart_cards = []
    try:
        start_time = time.time()
        raw_res = await ai_engine.get_response(db, content, conversation, media_b64=media_b64, user_msg_id=user_msg.id)
        resp_time = time.time() - start_time
        
        ai_intent = ai_engine.validate_intent(raw_res["ai_output"])
        
        if ai_intent.booking_in_progress or ai_intent.data or getattr(ai_intent, 'funnel_stage', 'none') != "none":
            new_data = ai_intent.data or {}
            new_data["funnel_stage"] = getattr(ai_intent, 'funnel_stage', 'none')
            new_data["booking_in_progress"] = getattr(ai_intent, 'booking_in_progress', False)
            await FunnelStateService.update_state(str(conversation.id), new_data)
            
        if ai_intent.intent in ["book_appointment", "create_order"]:
            await FunnelStateService.clear_state(str(conversation.id))
            
        provider = raw_res["provider"]
        model = raw_res["model"]

        # Set defaults from AI response FIRST — then override on error paths only.
        ai_msg_content = ai_intent.response
        if getattr(ai_intent, 'public_reply', None):
            import json
            ai_msg_content = json.dumps({
                "public_reply": ai_intent.public_reply,
                "private_dm": getattr(ai_intent, 'private_dm', '')
            })
            
        if ai_msg_content == "EOF":
            ai_msg_content = ""
            
        intent_value = ai_intent.intent

        if getattr(ai_intent, 'lead_priority', None) and ai_intent.lead_priority != "None":
            conversation.lead_priority = ai_intent.lead_priority
            db.add(conversation)

        # ── 7. Intent-specific processing ─────────────────────────────────────
        if ai_intent.intent in ["create_order", "suggest_product", "none"]:
            product_id_str = ai_intent.data.get("product_id") if ai_intent.data else None

            # Fallback for hidden JSON blocks embedded in response text by LLM
            if not product_id_str:
                import re
                card_match = re.search(r"```json\n(.*?)\n```", ai_msg_content, re.DOTALL)
                if card_match:
                    try:
                        import json
                        card_data = json.loads(card_match.group(1))
                        product_id_str = card_data.get("product_id")
                        # Strip it so it doesn't show raw json object as text to the user
                        ai_msg_content = ai_msg_content.replace(card_match.group(0), "").strip()
                    except (json.JSONDecodeError, AttributeError):
                        pass

            if not product_id_str:
                if ai_intent.intent == "suggest_product" or ai_intent.intent == "create_order":
                    intent_value = "none"
            else:
                try:
                    target_pid = uuid.UUID(product_id_str)
                    matched_product = next(
                        (p for p in products if p.id == target_pid), None
                    )

                    if matched_product:
                        if ai_intent.intent == "create_order":
                            new_order = Order(
                                business_id=business_id,
                                customer_id=customer.id,
                                status="pending",
                                total_amount=matched_product.price,
                                payload={
                                    "product_name": matched_product.name,
                                    "product_id": str(target_pid),
                                    "quantity": 1,
                                },
                            )
                            db.add(new_order)
                            
                            # Alert the merchant about the new order immediately
                            import asyncio
                            from app.services.notification_service import NotificationService
                            from app.models.business import BusinessFeature
                            tg_feat = await db.execute(select(BusinessFeature).where(
                                BusinessFeature.business_id == business_id, BusinessFeature.feature_type == "telegram"))
                            tg_int = tg_feat.scalar_one_or_none()
                            custom_token = (tg_int.config or {}).get("bot_token") if tg_int and tg_int.is_active else None

                            msg_alert = f"🛒 New Order Created!\nCustomer: {customer.name or 'Unknown'} ({customer.phone or 'No phone'})\nProduct: {matched_product.name}\nPrice: {matched_product.price}"
                            asyncio.create_task(NotificationService.dispatch_merchant_alert(business, "ORDER", msg_alert, custom_bot_token=custom_token))
                        elif ai_intent.intent == "suggest_product":
                            smart_cards.append({
                                "product_id": str(matched_product.id),
                                "product_name": matched_product.name,
                                "price": str(matched_product.price),
                                "image_url": matched_product.image_url or "https://via.placeholder.com/150"
                            })
                    else:
                        if not ai_msg_content.strip():
                            ai_msg_content = "عذراً، لم أتمكن من العثور على تفاصيل هذا المنتج." if detected_lang in ["ar", "Arabic"] else ("Özür dilerim, bu ürünü bulamadım." if detected_lang in ["tr", "Turkish"] else "I could not find that product in our catalog.")
                        intent_value = "none"

                except ValueError:
                    if not ai_msg_content.strip():
                        ai_msg_content = "عذراً، لم يتم العثور على المنتج المطلوب." if detected_lang in ["ar", "Arabic"] else ("Seçilen ürün bulunamadı." if detected_lang in ["tr", "Turkish"] else "Product not found.")
                    if ai_intent.intent in ["create_order", "suggest_product"]:
                        intent_value = "error"


        elif ai_intent.intent == "book_appointment":
            product_id_str = ai_intent.data.get("product_id") if ai_intent.data else None
            appointment_time = ai_intent.data.get("appointment_time") if ai_intent.data else None
            
            cust_name = ai_intent.data.get("customer_name") if ai_intent.data else None
            cust_phone = ai_intent.data.get("phone") if ai_intent.data else None
            staff_name = ai_intent.data.get("staff_name") if ai_intent.data else None
            
            # Persist customer info if provided
            if cust_name or cust_phone:
                if cust_name and not customer.name:
                    customer.name = cust_name
                if cust_phone and not customer.phone:
                    customer.phone = cust_phone
                db.add(customer)
                
            if not product_id_str or not appointment_time:
                # Let the AI's natural follow-up question pass to the user
                intent_value = "none"
            else:
                try:
                    target_pid = uuid.UUID(product_id_str)
                    matched_product = next(
                        (p for p in products if p.id == target_pid), None
                    )
                    
                    if matched_product and matched_product.item_type == "service":
                        from dateutil import parser
                        try:
                            start_dt = parser.parse(appointment_time)
                            end_dt = start_dt
                            if matched_product.duration:
                                from datetime import timedelta
                                end_dt = start_dt + timedelta(minutes=matched_product.duration)
                        except Exception:
                            start_dt = None
                            
                        if start_dt:
                            # Idempotency check: prevent duplicate appointments
                            existing_appt_res = await db.execute(
                                select(Appointment).where(
                                    Appointment.customer_id == customer.id,
                                    Appointment.business_id == business_id,
                                    Appointment.start_time == start_dt,
                                    Appointment.title.like(f"%{matched_product.name}%")
                                )
                            )
                            if existing_appt_res.scalar_one_or_none():
                                logger.info(f"Duplicate booking prevented for {start_dt}")
                            else:
                                title_suffix = f" (مع {staff_name})" if staff_name else ""
                                new_booking = Appointment(
                                    business_id=business_id,
                                    customer_id=customer.id,
                                    status="confirmed",
                                    title=f"{customer.name or 'Customer'} - {matched_product.name}{title_suffix}",
                                    start_time=start_dt,
                                    end_time=end_dt,
                                    notes=f"Booked via AI Chat. Service: {matched_product.name}",
                                    staff_name=staff_name
                                )
                                db.add(new_booking)
                                
                                staff_line = f"\nStaff: {staff_name}" if staff_name else ""
                                msg = f"New Appointment Booked:\nCustomer: {customer.name or 'Unknown'} ({customer.phone or 'No phone'})\nService: {matched_product.name}{staff_line}\nTime: {start_dt.strftime('%Y-%m-%d %H:%M')}\nPlatform: {customer.platform}"
                                import asyncio
                                from app.models.business import BusinessFeature
                                tg_feat = await db.execute(select(BusinessFeature).where(
                                    BusinessFeature.business_id == business_id, BusinessFeature.feature_type == "telegram"))
                                tg_int = tg_feat.scalar_one_or_none()
                                custom_token = (tg_int.config or {}).get("bot_token") if tg_int and tg_int.is_active else None
                                asyncio.create_task(NotificationService.dispatch_merchant_alert(business, "APPOINTMENT", msg, custom_bot_token=custom_token))
                        else:
                            ai_msg_content = "عذراً، لم أتمكن من فهم صيغة التاريخ والوقت." if detected_lang in ["ar", "Arabic"] else ("Tarih ve saat formatını anlayamadım." if detected_lang in ["tr", "Turkish"] else "I could not understand the date and time format you provided.")
                            intent_value = "error"
                    else:
                        ai_msg_content = "عذراً، لم أتمكن من العثور على هذه الخدمة في الكتالوج." if detected_lang in ["ar", "Arabic"] else ("Kataloğumuzda bu hizmeti bulamadım." if detected_lang in ["tr", "Turkish"] else "I could not find that service in our catalog.")
                        intent_value = "none"
                        
                except ValueError:
                    ai_msg_content = "حدث خطأ أثناء تحديد الخدمة." if detected_lang in ["ar", "Arabic"] else ("Hizmeti belirlerken bir hata oluştu." if detected_lang in ["tr", "Turkish"] else "There was an error identifying the service.")
                    intent_value = "error"

        elif ai_intent.intent == "handoff_human":
            import asyncio
            from app.models.business import BusinessFeature
            tg_feat = await db.execute(select(BusinessFeature).where(
                BusinessFeature.business_id == business_id, BusinessFeature.feature_type == "telegram"))
            tg_int = tg_feat.scalar_one_or_none()
            custom_token = (tg_int.config or {}).get("bot_token") if tg_int and tg_int.is_active else None
            
            msg_alert = f"🚨 طلب مساعدة وتواصل مع الإدارة!\nالعميل: {customer.name or 'غير معروف'} ({customer.phone or 'بدون رقم'})\nالمنصة: {customer.platform}\n\nيرجى الدخول وتفقد الرسائل أو متابعة الدردشة مباشرة!"
            asyncio.create_task(NotificationService.dispatch_merchant_alert(business, "SUPPORT", msg_alert, custom_bot_token=custom_token))
            # ai_msg_content and intent_value stay as the AI set them. The bot will continue interacting.

        elif ai_intent.intent == "technical_support":
            support_phone = await SettingsService.get(db, "support_phone")
            
            if support_phone and support_phone not in ai_msg_content:
                support_prefix = "\n\n⚠️ "
                if detected_lang in ["tr", "Turkish"]:
                    support_prefix += f"Destek Hattı: {support_phone}"
                elif detected_lang in ["ar", "Arabic"]:
                    support_prefix += f"رقم الدعم الفني: {support_phone}"
                else:
                    support_prefix += f"Support Line: {support_phone}"
                ai_msg_content = f"{ai_msg_content}{support_prefix}"
                
            intent_value = "technical_support"
            
            msg = f"Technical Support Request:\nCustomer: {customer.name or 'Unknown'} ({customer.phone or 'No phone'})\nPlatform: {customer.platform}\n\nPlease check your recent chats to assist them."
            import asyncio
            asyncio.create_task(NotificationService.dispatch_merchant_alert(business, "SUPPORT", msg))

        # Let AI handle the language fluidity naturally without overriding

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.error(f"AI processing failed: {e}\n{tb_str}")
        try:
            error_log = SystemErrorLog(
                business_id=business_id,
                error_type="ai_error",
                message=f"{str(e)}\n{tb_str[:500]}",
            )
            db.add(error_log)
        except Exception:
            pass
            
        import asyncio
        asyncio.create_task(NotificationService.dispatch_admin_error(
            f"AI Engine Failure [Business: {business_id}]", 
            f"Error: {e}\n\n{tb_str}"
        ))
        
        ai_msg_content = "Something went wrong on our end. Please try again in a moment."
        intent_value = "error"

    # ── 8. Persist the assistant reply ────────────────────────────────────────
    assistant_msg = Message(
        business_id=business_id,
        conversation_id=conversation.id,
        sender_type="assistant",
        content=ai_msg_content,
        response_time=resp_time,
    )
    db.add(assistant_msg)
    
    # ── 9. Update Usage Log ──────────────────────────────────────────────────
    tokens_used_now = (
        TokenService.count(content) +
        TokenService.count(ai_msg_content)
    )
    import sqlalchemy.exc
    
    today_date = date.today()
    try:
        if tokens_used_now > 0:
            from sqlalchemy import update
            today_res = await db.execute(
                select(UsageLog).where(
                    UsageLog.business_id == business_id,
                    UsageLog.date_logged == today_date,
                )
            )
            usage_today = today_res.scalar_one_or_none()
            if usage_today:
                await db.execute(
                    update(UsageLog)
                    .where(UsageLog.business_id == business_id, UsageLog.date_logged == today_date)
                    .values(
                        tokens_used=UsageLog.tokens_used + tokens_used_now,
                        request_count=UsageLog.request_count + 1
                    )
                )
            else:
                db.add(UsageLog(
                    business_id=business_id,
                    tokens_used=tokens_used_now,
                    request_count=1,
                    date_logged=today_date
                ))
    except sqlalchemy.exc.IntegrityError:
        # Race condition handle: another concurrent request created the row
        today_res = await db.execute(
            select(UsageLog).where(
                UsageLog.business_id == business_id,
                UsageLog.date_logged == today_date,
            )
        )
        usage_today = today_res.scalar_one()
        usage_today.tokens_used += tokens_used_now
        usage_today.request_count = (usage_today.request_count or 0) + 1

    # C3 Invalidate Cache immediately to ensure billing accuracy
    start_of_month = today_date.replace(day=1)
    await redis_client.delete(f"token_usage:{business_id}:{start_of_month.isoformat()}")
    # ── 10. Log detailed AI Analytics ─────────────────────────────────────────
    if provider != "unknown":
        input_tokens = TokenService.count(content)
        output_tokens = TokenService.count(ai_msg_content)
        total_tokens = input_tokens + output_tokens
        cost = CostService.calculate(provider, input_tokens, output_tokens)

        analytics_log = AIUsageLog(
            id=str(uuid.uuid4()),
            business_id=str(business_id),
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=cost
        )
        db.add(analytics_log)

    await db.commit()

    # ── 11. Trigger Auto-Tagging Async ─────────────────────────────────────────
    import asyncio
    from app.services.ai_tagging import auto_tag_customer
    from app.db.session import async_session_maker
    
    async def run_tagger(cid, c_id):
        async with async_session_maker() as session:
            await auto_tag_customer(session, str(cid), str(c_id))
            
    asyncio.create_task(run_tagger(customer.id, conversation.id))

    return (ai_msg_content, intent_value, str(user_msg.id), str(conversation.id), smart_cards)
