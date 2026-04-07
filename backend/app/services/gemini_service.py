import asyncio
import google.generativeai as genai
from app.core.config import settings

class GeminiService:

    @staticmethod
    async def generate(messages: list, model: str = "gemini-1.5-pro"):

        if not settings.GEMINI_API_KEY:
            raise Exception("Gemini API key missing")

        genai.configure(api_key=settings.GEMINI_API_KEY)

        # Inject visionary content or text content 
        genai_model = genai.GenerativeModel(model)

        # Gemini does not use a structured messages API — flatten to a single prompt.
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"[SYSTEM]\n{content}")
            elif role == "assistant":
                parts.append(f"[ASSISTANT]\n{content}")
            else:
                parts.append(f"[USER]\n{content}")

        parts.append("\nIMPORTANT: Return ONLY valid JSON.")
        prompt = "\n\n".join(parts)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            genai_model.generate_content,
            prompt
        )

        return response.text
