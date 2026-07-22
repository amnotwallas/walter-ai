import asyncio
import random
import time
import weakref
from typing import List, Optional, Any, Tuple
import litellm
import app.core.metrics as _metrics
from app.core.config import get_settings
from app.core.logger import get_logger

try:
    from opentelemetry import trace
except ImportError:
    trace = None

logger = get_logger(__name__)


def _parse_provider_model(model_name: str) -> Tuple[str, str]:
    if "/" in model_name:
        parts = model_name.split("/", 1)
        return parts[0], parts[1]
    return "unknown", model_name


class LiteLLMMetaclass(type):
    _consecutive_failures_by_loop = weakref.WeakKeyDictionary()

    @property
    def _consecutive_failures(cls) -> int:
        try:
            loop = asyncio.get_running_loop()
            if loop not in cls._consecutive_failures_by_loop:
                cls._consecutive_failures_by_loop[loop] = 0
            return cls._consecutive_failures_by_loop[loop]
        except RuntimeError:
            return getattr(cls, "_sync_consecutive_failures", 0)

    @_consecutive_failures.setter
    def _consecutive_failures(cls, val: int) -> None:
        try:
            loop = asyncio.get_running_loop()
            cls._consecutive_failures_by_loop[loop] = val
        except RuntimeError:
            cls._sync_consecutive_failures = val

    @_consecutive_failures.deleter
    def _consecutive_failures(cls) -> None:
        try:
            loop = asyncio.get_running_loop()
            if loop in cls._consecutive_failures_by_loop:
                del cls._consecutive_failures_by_loop[loop]
        except RuntimeError:
            if hasattr(cls, "_sync_consecutive_failures"):
                del cls._sync_consecutive_failures


