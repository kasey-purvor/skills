# Monitoring

> **Calibrate to the context.** This chapter describes the full observability stack —
> the shape it takes for a team operating a service that real users depend on. Most
> apps need a slice of it, not all of it. The cheapest slice is an external uptime check
> plus an error tracker, which catch "it's down" and "it's throwing" for almost no work;
> a small internal tool is often fine with those and structured logs. Metrics earn their
> keep when traffic grows beyond what you can eyeball; tracing, SLOs, and alerting
> with on-call earn theirs when multiple services and real users are involved. Scale
> the machinery to the blast radius of an outage. Reference material, not a checklist.

## The Problem

At 2pm a customer emails: checkout has been failing since the morning. Nothing alerted, because nothing was watching the error rate, and six hours of logs hold forty thousand lines. You find the cause within the hour (a payment provider timing out on one request in twenty), but the customer found it first, and nobody can say how many others gave up without writing. Monitoring is how you notice before the customer does, and how you know how bad it is.

---

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

A system serving real traffic benefits from all three: logs without metrics means you can't see trends; metrics without logs means you see something is wrong but can't investigate why; traces connect the other two across service boundaries. Smaller apps usually start with just logs and add the others as scale demands.

---

## Metric Types

Not all numbers are the same. There are four fundamental types, and using the wrong one produces misleading data:

### Counter

A value that only goes up. You look at the **rate** (change per unit time).

```typescript
// OTel JS API 1.x
// "How many orders a minute are we taking?"
const ordersCreated = meter.createCounter('app.order.created', { unit: '{order}' });

// Where the order is created. Attribute values must be bounded: see the cardinality warning below
ordersCreated.add(1, { 'order.channel': channel });
```

**Example:** Total HTTP requests, total errors, total bytes transferred.

**If you use a counter for "current connections":** It only goes up — you can't represent connections closing. Wrong type.

### Gauge

A value that goes up and down. You look at the **current value**.

```typescript
// OTel JS API 1.x
// "How many connections are open right now?"
// In OpenTelemetry, use UpDownCounter for values you increment/decrement:
const activeConnections = meter.createUpDownCounter('app.connection.active', { unit: '{connection}' });
activeConnections.add(1);   // connection opened
activeConnections.add(-1);  // connection closed

// Or use ObservableGauge when reading a current value from an external source:
const heapUsed = meter.createObservableGauge('app.memory.heap.used', {
  description: 'Current heap usage',
  unit: 'By',
});
heapUsed.addCallback((result) => result.observe(process.memoryUsage().heapUsed));
```

**OTel terminology note:** OpenTelemetry distinguishes between `UpDownCounter` (you increment/decrement it) and `ObservableGauge` (you read a value via callback). Both represent gauge-like metrics that go up and down. The concept is "gauge" — the OTel API has two instruments for it depending on how you collect the value. API 1.9 also has a synchronous `createGauge`, whose `record()` sets a value you hold directly, such as a last-success timestamp.

**Example:** Current memory usage, active connections, queue depth, CPU utilization.

**If you use a gauge for "total requests":** A counter is *monotonic*, so any drop in its value can only be a restart, and the backend compensates when it computes rates across restarts and across instances. A gauge makes no such promise: a restart looks like real traffic disappearing, and the rates come out wrong. Wrong type.

### Histogram

A distribution of values. You look at **percentiles** (p50, p95, p99).

```typescript
// OTel JS API 1.9; name, unit and buckets from the HTTP semantic conventions
const requestDuration = meter.createHistogram('http.server.request.duration', {
  unit: 's',
  // The SDK's default buckets (0, 5, 10 … 10000) suit milliseconds: recorded in seconds,
  // every request lands in one bucket. `advice` is marked experimental in the API.
  advice: { explicitBucketBoundaries: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10] },
});

const start = performance.now();  // monotonic: Date.now() jumps when the clock is adjusted
// ... handle request ...
requestDuration.record((performance.now() - start) / 1000, {
  'http.request.method': req.method,
  'http.route': route,  // the route pattern ('/users/:id'), never req.path, which mints a series per id
  'http.response.status_code': res.statusCode,
});
```

**Example:** Request latency, response body sizes, queue wait times.

**Naming.** Use the semantic-convention name where one exists, as above. Otherwise use dots between words and put the unit in the `unit` option, not the name. Never append `_total` or a unit to the name yourself: the Prometheus exporter adds `_total` to counters and a unit suffix to every name (`http_server_request_duration_seconds`).

### Summary

Similar to histogram but computes percentiles client-side rather than server-side. Less common — most teams use histograms, for a deciding reason: percentiles computed inside each process can't be combined (averaging five instances' p99s does not give the fleet's p99), whereas histogram buckets add up across instances and the backend computes percentiles from the total. OpenTelemetry has no Summary instrument at all.

---

