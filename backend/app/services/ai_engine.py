import json
import uuid
from typing import List
from app.schemas.chat import AIIntentSchema
from app.models.domain import Product, Message
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

class AIEngineService:
    def __init__(self, business_id: str, business_type: str, products: List[Product], funnel_state: dict = None, language: str = "en", ai_tone: str = "Professional", knowledge_base: str = None, bank_details: dict = None, is_tiktok_comment: bool = False, platform: str = "unknown", customer_name: str = None, customer_phone: str = None, staff_members: list = None, ai_instructions: str = "", flow_vars: dict = None):
        self.business_id = business_id
        self.business_type = business_type
        self.is_tiktok_comment = is_tiktok_comment
        self.platform = platform
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.products = products
        self.funnel_state = funnel_state or {}
        
        lang_map = {"ar": "Arabic", "en": "English", "tr": "Turkish"}
        self.language_code = language.lower()[:2]
        self.language = lang_map.get(self.language_code, "Arabic")
        
        self.ai_tone = ai_tone
        self.knowledge_base = knowledge_base or 'No specific knowledge base provided.'
        self.bank_details = bank_details
        self.staff_members = staff_members or []
        self.ai_instructions = ai_instructions
        self.flow_vars = flow_vars or {}

    async def generate_system_prompt(self, db, user_message: str = None) -> str:
        from app.services.prompt_factory import DomainPromptFactory
        from app.services.availability_service import AvailabilityService
        from app.services.knowledge_service import search_knowledge
        import datetime

        # Context Details
        products_context = json.dumps([
            {"id": str(p.id), "name": p.name, "price": p.price, "type": getattr(p, "item_type", "product"), "duration": getattr(p, "duration", 60), "image_available": bool(p.image_url)}
            for p in self.products[:50]
        ], ensure_ascii=False)
        
        availability_info = await AvailabilityService.get_top_free_slots(db, self.business_id, self.business_type)
        
        staff_str = ", ".join(self.staff_members) if self.staff_members else "General Staff"
        payment_info = json.dumps(self.bank_details, ensure_ascii=False) if self.bank_details else 'No specific payment instructions provided.'

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_ast = now_utc + datetime.timedelta(hours=3)
        date_str_today = now_ast.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S (AST/Turkey Time)")

        if user_message:
            try:
                knowledge_context_str = await search_knowledge(db, uuid.UUID(str(self.business_id)), user_message, top_k=5)
            except Exception as e:
                logger.error(f"Knowledge search error: {e}")
                knowledge_context_str = self.knowledge_base or ''
        else:
            knowledge_context_str = self.knowledge_base or ''

        return DomainPromptFactory.generate_prompt(
            business_type=self.business_type,
            customer_name=self.customer_name,
            customer_phone=self.customer_phone,
            products_context=products_context,
            staff_str=staff_str,
            availability_info=availability_info,
            knowledge_base=knowledge_context_str,
            payment_info=payment_info,
            language=self.language,
            ai_tone=self.ai_tone,
            date_str_today=date_str_today,
            funnel_state=self.funnel_state,
            ai_instructions=self.ai_instructions,
            flow_vars=self.flow_vars
        )

    def validate_input(self, text: str) -> bool:
        if not text: return True
        forbidden_phrases = ["ignore previous instructions", "system prompt", "you are no longer", "forget all instructions", "override instructions", "ignore all rules", "تجاهل التعليمات", "تجاهل الأوامر"]
        lower_text = str(text).lower()
        return not any(phrase in lower_text for phrase in forbidden_phrases)

    async def get_response(self, db, user_message: str, conversation=None, media_b64: str = None, user_msg_id=None) -> dict:
        from app.services.ai_router import AIRouter
        import hashlib
        from app.core.redis_client import redis_client

        # 1. Prompt Injection Defense
        if not self.validate_input(user_message):
            logger.warning(f"Prompt injection detected and blocked for business: {self.business_id}")
            return {
                "ai_output": '{"response": "أرجو منك البقاء في سياق خدماتنا.", "intent": "none", "data": {}}',
                "provider": "security_guard",
                "model": "rule_based"
            }
            
        # 2. Complexity Routing Heuristics
        is_simple = False
        lower_msg = str(user_message).strip().lower()
        if not self.funnel_state and len(lower_msg) < 50 and not any(kw in lower_msg for kw in ["buy", "order", "book", "cancel", "شراء", "حجز", "إلغاء", "بكم", "سعر", "price", "how much"]):
            is_simple = True

        system_prompt = await self.generate_system_prompt(db, user_message)
        messages = [{"role": "system", "content": system_prompt}]

        history_count = 0
        if conversation is not None:
            query = select(Message).where(
                Message.conversation_id == conversation.id,
                Message.business_id == uuid.UUID(self.business_id)
            )
            if user_msg_id:
                query = query.where(Message.id != user_msg_id)
            
            msg_res = await db.execute(query.order_by(Message.created_at.desc()).limit(10))
            for m in msg_res.scalars().all()[::-1]:
                history_count += 1
                messages.append({"role": "user" if m.sender_type == "user" else "assistant", "content": m.content})

        # 3. Safe Semantic Caching for generic small talk (ONLY IF NO HISTORY)
        cache_key = None
        if not self.funnel_state and is_simple and not media_b64 and history_count == 0:
            h = hashlib.md5(f"{self.business_id}:{lower_msg}".encode()).hexdigest()
            cache_key = f"ai_cache:{h}"
            try:
                cached_res = await redis_client.get(cache_key)
                if cached_res:
                    return {
                        "ai_output": cached_res,
                        "provider": "redis_cache",
                        "model": "semantic_hit"
                    }
            except Exception as e:
                logger.error(f"Redis cache read error: {e}")

        user_content = user_message
        
        reminder = "\n\n[CRITICAL REMINDER: You MUST reply with ONLY a valid JSON object. Put your reply inside the 'response' key. DO NOT output plain text.]"
        
        if media_b64:
            user_content = [{"type": "text", "text": (user_message or "Image") + reminder}, {"type": "image_url", "image_url": {"url": media_b64}}]
        else:
            user_content = str(user_message) + reminder
            
        messages.append({"role": "user", "content": user_content})

        # Apply Model Downgrade for Cost Saving
        target_override = "gpt-4o-mini" if is_simple else None

        try:
            result = await AIRouter.generate(db, messages, force_model=target_override, vision=bool(media_b64))
            cleaned_text = result["text"].strip()
            
            s = cleaned_text.find('{')
            e = cleaned_text.rfind('}')
            if s != -1 and e != -1:
                cleaned_text = cleaned_text[s:e+1]

            # Write to cache if it was marked simple
            if cache_key and result.get("provider") != "redis_cache":
                try:
                    await redis_client.setex(cache_key, 7200, cleaned_text) # Cache for 2 hours
                except Exception as e:
                    logger.error(f"Redis cache write error: {e}")

            return {
                "ai_output": cleaned_text,
                "provider": result["provider"],
                "model": result["model"],
            }
        except Exception as e:
            logger.error(f"AI Generator Error: {e}")
            raise Exception("AI processing failed")

    def validate_intent(self, ai_output_str_or_dict) -> AIIntentSchema:
        try:
            if isinstance(ai_output_str_or_dict, dict):
                data = ai_output_str_or_dict
            else:
                cleaned = str(ai_output_str_or_dict).strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                data = json.loads(cleaned.strip())
                
            return AIIntentSchema(**data)
        except Exception as e:
            logger.warning(f"Validation failed: {e}. Output was {ai_output_str_or_dict}")
            fallback_ar = "عذراً، حدث خطأ تقني بسيط أثناء معالجة طلبك المتسلسل. هل يمكنك تأكيد خيارك الأخير؟"
            fallback_tr = "İsteğinizi işlerken küçük bir teknik hata oluştu. Seçiminizi tekrar onaylayabilir misiniz?"
            fallback_en = "I encountered a minor formatting issue while processing your request. Could you clarify your choice?"
            
            fb = fallback_en
            if self.language_code == "ar": fb = fallback_ar
            elif self.language_code == "tr": fb = fallback_tr

            return AIIntentSchema(intent="none", confidence=0.0, response=fb, lead_priority="None", data={})
