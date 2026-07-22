# Runbook: Tool Execution Timeout

## Overview
This runbook outlines operational procedures for diagnosing and mitigating tool execution timeouts within agent workflows.

## 1. Symptoms
* End-users experience slow response times or request timeouts when calling agent endpoints.
* Agent execution hangs or fails during tool execution phase.
* High latency spikes in HTTP API endpoints handling tool invocation.

## 2. Active Alerts
* **`Highp95Latency`**
  * **Condition:** `p95 HTTP response duration > 2.0s` over a 5-minute window.
  * **Severity:** `warning`
* **`AgentToolFailures`**
  * **Condition:** `Failed tool execution rate > 0.1/sec` over a 5-minute window.
  * **Severity:** `warning`

## 3. Incident Verification
Search JSON application logs for failed tool execution events due to timeouts:
```json
{
  "level": "ERROR",
  "message": "Tool execution failed",
  "tool_status": "failed",
  "error_type": "TimeoutError",
  "tool_name": "bash_execution",
  "execution_time_seconds": 30.0
}
```
Run Prometheus metric query to check tool failure rates by error type:
```promql
rate(agent_tool_failures_total{error_type="TimeoutError"}[5m])
```

## 4. Immediate Mitigation Steps
1. **Kill Slow Session:**
   * Identify stuck process or agent session ID from application logs.
   * Terminate hanging subagent or background task using management endpoints or CLI commands.
2. **Check Adapter Endpoints:**
   * Verify responsiveness and network connectivity of downstream tool adapter endpoints and external APIs.
   * Inspect host system resource utilization (CPU, memory, file descriptors, network bandwidth).
3. **Isolate Failing Tools:**
   * Temporarily disable or throttle unresponsive tools in tool registry if downstream services are unresponsive.

## 5. Prevention & Long-Term Solutions
* **Enforce Tool Execution Limits:** Set explicit per-tool execution timeouts (e.g. maximum 15s - 30s per tool call) at the service level.
* **Implement Circuit Breaking:** Apply circuit breaker pattern around external tool adapters to short-circuit requests when failure/timeout threshold is exceeded.
* **Asynchronous Execution:** Offload long-running tool operations to async background workers.
