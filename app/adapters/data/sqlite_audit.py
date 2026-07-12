from typing import Optional
import aiosqlite
from app.domain.ports.audit import AuditPort

CREATE_CONVERSATIONS = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    query TEXT NOT NULL,
    response TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""

CREATE_TOOL_EXECUTIONS = """
CREATE TABLE IF NOT EXISTS tool_executions (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id),
    tool_name TEXT NOT NULL,
    args TEXT,
    result TEXT,
    latency_ms REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""

CREATE_SECURITY_EVENTS = """
CREATE TABLE IF NOT EXISTS security_events (
    id TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    query_snippet TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)"""


class SqliteAuditAdapter(AuditPort):
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path

    async def init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(CREATE_CONVERSATIONS)
            await db.execute(CREATE_TOOL_EXECUTIONS)
            await db.execute(CREATE_SECURITY_EVENTS)
            await db.commit()

    async def log_conversation(self, id: str, session_id: str, query: str, response: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                "INSERT INTO conversations (id, session_id, query, response) VALUES (?, ?, ?, ?)",
                (id, session_id, query, response),
            )
            await db.commit()

    async def log_tool_execution(
        self, id: str, conversation_id: Optional[str] = None, tool_name: str = "",
        args: str = "", result: str = "", latency_ms: float = 0.0
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                "INSERT INTO tool_executions (id, conversation_id, tool_name, args, result, latency_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (id, conversation_id, tool_name, args, result, latency_ms),
            )
            await db.commit()

    async def log_security_event(self, id: str, reason: str, query_snippet: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                "INSERT INTO security_events (id, reason, query_snippet) VALUES (?, ?, ?)",
                (id, reason, query_snippet),
            )
            await db.commit()

    async def get_anomalies(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            # Tools con error rate alto (result contiene 'Error')
            async with db.execute("""
                SELECT tool_name,
                       COUNT(*) as total,
                       SUM(CASE WHEN result LIKE 'Error%' THEN 1 ELSE 0 END) as errors
                FROM tool_executions
                GROUP BY tool_name
                HAVING errors * 1.0 / total > 0.8
            """) as cursor:
                high_failure = [row[0] async for row in cursor]

            # Sesiones con tokens altos (via query length como proxy)
            async with db.execute("""
                SELECT session_id, SUM(latency_ms) as total_latency
                FROM tool_executions te
                JOIN conversations c ON te.conversation_id = c.id
                GROUP BY session_id
                HAVING total_latency > (
                    SELECT AVG(latency_ms) * 3 FROM tool_executions
                )
            """) as cursor:
                slow_sessions = [row[0] async for row in cursor]

            # Tools más lentas
            async with db.execute("""
                SELECT tool_name, AVG(latency_ms) as avg_ms
                FROM tool_executions
                GROUP BY tool_name
                ORDER BY avg_ms DESC
                LIMIT 5
            """) as cursor:
                slow_tools = [{"tool": row[0], "avg_ms": round(row[1], 2)} async for row in cursor]

        return {
            "high_failure_tools": high_failure,
            "slow_sessions": slow_sessions,
            "slow_tools": slow_tools,
        }
