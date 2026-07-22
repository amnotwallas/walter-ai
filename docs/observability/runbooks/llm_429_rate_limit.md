# Runbook: LLM 429 Rate Limit

## Overview
This runbook provides actionable procedures for responding to rate-limiting errors (`429 Too Many Requests`) from LLM model providers (e.g., Groq, OpenAI, LiteLLM integration).

## 1. Symptoms
* Upstream LLM provider returns `HTTP 429 Too Many Requests` or `RateLimitError` exceptions.
* Increased API response latency or fallback activation logs in LiteLLM adapter.
* Agent execution failures due to LLM provider capacity limits.

## 2. Active Alerts
* **`LLMProviderFailures`**
  * **Condition:** `LLM execution failure rate > 0.1/sec` over a 2-minute window.
  * **Severity:** `critical`

## 3. Incident Verification
Run the following Prometheus query in Grafana / Prometheus console to confirm Rate Limit errors:
```promql
rate(llm_failures_total{error_type="RateLimitError"}[5m])
```
Inspect structured JSON application logs for matching exceptions:
```json
{
  "level": "ERROR",
  "message": "LLM provider rate limit exceeded",
  "error_type": "RateLimitError",
  "provider": "groq",
  "status_code": 429
}
```

## 4. Immediate Mitigation Steps
1. **Verify Auto-Fallback Triggers:**
   * Confirm that LiteLLM secondary provider fallback routing is active (e.g., failover from Groq to OpenAI or Anthropic).
   * Check fallback metric: `rate(llm_fallback_total[5m])`.
2. **Inspect API Key Quota & Usage:**
   * Log into the upstream provider dashboard (e.g., Groq Console / OpenAI Dashboard).
   * Check monthly credit limit, daily tier caps, and current token usage per minute (TPM) / requests per minute (RPM).
3. **Rotate or Swap API Keys:**
   * If quota on the primary key is exhausted, update the active environment variable `LLM_API_KEY` with a secondary funded key.
   * Reload configuration without restarting service if hot-reload is enabled, or perform a rolling restart.

## 5. Prevention & Long-Term Solutions
* **Adjust Quota & Tier Settings:** Upgrade provider account tier to higher RPM/TPM limits.
* **Lower Concurrent Request Count:** Configure concurrency caps and rate limiters on incoming agent requests.
* **Implement Adaptive Backoff:** Ensure LiteLLM retry logic uses exponential backoff with full jitter for 429 status codes.
