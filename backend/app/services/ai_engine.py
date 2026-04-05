import json
from typing import List
from app.schemas.chat import AIIntentSchema
from app.models.domain import Product, Message
from app.core.config import settings
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)

class AIEngineService:
    def __init__(self, business_type: str, products: List[Product], language: str = "en"):
        self.business_type = business_type
        self.products = products
        self.language = language
        
    def generate_system_prompt(self) -> str:
        products_context = json.dumps([
            {"id": str(p.id), "name": p.name, "price": p.price}
            for p in self.products[:50]
        ])
        return f"""You are an AI assistant for a '{self.business_type}' business.
Available products/services: {products_context}.
You MUST respond with a perfectly valid JSON object matching this schema:
{{
  "intent": "create_order" | "none" | "handoff_human" | "technical_support",
  "confidence": 0.9,
  "data": {{
    "customer_name": "string",
    "phone": "string",
    "product_id": "string",
    "notes": "string"
  }},
  "response": "string"
}}
CRITICAL RULE: If the user wants to order a product, YOU MUST accurately identify the 'product_id' from the list of available products and set the intent to 'create_order'.
If the product is not available, set intent to 'none'.
If the user wants to speak to a human, set intent to 'handoff_human'.
If the user is asking for technical help, bug reports, or error resolution about the platform itself, set intent to 'technical_support'.
Otherwise, use 'none'.

LANGUAGE RULE:
You MUST respond in the SAME language as the user input.
Do not translate.
Do not mix languages.
Arabic → Arabic
Turkish → Turkish
English → English

Your response MUST be exclusively in {self.language.upper()}.
"""

    async def get_response(self, db, user_message: str, conversation=None) -> dict:
        from app.services.ai_router import AIRouter

        system_prompt = self.generate_system_prompt()

        messages = [{"role": "system", "content": system_prompt}]

        if conversation is not None:
            msg_res = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(10)
            )
            history = msg_res.scalars().all()[::-1]
            for m in history:
                messages.append({
                    "role": "user" if m.sender_type == "user" else "assistant",
                    "content": m.content,
                })

        messages.append({"role": "user", "content": user_message})

        try:
            result = await AIRouter.generate(db, messages)
            response_text = result["text"]
            provider = result["provider"]
            model = result["model"]

            parsed_json = json.loads(response_text)
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
