import json
from typing import List
from app.schemas.chat import AIIntentSchema
from app.models.domain import Product, Message
from app.core.config import settings
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

class AIEngineService:
    def __init__(self, business_id: str, business_type: str, products: List[Product], language: str = "en", ai_tone: str = "Professional", knowledge_base: str = None, bank_details: dict = None, is_tiktok_comment: bool = False, platform: str = "unknown"):
        self.business_id = business_id
        self.business_type = business_type
        self.is_tiktok_comment = is_tiktok_comment
        self.platform = platform
        self.products = products
        lang_map = {"ar": "Arabic", "en": "English", "tr": "Turkish"}
        self.language = lang_map.get(language.lower(), language)
        self.ai_tone = ai_tone
        self.knowledge_base = knowledge_base
        self.bank_details = bank_details
        
    async def generate_system_prompt(self, db) -> str:
        products_context = json.dumps([
            {"id": str(p.id), "name": p.name, "price": p.price, "type": getattr(p, "item_type", "product"), "duration": getattr(p, "duration", 60), "image_available": bool(p.image_url)}
            for p in self.products[:50]
        ])
        
        # Fetch Booked Appointments natively
        from app.models.domain import Appointment
        import datetime
        now_naive = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        future_naive = now_naive + datetime.timedelta(days=60)
        date_str_today = now_naive.date().strftime("%Y-%m-%d")
        
        appointments_res = await db.execute(
            select(Appointment).where(
                Appointment.business_id == self.business_id, 
                Appointment.status.in_(["pending", "confirmed"]),
                Appointment.start_time >= now_naive,
                Appointment.start_time <= future_naive
            )
        )
        all_appts = appointments_res.scalars().all()
        booked_times = [
            f"{a.start_time.isoformat()} to {a.end_time.isoformat()}" for a in all_appts if a.start_time and a.end_time
        ]
        booked_context = json.dumps(booked_times)
        
        tone_instruction = ""
        if self.ai_tone == "Professional":
            tone_instruction = "Maintain a highly professional, polite, and objective tone. Focus on clarity and accuracy. Do not push products aggressively. Let the customer guide the interaction naturally."
        elif self.ai_tone == "Friendly":
            tone_instruction = "Be warm, approachable, and very friendly. Use simple language and occasional emojis. Talk like a helpful, caring friend."
        elif self.ai_tone == "Sales-driven":
            tone_instruction = "Be highly proactive, persuasive, and sales-oriented. Keep responses concise. The moment you detect a user's need, IMMEDIATELY suggest a relevant product, highlight its value, and push a call-to-action to purchase."
        else:
            tone_instruction = "Maintain a balanced, helpful tone."
            
        if self.platform.lower() == "instagram":
            tone_instruction += "\nBecause this is INSTAGRAM DIRECT, you must adopt a highly visual, aesthetic, and emoji-rich style. Focus heavily on descriptive aesthetics and encourage them to view images or links."

        payment_info = json.dumps(self.bank_details, ensure_ascii=False) if self.bank_details else 'No specific payment instructions provided.'
        policies = self.knowledge_base or 'No specific knowledge base provided.'

        schema_fields = f"""
  "intent": "create_order" | "book_appointment" | "none" | "handoff_human" | "technical_support",
  "confidence": 0.9,
  "lead_priority": "Hot" | "Warm" | "Cold" | "None",
  "data": {{
    "customer_name": "string",
    "phone": "string",
    "product_id": "UUID from the available products list",
    "appointment_time": "YYYY-MM-DD HH:MM",
    "notes": "string"
  }},
  "response": "string"
"""
        if self.is_tiktok_comment:
            schema_fields += """,
  "public_reply": "string (A short, highly engaging public reply to the TikTok comment to drive more interaction. Example: 'Great question! Sent you a DM details 😍')",
  "private_dm": "string (A persuasive direct message sent to their inbox to answer them and push a sale)"
"""

        return f"""Current Server Date: {date_str_today}

CRITICAL: THE CURRENT USER MESSAGE IS IN {self.language.upper()}. YOU MUST WRITE YOUR ENTIRE RESPONSE IN {self.language.upper()}. DO NOT USE ANY OTHER LANGUAGE!

You are an AI assistant for a '{self.business_type}' business.
Available products/services: {products_context}.
CURRENTLY BOOKED APPOINTMENT TIMES (DO NOT DOUBLE BOOK THESE): {booked_context}

KNOWLEDGE BASE AND POLICIES:
If the user asks about the business, policies, or how things work, prioritize these rules:
{policies}

PAYMENT AND BANK DETAILS:
If the user asks how to pay or asks for bank details, provide this exact information:
{payment_info}

PERSONALITY AND TONE RULE:
{tone_instruction}

You MUST respond with a perfectly valid JSON object matching this schema:
{{{schema_fields}}}
CRITICAL RULE 1: If the user wants to order a 'product', YOU MUST accurately identify the 'product_id' and set the intent to 'create_order'. IN ADDITION, inside your `response` string, you MUST include a short greeting text followed by a JSON block formatted exactly like this:
```json
{{"product_id": "UUID", "product_name": "Name", "price": "Price", "image_url": "URL"}}
```
This JSON block will be parsed by the UI into an interactive Smart Card.
CRITICAL RULE 2: If the user wants a 'service' or expresses interest (e.g., 'بدي', 'istiyorum', 'tamam'), you MUST set intent to 'book_appointment'. If they haven't provided a time yet, you MUST ASK for the time IN THEIR LANGUAGE inside the `response` property of your JSON. Never switch to English unless the user speaks English. Once they specify a time, verify it does NOT conflict with the BOOKED APPOINTMENT TIMES. If conflict: suggest a different time. If clear: provide 'product_id', and explicitly populate 'appointment_time' in the data payload.
If the product/service is not available, set intent to 'none'.
If the user wants to speak to a human, set intent to 'handoff_human'.
If the user is asking for technical help, bug reports, or error resolution about the platform itself, set intent to 'technical_support'.
Otherwise, use 'none'.

LEAD PRIORITY RULE:
"Hot": The user is highly interested, about to purchase, or asks for payment details.
"Warm": The user is asking about products, prices, or policies.
"Cold": The user is just saying hello or asking irrelevant questions.
"None": Unable to determine.

LANGUAGE RULE:
You are a multilingual assistant. Always respond in the SAME language the user is currently using.
STRICT RULE: The detected language of the VERY LAST message is {self.language.upper()}. You MUST respond ONLY in {self.language.upper()}. If you were speaking Arabic before, you MUST switch to {self.language.upper()} instantly.

FINAL ENFORCEMENT:
You MUST output ONLY a pure JSON object. NO markdown formatting, NO extra text outside the JSON.
"""

    async def get_response(self, db, user_message: str, conversation=None, media_b64: str = None, user_msg_id=None) -> dict:
        from app.services.ai_router import AIRouter

        system_prompt = await self.generate_system_prompt(db)

        messages = [{"role": "system", "content": system_prompt}]

        if conversation is not None:
            query = select(Message).where(Message.conversation_id == conversation.id)
            if user_msg_id:
                query = query.where(Message.id != user_msg_id)
            
            msg_res = await db.execute(
                query.order_by(Message.created_at.desc()).limit(10)
            )
            history = msg_res.scalars().all()[::-1]
            for m in history:
                messages.append({
                    "role": "user" if m.sender_type == "user" else "assistant",
                    "content": m.content,
                })

        if media_b64:
            user_msg_content = [
                {"type": "text", "text": user_message or "What is in this image?"},
                {"type": "image_url", "image_url": {"url": media_b64}}
            ]
        else:
            user_msg_content = user_message

        messages.append({"role": "user", "content": user_msg_content})

        try:
            result = await AIRouter.generate(db, messages, vision=bool(media_b64))
            response_text = result["text"]
            provider = result["provider"]
            model = result["model"]

            # Clean markdown code blocks from the response text
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            parsed_json = json.loads(cleaned_text)
            return {
                "ai_output": parsed_json,
                "provider": provider,
                "model": model,
            }
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            raise Exception("AI processing failed")

    def validate_intent(self, ai_output: dict) -> AIIntentSchema:
        """Validates that the AI output adheres strictly to the contract."""
        return AIIntentSchema(**ai_output)
