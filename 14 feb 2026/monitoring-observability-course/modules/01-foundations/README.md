# Module 1 — Observability Foundations

**Level:** Beginner  
**Duration:** ~8 hours  
**Prerequisites:** None

---

## Learning Objectives

By the end of this module you will be able to:

- Distinguish monitoring from observability and explain when each applies.
- Identify the three pillars of observability (metrics, logs, traces) and their use cases.
- Apply the four Golden Signals to evaluate any service.
- Define SLIs, SLOs, and SLAs and relate them to business outcomes.
- Calculate MTTR and MTTD and explain their operational significance.
- Recognize alert fatigue and apply strategies to reduce it.

---

## 1.1 Monitoring vs Observability

### Concepts

| Aspect | Monitoring | Observability |
|--------|-----------|---------------|
| Approach | Predefined checks against known failure modes | Ability to ask arbitrary questions about system state |
| Scope | "Is it broken?" | "Why is it broken?" |
| Data model | Dashboards, thresholds, alerts | Metrics + logs + traces correlated together |
| When it works best | Known-unknowns | Unknown-unknowns |

### Key Takeaway

Monitoring tells you *when* something is wrong. Observability helps you understand *why* without deploying new code.

### Study Questions

1. A service returns HTTP 500 errors. Your dashboard shows the error rate spike. Is this monitoring or observability?
2. You need to find out which specific database query is causing latency in a microservice you've never debugged before. Which approach do you need?
3. Can you have observability without monitoring? Can you have monitoring without observability?

---

## 1.2 Metrics vs Logs vs Traces

### The Three Pillars

#### Metrics
- **What:** Numeric measurements collected over time (time series).
- **Format:** `{name, labels, value, timestamp}` — e.g., `http_requests_total{method="GET", status="200"} 14523`
- **Strengths:** Cheap to store, fast to query, good for aggregation and alerting.
- **Weakness:** Low cardinality — you lose individual request detail.
- **Tools:** Prometheus, CloudWatch Metrics, Datadog Metrics, StatsD.

#### Logs
- **What:** Timestamped text records of discrete events.
- **Format:** Structured (JSON) or unstructured (plain text).
- **Strengths:** Rich context, captures individual events, good for debugging.
- **Weakness:** Expensive at scale, hard to correlate across services without structure.
- **Tools:** ELK Stack, Loki, CloudWatch Logs, Datadog Logs, Fluentd.

#### Traces
- **What:** End-to-end record of a request as it flows through distributed services.
- **Format:** Spans organized in a tree — each span has `{traceID, spanID, parentSpanID, service, operation, duration}`.
- **Strengths:** Shows causality across service boundaries, pinpoints bottlenecks.
- **Weakness:** Requires instrumentation in every service, sampling decisions affect completeness.
- **Tools:** Jaeger, Zipkin, Datadog APM, AWS X-Ray, OpenTelemetry.

### How They Relate

```
Alert fires (metric) → Check dashboard (metric) → Search logs (log) → Follow trace (trace) → Root cause
```

### Hands-On Exercise

1. Run a sample web application locally (any language).
2. Identify what data each pillar would capture for a single HTTP request.
3. Write down one question each pillar can answer that the others cannot.

---

## 1.3 The Four Golden Signals

Defined by Google's SRE book. These four signals cover the health of any user-facing system.

### 1. Latency
- **Definition:** Time to serve a request.
- **What to measure:** Distinguish successful requests from failed ones. A fast HTTP 500 is not a "good" response.
- **Typical metrics:** `p50`, `p95`, `p99` response time.
- **Example:** `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`

### 2. Traffic
- **Definition:** Demand on the system.
- **What to measure:** Requests per second, transactions per second, sessions, or whatever unit represents work.
- **Example:** `rate(http_requests_total[5m])`

### 3. Errors
- **Definition:** Rate of failed requests.
- **What to measure:** Explicit failures (HTTP 5xx), implicit failures (HTTP 200 with wrong content), policy violations (responses slower than SLO).
- **Example:** `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`

### 4. Saturation
- **Definition:** How "full" the service is.
- **What to measure:** CPU, memory, disk I/O, queue depth, connection pool usage. Most services degrade before hitting 100%.
- **Example:** `node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes`

### Exercise

Pick a service you use daily (e.g., a web API). For each Golden Signal:
1. Define the specific metric you would track.
2. Set a threshold that would trigger an alert.
3. Explain what action you would take when the alert fires.

---

## 1.4 SLIs, SLOs, and SLAs

### Definitions

| Term | Full Name | What It Is | Who Owns It |
|------|-----------|-----------|-------------|
| **SLI** | Service Level Indicator | A quantitative measure of service behavior (e.g., "99.2% of requests complete in < 300ms") | Engineering |
| **SLO** | Service Level Objective | A target value for an SLI (e.g., "99.9% availability over 30 days") | Engineering + Product |
| **SLA** | Service Level Agreement | A contract with consequences if the SLO is not met (e.g., "credits issued if uptime < 99.95%") | Business + Legal |

