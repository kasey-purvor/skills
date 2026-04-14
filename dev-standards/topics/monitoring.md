# Monitoring

## The Observability Pipeline

Observability has three pillars. [Logging](./logging.md) covers the first. This topic covers the other two (metrics and traces) plus the systems that tie everything together.

```
Your App                    Aggregation              Human Response
────────                    ───────────              ──────────────
Structured logs  ───────►  Log aggregator  ────────►  Search & debug
(JSON events)              (Datadog, Loki, CloudWatch)

Metrics          ───────►  Time-series DB  ────────►  Dashboards
(counters, gauges)         (Prometheus, Datadog, CloudWatch)

Traces           ───────►  Trace backend   ────────►  Request waterfall
(spans with IDs)           (Jaeger, Tempo, Datadog)

                           Alerts          ────────►  Runbooks
                           (threshold rules)          (step-by-step fix instructions)
```

**Logs** tell you *what happened* to individual requests.
**Metrics** tell you *how the system is performing* as a whole.
**Traces** tell you *what path a request took* and where time was spent.

You need all three. Logs without metrics means you can't see trends. Metrics without logs means you see something is wrong but can't investigate why. Traces connect the other two across service boundaries.

---

## Metric Types

Not all numbers are the same. There are four fundamental types, and using the wrong one produces misleading data:

### Counter

A value that only goes up. You look at the **rate** (change per unit time).

```typescript
// "How many requests per second are we handling?"
const requestCounter = meter.createCounter('http_requests_total');

// In your request handler
requestCounter.add(1, { method: req.method, path: req.path, status: res.statusCode });
```

**Example:** Total HTTP requests, total errors, total bytes transferred.

**If you use a counter for "current connections":** It only goes up — you can't represent connections closing. Wrong type.

### Gauge

A value that goes up and down. You look at the **current value**.

```typescript
// "How many connections are open right now?"
// In OpenTelemetry, use UpDownCounter for values you increment/decrement:
const activeConnections = meter.createUpDownCounter('active_connections');
activeConnections.add(1);   // connection opened
activeConnections.add(-1);  // connection closed

// Or use ObservableGauge when reading a current value from an external source:
meter.createObservableGauge('memory_usage_bytes', {
  description: 'Current memory usage',
}, (result) => {
  result.observe(process.memoryUsage().heapUsed);
});
```

**OTel terminology note:** OpenTelemetry distinguishes between `UpDownCounter` (you increment/decrement it) and `ObservableGauge` (you read a value via callback). Both represent gauge-like metrics that go up and down. The concept is "gauge" — the OTel API has two instruments for it depending on how you collect the value.

**Example:** Current memory usage, active connections, queue depth, CPU utilization.

**If you use a gauge for "total requests":** It resets to zero on process restart, losing all history. Wrong type.

### Histogram

A distribution of values. You look at **percentiles** (p50, p95, p99).

```typescript
// "How long do requests take?"
const latencyHistogram = meter.createHistogram('http_request_duration_ms');

// In your request handler
const start = Date.now();
// ... handle request ...
latencyHistogram.record(Date.now() - start, { method: req.method, path: req.path });
```

**Example:** Request latency, response body sizes, queue wait times.

### Summary

Similar to histogram but computes percentiles client-side rather than server-side. Less common — most teams use histograms.

---

## What to Measure

Two frameworks answer "what should I measure?" and prevent both measuring nothing (blindness) and measuring everything (noise).

### RED Method — For Request-Driven Services (APIs, web apps)

From Tom Wilkie (Grafana/Weaveworks), inspired by Google SRE's Four Golden Signals:

- **Rate** — How many requests per second?
- **Errors** — How many of those requests fail?
- **Duration** — How long do requests take?

These three numbers describe the health of your API at a glance:

```typescript
// Rate: counter
const requestRate = meter.createCounter('http_requests_total');

// Errors: counter (subset of rate)
const errorRate = meter.createCounter('http_errors_total');

// Duration: histogram
const requestDuration = meter.createHistogram('http_request_duration_ms');

// In middleware — measure all three automatically
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    const labels = { method: req.method, path: req.route?.path || req.path, status: String(res.statusCode) };
    requestRate.add(1, labels);
    if (res.statusCode >= 500) errorRate.add(1, labels);
    requestDuration.record(duration, labels);
  });
  next();
});
```

