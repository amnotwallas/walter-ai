import pytest
from unittest.mock import patch, AsyncMock
from app.adapters.llm.litellm_adapter import LiteLLMAdapter

@pytest.mark.asyncio
async def test_litellm_adapter_get_completion():
    adapter = LiteLLMAdapter()
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = "mock_response"
        
        response = await adapter.get_completion(messages, temperature=0.7)
        
        assert response == "mock_response"
        mock_acompletion.assert_called_once_with(
            model=adapter.model,
            messages=messages,
            temperature=0.7
        )

@pytest.mark.asyncio
async def test_litellm_adapter_get_streaming_completion():
    adapter = LiteLLMAdapter()
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = "mock_stream"
        
        response = await adapter.get_streaming_completion(messages, temperature=0.7)
        
        assert response == "mock_stream"
        mock_acompletion.assert_called_once_with(
            model=adapter.model,
            messages=messages,
            temperature=0.7,
            stream=True
        )

def test_litellm_adapter_properties():
    adapter = LiteLLMAdapter()
    assert adapter.client is None
    assert isinstance(adapter.model, str)
    assert isinstance(adapter.temperature, float)
