import pytest
from unittest.mock import patch, AsyncMock
from app.providers.llm_provider import LLMProvider

@pytest.mark.asyncio
async def test_llm_provider_get_completion():
    provider = LLMProvider()
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = "mock_response"
        
        response = await provider.get_completion(messages, temperature=0.7)
        
        assert response == "mock_response"
        mock_acompletion.assert_called_once_with(
            model=provider.model,
            messages=messages,
            temperature=0.7
        )

@pytest.mark.asyncio
async def test_llm_provider_get_streaming_completion():
    provider = LLMProvider()
    messages = [{"role": "user", "content": "Hello"}]
    
    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = "mock_stream"
        
        response = await provider.get_streaming_completion(messages, temperature=0.7)
        
        assert response == "mock_stream"
        mock_acompletion.assert_called_once_with(
            model=provider.model,
            messages=messages,
            temperature=0.7,
            stream=True
        )

def test_llm_provider_properties():
    provider = LLMProvider()
    assert provider.client is None
    assert isinstance(provider.model, str)
    assert isinstance(provider.temperature, float)