```python
# FastAPI middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration = (time.monotonic() - start) * 1000

    labels = {"method": request.method, "path": request.url.path, "status": str(response.status_code)}
    request_counter.add(1, labels)
    if response.status_code >= 500:
        error_counter.add(1, labels)
    request_duration.record(duration, labels)

    return response
```

### USE Method — For Resources (CPU, memory, disk, network)

From Brendan Gregg:

- **Utilization** — How busy is the resource? (CPU at 80%)
- **Saturation** — Is work queueing up? (50 requests waiting for a DB connection)
- **Errors** — Is the resource producing errors? (disk write failures)

These metrics are often provided by your infrastructure (Kubernetes, cloud provider) rather than your application code.

---

## Percentiles

Averages lie. If 99 requests take 10ms and 1 request takes 10 seconds, the average is 109ms — which describes nobody's actual experience.

**Percentiles tell the truth:**

| Percentile | Meaning | What it tells you |
|-----------|---------|-------------------|
| **p50** (median) | Half of requests are faster | The typical user experience |
| **p95** | 95% of requests are faster | Almost everyone's experience |
| **p99** | 99% of requests are faster | The worst experience except outliers |

If your p50 is 50ms but your p99 is 5 seconds, you have a **tail latency problem** — most users are fine, but 1 in 100 has a terrible experience. The average (maybe 100ms) hides this completely.

**Always monitor p95 and p99, not just averages.** Your SLOs (see below) should be defined in percentiles.

---

## SLIs, SLOs, and Error Budgets

These form the foundation of how production teams think about reliability:

### SLI (Service Level Indicator)

A measurement. The thing you're tracking.

*"What percentage of requests complete successfully in under 500ms?"*

### SLO (Service Level Objective)

A target for that measurement.

*"99.9% of requests should complete successfully in under 500ms, measured over a 30-day rolling window."*

99.9% sounds high, but it means:
- 30 days × 24 hours × 60 minutes = 43,200 minutes
- 0.1% error budget = 43.2 minutes of allowed downtime per month

### Error Budget

The math. If your SLO is 99.9%, your error budget is 0.1%.

Over 30 days with 1 million requests, **1,000 requests are allowed to fail or be slow.** Once burned through:
- Stop shipping features
- Focus on reliability improvements
- Ship only when the budget has recovered

This turns reliability into a measurable, manageable resource rather than a vague goal.

### SLA (Service Level Agreement)

A legal/contractual version of an SLO.

*"If we fail to meet 99.9% uptime, we give you a 10% service credit."*

SLAs have financial consequences. SLOs are internal engineering targets. You set your SLOs tighter than your SLAs so you have a safety margin.

---

## Alerting

Metrics become alerts when they cross thresholds. But **bad alerting is worse than no alerting** — alert fatigue causes teams to ignore real incidents.

### Good Alert Design

**Alert on symptoms, not causes:**
- Good: "Error rate > 1% for 5 minutes" (symptom — users are affected)
- Bad: "CPU > 80%" (cause — might be fine, might not)

High CPU might be normal during a batch job. High error rate is never normal. Alert on what matters to users.

**Base thresholds on SLOs:**
- If your SLO is 99.9% success rate, alert when the error rate threatens to burn through the budget
- Don't pick arbitrary numbers ("alert at 5 errors" — 5 out of how many?)

**Every alert needs a runbook:**
A document that says "when this alert fires, check these things in this order." If the oncall engineer has to guess what to do, the alert is incomplete.

**Alert on things requiring human action:**
If the system auto-recovers (a pod restarts, a circuit breaker resets), that's a metric to watch on a dashboard, not an alert to wake someone up.

### Alert Severity Levels

| Severity | Meaning | Response |
|----------|---------|----------|
| **Critical** | Users are actively affected, SLO at risk | Page oncall, immediate response |
| **Warning** | Something is degraded but still functional | Investigate during business hours |
| **Info** | Notable event, no action needed | Dashboard only, no notification |

