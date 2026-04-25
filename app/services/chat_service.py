from app.providers.llm_provider import LLMProvider
from app.core.prompts import SYSTEM_PROMPT
from typing import List

class ChatService:
    def __init__(self):
        self.llm = LLMProvider()

    def _build_messages(self, user_query: str, history: List = []):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Añadir historial (máximo los últimos 6 mensajes para ahorrar tokens)
        for msg in history[-6:]:
            messages.append({"role": msg.role, "content": msg.content})
            
        # Añadir la consulta actual
        messages.append({"role": "user", "content": user_query})
        return messages

    def get_response(self, user_query: str, history: List = []) -> str:
        messages = self._build_messages(user_query, history)
        completion = self.llm.completion(messages)
        return completion.choices[0].message.content

    def get_streaming_response(self, user_query: str, history: List = []):
        messages = self._build_messages(user_query, history)
        stream = self.llm.completion(messages, stream=True)
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {chunk.choices[0].delta.content}\n\n"