## What to Measure

Two frameworks answer "what should I measure?" and prevent both measuring nothing (blindness) and measuring everything (noise).

### RED Method — For Request-Driven Services (APIs, web apps)

From Tom Wilkie (Grafana/Weaveworks), inspired by Google SRE's Four Golden Signals:

- **Rate** — How many requests per second?
- **Errors** — How many of those requests fail?
- **Duration** — How long do requests take?

These three numbers describe the health of your API at a glance. In a middleware that fires *after* routing resolves, you record:

- A histogram of request duration (`http.server.request.duration`, above), labelled with method, route and status code. Its count is the rate, its count filtered to `status >= 500` is the error source, and its buckets give duration, so one instrument covers all three.

**Cardinality warning — read before choosing labels.** Label values must be bounded. Use the *route pattern* (`/users/:id`) as the `route` label, not the literal URL (`/users/123`). Literal URLs produce one label combination per unique ID — effectively unbounded cardinality. Datadog, Prometheus, and CloudWatch all charge or impose limits based on unique label combinations, and the cost of getting this wrong is real (series counts in the millions, query latency, dashboard timeouts).

**How each framework exposes the route pattern:**

- **Express:** `req.baseUrl + req.route?.path`, but only when every router is mounted on a fixed path: `req.baseUrl` is the matched string, not the pattern, so a mount such as `/orgs/:orgId` puts each id in the label. With parameterised mounts, use the `http.route` that `@opentelemetry/instrumentation-express` records. `req.route` is set only once a route matches, and its `path` omits the router's mount prefix (`/users/:id` and `/orders/:id` would both read `/:id`). Read it inside `res.on('finish')` from a middleware registered *early*: middleware registered after `app.use(router)` only runs if a handler calls `next()`, which a handler that sends a response doesn't. Label unmatched requests (404s) with a fixed value such as `unmatched`.
- **FastAPI:** `request.scope["route"].path` — similarly, available after routing resolves.
- **Next.js route handlers:** the dynamic-segment template (`/api/users/[id]`) from the file path.

Most observability libraries (`@opentelemetry/instrumentation-express`, `@opentelemetry/instrumentation-fastapi`, Datadog APM) capture these labels correctly out of the box — **prefer the auto-instrumentation package over hand-written middleware** for this exact reason. OTel's HTTP semantic conventions define the canonical label names (`http.request.method`, `http.route`, `http.response.status_code`) that dashboards expect.

**Outbound dependencies.** For each service you call, emit these too, labelled with the dependency's name (a bounded value):

- **Retry attempts by outcome**: a counter labelled with whether the call succeeded after a retry, failed again, or gave up. A rising retry rate is the early warning that arrives before errors reach users.
- **Breaker state**: a gauge of each circuit breaker's current state, plus a counter of open events. Show both on a dashboard; alert on the error rate the open circuit produces, not on the open itself.
- **Timeouts**: a counter of calls cut off by their deadline.
- **Pool wait**: a histogram of how long callers wait for a database or HTTP connection, which is the USE method's saturation signal (below).

### USE Method — For Resources (CPU, memory, disk, network)

From Brendan Gregg:

- **Utilization** — How busy is the resource? (CPU at 80%)
- **Saturation** — Is work queueing up? (50 requests waiting for a DB connection)
- **Errors** — Is the resource producing errors? (disk write failures)

These metrics are often provided by your infrastructure (Kubernetes, cloud provider) rather than your application code.

### Background Work — Scheduled Jobs and Queue Consumers