class LiteLLMAdapter(metaclass=LiteLLMMetaclass):
    """
    Concrete adapter using LiteLLM with exponential backoff retries, failover, and metrics.
    """
    _locks_by_loop = weakref.WeakKeyDictionary()
    _max_retries: int = 3
    _base_delay: float = 0.05

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        if loop not in cls._locks_by_loop:
            cls._locks_by_loop[loop] = asyncio.Lock()
        return cls._locks_by_loop[loop]

    @property
    def model(self) -> str:
        return get_settings().llm_model

    @property
    def temperature(self) -> float:
        return get_settings().llm_temperature

    async def get_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> Any:
        retries = max_retries if max_retries is not None else self._max_retries
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "timeout": 30.0,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        primary_model = self.model
        primary_provider, primary_model_name = _parse_provider_model(primary_model)

        start_time = time.perf_counter()
        last_exception = None

        for attempt in range(retries):
            current_model = kwargs.get("model", self.model)
            provider, model_name = _parse_provider_model(current_model)

            tracer = trace.get_tracer("walter-ai") if trace is not None else None
            span_ctx = None
            if tracer is not None:
                span_ctx = tracer.start_as_current_span("llm_completion")
                span_ctx.__enter__()
                span = trace.get_current_span()
                if span:
                    span.set_attribute("llm.model", current_model)
            try:
                try:
                    response = await litellm.acompletion(**kwargs)
                    latency = time.perf_counter() - start_time
                    async with self._get_lock():
                        LiteLLMAdapter._consecutive_failures = 0
                    if current_model == primary_model:
                        _metrics.llm_circuit_breaker_active.labels(
                            provider=primary_provider, model=primary_model_name
                        ).set(0)

                    usage = getattr(response, "usage", None)
                    if usage:
                        logger.info(
                            f"LLM completion successful | Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out (total: {usage.total_tokens})",
                            extra={
                                "event": "llm_completion_success",
                                "input_tokens": usage.prompt_tokens,
                                "output_tokens": usage.completion_tokens,
                                "total_tokens": usage.total_tokens,
                                "model": current_model,
                                "provider": provider,
                                "latency": latency,
                            },
                        )
                        _metrics.llm_tokens_total.labels(type="input").inc(usage.prompt_tokens)
                        _metrics.llm_tokens_total.labels(type="output").inc(usage.completion_tokens)
                    else:
                        logger.info(
                            f"LLM completion successful | Latency: {latency:.3f}s",
                            extra={
                                "event": "llm_completion_success",
                                "model": current_model,
                                "provider": provider,
                                "latency": latency,
                            },
                        )
                    return response
                except Exception as e:
                    last_exception = e
                    should_fallback = False
                    async with self._get_lock():
                        LiteLLMAdapter._consecutive_failures += 1
                        settings = get_settings()
                        if (
                            settings.llm_fallback
                            and LiteLLMAdapter._consecutive_failures >= settings.llm_max_failures
                        ):
                            should_fallback = True
                            LiteLLMAdapter._consecutive_failures = 0

                    _metrics.llm_failures_total.labels(
                        provider=provider, model=model_name, error_type=type(e).__name__
                    ).inc()

                    if should_fallback:
                        _metrics.llm_circuit_breaker_active.labels(
                            provider=primary_provider, model=primary_model_name
                        ).set(1)
                        _metrics.llm_fallback_total.inc()
                        logger.warning(
                            f"LLM fallback activado tras {settings.llm_max_failures} fallos. Usando: {settings.llm_fallback}"
                        )
                        fallback_kwargs = kwargs.copy()
                        fallback_kwargs["model"] = settings.llm_fallback
                        fb_provider, fb_model_name = _parse_provider_model(settings.llm_fallback)
                        fb_tracer = trace.get_tracer("walter-ai") if trace is not None else None
                        fb_span_ctx = None
                        if fb_tracer is not None:
                            fb_span_ctx = fb_tracer.start_as_current_span("llm_completion")
                            fb_span_ctx.__enter__()
                            span = trace.get_current_span()
                            if span:
                                span.set_attribute("llm.model", settings.llm_fallback)
                        try:
                            response = await litellm.acompletion(**fallback_kwargs)
                            latency = time.perf_counter() - start_time
                            async with self._get_lock():
                                LiteLLMAdapter._consecutive_failures = 0
                            usage = getattr(response, "usage", None)
                            if usage:
                                logger.info(
                                    f"LLM completion successful | Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out (total: {usage.total_tokens})",
                                    extra={
                                        "event": "llm_completion_success",
                                        "input_tokens": usage.prompt_tokens,
                                        "output_tokens": usage.completion_tokens,
                                        "total_tokens": usage.total_tokens,
                                        "model": settings.llm_fallback,
                                        "provider": fb_provider,
                                        "latency": latency,
                                    },
                                )
                                _metrics.llm_tokens_total.labels(type="input").inc(usage.prompt_tokens)
                                _metrics.llm_tokens_total.labels(type="output").inc(usage.completion_tokens)
                            else:
                                logger.info(
                                    f"LLM completion successful | Latency: {latency:.3f}s",
                                    extra={
                                        "event": "llm_completion_success",
                                        "model": settings.llm_fallback,
                                        "provider": fb_provider,
                                        "latency": latency,
                                    },
                                )
                            return response
                        except Exception as fb_err:
                            last_exception = fb_err
                            _metrics.llm_failures_total.labels(
                                provider=fb_provider, model=fb_model_name, error_type=type(fb_err).__name__
                            ).inc()
                            logger.error(
                                f"llm_completion_failed | Fallback model {settings.llm_fallback} failed: {fb_err}",
                                extra={
                                    "event": "llm_completion_failed",
                                    "model": settings.llm_fallback,
                                    "provider": fb_provider,
                                    "error": str(fb_err),
                                },
                            )
                            raise fb_err
                        finally:
                            if fb_span_ctx is not None:
                                fb_span_ctx.__exit__(None, None, None)

                    if attempt < retries - 1:
                        _metrics.llm_retries_total.labels(
                            provider=provider, model=model_name
                        ).inc()
                        logger.warning(
                            f"llm_retry_attempt | Attempt {attempt + 1}/{retries} failed for model {current_model}: {e}",
                            extra={
                                "event": "llm_retry_attempt",
                                "attempt": attempt + 1,
                                "model": current_model,
                                "provider": provider,
                                "error": str(e),
                            },
                        )
                        backoff_delay = (2 ** attempt) * self._base_delay + random.uniform(0, 0.01)
                        await asyncio.sleep(backoff_delay)
            finally:
                if span_ctx is not None:
                    span_ctx.__exit__(None, None, None)

        logger.error(
            f"llm_completion_failed | All {retries} attempts failed for model {kwargs.get('model', self.model)}: {last_exception}",
            extra={
                "event": "llm_completion_failed",
                "model": kwargs.get("model", self.model),
                "provider": primary_provider,
                "error": str(last_exception),
            },
        )
        raise last_exception

    async def get_streaming_completion(
        self,
        messages: List[dict],
        tools: Optional[List[dict]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> Any:
        retries = max_retries if max_retries is not None else self._max_retries
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
            "timeout": 30.0,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        primary_model = self.model
        primary_provider, primary_model_name = _parse_provider_model(primary_model)

        start_time = time.perf_counter()
        last_exception = None
        response = None
        active_model = kwargs.get("model", self.model)

        for attempt in range(retries):
            current_model = kwargs.get("model", self.model)
            provider, model_name = _parse_provider_model(current_model)

            tracer = trace.get_tracer("walter-ai") if trace is not None else None
            span_ctx = None
            if tracer is not None:
                span_ctx = tracer.start_as_current_span("llm_completion")
                span_ctx.__enter__()
                span = trace.get_current_span()
                if span:
                    span.set_attribute("llm.model", current_model)
            try:
                try:
                    response = await litellm.acompletion(**kwargs)
                    async with self._get_lock():
                        LiteLLMAdapter._consecutive_failures = 0
                    if current_model == primary_model:
                        _metrics.llm_circuit_breaker_active.labels(
                            provider=primary_provider, model=primary_model_name
                        ).set(0)
                    active_model = current_model
                    break
                except Exception as e:
                    last_exception = e
                    should_fallback = False
                    async with self._get_lock():
                        LiteLLMAdapter._consecutive_failures += 1
                        settings = get_settings()
                        if (
                            settings.llm_fallback
                            and LiteLLMAdapter._consecutive_failures >= settings.llm_max_failures
                        ):
                            should_fallback = True
                            LiteLLMAdapter._consecutive_failures = 0

                    _metrics.llm_failures_total.labels(
                        provider=provider, model=model_name, error_type=type(e).__name__
                    ).inc()

                    if should_fallback:
                        _metrics.llm_circuit_breaker_active.labels(
                            provider=primary_provider, model=primary_model_name
                        ).set(1)
                        _metrics.llm_fallback_total.inc()
                        logger.warning(
                            f"LLM fallback activado tras {settings.llm_max_failures} fallos. Usando: {settings.llm_fallback}"
                        )
                        fallback_kwargs = kwargs.copy()
                        fallback_kwargs["model"] = settings.llm_fallback
                        fb_provider, fb_model_name = _parse_provider_model(settings.llm_fallback)
                        fb_tracer = trace.get_tracer("walter-ai") if trace is not None else None
                        fb_span_ctx = None
                        if fb_tracer is not None:
                            fb_span_ctx = fb_tracer.start_as_current_span("llm_completion")
                            fb_span_ctx.__enter__()
                            span = trace.get_current_span()
                            if span:
                                span.set_attribute("llm.model", settings.llm_fallback)
                        try:
                            response = await litellm.acompletion(**fallback_kwargs)
                            async with self._get_lock():
                                LiteLLMAdapter._consecutive_failures = 0
                            active_model = settings.llm_fallback
                            break
                        except Exception as fb_err:
                            last_exception = fb_err
                            _metrics.llm_failures_total.labels(
                                provider=fb_provider, model=fb_model_name, error_type=type(fb_err).__name__
                            ).inc()
                            logger.error(
                                f"llm_completion_failed | Fallback model {settings.llm_fallback} failed: {fb_err}",
                                extra={
                                    "event": "llm_completion_failed",
                                    "model": settings.llm_fallback,
                                    "provider": fb_provider,
                                    "error": str(fb_err),
                                },
                            )
                            kwargs["model"] = settings.llm_fallback
                        finally:
                            if fb_span_ctx is not None:
                                fb_span_ctx.__exit__(None, None, None)

                    if attempt < retries - 1:
                        _metrics.llm_retries_total.labels(
                            provider=provider, model=model_name
                        ).inc()
                        logger.warning(
                            f"llm_retry_attempt | Stream attempt {attempt + 1}/{retries} failed for model {current_model}: {e}",
                            extra={
                                "event": "llm_retry_attempt",
                                "attempt": attempt + 1,
                                "model": current_model,
                                "provider": provider,
                                "error": str(e),
                            },
                        )
                        backoff_delay = (2 ** attempt) * self._base_delay + random.uniform(0, 0.01)
                        await asyncio.sleep(backoff_delay)
            finally:
                if span_ctx is not None:
                    span_ctx.__exit__(None, None, None)

        if response is None:
            final_provider, final_model_name = _parse_provider_model(kwargs.get("model", self.model))
            logger.error(
                f"llm_completion_failed | All {retries} stream attempts failed for model {kwargs.get('model', self.model)}: {last_exception}",
                extra={
                    "event": "llm_completion_failed",
                    "model": kwargs.get("model", self.model),
                    "provider": final_provider,
                    "error": str(last_exception),
                },
            )
            raise last_exception

        async def stream_wrapper():
            prompt_tokens = 0
            completion_tokens = 0
            first_token_latency = None
            success = False
            tracer = trace.get_tracer("walter-ai") if trace is not None else None
            span_ctx = None
            if tracer is not None:
                span_ctx = tracer.start_as_current_span("llm_streaming_completion")
                span_ctx.__enter__()
                span = trace.get_current_span()
                if span:
                    span.set_attribute("llm.model", active_model)
            try:
                async for chunk in response:
                    if first_token_latency is None:
                        first_token_latency = time.perf_counter() - start_time
                    usage = getattr(chunk, "usage", None)
                    if usage:
                        prompt_tokens = usage.prompt_tokens
                        completion_tokens = usage.completion_tokens
                    yield chunk
                success = True
            except Exception as e:
                provider, model_name = _parse_provider_model(active_model)
                _metrics.llm_failures_total.labels(
                    provider=provider, model=model_name, error_type=type(e).__name__
                ).inc()
                async with self._get_lock():
                    LiteLLMAdapter._consecutive_failures += 1
                # Trip circuit breaker if consecutive failures limit is reached midstream
                async with self._get_lock():
                    settings = get_settings()
                    if (
                        settings.llm_fallback
                        and LiteLLMAdapter._consecutive_failures >= settings.llm_max_failures
                    ):
                        _metrics.llm_circuit_breaker_active.labels(
                            provider=primary_provider, model=primary_model_name
                        ).set(1)
                        LiteLLMAdapter._consecutive_failures = 0
                logger.error(
                    f"llm_completion_failed | Stream failed midstream for model {active_model}: {e}",
                    extra={
                        "event": "llm_completion_failed",
                        "model": active_model,
                        "provider": provider,
                        "error": str(e),
                    },
                )
                raise e
            finally:
                if span_ctx is not None:
                    span_ctx.__exit__(None, None, None)
                if success:
                    total_latency = time.perf_counter() - start_time
                    ttft_str = f" | TTFT: {first_token_latency:.3f}s" if first_token_latency is not None else ""
                    provider, _ = _parse_provider_model(active_model)
                    logger.info(
                        f"LLM stream completed | Tokens: {prompt_tokens} in, {completion_tokens} out (total: {prompt_tokens + completion_tokens}){ttft_str}",
                        extra={
                            "event": "llm_completion_success",
                            "input_tokens": prompt_tokens,
                            "output_tokens": completion_tokens,
                            "total_tokens": prompt_tokens + completion_tokens,
                            "model": active_model,
                            "provider": provider,
                            "ttft": first_token_latency,
                            "total_latency": total_latency,
                        },
                    )
                    _metrics.llm_tokens_total.labels(type="input").inc(prompt_tokens)
                    _metrics.llm_tokens_total.labels(type="output").inc(completion_tokens)

        return stream_wrapper()
