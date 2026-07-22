# Incident Post-Mortem: Groq Provider LLM 429 Rate Limit Outage

## Incident Summary

| Field | Details |
| :--- | :--- |
| **Incident ID** | INC-20260721-01 |
| **Date / Time** | 2026-07-21 14:15 UTC – 14:42 UTC |
| **Duration** | 27 minutes |
| **Impacted Service** | Agent LLM Execution Pipeline / Core API |
| **Severity** | High (P2) |
| **Primary Trigger** | Groq Provider HTTP 429 Too Many Requests quota exhaustion |
| **Incident Commander** | On-Call Reliability Engineer |

---

## Executive Summary

On July 21, 2026, at 14:15 UTC, the primary LLM provider (Groq) began rejecting requests with `HTTP 429 Too Many Requests` errors. This resulted in elevated failure rates in agent task execution and triggered the `LLMProviderFailures` critical alert. Automated fallback routing to secondary provider (OpenAI) engaged partially, but initial fallback key configuration issues delayed full recovery until 14:42 UTC. Total customer-facing service degradation lasted 27 minutes, during which ~18% of LLM execution requests failed.

---

## Timeline

* **14:15 UTC** – Upstream Groq API quota reached monthly threshold; Groq endpoint begins returning `HTTP 429 RateLimitError`.
* **14:17 UTC** – Alert `LLMProviderFailures` fires in Alertmanager (`LLM execution failure rate > 0.1/sec` over 2m window).
* **14:19 UTC** – On-call engineer receives PagerDuty alert and acknowledges incident.
* **14:22 UTC** – Engineer verifies rate limit errors in Grafana logs via query `rate(llm_failures_total{error_type="RateLimitError"}[5m])`.
* **14:26 UTC** – Primary mitigation attempt: LiteLLM provider fallback triggered. Fallback to secondary provider failed due to expired secondary API key.
* **14:32 UTC** – Secondary key updated and loaded into production environment secrets.
* **14:38 UTC** – Traffic successfully fails over 100% to secondary provider. Error rate drops to 0%.
* **14:42 UTC** – Incident declared mitigated. `LLMProviderFailures` alert resolves.

---

## Root Cause Analysis

1. **Primary Root Cause:**
   The primary LLM provider (Groq) account exceeded its tier limits for Tokens Per Minute (TPM) and monthly usage quota during a peak traffic burst.

2. **Contributing Factors:**
   * Secondary fallback provider API key had expired prior to the incident without active key rotation monitoring.
   * Rate limiting settings on the internal agent request queue were set higher than the provider's upstream rate limits.

---

## Metrics & Impact

* **Peak Failure Rate:** 0.42 errors/sec
* **Total Affected Requests:** 312 agent requests
* **SLA Impact:** 99.1% success rate during 1-hour window (target: 99.9%)
* **Active Alerts Triggered:** `LLMProviderFailures`

---

## Action Items & Preventative Measures

| Task Description | Type | Owner | Target Date | Status |
| :--- | :--- | :--- | :--- | :--- |
| Upgrade Groq account tier to Enterprise limits | Prevention | Operations | 2026-07-23 | Pending |
| Implement automated API key health check & expiration alerts | Detection | Security / Platform | 2026-07-25 | Open |
| Add client-side rate limiting to throttle traffic before upstream limits | Prevention | Backend | 2026-07-28 | Open |
| Update LiteLLM provider fallback runbook with dual-key validation steps | Documentation | SRE | 2026-07-22 | Completed |
