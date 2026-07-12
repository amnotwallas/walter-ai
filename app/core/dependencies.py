import os
from typing import Optional
from app.adapters.llm.litellm_adapter import LiteLLMAdapter
from app.adapters.data.json_loader import JSONDataLoaderAdapter
from app.domain.services.agent import AgentService
from app.adapters.data.sqlite_audit import SqliteAuditAdapter
from app.domain.ports.audit import AuditPort

_llm_adapter = LiteLLMAdapter()
_data_provider = JSONDataLoaderAdapter()

if os.getenv("VERCEL") == "1":
    _audit_adapter = None
else:
    _audit_adapter = SqliteAuditAdapter(db_path="audit.db")

_agent_service = AgentService(llm=_llm_adapter, data_provider=_data_provider, audit=_audit_adapter)


def get_agent_service() -> AgentService:
    return _agent_service


def get_audit() -> Optional[AuditPort]:
    return _audit_adapter
