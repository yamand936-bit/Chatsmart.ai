class CostService:

    @staticmethod
    def calculate(provider, input_tokens, output_tokens):

        if provider == "openai":
            return (input_tokens * 0.00001) + (output_tokens * 0.00003)

        elif provider == "gemini":
            return 0  # To be implemented when gemini has fixed pricing

        return 0
