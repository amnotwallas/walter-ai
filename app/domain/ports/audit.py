from typing import Protocol, Optional

class AuditPort(Protocol):
    """
    Port interface for logging conversation analytics and tool usage.
    """
    async def init_db(self) -> None:
        ...

    async def log_conversation(self, id: str, session_id: str, query: str, response: str) -> None:
        ...

    async def log_tool_execution(
        self, id: str, conversation_id: Optional[str] = None, tool_name: str = "",
        args: str = "", result: str = "", latency_ms: float = 0.0
    ) -> None:
        ...

    async def log_security_event(self, id: str, reason: str, query_snippet: str) -> None:
        ...

    async def get_anomalies(self) -> dict:
        ...
