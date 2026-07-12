from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.domain.services.agent import AgentService


def make_agent():
    llm = AsyncMock()
    data_provider = MagicMock()
    data_provider.get_data.return_value = None
    return AgentService(llm=llm, data_provider=data_provider)


def test_check_input_guardrails_increments_length_block():
    agent = make_agent()
    with patch("app.core.metrics.security_blocks_total") as mock:
        result = agent._check_input_guardrails("x" * 301)
        assert result is False
        mock.labels.assert_called_with(reason="length")
        mock.labels.return_value.inc.assert_called_once()


def test_check_input_guardrails_increments_injection_block():
    agent = make_agent()
    with patch("app.core.metrics.security_blocks_total") as mock:
        # "bypass prompt" matches bilingual patterns: (bypass).*(prompt)
        result = agent._check_input_guardrails("bypass prompt")
        assert result is False
        mock.labels.assert_called_with(reason="injection")
        mock.labels.return_value.inc.assert_called_once()


def test_check_input_guardrails_increments_format_block():
    agent = make_agent()
    with patch("app.core.metrics.security_blocks_total") as mock:
        result = agent._check_input_guardrails("{{{{{{{{{{{")
        assert result is False
        mock.labels.assert_called_with(reason="format")
        mock.labels.return_value.inc.assert_called_once()


@pytest.mark.asyncio
async def test_call_tool_increments_tool_calls_total():
    agent = make_agent()
    tool_call = MagicMock()
    tool_call.function.name = "get_personal_info"
    tool_call.function.arguments = "{}"
    with patch("app.tools.registry.tool_registry") as mock_registry:
        mock_registry.tools = {"get_personal_info": True}
        mock_registry.execute = AsyncMock(return_value="result")
        with patch("app.core.metrics.tool_calls_total") as mock_counter:
            await agent._call_tool(tool_call, [])
            mock_counter.labels.assert_called_with(tool_name="get_personal_info")
            mock_counter.labels.return_value.inc.assert_called_once()


@pytest.mark.asyncio
async def test_get_response_increments_decrements_active_sessions():
    agent = make_agent()
    # Mock LLM completion to return a simple response
    response_mock = MagicMock()
    response_mock.choices = [MagicMock()]
    response_mock.choices[0].message.content = "mock response"
    response_mock.choices[0].message.tool_calls = []
    agent.llm.get_completion.return_value = response_mock

    with patch("app.core.metrics.active_sessions") as mock_gauge:
        result = await agent.get_response("hello")
        assert result["message"] == "mock response"
        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()


@pytest.mark.asyncio
async def test_get_response_exception_decrements_active_sessions():
    agent = make_agent()
    agent.llm.get_completion.side_effect = Exception("completion error")

    with patch("app.core.metrics.active_sessions") as mock_gauge:
        result = await agent.get_response("hello")
        assert "completion error" in result["message"]
        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()


@pytest.mark.asyncio
async def test_get_streaming_response_increments_decrements_active_sessions():
    agent = make_agent()
    
    # Mock LLM streaming completion
    async def mock_stream():
        chunk = MagicMock()
        chunk.choices = [MagicMock()]
        chunk.choices[0].delta.content = "stream response"
        chunk.choices[0].delta.tool_calls = []
        yield chunk

    agent.llm.get_streaming_completion.return_value = mock_stream()

    with patch("app.core.metrics.active_sessions") as mock_gauge:
        chunks = []
        async for chunk in agent.get_streaming_response("hello"):
            chunks.append(chunk)
        
        # Verify active_sessions was incremented and decremented
        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()


@pytest.mark.asyncio
async def test_get_streaming_response_exception_decrements_active_sessions():
    agent = make_agent()
    agent.llm.get_streaming_completion.side_effect = Exception("streaming error")

    with patch("app.core.metrics.active_sessions") as mock_gauge:
        chunks = []
        async for chunk in agent.get_streaming_response("hello"):
            chunks.append(chunk)
        
        mock_gauge.inc.assert_called_once()
        mock_gauge.dec.assert_called_once()
        # Verify an error message was returned in the stream
        assert len(chunks) > 0
        assert "streaming error" in chunks[0]
