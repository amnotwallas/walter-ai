from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.adapters.llm.litellm_adapter import LiteLLMAdapter


@pytest.fixture(autouse=True)
def reset_consecutive_failures():
    LiteLLMAdapter._consecutive_failures = 0
    yield
    LiteLLMAdapter._consecutive_failures = 0


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
async def test_get_completion_fallback_trigger_and_metrics():
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
         patch("app.core.metrics.llm_tokens_total") as mock_token_counter:

        mock_acompletion.side_effect = acompletion_side_effect

        with pytest.raises(Exception, match="API Error 1"):
            await adapter.get_completion(messages=[{"role": "user", "content": "hi"}])
        assert LiteLLMAdapter._consecutive_failures == 1

        with pytest.raises(Exception, match="API Error 2"):
            await adapter.get_completion(messages=[{"role": "user", "content": "hi"}])
        assert LiteLLMAdapter._consecutive_failures == 2

        response = await adapter.get_completion(messages=[{"role": "user", "content": "hi"}])
        
        assert response == mock_response
        assert LiteLLMAdapter._consecutive_failures == 0
        mock_fallback_counter.inc.assert_called_once()
        
        assert mock_acompletion.call_count == 4
        called_kwargs = mock_acompletion.call_args_list[3][1]
        assert called_kwargs["model"] == "openai/gpt-4o-mini"
        assert mock_token_counter.labels.call_count >= 1

