from prometheus_client import Counter, Gauge
from app.core.metrics import (
    llm_tokens_total,
    llm_fallback_total,
    active_sessions,
    security_blocks_total,
    tool_calls_total,
)


def test_llm_tokens_total_is_counter():
    assert isinstance(llm_tokens_total, Counter)


def test_llm_tokens_total_has_type_label():
    llm_tokens_total.labels(type="input").inc(10)
    # No debe lanzar excepción


def test_active_sessions_is_gauge():
    assert isinstance(active_sessions, Gauge)


def test_security_blocks_total_has_reason_label():
    security_blocks_total.labels(reason="length").inc()


def test_tool_calls_total_has_tool_name_label():
    tool_calls_total.labels(tool_name="get_personal_info").inc()


def test_llm_fallback_total_is_counter():
    assert isinstance(llm_fallback_total, Counter)
