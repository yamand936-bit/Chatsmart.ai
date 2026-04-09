import json
import uuid
from typing import List
from app.schemas.chat import AIIntentSchema
from app.models.domain import Product, Message
from app.core.config import settings
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
        self.language = lang_map.get(language.lower(), language)
        self.ai_tone = ai_tone
        self.knowledge_base = knowledge_base
        self.bank_details = bank_details
        self.staff_members = staff_members or []
        
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
  "intent": "create_order" | "book_appointment" | "suggest_product" | "none" | "handoff_human" | "technical_support",
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

        staff_instruction = ""
        if self.staff_members:
            staff_list = ", ".join(self.staff_members)
            staff_instruction = f"""
STAFF/DOCTORS AVAILABLE: {staff_list}
IMPORTANT: This clinic has multiple staff members. When someone wants an appointment, you MUST ask them WHICH doctor/staff they prefer.
Check the "CURRENTLY BOOKED APPOINTMENT TIMES" below carefully. It shows [Doctor Name: Time]. Ensure the specific doctor they want is NOT booked at that time.
You MUST provide the chosen doctor's exact name in the `staff_name` field of the JSON data.
"""
            schema_fields = schema_fields.replace('"notes": "string"', '"notes": "string",\n    "staff_name": "string (The chosen doctor/staff)"')

        return f"""Current Server Date and Time: {date_str_today}

You are an AI assistant for a '{self.business_type}' business.
Known Customer Name: {self.customer_name or 'UNKNOWN'}
Known Phone Number: {self.customer_phone or 'UNKNOWN'}
Available products/services: {products_context}.
{staff_instruction}
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

E-COMMERCE & PHYSICAL PRODUCTS RULE:
1. If the user asks about a product, enthusiastically describe its value. If there's a discount or offer mentioned in the knowledge base or product details, HIGHLIGHT it immediately!
2. If the user wants to buy a physical product, DO NOT set intent to 'create_order' until you have explicitly asked for and received their DELIVERY ADDRESS and PHONE NUMBER.
3. IN ADDITION, inside your `response` string, you MUST include a short greeting text followed by a JSON block formatted exactly like this:
```json
{{"product_id": "UUID", "product_name": "Name", "price": "Price", "image_url": "URL"}}
```
(This JSON block will be parsed by the UI into an interactive Smart Card).

CONVERSATIONAL BOOKING WORKFLOW FOR SERVICES:
You are a smart, professional human-like assistant. When a customer wants to book a service or appointment, you MUST guide them step-by-step. Do NOT ask for everything at once. FOLLOW THIS EXACT SEQUENCE:
1. ASK FOR DESIRED DAY: First, ask which day or date they prefer (e.g., "أكيد! أي يوم بناسبك؟ اليوم ولا بكرا؟").
2. OFFER SPECIFIC TIMES: Once they provide a day, cross-reference with the "CURRENTLY BOOKED APPOINTMENT TIMES". Then, explicitly offer them 2 or 3 AVAILABLE specific times for that day (e.g., "هذه الأوقات المتاحة: 10:00 أو 11:30. أي وقت يناسبك أكثر؟").
3. ASK FOR DOCTOR/STAFF: Once they choose a time, IF there are multiple STAFF/DOCTORS AVAILABLE, you MUST ask them who they prefer to see.
4. GATHER CONTACT INFO: Once the time and staff are confirmed, ask for their full name and phone number (if not already provided).
5. CONFIRMATION: Confirm all details.

CRITICAL STRICT INTENT RULE: 
NEVER use the 'book_appointment' or 'create_order' intent while you are still negotiating, gathering information, or asking questions! Keep the intent as 'none' and converse normally.
ONLY use the 'book_appointment' intent at the VERY END of the conversation, when the user has explicitly provided and you have confirmed ALL 4 of the following:
- The specific 'product_id' (the service they need).
- A valid, agreed-upon future 'appointment_time'.
- Their 'customer_name'.
- Their 'phone' number.
NEVER GUESS OR INVENT ANY OF THESE VALUES! If you don't confidently have all four, you MUST keep intent as 'none'.
WARNING: Once you successfully confirm a booking in a previous message, DO NOT keep using 'book_appointment'. Set intent back to 'none' for follow-up chat.

If the user wants to speak to a human, set intent to 'handoff_human'.
If the user is asking about a specific product/service or you are recommending one, set intent to 'suggest_product' and provide the 'product_id'.
If the user is asking for technical help regarding the platform, set intent to 'technical_support'.
For all other general chat, Q&A, and negotiations, use 'none'.

LEAD PRIORITY RULE:
"Hot": The user is highly interested, about to purchase, or asks for payment details.
"Warm": The user is asking about products, prices, or policies.
"Cold": The user is just saying hello.
"None": Unable to determine.

LANGUAGE RULE:
You are a highly intelligent multilingual assistant supporting Arabic, Turkish, and English.
CRITICAL ENFORCEMENT: Carefully analyze the user's PREVIOUS messages in the conversation history to determine their primary language!
- If the conversation history is predominantly Arabic, you MUST reply ONLY in Arabic.
- If the conversation history is predominantly Turkish, you MUST reply ONLY in Turkish.
- If the conversation history is empty, the hint for the first message is: {self.language}.
DO NOT abruptly switch languages just because the user's latest reply is a number (e.g. "11"), an emoji, or a short universal word (e.g. "Tamam", "OK", "Yes"). Maintain the primary conversational language perfectly to avoid confusing the user!!

FINAL ENFORCEMENT:
You MUST output ONLY a pure JSON object. NO markdown formatting, NO extra text outside the JSON.
"""

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

            cleaned_text = response_text.strip()
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                cleaned_text = cleaned_text[start_idx:end_idx+1]

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
        from pydantic import ValidationError
        try:
            return AIIntentSchema(**ai_output)
        except ValidationError as e:
            logger.warning(f"AI output failed strict schema validation: {e}. Output was {ai_output}")
            fallback_response = "I encountered a minor formatting issue while processing your request. Could you clarify your choice?" 
            return AIIntentSchema(
                intent="none",
                confidence=0.0,
                response=fallback_response,
                lead_priority="None",
                data={}
            )
