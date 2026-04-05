import json

class CustomAIService:
    @staticmethod
    async def generate(messages: list):
        # Stub for future integration
        # Returns mock JSON to prevent breaking chat loop
        data = {
            "intent": "none",
            "confidence": 1.0,
            "data": {},
            "response": "Custom AI not implemented yet. Please switch to OpenAI or Gemini."
        }
        return json.dumps(data)