---

## Distributed Tracing

Logs tell you what happened in one service. Traces tell you what happened across all services for one request.

### The Anatomy of a Trace

```
Trace ID: abc-123
│
├─ Span: API Gateway (total: 850ms)
│  ├─ Span: Authenticate user (45ms)
│  ├─ Span: Order Service (680ms)
│  │  ├─ Span: Validate inventory (120ms)
│  │  │  └─ Span: DB query: SELECT stock (15ms)
│  │  ├─ Span: Charge payment (400ms)
│  │  │  └─ Span: HTTP POST to Stripe (380ms)  ← the bottleneck!
│  │  └─ Span: Send confirmation email (160ms)
│  │     └─ Span: HTTP POST to SendGrid (150ms)
│  └─ Span: Serialize response (5ms)
```

Each **span** records:
- Start time and duration
- Operation name ("HTTP POST to Stripe")
- Status (success/error)
- Attributes (HTTP status code, user ID, etc.)

A **trace** is the full tree for one request. The tree shows exactly where time was spent — in this case, 380ms out of 850ms was waiting for Stripe. That's your bottleneck.

### Context Propagation

When Service A calls Service B via HTTP, it includes the trace ID in a header (`traceparent`). Service B reads the header and adds its spans to the same trace.

This is standardized by the **W3C Trace Context** specification — a standard header format so different tracing systems can interoperate.

### Sampling

Tracing every request in a high-traffic system is expensive (storage, processing). Sampling means only tracing a percentage:

- **Head-based sampling:** Decide at the entry point — "trace 10% of requests." Simple, random.
- **Tail-based sampling:** Collect everything, but only keep interesting traces (errors, slow requests). More useful but more complex to operate.

### When Is Tracing Worth It?

| System | Tracing needed? | Why |
|--------|----------------|-----|
| Single service | Probably not | Logs and metrics are sufficient |
| 2-3 services | Maybe | Depends on interaction complexity |
| Many microservices | Almost certainly | Without tracing, cross-service debugging is guesswork |
| Serverless functions | Often helpful | Functions calling functions calling functions — hard to follow otherwise |

---

## OpenTelemetry (OTel)

The industry-standard framework for instrumenting your code to produce logs, metrics, and traces.

### The Problem OTel Solves

Before OpenTelemetry, you used different libraries for each signal: pino for logs, prom-client for metrics, jaeger-client for traces. Each had its own API, configuration, and export format. Switching from Datadog to Grafana meant rewriting all your instrumentation.

**OpenTelemetry unifies all three** under one framework. Instrument once, export to any backend.

### Auto-Instrumentation

For many common libraries, you don't write instrumentation manually. OTel has packages that automatically create spans for HTTP requests, database queries, and framework operations:

**TypeScript:**

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: 'https://your-collector.example.com/v1/traces',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
// That's it — HTTP requests, DB queries, etc. are now traced automatically
```

**Python:**

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure the tracer
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

### Manual Spans

For custom business logic that auto-instrumentation doesn't cover:

```typescript
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(orderId: string) {
  const span = tracer.startSpan('process-order', {
    attributes: { 'order.id': orderId },
  });

  try {
    await validateInventory(orderId);
    await chargePayment(orderId);
    span.setStatus({ code: SpanStatusCode.OK });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    span.setStatus({ code: SpanStatusCode.ERROR, message });
    if (err instanceof Error) span.recordException(err);
    throw err;
  } finally {
    span.end();
  }
}
```

```python
from opentelemetry import trace

tracer = trace.get_tracer("my-service")

