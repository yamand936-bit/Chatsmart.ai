import logging
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

class AIRouter:

    @staticmethod
    async def generate(db, messages: list):
        provider = await SettingsService.get(db, "ai_provider")

        try:
            if provider == "openai":
                from app.services.openai_service import OpenAIService
                text = await OpenAIService.generate(messages)
                return {"text": text, "provider": provider, "model": "gpt-4o-mini"}

            elif provider == "gemini":
                from app.services.gemini_service import GeminiService
                text = await GeminiService.generate(messages)
                return {"text": text, "provider": provider, "model": "gemini-1.5-flash"}

            elif provider == "custom":
                from app.services.custom_ai_service import CustomAIService
                text = await CustomAIService.generate(messages)
                return {"text": text, "provider": provider, "model": "custom"}
        except Exception as e:
            if provider == "openai":
                logger.error(f"OpenAI (primary) failed with no fallback available: {e}")
                raise
            logger.error(f"Error with primary provider {provider}: {e}. Falling back to OpenAI.")
            from app.services.openai_service import OpenAIService
            text = await OpenAIService.generate(messages)
            return {"text": text, "provider": "openai", "model": "gpt-4o-mini"}

        # Catch-all: provider value not recognised — fall back to OpenAI
        logger.warning(f"Unrecognised ai_provider value '{provider}'. Falling back to OpenAI.")
        from app.services.openai_service import OpenAIService
        text = await OpenAIService.generate(messages)
        return {"text": text, "provider": "openai", "model": "gpt-4o-mini"}
