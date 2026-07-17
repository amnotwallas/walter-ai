from typing import Protocol, Any, List, Optional

class LLMPort(Protocol):
    """
    Port interface for LLM completion client.
    """
    @property
    def model(self) -> str:
        ...

    @property
    def temperature(self) -> float:
        ...

    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        ...

    async def get_streaming_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        ...
