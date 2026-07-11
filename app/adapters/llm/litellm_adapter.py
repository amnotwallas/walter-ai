from typing import List, Optional, Any
import litellm
from app.core.config import get_settings
from app.domain.ports.llm import LLMClientPort

class LiteLLMAdapter(LLMClientPort):
    """
    Concrete adapter implementing the LLMClientPort using LiteLLM.
    Implements Singleton pattern.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> str:
        return get_settings().llm_model

    @property
    def temperature(self) -> float:
        return get_settings().llm_temperature

    @property
    def client(self) -> Any:
        # Backward-compatible property
        return None

    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
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
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        return await litellm.acompletion(**kwargs)
