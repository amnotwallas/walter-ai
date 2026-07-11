from app.adapters.llm.litellm_adapter import LiteLLMAdapter
from app.adapters.data.json_loader import JSONDataLoaderAdapter
from app.domain.services.agent import AgentService

_llm_adapter = LiteLLMAdapter()
_data_provider = JSONDataLoaderAdapter()
_agent_service = AgentService(llm=_llm_adapter, data_provider=_data_provider)

def get_agent_service() -> AgentService:
    return _agent_service
