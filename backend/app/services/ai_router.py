import logging
from app.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

class AIRouter:

    @staticmethod
    async def generate(db, messages: list, force_model: str = None, vision: bool = False):
        provider = force_model or await SettingsService.get(db, "ai_provider")
        
        openai_model = "gpt-4o" if vision else "gpt-4o-mini"
        openai_fallback = "gpt-4o-mini"
        
        # User specified gemini-3.1-pro-high, we use standard gemini-1.5-pro or gemini-pro as primary
        gemini_model = "gemini-1.5-pro" if vision else "gemini-pro"
        gemini_fallback = "gemini-1.5-flash"

        for attempt in range(2):
            try:
                if provider == "openai":
                    from app.services.openai_service import OpenAIService
                    text = await OpenAIService.generate(messages, model=openai_model)
                    return {"text": text, "provider": provider, "model": openai_model}

                elif provider == "gemini":
                    from app.services.gemini_service import GeminiService
                    text = await GeminiService.generate(messages, model=gemini_model)
                    return {"text": text, "provider": provider, "model": gemini_model}

                elif provider == "custom":
                    from app.services.custom_ai_service import CustomAIService
                    text = await CustomAIService.generate(messages)
                    return {"text": text, "provider": provider, "model": "custom"}
                    
            except Exception as e:
                err_str = str(e).upper()
                if "503" in err_str or "MODEL_CAPACITY_EXHAUSTED" in err_str or "429" in err_str:
                    if attempt == 0:
                        import asyncio
                        logger.warning(f"AI Provider Capacity Exhausted (attempt 1). Backing off for 10 seconds: {e}")
                        await asyncio.sleep(10)
                        continue
                    else:
                        logger.warning(f"Retries exhausted for {provider}. Falling back to lighter model.")
                        try:
                            if provider == "gemini":
                                from app.services.gemini_service import GeminiService
                                text = await GeminiService.generate(messages, model=gemini_fallback)
                                return {"text": text, "provider": provider, "model": gemini_fallback}
                            elif provider == "openai":
                                from app.services.openai_service import OpenAIService
                                text = await OpenAIService.generate(messages, model=openai_fallback)
                                return {"text": text, "provider": provider, "model": openai_fallback}
                        except Exception as inner_e:
                            logger.error(f"Fallback model also failed: {inner_e}")
                            # Cross-provider failover
                            cross_provider = "gemini" if provider == "openai" else "openai"
                            logger.warning(f"Attempting cross-provider failover to {cross_provider}")
                            try:
                                if cross_provider == "gemini":
                                    from app.services.gemini_service import GeminiService
                                    text = await GeminiService.generate(messages, model=gemini_fallback)
                                    return {"text": text, "provider": "gemini", "model": gemini_fallback}
                                else:
                                    from app.services.openai_service import OpenAIService
                                    text = await OpenAIService.generate(messages, model=openai_fallback)
                                    return {"text": text, "provider": "openai", "model": openai_fallback}
                            except Exception as cross_err:
                                logger.error(f"Cross-provider failover also failed: {cross_err}")
                                break
                else:
                    logger.error(f"Error with primary provider {provider}: {e}")
                    break

        # Absolute Catch-all: Fallback to OpenAI mini
        logger.warning(f"Unrecognised or fully failed provider '{provider}'. Absolute Fallback to OpenAI gpt-4o-mini.")
        try:
            from app.services.openai_service import OpenAIService
            text = await OpenAIService.generate(messages, model="gpt-4o-mini")
            return {"text": text, "provider": "openai", "model": "gpt-4o-mini"}
        except Exception as crash_err:
            logger.error(f"Absolute Fallback crashed: {crash_err}")
            raise Exception("All AI systems exhausted")
