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
