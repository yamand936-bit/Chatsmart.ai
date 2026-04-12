import json
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    @staticmethod
    async def generate(messages: list, model: str = "gpt-4o-mini", force_json: bool = True):
        from openai import AsyncOpenAI
        from app.core.config import settings

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise Exception("OpenAI API key missing")

        client = AsyncOpenAI(api_key=api_key)
        try:
            kwargs = {
                "model": model,
                "messages": messages,
            }
            if force_json:
                kwargs["response_format"] = {"type": "json_object"}
                
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise Exception("AI processing failed")
