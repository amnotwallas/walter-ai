import pytest
import pytest_asyncio
import aiosqlite
from unittest.mock import AsyncMock, MagicMock, patch
from app.domain.services.agent import AgentService
from app.adapters.data.sqlite_audit import SqliteAuditAdapter

@pytest_asyncio.fixture
async def real_audit_adapter(tmp_path):
    db_path = str(tmp_path / "integration_audit.db")
    adapter = SqliteAuditAdapter(db_path=db_path)
    await adapter.init_db()
    yield adapter

@pytest.mark.asyncio
async def test_agent_and_audit_integration_no_fk_violation(real_audit_adapter):
    llm = AsyncMock()
    data_provider = MagicMock()
    data_provider.get_data.return_value = None
    agent = AgentService(llm=llm, data_provider=data_provider, audit=real_audit_adapter)

    # Mock LLM completion to first call a tool, then return a final answer
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
    response_final.choices[0].message.content = "Final response text"
    response_final.choices[0].message.tool_calls = []
    
    llm.get_completion.side_effect = [response_with_tool, response_final]

    with patch("app.domain.services.agent.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="tool_result")
        
        result = await agent.get_response(user_query="Who is Walter?", session_id="session-456")
        assert result["message"] == "Final response text"

    # Verify database state
    async with aiosqlite.connect(real_audit_adapter.db_path) as db:
        async with db.execute("SELECT id, session_id, query, response FROM conversations") as cursor:
            conversations = await cursor.fetchall()
        assert len(conversations) == 1
        conv_id, sess_id, query, response = conversations[0]
        assert sess_id == "session-456"
        assert query == "Who is Walter?"
        assert response == "Final response text"

        async with db.execute("SELECT id, conversation_id, tool_name, result FROM tool_executions") as cursor:
            tool_executions = await cursor.fetchall()
        assert len(tool_executions) == 1
        tool_id, tool_conv_id, tool_name, tool_result = tool_executions[0]
        assert tool_conv_id == conv_id
        assert tool_name == "get_personal_info"
        assert tool_result == "tool_result"


@pytest.mark.asyncio
async def test_agent_and_audit_integration_streaming_no_fk_violation(real_audit_adapter):
    llm = AsyncMock()
    data_provider = MagicMock()
    data_provider.get_data.return_value = None
    agent = AgentService(llm=llm, data_provider=data_provider, audit=real_audit_adapter)

    # Mock LLM streaming completion
    async def mock_stream_with_tool():
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        tc = MagicMock()
        tc.index = 0
        tc.id = "tc-stream-1"
        tc.function.name = "get_personal_info"
        tc.function.arguments = '{"arg1": "val1"}'
        chunk1.choices[0].delta.content = None
        chunk1.choices[0].delta.tool_calls = [tc]
        yield chunk1

    async def mock_stream_final():
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = "Streaming final response"
        chunk2.choices[0].delta.tool_calls = []
        yield chunk2

    llm.get_streaming_completion.side_effect = [mock_stream_with_tool(), mock_stream_final()]

    with patch("app.domain.services.agent.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="tool_stream_result")

        chunks = []
        async for chunk in agent.get_streaming_response(user_query="Tell me about Walter", session_id="session-stream-1"):
            chunks.append(chunk)

    # Verify database state
    async with aiosqlite.connect(real_audit_adapter.db_path) as db:
        async with db.execute("SELECT id, session_id, query, response FROM conversations") as cursor:
            conversations = await cursor.fetchall()
        assert len(conversations) == 1
        conv_id, sess_id, query, response = conversations[0]
        assert sess_id == "session-stream-1"
        assert query == "Tell me about Walter"
        assert response == "Streaming final response"

        async with db.execute("SELECT id, conversation_id, tool_name, result FROM tool_executions") as cursor:
            tool_executions = await cursor.fetchall()
        assert len(tool_executions) == 1
        tool_id, tool_conv_id, tool_name, tool_result = tool_executions[0]
        assert tool_conv_id == conv_id
        assert tool_name == "get_personal_info"
        assert tool_result == "tool_stream_result"