async def process_order(order_id: str):
    with tracer.start_as_current_span("process-order", attributes={"order.id": order_id}) as span:
        try:
            await validate_inventory(order_id)
            await charge_payment(order_id)
        except Exception as e:
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise
```

### When to Use OTel vs Simpler Tools

| Situation | Recommendation |
|-----------|---------------|
| Small project, single service, just need logs | pino/structlog is sufficient — OTel is overkill |
| Single service, need metrics too | pino + prom-client (or equivalent) — still simpler than OTel |
| Multiple services, need tracing | OTel is worth the setup cost |
| Want vendor flexibility (might switch from Datadog to Grafana) | OTel from the start — changing exporters is easy, rewriting instrumentation isn't |
| Already using a vendor SDK (Datadog APM, New Relic) | Use their SDK — it's simpler. Migrate to OTel later if vendor lock-in becomes a problem |

---

## Dashboards

Metrics are only useful if you can see them. A dashboard is a visual display of your key metrics.

### What a Good Dashboard Looks Like

For an API service, the main dashboard should show the RED metrics at a glance:

```
┌─ Request Rate ──────────┐ ┌─ Error Rate ─────────────┐
│  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁       │ │  ▁▁▁▁▁▁▁▁▁▁▁▁▃▅▁▁▁▁▁   │
│  450 req/s               │ │  0.3% (SLO: < 0.1%)     │
└──────────────────────────┘ └──────────────────────────┘
┌─ Latency (p50/p95/p99) ─┐ ┌─ Active Connections ─────┐
│  p50: ▁▁▁▁▁▁▁▁▁▁ 45ms   │ │  ▅▅▅▅▅▅▅▅▆▇▇▇▅▅▅▅▅▅   │
│  p95: ▂▂▂▂▂▂▃▃▂▂ 180ms  │ │  234 / 500 max          │
│  p99: ▃▃▃▄▅▅▄▃▃▃ 950ms  │ │                          │
└──────────────────────────┘ └──────────────────────────┘
```

### Dashboard Layers

| Layer | Purpose | Audience |
|-------|---------|----------|
| **Overview** | RED metrics, SLO status, system health | Everyone, at a glance |
| **Service detail** | Per-endpoint latency, error breakdown, dependency health | Engineers debugging |
| **Infrastructure** | CPU, memory, disk, network (USE metrics) | Platform/ops team |

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Monitor only averages | Track percentiles (p50, p95, p99) | Averages hide tail latency — 1% of users might have 100x worse experience |
| Alert on causes (CPU > 80%) | Alert on symptoms (error rate > 1%) | High CPU might be fine; high error rate never is |
| Alert on everything | Alert only on things requiring human action | Alert fatigue — team ignores alerts, misses real incidents |
| Use a gauge for cumulative values | Use a counter — look at the rate | Gauges reset on restart, losing history |
| Use a counter for current-state values | Use a gauge — it goes up and down | Counters can't represent decreases |
| Skip percentiles on latency metrics | Use histograms, report p50/p95/p99 | Average latency of 100ms could mean p99 of 10 seconds |
| Pick arbitrary alert thresholds | Base thresholds on SLOs | "Alert at 5 errors" means nothing without knowing the total request volume |
| Create alerts without runbooks | Every alert gets a runbook | Without steps to follow, alerts just cause panic |

---

## Deciding for Your Project

1. **What metrics do you need?** Start with RED (Rate, Errors, Duration) for every API endpoint. Add USE metrics for infrastructure later.
2. **What's your observability backend?** Datadog, Grafana Cloud, AWS CloudWatch, self-hosted Prometheus + Grafana — this determines exporters and cost.
3. **Do you need tracing?** Only if you have multiple services or complex async flows. Don't over-engineer for a monolith.
4. **OpenTelemetry or vendor SDK?** OTel for vendor flexibility. Vendor SDK for simplicity and tighter integration. Either works.
5. **What are your SLOs?** Define them early — they drive alert thresholds and dashboard design.
6. **What runbooks exist?** An alert without a runbook is just noise. Write the runbook when you create the alert.

---

## Related Topics

- **Structured logs** — see [Logging](./logging.md) for the event-level signal that metrics aggregate and traces connect
- **Health checks** — see [Resilience](./resilience.md) for liveness/readiness probes that platforms use alongside metrics
- **Error classification** — see [Error Handling](./error-handling.md) for operational vs programming error distinction that affects which metrics increment
- **Timeout and retry metrics** — see [Resilience](./resilience.md) for the patterns that produce the metrics you should track (retry rate, circuit breaker state)
- **Configuration of backends** — see [Configuration](./configuration.md) for configuring OTel exporter URLs, sampling rates, etc.
