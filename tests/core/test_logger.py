import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.logger import JsonFormatter
from app.domain.services.agent import AgentService


def test_json_formatter_includes_structured_fields():
    formatter = JsonFormatter()
    logger_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    logger_record.event = "tool_execution_completed"
    logger_record.session_id = "session-123"
    logger_record.tool_name = "get_personal_info"
    logger_record.tool_status = "success"
    logger_record.tool_latency_ms = 42.5
    logger_record.error_type = "ValueError"

    formatted_output = formatter.format(logger_record)
    parsed = json.loads(formatted_output)

    assert parsed["event"] == "tool_execution_completed"
    assert parsed["session_id"] == "session-123"
    assert parsed["tool_name"] == "get_personal_info"
    assert parsed["tool_status"] == "success"
    assert parsed["tool_latency_ms"] == 42.5
    assert parsed["error_type"] == "ValueError"


@pytest.mark.asyncio
async def test_call_tool_logs_structured_events_success():
    llm = AsyncMock()
    data_provider = MagicMock()
    agent = AgentService(llm=llm, data_provider=data_provider)

    tool_call = MagicMock()
    tool_call.function.name = "get_personal_info"
    tool_call.function.arguments = "{}"

    with patch("app.domain.services.agent.tool_registry.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "tool_result"
        with patch("app.domain.services.agent.logger") as mock_logger:
            res = await agent._call_tool(tool_call, [], session_id="test-session-456")
            assert res == "tool_result"

            assert mock_logger.info.call_count >= 2
            start_call_kwargs = mock_logger.info.call_args_list[0].kwargs
            assert start_call_kwargs["extra"]["event"] == "tool_execution_started"
            assert start_call_kwargs["extra"]["session_id"] == "test-session-456"
            assert start_call_kwargs["extra"]["tool_name"] == "get_personal_info"
            assert start_call_kwargs["extra"]["tool_status"] == "started"

            completed_call_kwargs = mock_logger.info.call_args_list[1].kwargs
            assert completed_call_kwargs["extra"]["event"] == "tool_execution_completed"
            assert completed_call_kwargs["extra"]["session_id"] == "test-session-456"
            assert completed_call_kwargs["extra"]["tool_name"] == "get_personal_info"
            assert completed_call_kwargs["extra"]["tool_status"] == "success"
            assert "tool_latency_ms" in completed_call_kwargs["extra"]


@pytest.mark.asyncio
async def test_call_tool_logs_structured_events_failure():
    llm = AsyncMock()
    data_provider = MagicMock()
    agent = AgentService(llm=llm, data_provider=data_provider)

    tool_call = MagicMock()
    tool_call.function.name = "failing_tool"
    tool_call.function.arguments = "{}"

    with patch("app.domain.services.agent.tool_registry.execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = RuntimeError("Tool crashed")
        with patch("app.domain.services.agent.logger") as mock_logger:
            res = await agent._call_tool(tool_call, [], session_id="test-session-789")
            assert "failed" in res

            failed_call_kwargs = mock_logger.error.call_args_list[0].kwargs
            assert failed_call_kwargs["extra"]["event"] == "tool_execution_failed"
            assert failed_call_kwargs["extra"]["session_id"] == "test-session-789"
            assert failed_call_kwargs["extra"]["tool_name"] == "failing_tool"
            assert failed_call_kwargs["extra"]["tool_status"] == "failed"
            assert failed_call_kwargs["extra"]["error_type"] == "RuntimeError"
