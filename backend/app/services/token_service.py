import tiktoken

class TokenService:

    @staticmethod
    def count(text: str, model="gpt-4"):
        try:
            enc = tiktoken.encoding_for_model(model)
            return len(enc.encode(text))
        except:
            return int(len(text) / 4)
