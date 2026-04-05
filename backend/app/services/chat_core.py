import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.models.domain import Customer, Conversation, Message, Product, Order, UsageLog
from app.models.business import Business
from app.services.ai_engine import AIEngineService
from app.config.plans import PLANS
from app.services.settings_service import SettingsService
from app.models.ai_usage_log import AIUsageLog
from app.services.token_service import TokenService
from app.services.cost_service import CostService
import re

def detect_language(text: str) -> str:
    if not text:
        return "en"
    if re.search(r'[\u0600-\u06FF\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]', text):
        return "ar"
    if re.search(r'[çğışöüÇĞİIŞÖÜ]', text):
        return "tr"
    return "en"


async def process_chat_core(
    db: AsyncSession,
    business_id: uuid.UUID,
    customer_platform: str,
    external_id: str,
    content: str,
) -> tuple[str, str, str, str]:
    """
    Single source of truth for AI chat processing.
    Called by: /api/chat/message (simulator) and all integration webhooks.
    Returns: (ai_response, intent, message_id, conversation_id)
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
        try:
            customer = Customer(
                business_id=business_id,
                platform=customer_platform,
                external_id=external_id,
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

    # ── 3. Persist the incoming user message ──────────────────────────────────
    user_msg = Message(
        business_id=business_id,
        conversation_id=conversation.id,
        sender_type="user",
        content=content,
    )
    db.add(user_msg)
    await db.flush()

    # ── 4. Human-handoff guard — skip AI when an agent is active ─────────────
    if conversation.status == "human":
        await db.commit()
        return ("", "human_handoff_active", str(user_msg.id), str(conversation.id))

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
        return ("This service is temporarily unavailable.", "business_disabled", str(user_msg.id), str(conversation.id))

    p_res = await db.execute(
        select(Product).where(
            Product.business_id == business_id,
            Product.is_active == True,
        )
    )
    products = p_res.scalars().all()

    # ── 5.5. Token Limit Enforcement (monthly) ───────────────────────────────
    start_of_month = date.today().replace(day=1)

    u_res = await db.execute(
        select(func.sum(UsageLog.tokens_used)).where(
            UsageLog.business_id == business_id,
            UsageLog.date_logged >= start_of_month,
        )
    )
    tokens_used = u_res.scalar() or 0

    plan_limit_str = await SettingsService.get(db, f"{business.plan_name}_tokens")
    plan_limit = int(plan_limit_str) if plan_limit_str else None

    if plan_limit is not None and tokens_used >= plan_limit:
        ai_msg_content = "Token limit reached"
        intent_value = "limit_reached"
        # Persist the assistant reply
        assistant_msg = Message(
            business_id=business_id,
            conversation_id=conversation.id,
            sender_type="assistant",
            content=ai_msg_content,
        )
        db.add(assistant_msg)
        await db.commit()
        return (ai_msg_content, intent_value, str(user_msg.id), str(conversation.id))

    # ── 6. Call AI engine ─────────────────────────────────────────────────────
    detected_lang = detect_language(content)
    ai_engine = AIEngineService(business_type=business.business_type, products=products, language=detected_lang)

    provider = "unknown"
    model = "unknown"

    try:
        raw_res = await ai_engine.get_response(db, content, conversation)
        ai_intent = ai_engine.validate_intent(raw_res["ai_output"])
        
        provider = raw_res["provider"]
        model = raw_res["model"]

        # Set defaults from AI response FIRST — then override on error paths only.
        ai_msg_content = ai_intent.response
        intent_value = ai_intent.intent

        # ── 7. Intent-specific processing ─────────────────────────────────────
        if ai_intent.intent == "create_order":
            product_id_str = ai_intent.data.get("product_id") if ai_intent.data else None

            if not product_id_str:
                # AI did not identify a product — do not create order.
                ai_msg_content = "I need to know exactly which product you want. Could you please clarify?"
                intent_value = "none"
            else:
                try:
                    target_pid = uuid.UUID(product_id_str)
                    matched_product = next(
                        (p for p in products if p.id == target_pid), None
                    )

                    if matched_product:
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
                        # ai_msg_content and intent_value stay as the AI set them.
                    else:
                        ai_msg_content = "I could not find that product in our current catalog. Please try again."
                        intent_value = "none"

                except ValueError:
                    # AI returned a non-UUID string for product_id.
                    ai_msg_content = "There was an error identifying the product. Please describe what you want again."
                    intent_value = "error"

        elif ai_intent.intent == "handoff_human":
            conversation.status = "human"
            db.add(conversation)
            # ai_msg_content and intent_value stay as the AI set them.

        elif ai_intent.intent == "technical_support":
            support_phone = await SettingsService.get(db, "support_phone")
            ai_msg_content = f"⚠️ Support Required\n\n📞 {support_phone}"
            intent_value = "technical_support"

        # Language Failsafe
        resp_lang = detect_language(ai_msg_content)
        if resp_lang != detected_lang and intent_value == "none":
            if detected_lang == "ar":
                ai_msg_content = "أرجو إعادة صياغة طلبك لو سمحت"
            elif detected_lang == "tr":
                ai_msg_content = "Lütfen isteğinizi yeniden ifade edin"
            else:
                ai_msg_content = "Please rephrase your request"
            intent_value = "none"

    except Exception:
        ai_msg_content = "Something went wrong on our end. Please try again in a moment."
        intent_value = "error"

    # ── 8. Persist the assistant reply ────────────────────────────────────────
    assistant_msg = Message(
        business_id=business_id,
        conversation_id=conversation.id,
        sender_type="assistant",
        content=ai_msg_content,
    )
    db.add(assistant_msg)
    
    # ── 9. Update Usage Log ──────────────────────────────────────────────────
    tokens_used_now = (
        TokenService.count(content) +
        TokenService.count(ai_msg_content)
    )
    today_res = await db.execute(
        select(UsageLog).where(
            UsageLog.business_id == business_id,
            UsageLog.date_logged == date.today(),
        )
    )
    usage_today = today_res.scalar_one_or_none()
    if usage_today:
        usage_today.tokens_used += tokens_used_now
        usage_today.request_count = (usage_today.request_count or 0) + 1
    else:
        db.add(UsageLog(
            business_id=business_id,
            tokens_used=tokens_used_now,
            request_count=1,
        ))

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

    return (ai_msg_content, intent_value, str(user_msg.id), str(conversation.id))