RED assumes requests arrive. A scheduled job or a queue consumer fails by going quiet, and no error-rate alert fires on silence, so watch for absence. [Resilience](./resilience.md#background-jobs) covers making the job itself safe; these are the signals that tell you it stopped:

- **Heartbeat (dead man's switch).** Each successful run pings an external monitor, which alerts when the ping does *not* arrive on time. A job cannot report that it never started.
- **Last success.** A gauge holding the time of the last successful run; alert when it is older than the schedule plus some slack.
- **Duration and rows processed** per run, so a run that takes four times as long, or succeeds on zero rows, stands out.
- **Queues:** alert on the age of the oldest waiting item rather than on depth alone (a deep queue that drains on time is fine; a shallow one stuck for an hour is not), and on the dead-letter count, because each message there is work that will not happen without a human.

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

**When you track latency at all, prefer percentiles (p95/p99) over averages** — the average hides exactly the requests you care about. If you define SLOs (see below), define them in percentiles for the same reason.

---

## SLIs, SLOs, and Error Budgets

This is how teams operating a service that users depend on think about reliability — it earns its keep once there's real traffic and someone on the hook for uptime. A small internal tool can skip the formality; the concepts are still worth knowing:

### SLI (Service Level Indicator)

A measurement. The thing you're tracking.

*"What percentage of requests complete successfully in under 500ms?"*

### SLO (Service Level Objective)

A target for that measurement.

*"99.9% of requests should complete successfully in under 500ms, measured over a 30-day rolling window."*

99.9% sounds high, but it means:
- 30 days × 24 hours × 60 minutes = 43,200 minutes
- 0.1% error budget = 43.2 minutes of allowed downtime per month

That is the **time-based** reading, which suits an uptime probe: count the bad minutes. The error budget below uses the **request-based** reading, which suits a request SLI: count the bad requests. They diverge when traffic is uneven, because an hour down at 3am burns far fewer requests than an hour at noon, so say which one each SLO uses.

### Error Budget

The math. If your SLO is 99.9%, your error budget is 0.1%.

Over 30 days with 1 million requests, **1,000 requests are allowed to fail or be slow.** What happens once it is burned through is an **error-budget policy**, agreed in advance with product: typically, pause feature releases, spend the time on reliability, and resume when the budget recovers. Agreeing it beforehand is what makes it hold; a freeze negotiated mid-incident rarely does.

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
- If your SLO is 99.9% success rate, alert on the **burn rate**, how fast errors are consuming the budget, over two windows at once. For example, page when both the last hour and the last five minutes burn at 14.4 times the sustainable rate (2% of a 30-day budget in one hour), and open a ticket for a slow burn over days. The long window shows it matters; the short one stops the alert firing after the problem has ended
- Don't pick arbitrary numbers ("alert at 5 errors" — 5 out of how many?)

**Every alert needs a runbook:**
A document that says "when this alert fires, check these things in this order." If the oncall engineer has to guess what to do, the alert is incomplete.

**Alert on things requiring human action:**
If the system auto-recovers (a pod restarts, a circuit breaker resets), that's a metric to watch on a dashboard, not an alert to wake someone up.

### Alert Severity Levels

| Severity | Meaning | Response |
|----------|---------|----------|
| **Critical** | Users are actively affected, SLO at risk | Page oncall, immediate response |
| **Warning** | Something is degraded but still functional | Open a ticket, investigate during business hours |

A notable event that needs no action is not an alert at all: put it on a dashboard and send no notification.

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

Attributes follow the same rules as log fields ([Logging](./logging.md#dont-log)). HTTP auto-instrumentation records the query string (`url.query`) and redacts only a short built-in list of signature keys such as `sig` and `X-Amz-Signature`, so `?token=` or `?email=` reaches the trace backend unless you scrub centrally in a Collector (below), or set both `redactedQueryParamsServer` (server spans) and `redactedQueryParams` (client spans). Each replaces the built-in list rather than adding to it, and neither falls back to the other.

A **trace** is the full tree for one request. The tree shows exactly where time was spent — in this case, 380ms out of 850ms was waiting for Stripe. That's your bottleneck.

### Context Propagation

When Service A calls Service B via HTTP, it includes the trace ID in a header (`traceparent`). Service B reads the header and adds its spans to the same trace.

This is standardized by the **W3C Trace Context** specification — a standard header format so different tracing systems can interoperate.

### Sampling

Tracing every request in a high-traffic system is expensive (storage, processing). Sampling means only tracing a percentage:

- **Head-based sampling:** Decide at the entry point — "trace 10% of requests." Simple, random.
- **Tail-based sampling:** Collect everything, but only keep interesting traces (errors, slow requests). More useful but more complex to operate, and it runs in a Collector (below), because no single process sees the whole trace.

An unsampled request still carries a valid trace ID in its `traceparent` header, so logs stamped with that ID stay searchable when the trace itself was dropped.

### When Is Tracing Worth It?

| System | Tracing needed? | Why |
|--------|----------------|-----|
| Single service | Often, once you chase latency | Auto-instrumentation is cheap, and its spans show N+1 queries and slow outbound calls that logs and metrics only hint at |
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
// instrumentation.ts: OTel JS SDK 2.x or 3.x (3.x needs Node 22.15+). Load it before your app code (see below).
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),  // reads OTEL_EXPORTER_OTLP_ENDPOINT
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
// HTTP requests, DB queries, etc. are now traced, provided this ran first. Recent versions
// also export metrics and log records (pino's included) over OTLP when no exporter is set:
// OTEL_LOGS_EXPORTER=none keeps logs on stdout only (see Logging).
```

**The SDK must start before `express`, `pg` and the other instrumented modules are imported.** Auto-instrumentation patches modules as they load, so an SDK started after `import express` patches nothing and emits no spans, without any error. Load it with a flag: `node --require ./instrumentation.js app.js` (CommonJS), or `node --import ./instrumentation.mjs app.mjs` plus OTel's loader hook `--experimental-loader=@opentelemetry/instrumentation/hook.mjs` (ESM). With no file at all, `node --require @opentelemetry/auto-instrumentations-node/register app.js` does the same, configured entirely by environment variables. Set `OTEL_SERVICE_NAME` (otherwise every span shows up as `unknown_service`) and point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector or backend rather than hard-coding a URL.

**Python:**

```python
# opentelemetry-sdk 1.x
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure the tracer (reads OTEL_SERVICE_NAME and OTEL_EXPORTER_OTLP_ENDPOINT)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

Python also has a zero-code route: install `opentelemetry-distro`, run `opentelemetry-bootstrap -a install` to add instrumentations for the libraries you use, then start the app as `opentelemetry-instrument uvicorn main:app`, configured by the same environment variables.

**Direct export or a Collector?** The OpenTelemetry Collector is a separate process that receives telemetry, processes it, and forwards it to one or more backends. With one service, or a vendor's SDK, export straight from the SDK and skip it. Run one when you need what only a central hop can do: tail-based sampling, scrubbing attributes in one place for every service, sending to more than one backend, or switching backends without redeploying the apps. The apps then point `OTEL_EXPORTER_OTLP_ENDPOINT` at the Collector.

### Manual Spans

For custom business logic that auto-instrumentation doesn't cover:

```typescript
// OTel JS API 1.x
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(orderId: string) {
  // startActiveSpan makes the span current inside the callback, so auto-instrumented
  // DB and HTTP calls nest under it. tracer.startSpan would leave them parented elsewhere.
  return tracer.startActiveSpan('process-order', {
    attributes: { 'order.id': orderId },
  }, async (span) => {
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
  });
}
```

```python
# opentelemetry-api 1.x
from opentelemetry import trace

tracer = trace.get_tracer("my-service")

async def process_order(order_id: str):
    # start_as_current_span records an escaping exception and sets ERROR status itself
    with tracer.start_as_current_span("process-order", attributes={"order.id": order_id}):
        await validate_inventory(order_id)
        await charge_payment(order_id)
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
| Monitor latency only as an average | Record a histogram, report p50/p95/p99 | Averages hide tail latency — an average of 100ms could mean a p99 of 10 seconds |
| Alert on causes (CPU > 80%) | Alert on symptoms (error rate > 1%) | High CPU might be fine; high error rate never is |
| Alert on everything | Alert only on things requiring human action | Alert fatigue — team ignores alerts, misses real incidents |
| Use a gauge for cumulative values | Use a counter — look at the rate | A counter's monotonicity lets the backend detect restarts and compute correct rates across them and across instances |
| Use a counter for current-state values | Use a gauge — it goes up and down | Counters can't represent decreases |
| Pick arbitrary alert thresholds | Base thresholds on SLOs | "Alert at 5 errors" means nothing without knowing the total request volume |
| Create alerts without runbooks | Every alert gets a runbook | Without steps to follow, alerts just cause panic |

---

## Deciding for Your Project

1. **What metrics do you need?** Start with RED (Rate, Errors, Duration) for every API endpoint. Add USE metrics for infrastructure later.
2. **What's your observability backend?** Datadog, Grafana Cloud, AWS CloudWatch, self-hosted Prometheus + Grafana — this determines exporters and cost.
3. **Do you need tracing?** Across multiple services or complex async flows, yes. In a single service, auto-instrumentation is cheap and pays off once you chase latency (N+1 queries, slow outbound calls); hold off on hand-written spans until then.
4. **OpenTelemetry or vendor SDK?** OTel for vendor flexibility. Vendor SDK for simplicity and tighter integration. Either works.
5. **What are your SLOs?** Define them early — they drive alert thresholds and dashboard design.
6. **What runbooks exist?** An alert without a runbook is just noise. Write the runbook when you create the alert.

---

## Related Topics

- **Structured logs** — see [Logging](./logging.md) for the event-level signal that metrics aggregate and traces connect
- **Trace-log correlation** — see [Logging](./logging.md#opentelemetry-and-your-logger) for stamping trace and span IDs on every log line, and its don't-log rules, which span attributes follow
- **Health checks** — see [Resilience](./resilience.md) for liveness/readiness probes that platforms use alongside metrics
- **Background jobs** — see [Resilience](./resilience.md#background-jobs) for idempotent handlers, single-flight scheduled runs and recording each run's outcome, which the Background Work signals above alert on
- **Error classification** — see [Error Handling](./error-handling.md) for operational vs programming error distinction that affects which metrics increment
- **Retry, timeout and breaker patterns** — see [Resilience](./resilience.md) for how retries, deadlines and circuit breakers behave; the metrics to emit for them are listed under RED above
- **Canary and rollback** — see [Deployment](./deployment.md) for canary releases judged on these metrics, and the rollback checklist your runbooks point to
- **Usage vs system health** — see [Product Analytics](./product-analytics.md) for measuring whether users engage with features (analytics asks "is anyone using it?"; monitoring asks "is it up?")
