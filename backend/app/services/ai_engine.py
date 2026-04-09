import json
import uuid
from typing import List
from app.schemas.chat import AIIntentSchema
from app.models.domain import Product, Message
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

class AIEngineService:
    def __init__(self, business_id: str, business_type: str, products: List[Product], language: str = "en", ai_tone: str = "Professional", knowledge_base: str = None, bank_details: dict = None, is_tiktok_comment: bool = False, platform: str = "unknown", customer_name: str = None, customer_phone: str = None, staff_members: list = None):
        self.business_id = business_id
        self.business_type = business_type
        self.is_tiktok_comment = is_tiktok_comment
        self.platform = platform
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.products = products
        
        lang_map = {"ar": "Arabic", "en": "English", "tr": "Turkish"}
        self.language_code = language.lower()[:2]
        self.language = lang_map.get(self.language_code, "Arabic")
        
        self.ai_tone = ai_tone
        self.knowledge_base = knowledge_base or 'No specific knowledge base provided.'
        self.bank_details = bank_details
        self.staff_members = staff_members or []

    async def generate_system_prompt(self, db) -> str:
        # Context Details
        products_context = json.dumps([
            {"id": str(p.id), "name": p.name, "price": p.price, "type": getattr(p, "item_type", "product"), "duration": getattr(p, "duration", 60), "image_available": bool(p.image_url)}
            for p in self.products[:50]
        ], ensure_ascii=False)
        
        # Booking Timeline
        import datetime
        from app.models.domain import Appointment
        now_naive = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        future_naive = now_naive + datetime.timedelta(days=60)
        date_str_today = now_naive.strftime("%Y-%m-%d %H:%M:%S (UTC)")
        
        appointments_res = await db.execute(
            select(Appointment).where(
                Appointment.business_id == uuid.UUID(self.business_id), 
                Appointment.status.in_(["pending", "confirmed"]),
                Appointment.start_time >= now_naive,
                Appointment.start_time <= future_naive
            )
        )
        all_appts = appointments_res.scalars().all()
        booked_times = [
            f"{a.staff_name or 'General'}: {a.start_time.isoformat()} to {a.end_time.isoformat()}" for a in all_appts if a.start_time and a.end_time
        ]
        
        staff_str = ", ".join(self.staff_members) if self.staff_members else "General Staff"
        payment_info = json.dumps(self.bank_details, ensure_ascii=False) if self.bank_details else 'No specific payment instructions provided.'

        schema_json = json.dumps(AIIntentSchema.model_json_schema(), indent=2)

        prompt = f"""Current Server Date and Time: {date_str_today}

You are an AI assistant for a '{self.business_type}' business.
Known Customer Name: {self.customer_name or 'UNKNOWN'}
Known Phone Number: {self.customer_phone or 'UNKNOWN'}

Available products/services: {products_context}
Available Staff/Doctors: {staff_str}
Currently Booked Times: {booked_times}

KNOWLEDGE BASE:
{self.knowledge_base}

PAYMENT/BANK DETAILS:
{payment_info}

CRITICAL JSON SCHEMA:
You MUST output a valid JSON object strictly adhering to this JSON Schema. Do NOT wrap it in markdown. Do NOT add explanation text outside the JSON.
{schema_json}

LANGUAGE RULE:
You are a highly intelligent multilingual assistant supporting Arabic, Turkish, and English.
CRITICAL ENFORCEMENT: Carefully analyze the user's PREVIOUS messages in the conversation history to determine their primary language!
- If the conversation history is predominantly Arabic, you MUST reply ONLY in Arabic.
- If the conversation history is predominantly Turkish, you MUST reply ONLY in Turkish.
- If the conversation history is empty, the hint for the first message is: {self.language}.
DO NOT abruptly switch languages just because the user's latest reply is a number (e.g. "11"), an emoji, or a short universal word (e.g. "Tamam", "OK", "Yes"). Maintain the primary conversational language perfectly to avoid confusing the user!!

E-COMMERCE & PHYSICAL PRODUCTS RULE:
1. If the user asks about a product, enthusiastically describe its value. If there's a discount or offer mentioned in the knowledge base, HIGHLIGHT it immediately!
2. DO NOT set intent to 'create_order' until you have explicitly asked for and received their DELIVERY ADDRESS and PHONE NUMBER.
3. If recommending a product, output the product JSON card inside your `response` string. Format: ```json\n{{"product_id": "UUID", "product_name": "Name", "price": "Price", "image_url": "URL"}}\n```

CONVERSATIONAL BOOKING WORKFLOW FOR SERVICES:
Follow this EXACT step-by-step sequence when they want an appointment. Do NOT ask everything at once!
1. ASK FOR DAY: "أي يوم يناسبك لتحديد الموعد؟"
2. OFFER TIMES: Once they provide a day, check the Currently Booked Times. Provide 2-3 specific available times (e.g., "10:00, 11:30").
3. ASK FOR DOCTOR: Once they choose a time, IF there are multiple doctors available, ask who they prefer.
4. GATHER CONTACT INFO: Ask for full name and phone if unknown.
5. COMPLETE: Once all 4 rules are met (product_id, time, name, phone), set intent to 'book_appointment'. DO NOT USE IT BEFORE THEN.

INTENT USAGE:
- 'book_appointment' or 'create_order' ONLY when ALL conditions are fully confirmed.
- 'suggest_product' when you mention a product.
- 'handoff_human' if they demand a real person.
- 'technical_support' for app issues.
- 'none' for all chit-chat and negotiations.
"""
        return prompt

    async def get_response(self, db, user_message: str, conversation=None, media_b64: str = None, user_msg_id=None) -> dict:
        from app.services.ai_router import AIRouter

        system_prompt = await self.generate_system_prompt(db)
        messages = [{"role": "system", "content": system_prompt}]

        if conversation is not None:
            query = select(Message).where(
                Message.conversation_id == conversation.id,
                Message.business_id == uuid.UUID(self.business_id)
            )
            if user_msg_id:
                query = query.where(Message.id != user_msg_id)
            
            msg_res = await db.execute(query.order_by(Message.created_at.desc()).limit(10))
            for m in msg_res.scalars().all()[::-1]:
                messages.append({"role": "user" if m.sender_type == "user" else "assistant", "content": m.content})

        user_content = user_message
        if media_b64:
            user_content = [{"type": "text", "text": user_message or "Image"}, {"type": "image_url", "image_url": {"url": media_b64}}]
        
        messages.append({"role": "user", "content": user_content})

        try:
            result = await AIRouter.generate(db, messages, vision=bool(media_b64))
            cleaned_text = result["text"].strip()
            
            s = cleaned_text.find('{')
            e = cleaned_text.rfind('}')
            if s != -1 and e != -1:
                cleaned_text = cleaned_text[s:e+1]

            return {
                "ai_output": json.loads(cleaned_text),
                "provider": result["provider"],
                "model": result["model"],
            }
        except Exception as e:
            logger.error(f"AI Generator Error: {e}")
            raise Exception("AI processing failed")

    def validate_intent(self, ai_output: dict) -> AIIntentSchema:
        try:
            return AIIntentSchema(**ai_output)
        except Exception as e:
            logger.warning(f"Validation failed: {e}. Output was {ai_output}")
            fallback_ar = "عذراً، حدث خطأ تقني بسيط أثناء معالجة طلبك المتسلسل. هل يمكنك تأكيد خيارك الأخير؟"
            fallback_tr = "İsteğinizi işlerken küçük bir teknik hata oluştu. Seçiminizi tekrar onaylayabilir misiniz?"
            fallback_en = "I encountered a minor formatting issue while processing your request. Could you clarify your choice?"
            
            fb = fallback_en
            if self.language_code == "ar": fb = fallback_ar
            elif self.language_code == "tr": fb = fallback_tr

            return AIIntentSchema(intent="none", confidence=0.0, response=fb, lead_priority="None", data={})
