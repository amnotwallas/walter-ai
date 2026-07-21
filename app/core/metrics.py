from prometheus_client import Counter, Gauge

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens consumed",
    ["type"],  # input | output
)

llm_fallback_total = Counter(
    "llm_fallback_total",
    "Times the LLM auto-fallback was triggered",
)

active_sessions = Gauge(
    "active_sessions",
    "Currently active chat sessions",
)

security_blocks_total = Counter(
    "security_blocks_total",
    "Requests blocked by the security guardrail",
    ["reason"],  # length | injection | format
)

tool_calls_total = Counter(
    "tool_calls_total",
    "Agent tool calls dispatched",
    ["tool_name"],
)

llm_retries_total = Counter(
    "llm_retries_total",
    "Total LLM retry requests",
    ["provider", "model"]
)

llm_failures_total = Counter(
    "llm_failures_total",
    "Total LLM completion failures",
    ["provider", "model", "error_type"]
)

llm_circuit_breaker_active = Gauge(
    "llm_circuit_breaker_active",
    "Circuit breaker tripped status (1=active/tripped, 0=inactive)",
    ["provider", "model"]
)

