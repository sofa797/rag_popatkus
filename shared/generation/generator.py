import requests
from shared.utils.config import Config


class Generator:
    def __init__(self):
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {Config.MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        self.model = Config.MISTRAL_MODEL

    def build_prompt(self, query, context_chunks):
        context = "\n\n".join([
            c["text"] for c in context_chunks
        ])
        return Config.PROMPT.format(context=context, query=query)
    
    def generate(self, query, context_chunks):
        prompt = self.build_prompt(query, context_chunks)
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": Config.TEMPERATURE,
            "max_tokens": Config.MAX_TOKENS
        }
        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload
        )
        if response.status_code != 200:
            return f"error LLM: {response.text}"
        return response.json()["choices"][0]["message"]["content"]
