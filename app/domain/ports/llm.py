from abc import ABC, abstractmethod
from typing import List, Optional, Any

class LLMClientPort(ABC):
    @property
    @abstractmethod
    def model(self) -> str:
        pass

    @property
    @abstractmethod
    def temperature(self) -> float:
        pass

    @abstractmethod
    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        pass

    @abstractmethod
    async def get_streaming_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        pass

