from app.adapters.llm.litellm_adapter import LiteLLMAdapter
from app.domain.services.agent import AgentService

# Singletons initialized once
_llm_adapter = LiteLLMAdapter()
_agent_service = AgentService(llm=_llm_adapter)

def get_agent_service() -> AgentService:
    return _agent_service
