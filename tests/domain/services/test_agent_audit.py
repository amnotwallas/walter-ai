import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.domain.services.agent import AgentService
from app.domain.ports.audit import AuditPort

def make_agent(audit_mock=None):
    llm = AsyncMock()
    data_provider = MagicMock()
    data_provider.get_data.return_value = None
    return AgentService(llm=llm, data_provider=data_provider, audit=audit_mock)

@pytest.mark.asyncio
async def test_agent_service_accepts_audit_param():
    audit_mock = AsyncMock(spec=AuditPort)
    agent = make_agent(audit_mock)
    assert agent.audit == audit_mock

@pytest.mark.asyncio
async def test_get_response_logs_conversation():
    audit_mock = AsyncMock(spec=AuditPort)
    agent = make_agent(audit_mock)
    
    # Mock LLM completion to return a simple response
    response_mock = MagicMock()
    response_mock.choices = [MagicMock()]
    response_mock.choices[0].message.content = "mock response"
    response_mock.choices[0].message.tool_calls = []
    agent.llm.get_completion.return_value = response_mock

    result = await agent.get_response(user_query="hello query", session_id="test-session")
    assert result["message"] == "mock response"
    
    audit_mock.log_conversation.assert_called_once()
    called_kwargs = audit_mock.log_conversation.call_args.kwargs
    assert called_kwargs["session_id"] == "test-session"
    assert called_kwargs["query"] == "hello query"
    assert called_kwargs["response"] == "mock response"
    assert "id" in called_kwargs

@pytest.mark.asyncio
async def test_get_streaming_response_logs_conversation():
    audit_mock = AsyncMock(spec=AuditPort)
    agent = make_agent(audit_mock)
    
    # Mock LLM streaming completion
    async def mock_stream():
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "stream response"
        chunk.choices[0].delta.tool_calls = []
        yield chunk

    agent.llm.get_streaming_completion.return_value = mock_stream()

    chunks = []
    async for chunk in agent.get_streaming_response(user_query="hello query", session_id="test-session"):
        chunks.append(chunk)
    
    audit_mock.log_conversation.assert_called_once()
    called_kwargs = audit_mock.log_conversation.call_args.kwargs
    assert called_kwargs["session_id"] == "test-session"
    assert called_kwargs["query"] == "hello query"
    assert called_kwargs["response"] == "stream response"
    assert "id" in called_kwargs

@pytest.mark.asyncio
async def test_call_tool_logs_tool_execution():
    audit_mock = AsyncMock(spec=AuditPort)
    agent = make_agent(audit_mock)
    
    tool_call = MagicMock()
    tool_call.function.name = "get_personal_info"
    tool_call.function.arguments = '{"arg1": "val1"}'
    
    with patch("app.domain.services.agent.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="tool_result")
        
        await agent._call_tool(tool_call, [])
        
        audit_mock.log_tool_execution.assert_called_once()
        called_kwargs = audit_mock.log_tool_execution.call_args.kwargs
        assert called_kwargs["conversation_id"] is None
        assert called_kwargs["tool_name"] == "get_personal_info"
        assert called_kwargs["args"] == "{'arg1': 'val1'}"
        assert called_kwargs["result"] == "tool_result"
        assert isinstance(called_kwargs["latency_ms"], float)
        assert "id" in called_kwargs
