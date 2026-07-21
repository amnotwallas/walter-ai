import pytest
from unittest.mock import patch, AsyncMock, ANY
from app.adapters.llm.litellm_adapter import LiteLLMAdapter

@pytest.mark.asyncio
async def test_litellm_adapter_get_completion():
    adapter = LiteLLMAdapter()
    messages = [{"role": "user", "content": "Hello"}]
    
    class MockUsage:
        def __init__(self, prompt_tokens, completion_tokens, total_tokens):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = total_tokens

    class MockResponse:
        def __init__(self, usage=None):
            self.usage = usage

    mock_response = MockResponse(MockUsage(10, 20, 30))
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
         patch("app.adapters.llm.litellm_adapter.logger.info") as mock_logger_info:
        mock_acompletion.return_value = mock_response
        
        response = await adapter.get_completion(messages, temperature=0.7)
        
        assert response == mock_response
        mock_acompletion.assert_called_once_with(
            model=adapter.model,
            messages=messages,
            temperature=0.7,
            timeout=30.0
        )
        mock_logger_info.assert_called_once()
        args, kwargs = mock_logger_info.call_args
        assert "LLM completion successful" in args[0]
        assert kwargs["extra"]["input_tokens"] == 10
        assert kwargs["extra"]["output_tokens"] == 20
        assert kwargs["extra"]["total_tokens"] == 30
        assert kwargs["extra"]["model"] == adapter.model
        assert kwargs["extra"]["event"] == "llm_completion_success"

@pytest.mark.asyncio
async def test_litellm_adapter_get_streaming_completion():
    adapter = LiteLLMAdapter()
    messages = [{"role": "user", "content": "Hello"}]
    
    class MockUsage:
        def __init__(self, prompt_tokens, completion_tokens, total_tokens):
            self.prompt_tokens = prompt_tokens
            self.completion_tokens = completion_tokens
            self.total_tokens = total_tokens
            
    class MockChunk:
        def __init__(self, usage=None):
            self.usage = usage

    async def mock_stream():
        yield MockChunk()
        yield MockChunk(MockUsage(5, 10, 15))

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion, \
         patch("app.adapters.llm.litellm_adapter.logger.info") as mock_logger_info:
        mock_acompletion.return_value = mock_stream()
        
        response = await adapter.get_streaming_completion(messages, temperature=0.7)
        
        # Iterate to exhaust the generator
        chunks = []
        async for chunk in response:
            chunks.append(chunk)
            
        assert len(chunks) == 2
        mock_acompletion.assert_called_once_with(
            model=adapter.model,
            messages=messages,
            temperature=0.7,
            stream=True,
            stream_options={"include_usage": True},
            timeout=30.0
        )
        mock_logger_info.assert_called_once()
        args, kwargs = mock_logger_info.call_args
        assert "LLM stream completed" in args[0]
        assert kwargs["extra"]["input_tokens"] == 5
        assert kwargs["extra"]["output_tokens"] == 10
        assert kwargs["extra"]["total_tokens"] == 15
        assert kwargs["extra"]["model"] == adapter.model
        assert kwargs["extra"]["event"] == "llm_completion_success"

def test_litellm_adapter_properties():
    adapter = LiteLLMAdapter()
    assert isinstance(adapter.model, str)
    assert isinstance(adapter.temperature, float)
