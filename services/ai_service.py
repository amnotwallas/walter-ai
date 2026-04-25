import groq
from api.core.config import get_settings
from api.core.prompts import SYSTEM_PROMPT

settings = get_settings()
client = groq.Groq(api_key=settings.GROQ_API_KEY)

class AIService:
    @staticmethod
    def get_chat_response(query: str):
        """Genera una respuesta síncrona simple."""
        completion = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.5,
            max_tokens=200
        )
        return completion.choices[0].message.content

    @staticmethod
    def stream_chat_response(query: str):
        """Genera una respuesta en streaming (SSE)."""
        stream = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query}
            ],
            temperature=0.5,
            max_tokens=200,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
