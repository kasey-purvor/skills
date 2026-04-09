# Monitoring Standards

**Status:** Draft (foundational — expand during project brainstorming)

## Core Principle

Know if your system is healthy without manually checking. Get alerted when things go wrong.

---

## Tier Requirements

### Exploratory

- Console output sufficient
- Manual checks acceptable

### Internal

- Persistent logs (file or database)
- Basic health indicators in logs
- Post-run summary (success/failure counts)

### Production

- Metrics collection (rates, durations, error counts)
- Alerting on failures
- Dashboards for visibility
- Log aggregation for searchability

---

## Related Topics

- **Log levels, formats, output destinations**: See [Logging Standards](./logging.md) — this topic focuses on metrics, alerting, and dashboards; logging covers the raw records
- **Error rates and failure patterns**: See [Error Handling Standards](./error-handling.md) — error categorisation determines what monitoring should detect and alert on
- **Failure modes to monitor for**: See [Reliability Standards](./reliability.md) — retry exhaustion, circuit breaker trips, dead letter accumulation

---

## Key Concepts

| Concept | Question It Answers | Examples |
|---------|---------------------|----------|
| **Metrics** | How much / how fast? | "500 items/hour, 2% error rate" |
| **Traces** | Where did time go? | "DB: 1.2s, API: 0.8s, Transform: 0.3s" |
| **Alerts** | Is something wrong? | "Error rate > 5% for 5 minutes" |

---

## Key Metrics to Consider

| Category | Examples |
|----------|----------|
| **Throughput** | Items processed/minute, requests/second |
| **Latency** | Processing time per item, p50/p95/p99 |
| **Errors** | Error count, error rate, errors by type |
| **Saturation** | Queue depth, memory usage, connection pool |
| **Business** | Records created, API calls made, costs incurred |

---

## Alerting Principles

- Alert on **symptoms** (users affected), not causes (CPU high)
- Every alert should be **actionable**
- Include context: what failed, where to look, what to do
- Avoid alert fatigue — don't alert on things that don't need immediate action

---

## Tooling Options

| Category | Options |
|----------|---------|
| **Metrics** | Prometheus, Datadog, CloudWatch, statsd |
| **Logs** | ELK stack, Loki, CloudWatch Logs, Papertrail |
| **Alerting** | PagerDuty, Opsgenie, Slack webhooks, email |
| **Dashboards** | Grafana, Datadog, CloudWatch |

---

## Expand During Brainstorming

When productionizing, discuss:

- What metrics matter for this system?
- What failure modes need alerts?
- Where do logs go? How long retained?
- Who gets alerted? How?
- What SLAs/SLOs apply?
