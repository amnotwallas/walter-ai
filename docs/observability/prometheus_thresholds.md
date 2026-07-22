# Prometheus Alert Thresholds & Design Justifications

This document details the design rationale and threshold justifications for the alerting rules configured in `prometheus/alert.rules.yml`.

## Alert Rule Summary

| Alert Name | Metric Expression / Condition | Window (`for`) | Severity |
| :--- | :--- | :--- | :--- |
| `High5xxErrorRate` | HTTP 5xx rate / Total HTTP rate > 5% | 5m | critical |
| `Highp95Latency` | p95 HTTP response duration > 2.0s | 5m | warning |
| `LLMProviderFailures` | LLM execution failure rate > 0.1/sec | 2m | critical |
| `AgentToolFailures` | Failed tool execution rate > 0.1/sec | 5m | warning |

---

## Threshold Rationale & Design Justifications

### 1. High HTTP 5xx Error Rate (`High5xxErrorRate`)
* **Threshold:** `> 0.05` (5% of total requests returning HTTP 5xx errors over a 5-minute window)
* **Severity:** `critical`
* **Justification:** 
  A 5% error rate on 5xx status codes represents significant service degradation or backend instability affecting user requests. Setting the threshold at 5% prevents transient single-request anomalies from causing alert fatigue while guaranteeing immediate visibility for systemic backend failures. The 5-minute window filters out brief spikes during deploys or brief network re-connections.

### 2. High p95 Latency (`Highp95Latency`)
* **Threshold:** `> 2.0s` (95th percentile latency exceeding 2 seconds over a 5-minute window)
* **Severity:** `warning`
* **Justification:**
  While LLM applications inherently process complex asynchronous requests, high interactive latency degraded response responsiveness for standard API endpoints. A p95 latency target of 2.0 seconds establishes an upper boundary for healthy performance. A 5-minute evaluation window gives adequate time for normal distribution smoothing without delaying warning notifications when sustained slowdowns occur.

### 3. LLM Provider Execution Failures (`LLMProviderFailures`)
* **Threshold:** `> 0.1` (LLM provider failure rate exceeding 0.1 errors/second over a 2-minute window)
* **Severity:** `critical`
* **Justification:**
  LLM providers (e.g., Groq, OpenAI) power core system cognitive capabilities. Sustained errors exceeding 0.1 errors/sec over 2 minutes indicate critical failures such as upstream outage, API key revocation, quota exhaustion, or persistent rate limiting. The tighter 2-minute window ensures rapid reaction time so failover or fallback mechanisms can be engaged promptly.

### 4. Agent Tool Execution Failures (`AgentToolFailures`)
* **Threshold:** `> 0.1` (Failed agent tool execution rate exceeding 0.1 failures/second over a 5-minute window)
* **Severity:** `warning`
* **Justification:**
  Agent tools execute secondary actions (file operations, external API calls, command execution). Persistent tool failures (>0.1/sec over 5m) signal environmental issues (missing permissions, missing CLI utilities, dependency outages) that impair agent autonomy without necessarily bringing down the main HTTP API server.
