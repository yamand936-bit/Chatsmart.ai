import json
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIService:
    @staticmethod
    async def generate(messages: list, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI

        from app.core.config import settings

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise Exception("OpenAI API key missing")

        client = AsyncOpenAI(api_key=api_key)
        try:
            response = await client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise Exception("AI processing failed")
