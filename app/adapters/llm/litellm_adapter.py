from typing import List, Optional, Any
import litellm
import app.core.metrics as _metrics
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domain.ports.llm import LLMClientPort

logger = get_logger(__name__)

class LiteLLMAdapter(LLMClientPort):
    """
    Concrete adapter implementing the LLMClientPort using LiteLLM.
    Implements Singleton pattern.
    """
    _instance = None
    _consecutive_failures: int = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def model(self) -> str:
        return get_settings().llm_model

    @property
    def temperature(self) -> float:
        return get_settings().llm_temperature

    @property
    def client(self) -> Any:
        # Backward-compatible property
        return None

    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        try:
            response = await litellm.acompletion(**kwargs)
            LiteLLMAdapter._consecutive_failures = 0
        except Exception as e:
            LiteLLMAdapter._consecutive_failures += 1
            settings = get_settings()
            if (
                settings.llm_fallback
                and LiteLLMAdapter._consecutive_failures >= settings.llm_max_failures
            ):
                _metrics.llm_fallback_total.inc()
                logger.warning(
                    f"LLM fallback activado tras {settings.llm_max_failures} fallos. Usando: {settings.llm_fallback}"
                )
                kwargs["model"] = settings.llm_fallback
                LiteLLMAdapter._consecutive_failures = 0
                response = await litellm.acompletion(**kwargs)
            else:
                raise
        usage = getattr(response, "usage", None)
        if usage:
            logger.info(
                f"LLM completion successful | Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out (total: {usage.total_tokens})",
                extra={
                    "input_tokens": usage.prompt_tokens,
                    "output_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "model": kwargs.get("model", self.model)
                }
            )
            _metrics.llm_tokens_total.labels(type="input").inc(usage.prompt_tokens)
            _metrics.llm_tokens_total.labels(type="output").inc(usage.completion_tokens)
        return response

    async def get_streaming_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
    ) -> Any:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        response = await litellm.acompletion(**kwargs)
        
        async def stream_wrapper():
            prompt_tokens = 0
            completion_tokens = 0
            try:
                async for chunk in response:
                    usage = getattr(chunk, "usage", None)
                    if usage:
                        prompt_tokens = usage.prompt_tokens
                        completion_tokens = usage.completion_tokens
                    yield chunk
            finally:
                logger.info(
                    f"LLM stream completed | Tokens: {prompt_tokens} in, {completion_tokens} out (total: {prompt_tokens + completion_tokens})",
                    extra={
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "model": self.model
                    }
                )
                _metrics.llm_tokens_total.labels(type="input").inc(prompt_tokens)
                _metrics.llm_tokens_total.labels(type="output").inc(completion_tokens)
            
        return stream_wrapper()