### Relationship

```
SLI (measurement) → SLO (target) → SLA (contract)
```

- SLIs are the raw data.
- SLOs are internal goals — they should be stricter than SLAs.
- SLAs are external promises — breaching them has financial or legal consequences.

### Error Budgets

- **Error budget** = `1 - SLO`. If your SLO is 99.9%, your error budget is 0.1%.
- Over 30 days, 0.1% = ~43 minutes of allowed downtime.
- Error budgets balance reliability with feature velocity: if the budget is spent, freeze deployments and fix reliability.

### Common SLI Categories

| Category | Example SLI |
|----------|------------|
| Availability | Proportion of successful requests |
| Latency | Proportion of requests faster than threshold |
| Throughput | Requests processed per second |
| Correctness | Proportion of requests returning correct data |
| Freshness | Proportion of data updated within threshold |

### Exercise

1. Define 2 SLIs for a checkout API.
2. Set SLOs for each SLI.
3. Calculate the error budget for a 30-day window.
4. Describe what happens when the error budget is exhausted.

---

## 1.5 MTTR and MTTD

### Definitions

| Metric | Full Name | Measures |
|--------|-----------|----------|
| **MTTD** | Mean Time to Detect | Average time from incident start to detection |
| **MTTR** | Mean Time to Recover | Average time from detection to resolution |

### The Incident Timeline

```
Incident starts → [MTTD] → Alert fires → Acknowledge → Diagnose → Fix → Verify → [MTTR] → Resolved
```

### Why They Matter

- **MTTD** reflects the quality of your monitoring and alerting.
- **MTTR** reflects the quality of your runbooks, tooling, and team processes.
- Total impact = MTTD + MTTR. Reducing either reduces customer impact.

### Strategies to Reduce MTTD

1. Monitor SLIs, not just infrastructure metrics.
2. Use anomaly detection for unknown failure modes.
3. Implement synthetic monitoring (proactive checks).
4. Reduce alert noise so real alerts are noticed faster.

### Strategies to Reduce MTTR

1. Maintain runbooks for common failure scenarios.
2. Automate remediation for known issues (auto-scaling, restarts).
3. Use distributed tracing to speed up root cause analysis.
4. Practice incident response with game days.

### Exercise

1. An API went down at 14:00. The alert fired at 14:12. The fix was deployed at 14:45. Calculate MTTD and MTTR.
2. List three changes that would reduce MTTD for this scenario.

---

## 1.6 Alert Fatigue

### What It Is

Alert fatigue occurs when operators receive so many alerts that they start ignoring them. This leads to missed real incidents.

### Causes

- Alerting on metrics instead of symptoms (e.g., "CPU > 80%" instead of "error rate > 1%").
- Thresholds set too aggressively.
- No deduplication — the same issue triggers multiple alerts.
- Alerts with no clear action ("what am I supposed to do with this?").
- Flapping alerts that fire and resolve repeatedly.

### Principles for Effective Alerting

1. **Every alert must be actionable.** If there's no action to take, it's not an alert — it's a log entry.
2. **Alert on symptoms, not causes.** Users care about errors and latency, not CPU usage.
3. **Use severity levels.** Not everything is P1.
   - **P1 / Critical:** Customer-facing impact, immediate response required.
   - **P2 / Warning:** Degradation likely if not addressed within hours.
   - **P3 / Info:** Awareness only, review during business hours.
4. **Set appropriate windows.** Alert on `rate(errors[5m]) > 0.01`, not on a single error.
5. **Include context in alerts.** Service name, environment, runbook link, recent changes.
6. **Review alerts regularly.** Delete or tune alerts that are consistently ignored.

### Alert Quality Metrics

| Metric | Target |
|--------|--------|
| Signal-to-noise ratio | > 80% of alerts lead to action |
| Time to acknowledge | < 5 minutes for P1 |
| Alerts per on-call shift | < 20 (Google SRE recommendation) |
| Flapping alerts | 0 |

### Exercise

1. Audit a set of 10 sample alerts. Classify each as actionable or noise.
2. Rewrite 3 noisy alerts to be symptom-based and actionable.
3. Design an alert escalation policy with P1/P2/P3 levels.

---

## Module 1 Assessment

### Knowledge Check

1. Explain the difference between monitoring and observability in two sentences.
2. A service has an SLO of 99.95% availability. How many minutes of downtime are allowed per month?
3. Which Golden Signal would you check first if users report "the page is slow"?
4. You receive 50 alerts per on-call shift and only 8 require action. What is the signal-to-noise ratio and what should you do?
5. Draw the incident timeline and label MTTD and MTTR.

### Practical Project

Set up a simple web application and define:
- 3 SLIs with corresponding SLOs
- An error budget policy
- An alerting strategy using the Golden Signals
- A runbook template for the most likely failure mode

---

## Next Module

→ [Module 2 — Prometheus](../02-prometheus/README.md)
