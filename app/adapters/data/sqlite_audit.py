from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, select, func, case, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ToolExecution(Base):
    __tablename__ = "tool_executions"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True)
    tool_name = Column(String, nullable=False)
    args = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(String, primary_key=True)
    reason = Column(String, nullable=False)
    query_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class SqliteAuditAdapter:
    def __init__(self, db_path: str = "audit.db"):
        self.db_path = db_path
        self.cache_ttl = 60
        self._cached_anomalies = None
        self._cache_expiry = 0.0
        import asyncio
        self._lock = asyncio.Lock()
        
        # SQLite Async connection string using aiosqlite
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{self.db_path}", echo=False)
        self.SessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def log_conversation(self, id: str, session_id: str, query: str, response: str) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                convo = Conversation(id=id, session_id=session_id, query=query, response=response)
                session.add(convo)

    async def log_tool_execution(
        self, id: str, conversation_id: Optional[str] = None, tool_name: str = "",
        args: str = "", result: str = "", latency_ms: float = 0.0
    ) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                execution = ToolExecution(
                    id=id,
                    conversation_id=conversation_id,
                    tool_name=tool_name,
                    args=args,
                    result=result,
                    latency_ms=latency_ms
                )
                session.add(execution)

    async def log_security_event(self, id: str, reason: str, query_snippet: str) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                event_obj = SecurityEvent(id=id, reason=reason, query_snippet=query_snippet)
                session.add(event_obj)

    async def _fetch_anomalies_from_db(self) -> dict:
        async with self.SessionLocal() as session:
            # 1. High failure rate tools
            error_case = case((ToolExecution.result.like("Error%"), 1), else_=0)
            q1 = (
                select(ToolExecution.tool_name)
                .group_by(ToolExecution.tool_name)
                .having(func.sum(error_case) * 1.0 / func.count() > 0.8)
            )
            res1 = await session.execute(q1)
            high_failure = [row[0] for row in res1]

            # 2. Slow sessions
            subq = select(func.avg(ToolExecution.latency_ms) * 3)
            q2 = (
                select(Conversation.session_id)
                .join(ToolExecution, ToolExecution.conversation_id == Conversation.id)
                .group_by(Conversation.session_id)
                .having(func.sum(ToolExecution.latency_ms) > subq.scalar_subquery())
            )
            res2 = await session.execute(q2)
            slow_sessions = [row[0] for row in res2]

            # 3. Slowest tools
            q3 = (
                select(ToolExecution.tool_name, func.avg(ToolExecution.latency_ms).label("avg_ms"))
                .group_by(ToolExecution.tool_name)
                .order_by(func.avg(ToolExecution.latency_ms).desc())
                .limit(5)
            )
            res3 = await session.execute(q3)
            slow_tools = [{"tool": row[0], "avg_ms": round(row[1], 2)} for row in res3]

        return {
            "high_failure_tools": high_failure,
            "slow_sessions": slow_sessions,
            "slow_tools": slow_tools,
        }

    async def get_anomalies(self) -> dict:
        import time
        now = time.time()
        if self._cached_anomalies is not None and now < self._cache_expiry:
            return self._cached_anomalies

        async with self._lock:
            # Recheck after acquiring lock
            now = time.time()
            if self._cached_anomalies is not None and now < self._cache_expiry:
                return self._cached_anomalies

            anomalies = await self._fetch_anomalies_from_db()
            self._cached_anomalies = anomalies
            self._cache_expiry = now + self.cache_ttl
            return anomalies
