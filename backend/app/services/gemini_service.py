import asyncio
import google.generativeai as genai
from app.core.config import settings

class GeminiService:

    @staticmethod
    async def generate(messages: list, model: str = "gemini-1.5-pro", force_json: bool = True):

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

        if force_json:
            parts.append("\nIMPORTANT: Return ONLY valid JSON.")
        
        prompt = "\n\n".join(parts)

        generation_config = genai.types.GenerationConfig(
            max_output_tokens=500,
            temperature=0.3
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda p: genai_model.generate_content(p, generation_config=generation_config, request_options={'timeout': 8.0}),
            prompt
        )

        return response.text
