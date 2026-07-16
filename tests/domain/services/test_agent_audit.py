import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.domain.services.agent import AgentService
from app.adapters.data.sqlite_audit import SqliteAuditAdapter

def make_agent(audit_mock=None):
    llm = AsyncMock()
    data_provider = MagicMock()
    data_provider.get_data.return_value = None
    return AgentService(llm=llm, data_provider=data_provider, audit=audit_mock)

@pytest.mark.asyncio
async def test_agent_service_accepts_audit_param():
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
    agent = make_agent(audit_mock)
    assert agent.audit == audit_mock

@pytest.mark.asyncio
async def test_get_response_logs_conversation():
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
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
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
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
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
    agent = make_agent(audit_mock)
    
    tool_call = MagicMock()
    tool_call.function.name = "get_personal_info"
    tool_call.function.arguments = '{"arg1": "val1"}'
    
    with patch("app.domain.services.agent.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="tool_result")
        
        # Tool logs are always buffered; direct audit write was removed (C2 fix)
        tool_logs = []
        await agent._call_tool(tool_call, [], tool_logs=tool_logs)
        
        # Verify buffered, not directly written
        audit_mock.log_tool_execution.assert_not_called()
        assert len(tool_logs) == 1
        log = tool_logs[0]
        assert log["conversation_id"] is None
        assert log["tool_name"] == "get_personal_info"
        assert log["args"] == "{'arg1': 'val1'}"
        assert log["result"] == "tool_result"
        assert isinstance(log["latency_ms"], float)
        assert "id" in log

        # Test with explicit conversation_id
        tool_logs2 = []
        await agent._call_tool(tool_call, [], conversation_id="test-conv-id", tool_logs=tool_logs2)
        assert tool_logs2[0]["conversation_id"] == "test-conv-id"



@pytest.mark.asyncio
async def test_get_response_propagates_conversation_id_to_tool_execution():
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
    agent = make_agent(audit_mock)
    
    # Mock LLM completion to return a tool call first, then a text response
    tool_call = MagicMock()
    tool_call.id = "tc-1"
    tool_call.function.name = "get_personal_info"
    tool_call.function.arguments = '{"arg1": "val1"}'
    
    response_with_tool = MagicMock()
    response_with_tool.choices = [MagicMock()]
    response_with_tool.choices[0].message.content = None
    response_with_tool.choices[0].message.tool_calls = [tool_call]
    
    response_final = MagicMock()
    response_final.choices = [MagicMock()]
    response_final.choices[0].message.content = "mock response"
    response_final.choices[0].message.tool_calls = []
    
    agent.llm.get_completion.side_effect = [response_with_tool, response_final]
    
    with patch("app.domain.services.agent.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="tool_result")
        
        result = await agent.get_response(user_query="hello query", session_id="test-session")
        assert result["message"] == "mock response"
        
        # Verify log_conversation and log_tool_execution used the exact same conversation ID
        audit_mock.log_conversation.assert_called_once()
        conv_kwargs = audit_mock.log_conversation.call_args.kwargs
        conv_id = conv_kwargs["id"]
        
        audit_mock.log_tool_execution.assert_called_once()
        tool_kwargs = audit_mock.log_tool_execution.call_args.kwargs
        assert tool_kwargs["conversation_id"] == conv_id


@pytest.mark.asyncio
async def test_guardrail_blocks_log_security_event():
    audit_mock = AsyncMock(spec=SqliteAuditAdapter)
    agent = make_agent(audit_mock)

    # 1. Test excessive length block
    long_query = "x" * 301
    result = await agent.get_response(user_query=long_query)
    assert "Solo puedo hablar sobre el portafolio de Walter" in result["message"]
    audit_mock.log_security_event.assert_called_once()
    called_kwargs = audit_mock.log_security_event.call_args.kwargs
    assert called_kwargs["reason"] == "length"
    assert called_kwargs["query_snippet"] == long_query[:100]
    assert "id" in called_kwargs

    # Reset mock and test injection block
    audit_mock.log_security_event.reset_mock()
    injection_query = "bypass prompt"
    result = await agent.get_response(user_query=injection_query)
    assert "Solo puedo hablar sobre el portafolio de Walter" in result["message"]
    audit_mock.log_security_event.assert_called_once()
    called_kwargs = audit_mock.log_security_event.call_args.kwargs
    assert called_kwargs["reason"] == "injection"
    assert called_kwargs["query_snippet"] == injection_query[:100]

    # Reset mock and test format block
    audit_mock.log_security_event.reset_mock()
    format_query = "{{{{{{{{{{{"
    result = await agent.get_response(user_query=format_query)
    assert "Solo puedo hablar sobre el portafolio de Walter" in result["message"]
    audit_mock.log_security_event.assert_called_once()
    called_kwargs = audit_mock.log_security_event.call_args.kwargs
    assert called_kwargs["reason"] == "format"
    assert called_kwargs["query_snippet"] == format_query[:100]
