from abc import ABC, abstractmethod


class AuditPort(ABC):
    @abstractmethod
    async def log_conversation(self, id: str, session_id: str, query: str, response: str) -> None: ...

    @abstractmethod
    async def log_tool_execution(
        self, id: str, conversation_id: str, tool_name: str,
        args: str, result: str, latency_ms: float
    ) -> None: ...

    @abstractmethod
    async def log_security_event(self, id: str, reason: str, query_snippet: str) -> None: ...

    @abstractmethod
    async def get_anomalies(self) -> dict: ...
