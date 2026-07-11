import litellm
from app.core.config import get_settings
from typing import List, Optional, Any

class LLMProvider:
    """
    Provider class for LLM interactions using LiteLLM.
    Supports any provider configured via config/llm.yml.
    Implements Singleton pattern to reuse settings.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            settings = get_settings()
            cls._model = settings.llm_model
            cls._temperature = settings.llm_temperature
        return cls._instance

    @property
    def model(self) -> str:
        return self._model

    @property
    def temperature(self) -> float:
        return self._temperature

    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        """Generates a non-streaming asynchronous completion."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        return await litellm.acompletion(**kwargs)

    async def get_streaming_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        """Generates a streaming asynchronous completion."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        
        return await litellm.acompletion(**kwargs)
