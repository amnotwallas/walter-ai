from prometheus_client import Counter, Gauge
from app.core.metrics import (
    llm_tokens_total,
    llm_fallback_total,
    active_sessions,
    security_blocks_total,
    tool_calls_total,
    llm_retries_total,
    llm_failures_total,
    llm_circuit_breaker_active,
)


def test_llm_tokens_total_is_counter():
    assert isinstance(llm_tokens_total, Counter)


def test_llm_tokens_total_has_type_label():
    llm_tokens_total.labels(type="input").inc(10)


def test_active_sessions_is_gauge():
    assert isinstance(active_sessions, Gauge)


def test_security_blocks_total_has_reason_label():
    security_blocks_total.labels(reason="length").inc()


def test_tool_calls_total_has_tool_name_label():
    tool_calls_total.labels(tool_name="get_personal_info").inc()


def test_llm_fallback_total_is_counter():
    assert isinstance(llm_fallback_total, Counter)


def test_llm_retries_total_has_provider_model_labels():
    assert isinstance(llm_retries_total, Counter)
    llm_retries_total.labels(provider="groq", model="llama-4").inc()


def test_llm_failures_total_has_labels():
    assert isinstance(llm_failures_total, Counter)
    llm_failures_total.labels(provider="groq", model="llama-4", error_type="Exception").inc()


def test_llm_circuit_breaker_active_is_gauge():
    assert isinstance(llm_circuit_breaker_active, Gauge)
    llm_circuit_breaker_active.labels(provider="groq", model="llama-4").set(1)
