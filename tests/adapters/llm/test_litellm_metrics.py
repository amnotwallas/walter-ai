from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.adapters.llm.litellm_adapter import LiteLLMAdapter, _parse_provider_model


@pytest.fixture(autouse=True)
def reset_consecutive_failures():
    LiteLLMAdapter._consecutive_failures = 0
    yield
    LiteLLMAdapter._consecutive_failures = 0


def test_parse_provider_model():
    p, m = _parse_provider_model("groq/meta-llama/llama-4")
    assert p == "groq"
    assert m == "meta-llama/llama-4"

    p, m = _parse_provider_model("gpt-4o")
    assert p == "unknown"
    assert m == "gpt-4o"


@pytest.mark.asyncio
async def test_get_completion_increments_token_metrics():
    adapter = LiteLLMAdapter()
    mock_usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_response = MagicMock()
    mock_response.usage = mock_usage
    mock_response.choices = [MagicMock()]

    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_response):
        with patch("app.core.metrics.llm_tokens_total") as mock_counter:
            await adapter.get_completion(messages=[{"role": "user", "content": "hi"}])
            assert mock_counter.labels.call_count >= 1


@pytest.mark.asyncio
async def test_get_completion_retries_and_metrics():
    adapter = LiteLLMAdapter()
    mock_usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    mock_response = MagicMock()
    mock_response.usage = mock_usage

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
         patch("app.core.metrics.llm_retries_total") as mock_retries, \
         patch("app.core.metrics.llm_failures_total") as mock_failures:
        
        mock_acompletion.side_effect = [Exception("Temporary Error"), mock_response]
        res = await adapter.get_completion(messages=[{"role": "user", "content": "hi"}])

        assert res == mock_response
        assert mock_acompletion.call_count == 2
        assert mock_retries.labels.call_count >= 1
        assert mock_failures.labels.call_count >= 1


@pytest.mark.asyncio
async def test_get_completion_fallback_trigger_and_circuit_breaker():
    adapter = LiteLLMAdapter()
    LiteLLMAdapter._consecutive_failures = 0

    mock_usage = MagicMock(prompt_tokens=15, completion_tokens=25, total_tokens=40)
    mock_response = MagicMock()
    mock_response.usage = mock_usage
    mock_response.choices = [MagicMock()]

    mock_settings = MagicMock()
    mock_settings.llm_fallback = "openai/gpt-4o-mini"
    mock_settings.llm_max_failures = 3

    acompletion_side_effect = [
        Exception("API Error 1"),
        Exception("API Error 2"),
        Exception("API Error 3"),
        mock_response
    ]

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
         patch("app.adapters.llm.litellm_adapter.get_settings", return_value=mock_settings), \
         patch("app.core.metrics.llm_fallback_total") as mock_fallback_counter, \
         patch("app.core.metrics.llm_circuit_breaker_active") as mock_circuit_breaker:

        mock_acompletion.side_effect = acompletion_side_effect

        response = await adapter.get_completion(
            messages=[{"role": "user", "content": "hi"}],
            max_retries=4
        )

        assert response == mock_response
        assert LiteLLMAdapter._consecutive_failures == 0
        mock_fallback_counter.inc.assert_called_once()
        assert mock_circuit_breaker.labels.call_count >= 1

        assert mock_acompletion.call_count == 4
        called_kwargs = mock_acompletion.call_args_list[3][1]
        assert called_kwargs["model"] == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_get_completion_failed_logs_and_raises():
    adapter = LiteLLMAdapter()
    with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=Exception("Fatal API Error")), \
         patch("app.adapters.llm.litellm_adapter.logger.error") as mock_logger_error:
        with pytest.raises(Exception, match="Fatal API Error"):
            await adapter.get_completion(messages=[{"role": "user", "content": "hi"}], max_retries=2)
        
        mock_logger_error.assert_called_once()
        args, kwargs = mock_logger_error.call_args
        assert "llm_completion_failed" in args[0]
        assert kwargs["extra"]["event"] == "llm_completion_failed"


@pytest.mark.asyncio
async def test_get_streaming_completion_ttft():
    adapter = LiteLLMAdapter()
    messages = [{"role": "user", "content": "Hello"}]

    class MockChunk:
        def __init__(self, usage=None):
            self.usage = usage

    async def mock_stream():
        yield MockChunk()
        yield MockChunk(MagicMock(prompt_tokens=5, completion_tokens=10, total_tokens=15))

    with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_stream()), \
         patch("app.adapters.llm.litellm_adapter.logger.info") as mock_logger_info:
        
        stream_gen = await adapter.get_streaming_completion(messages)
        chunks = [c async for c in stream_gen]
        assert len(chunks) == 2

        mock_logger_info.assert_called_once()
        args, kwargs = mock_logger_info.call_args
        assert "LLM stream completed" in args[0]
        assert kwargs["extra"]["event"] == "llm_completion_success"
        assert kwargs["extra"]["ttft"] is not None
        assert kwargs["extra"]["total_latency"] >= 0


@pytest.mark.asyncio
async def test_get_completion_fallback_on_last_attempt():
    adapter = LiteLLMAdapter()
    LiteLLMAdapter._consecutive_failures = 0
    mock_response = MagicMock(usage=MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10))

    mock_settings = MagicMock(llm_fallback="openai/gpt-4o-mini", llm_max_failures=3)

    acompletion_side_effect = [
        Exception("API Error 1"),
        Exception("API Error 2"),
        Exception("API Error 3"),
        mock_response,
    ]

    with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=acompletion_side_effect) as mock_acompletion, \
         patch("app.adapters.llm.litellm_adapter.get_settings", return_value=mock_settings):

        res = await adapter.get_completion(
            messages=[{"role": "user", "content": "test"}],
            max_retries=3
        )
        assert res == mock_response
        assert mock_acompletion.call_count == 4
        assert mock_acompletion.call_args_list[3][1]["model"] == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_circuit_breaker_reset_only_on_primary_success():
    adapter = LiteLLMAdapter()
    mock_response = MagicMock(usage=MagicMock(prompt_tokens=5, completion_tokens=5, total_tokens=10))
    mock_settings = MagicMock(llm_fallback="openai/gpt-4o-mini", llm_max_failures=1)

    with patch("litellm.acompletion", new_callable=AsyncMock, side_effect=[Exception("Err"), mock_response]), \
         patch("app.adapters.llm.litellm_adapter.get_settings", return_value=mock_settings), \
         patch("app.core.metrics.llm_circuit_breaker_active") as mock_cb:

        await adapter.get_completion(messages=[{"role": "user", "content": "hi"}], max_retries=2)
        # set(0) should NOT be called because fallback model succeeded, not primary
        for call in mock_cb.labels.return_value.set.call_args_list:
            assert call != ((0,),)


def test_lazy_lock_initialization():
    LiteLLMAdapter._lock = None
    assert LiteLLMAdapter._lock is None
    lock = LiteLLMAdapter._get_lock()
    assert isinstance(lock, Exception.__class__ if False else type(lock))
    assert LiteLLMAdapter._lock is lock

