import groq
from app.core.config import get_settings
from typing import List, Optional, Any

class LLMProvider:
    """
    Provider class for LLM interactions using AsyncGroq SDK.
    Implements Singleton pattern to reuse the client and connection pool.
    """
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMProvider, cls).__new__(cls)
            settings = get_settings()
            cls._client = groq.AsyncGroq(api_key=settings.GROQ_API_KEY)
            cls._model = settings.MODEL_NAME
        return cls._instance

    @property
    def client(self) -> groq.AsyncGroq:
        return self._client

    @property
    def model(self) -> str:
        return self._model

    async def get_completion(
        self, 
        messages: List[dict], 
        tools: Optional[List[dict]] = None, 
        tool_choice: str = "auto",
        temperature: float = 0.5
    ) -> Any:
        """
        Generates a non-streaming asynchronous completion.
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        return await self.client.chat.completions.create(**kwargs)

    async def get_streaming_completion(
        self, 
        messages: List[dict], 
        tools: Optional[List[dict]] = None, 
        tool_choice: str = "auto",
        temperature: float = 0.5
    ) -> Any:
        """
        Generates a streaming asynchronous completion.
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        return await self.client.chat.completions.create(**kwargs)
