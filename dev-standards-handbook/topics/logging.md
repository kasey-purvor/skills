# Logging

> **Calibrate to the context — but note the core habit is nearly free.** Structured
> logging with a proper logger is a one-line setup and pays for itself on anything
> deployed, so it's worth doing almost everywhere. What scales with the app is the
> machinery around it: error-tracking services, cross-service correlation, and OTel
> integration earn their keep with real users and multiple services. The don't-log
> rules (secrets, PII) are security rules and hold at any size. Reference material,
> not a checklist.

## The Problem

```typescript
console.log("User signed up");
console.log("Payment failed for user 123");
console.log("Error: " + err.message);
```

This works on your laptop. In production with thousands of requests per second:

```
User signed up
Payment failed for user 123
User signed up
Error: connection refused
User signed up
Payment failed for user 456
```

Which user signed up? Which payment failed? Was the connection error related to the payment failure? You can't tell. Unstructured text with no context, no way to filter, no way to correlate.

---

## Structured Logging

Every log entry is a JSON object with consistent fields:

```json
{
  "timestamp": "2026-04-01T10:23:45.123Z",
  "level": "info",
  "message": "User signed up",
  "service": "api",
  "userId": "user_123",
  "request_id": "abc-456-def"
}
```

```json
{
  "timestamp": "2026-04-01T10:23:45.456Z",
  "level": "error",
  "message": "Payment failed after retries exhausted",
  "service": "api",
  "userId": "user_123",
  "orderId": "order_789",
  "request_id": "abc-456-def",
  "error": "connection refused to stripe.com:443"
}
```

Now you can: search for `userId=user_123`, filter by `level=error`, correlate the signup and payment failure by `request_id`, build dashboards of error rates over time.

### TypeScript Logger Options

| | pino | Winston |
|--|------|---------|
| **Design** | JSON-first, minimal API | Flexible, multi-transport |
| **Performance** | Fastest Node.js logger (5-10x faster than Winston) | Acceptable, but slower — matters in Lambda where you pay per ms |
| **Structured output** | JSON by default, no configuration needed | JSON by default, but timestamps need `format.timestamp()` combined with `format.json()` |
| **Child loggers** | Built-in — `logger.child({ handler: "name" })` adds fields to all entries | Built-in too — the same `logger.child()` call (since v3.2.0) |
| **Transports** (plugins for sending logs to different destinations) | Fewer, run in a worker thread since v7 (`pino.transport()`) so shipping stays off the main thread. Stdout, collected by your platform (CloudWatch, Datadog), is still the usual output | Many — file, database, cloud services, HTTP. Useful when you need to send logs to multiple places simultaneously |
| **Dev readability** | Needs `pino-pretty` companion package for human-readable local output | Configurable format per environment |
| **Best for** | APIs and serverless functions sending structured JSON to CloudWatch, Datadog, etc. | Complex applications that route logs to multiple destinations, or teams already using Winston |

**Recommended default: pino.** It does one thing well (structured JSON logging), it's fast, and the child logger API solves the "add context to every log call" problem cleanly. Winston is a reasonable choice if your team already uses it or you need its transport ecosystem.

### TypeScript — pino

```typescript
// pino 9
import pino from 'pino';

const logger = pino({
  level: env.LOG_LEVEL,  // from your config module — see Configuration topic
});

// Structured: pass context as an object, message as second argument
logger.info({ userId: user.id }, 'User signed up');  // the id, never the email
logger.error({ userId: user.id, orderId, err }, 'Payment failed after retries exhausted');

// Child loggers — bind context that applies to all subsequent calls
const requestLogger = logger.child({ request_id: requestId, path: req.path });
requestLogger.info('Request received');  // request_id and path are included automatically
requestLogger.info({ userId }, 'Authenticated');  // request_id, path, AND userId
```

Winston 3 takes the message first and the context second (`logger.info('User signed up', { userId })`), has the same `logger.child()`, and stamps a time only once you list `format.timestamp()` with `format.json()` inside `format.combine()`.

### Python Logger Options

| | structlog | python-json-logger |
|--|-----------|-------------------|
| **Design** | Structured-first with context binding, wraps standard logging | Thin JSON wrapper around standard `logging` module |
| **Context binding** | Built-in — `logger.bind(key=value)` returns a new logger with that context attached | Not built-in — you manage context manually or through `logging.LoggerAdapter` |
| **Setup** | More upfront configuration (processors pipeline) | Minimal — swap the formatter on an existing handler |
| **Ecosystem** | Growing, well-maintained, strong in the web API space | Simpler, widely used, stable |
| **Best for** | Web services that need request-scoped context (trace IDs, user IDs) threaded through logs automatically | Projects that already use standard `logging` and want JSON output with minimal changes |

**Recommended default: structlog.** Its context binding is the killer feature — it eliminates the "pass the logger everywhere" problem the same way pino's child loggers do. python-json-logger is a reasonable choice if you have an existing codebase using standard `logging` and want to add JSON output without a bigger refactor.

### Python — structlog

```python
# structlog 25
import structlog

logger = structlog.get_logger()

# Structured: pass context as keyword arguments
logger.info("User signed up", user_id=user.id)  # the id, never the email
# Inside an except block: .exception() keeps the traceback, which str(e) would drop
logger.exception("Payment failed after retries exhausted", user_id=user.id, order_id=order_id)

# Bound loggers — like pino child loggers
request_logger = logger.bind(request_id=request_id, path=request.url.path)
request_logger.info("Request received")
request_logger.info("Authenticated", user_id=user.id)
```

python-json-logger swaps a `JsonFormatter` onto a standard `logging` handler and takes context through `extra={...}` on every call; it has no binding, so request context means a `LoggerAdapter` or passing fields by hand.

---

## Correlation IDs

When a request flows through your system, you need to connect all log entries for that request. A **correlation ID** (the generic term — distributed tracing systems call a closely-related concept a "trace ID") is a unique identifier generated at the entry point and attached to every log entry for that request.

```
Request arrives → Generate ID: req_abc123
→ {"request_id": "req_abc123", "message": "Request received"}
→ {"request_id": "req_abc123", "message": "Fetching user from DB"}
→ {"request_id": "req_abc123", "message": "Payment failed"}
```

Search for `request_id=req_abc123` and you get the complete story. Use the same field name, `request_id`, in every language, so one search covers every service (the rule is about the correlation field; other fields can follow each language's casing). An ID you mint yourself is not a W3C trace ID, so don't call it `trace_id`: switch to OTel's `trace_id` / `span_id` fields only once OTel generates them.

### Correlation ID, span, trace — the vocabulary

A *correlation ID* (or request ID) is the one identifier tying together everything done for a single request — search it, get the whole story. A *span* is one timed unit of work inside that request ("query the database", "call the payment API"), recording its duration and outcome. A *trace* is the whole tree of spans; every span shares one **trace ID** and records its parent, so the steps assemble into a tree showing where time went.

In a single service, a correlation ID on every log line is enough. Across services, the trace ID *is* the correlation ID — it rides a standard header (W3C `traceparent`) so the next service keeps the same ID and adds its own spans. [Monitoring](./monitoring.md) covers how to read a trace; here we only care that the ID lands on every log line.

### OpenTelemetry and your logger

Does OpenTelemetry replace `pino` / `structlog`? **No — it sits alongside them.** You keep logging with your existing logger; OTel's job is to *correlate* those logs with traces and give you one pipeline to ship telemetry. The payoff for logging is **trace-log correlation**: OTel exposes the current trace ID and span ID, and you stamp them on every log line, so clicking a slow span in your tracing UI jumps straight to that request's logs. Keep two mechanisms apart. **Correlation**, stamping `trace_id` and `span_id` on the lines your logger already writes, is the part you want, and it rests on the stable trace API: `@opentelemetry/instrumentation-pino` does it automatically under Node auto-instrumentation, and in Python `LoggingInstrumentor` does it for standard `logging`, or a few-line structlog processor reads `trace.get_current_span().get_span_context()`. A **log bridge** goes further and forwards the log records themselves into OTel's logs SDK. In Node it is on by default once the SDK starts: `instrumentation-pino` sends every record to the logs SDK, and `NodeSDK` exports them over OTLP unless `OTEL_LOGS_EXPORTER=none`. If stdout is your log path, set that (or the instrumentation's `disableLogSending: true`), or you pay for, and must govern, a second log store. The JS Logs API and SDK went stable in October 2026 (`@opentelemetry/api` 1.10, SDK 3.0); Python's Logs signal is still at *Development*, and there the bridge is opt-in. The default stays JSON to stdout, collected by your platform.

**Decide this early.** If you're adopting OTel, use its trace ID as your log correlation ID and let its SDKs own cross-service propagation (the `traceparent` header). If you're not using OTel yet, run your own correlation ID — the propagation pattern below works regardless of which ID you carry, and swaps cleanly to OTel's trace ID later. [Monitoring](./monitoring.md) covers the tracing side: spans, auto-instrumentation, and the collector/exporter pipeline.

### Automatic Propagation

You don't want to pass the correlation ID to every function manually. Use language-level context storage:

**TypeScript — AsyncLocalStorage:**

```typescript
// Node 20+, Express, pino 9
import { AsyncLocalStorage } from 'async_hooks';

// Create a context store. The store key is arbitrary —
// the point is that it travels with the request automatically.
const requestContext = new AsyncLocalStorage<{ requestId: string }>();

// Middleware: pick up an incoming ID or generate one, then store in context.
// Choose the incoming header based on your stack: OTel uses `traceparent`;
// a custom setup might use `x-request-id` or `x-correlation-id`. Pick one
// and be consistent across your services.
// The incoming value is client input that lands in every log line: accept it only
// if well-formed (or only from your own edge proxy), otherwise mint a fresh one.
const REQUEST_ID = /^[A-Za-z0-9._-]{1,64}$/;
app.use((req, res, next) => {
  const incoming = req.headers['x-request-id'] as string | undefined;
  const requestId = incoming && REQUEST_ID.test(incoming) ? incoming : crypto.randomUUID();
  res.setHeader('x-request-id', requestId);  // before next(), so 404s and error responses carry it too
  requestContext.run({ requestId }, () => next());
});

// Anywhere in your code — no need to pass the ID through every function
export function getRequestId(): string {
  return requestContext.getStore()?.requestId ?? 'no-request';
}

// Your logger can use it automatically
const logger = pino({
  mixin() {
    return { request_id: getRequestId() };
  },
});
```

`AsyncLocalStorage` stores context that automatically follows async operations — when an `await` resumes, it's still in the same context. This is how Node.js solves the "pass context everywhere" problem.

**Python — contextvars:**

```python
# structlog 25, FastAPI
import re
import uuid
import structlog

# Middleware: pick up a well-formed incoming header or generate one.
# As above, the header name is a project decision — align it with whatever
# your other services send, or adopt OTel and let it own propagation.
REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    incoming = request.headers.get("x-request-id", "")
    request_id = incoming if REQUEST_ID.fullmatch(incoming) else str(uuid.uuid4())
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response

# Anywhere — access without passing through function arguments
def get_request_id() -> str:
    return structlog.contextvars.get_contextvars().get("request_id", "no-request")

# Configure structlog to include it automatically
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # first: adds request_id to every entry
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,     # logger.exception() tracebacks as JSON
        structlog.processors.JSONRenderer(),      # local dev: swap the last two for structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(settings.log_level),  # "info" in production; the default emits debug too
)
```

`structlog.contextvars` is built on `contextvars`, Python's built-in equivalent of AsyncLocalStorage — context that follows async operations.

**Hand the ID back.** Both middlewares echo the ID as a response header, so a user's bug report or a frontend error event can carry the value you will search for. In FastAPI an unhandled exception skips the line after `call_next`, because Starlette renders that 500 outside your middleware, so a 500 carries no `x-request-id` header. The error body carries the ID instead: [Error Handling](./error-handling.md) puts it in the problem-details body, read through this same accessor and never minted again. For a frontend on another origin, also send `Access-Control-Expose-Headers: x-request-id` (the `cors` package's `exposedHeaders`, Starlette's `expose_headers`), because browsers hide non-safelisted response headers from cross-origin scripts.

### Cross-Service Propagation

When Service A calls Service B, include the correlation ID in a request header and have Service B's middleware pick it up. The specific header name is a project choice — use the same one consistently across services. If you go OTel, its SDKs inject and extract `traceparent` automatically; you don't write the propagation code yourself. HTTP is not the only hop: when work goes onto a queue or into a background job, carry the ID in the message headers or job metadata and bind it again in the consumer, or the trail stops at the enqueue.

---

## Log Levels

| Level | When to use | Example |
|-------|------------|---------|
| **debug** | Detailed info for development, too noisy for production | "Parsed request body: {fields}", "Cache miss for key X" |
| **info** | Normal operations worth recording | "User signed up", "Order created", "Deploy started" |
| **warn** | Something unexpected but handled — operational errors | "Rate limit hit for user", "Retry attempt 2/3", "Deprecated API called" |
| **error** | Something failed that shouldn't have — programming errors | "Unhandled exception", "Database schema mismatch", "Payment failed after retries exhausted" |
| **fatal** | System is going down | "Cannot connect to database, shutting down" |

### The Operational vs Programming Error Distinction

This connects directly to [Error Handling](./error-handling.md):

- **Operational errors** (expected failures) → log at **warn**. A user sending invalid data is normal. A rate limit being hit is normal. These aren't bugs.
- **Programming errors** (bugs) → log at **error**. An unhandled exception is a bug. A null reference is a bug. These need attention.

The split is a default, and the test behind it is whether this one occurrence needs a human to act. An operational failure that does, such as a payment that still failed after its retries ran out, goes at **error**; a single retry that then succeeded stays at warn.

If you log everything at ERROR, your error alerts fire for expected situations (user typos, rate limits) and you get **alert fatigue** — the team learns to ignore alerts, and then ignores real incidents too.

### Setting Log Level by Environment

Use your [Configuration](./configuration.md) setup:

```typescript
// In development: LOG_LEVEL=debug (see everything)
// In production: LOG_LEVEL=info (skip debug noise)
const logger = pino({ level: env.LOG_LEVEL });
```

---

## What to Log

### Do Log

- **Request start and end** — method, path, status code, duration
- **Business events** — user signed up, order placed, payment processed. Audit events (who changed a role, who exported what) are a separate stream with its own retention: see [Authentication & Authorization](./authentication-authorization.md#audit-logging).
- **Errors with context** — the error, plus what the system was trying to do, for whom, with what data
- **State transitions** — circuit breaker opened, feature flag changed, config reloaded
- **Retry attempts** — which attempt, what failed, how long until next retry

### Don't Log

- **Secrets** — API keys, passwords, tokens. Scrub these from log output. A common mistake: logging an entire config object that contains secrets.
- **Personal data** — Log the user ID, not the email, name or IP address, unless a decided purpose needs it. Under GDPR or CCPA, a log line holding personal data is personal data like any other. The rule covers every telemetry store, not just log lines: span attributes ([Monitoring](./monitoring.md)), error-tracker events (below) and analytics properties ([Product Analytics](./product-analytics.md)).
- **URLs with query strings** — Reset tokens, invite codes and email addresses ride in query strings. Log the path or route pattern, never `req.url` or `req.originalUrl`.
- **Request/response bodies at INFO level** — Full bodies create massive log volume. Use DEBUG level, and never in production unless actively investigating.
- **Health check requests** — Your load balancer hits `/health` every 5 seconds. That's noise, not signal. Filter these out.

**Retention.** Give every log store a retention period rather than keeping logs forever. Cost grows with it, and personal data may be kept only as long as its purpose needs (GDPR's storage-limitation principle). Thirty to ninety days is a common range for operational logs; audit logs follow their own, longer rule. Restrict who can read a log store as you would the database.

### Scrubbing Sensitive Data

```typescript
// BAD: logs the entire config including secrets
logger.info({ config: env }, 'Config loaded');

// GOOD: log only safe fields
logger.info({
  port: env.PORT,
  logLevel: env.LOG_LEVEL,
  nodeEnv: env.NODE_ENV,
}, 'Config loaded');
```

```python
# structlog 25
# BAD: logs request body which might contain passwords
logger.info("Login attempt", body=request.body)

# GOOD: log only what you need
logger.info("Login attempt", user_id=user.id)  # no password, no email
```

**Back the call sites with redaction in the logger,** which catches the field somebody forgot:

```typescript
// pino 9+
const logger = pino({
  redact: {
    paths: ['req.headers.authorization', 'req.headers.cookie', 'password', '*.password', '*.token'],
    censor: '[Redacted]',
  },
  serializers: { err: safeErrorSerializer },  // see "Error text is data" below
});
```

Paths name keys, and `*` matches exactly one level (`*.password` catches `user.password`, not `a.b.password`), so list each place a secret can appear. structlog has no built-in equivalent: add a processor before the renderer, a function of `(logger, method_name, event_dict)` that overwrites known keys and returns the dict.

**Error text is data.** Redaction sees keys, never the text inside a string, and a database error's text carries user data. Drizzle's `DrizzleQueryError` message reads `Failed query: <sql> params: <values>`, and pino's default `err` serializer copies the message and every enumerable property, `params` included. A Postgres unique violation's `detail` names the duplicate value. So log a safe serialisation of errors, never the raw object. Keep the class, the database error code and constraint name, messages you wrote yourself, and the fields your own error classes add, such as `service`; drop a driver's message, parameters and detail, and the stack's leading lines, which repeat the message. In pino, override the `err` serializer once, as above, so every `{ err }` goes through it. In SQLAlchemy, `create_engine(..., hide_parameters=True)` keeps bound values out of its error text, but the database's own detail still needs the same care.

**Pin it with a canary test.** Send a request that carries a known canary value in a password field, a token and a query string, capture the logger's output, and assert the canary appears nowhere. It catches what review misses: a new field, a changed serializer, an error that echoes its input.

---

## Request Logging Middleware

A common pattern — log every request automatically:

### TypeScript (Express + pino)

```typescript
// Express, pino 9. Register after the propagation middleware above.
app.use((req, res, next) => {
  const start = Date.now();
  const requestId = getRequestId();  // the ID the propagation middleware stored: don't mint a second one

  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info({
      request_id: requestId,
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      durationMs: duration,
    }, 'Request completed');
  });

  next();
});
```

In production, `pino-http` does this for you: it accepts your ID through `genReqId`, gives each request a child logger as `req.log`, and skips health checks through `autoLogging.ignore`. Its default request serializer logs the full URL, query string included, and every header, so pair it with the redaction above and a `req` serializer that keeps only the path.

### Python (FastAPI)

```python
# structlog 25, FastAPI. request_id arrives through merge_contextvars when this runs inside
# the propagation middleware: Starlette runs the last-registered middleware outermost,
# so register this one first.
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    status_code = 500  # if call_next raises: Starlette renders this 500 outside every middleware
    try:
        response = await call_next(request)  # re-raises the app's exception
        status_code = response.status_code
        return response
    finally:
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round((time.monotonic() - start) * 1000, 2),
        )
```

---

## Frontend Logging

Backend logging is well-understood: use a structured logger, write JSON, ship to an aggregator. Frontend logging is different — there's no persistent process, no log files, and `console.log` is the only built-in tool.

**The problem with `console.log` in production:** It only exists in the user's browser DevTools. Once the tab closes, it's gone. If a rep hits an error at 9am and reports it at 2pm, the console output is lost. Fifty `console.error` calls scattered across your codebase are invisible to you — they're visible only to the user who probably isn't looking.

**What to do instead:**

1. **Error-path events go to your error tracking service** (Sentry, Datadog, etc.), not `console.error`. Use global error handlers — React error boundaries, QueryCache/MutationCache `onError` hooks, `window.onerror` — so you don't need to wire up every catch block manually.

2. **Debug logging goes behind a flag.** If you need `console.log` for development, gate it: `if (import.meta.env.DEV) console.log(...)`. Better yet, remove it before committing. Production bundles shouldn't contain debug logging.

3. **Product-level events go to your analytics service** (see [Product Analytics](./product-analytics.md)), not console. "User viewed dashboard" is analytics, not a log.

4. **Catch blocks should not swallow errors.** The pattern `catch (err) { console.error(err); return []; }` is the most common frontend logging anti-pattern. The error is "logged" to a place nobody sees, the component receives empty data as if nothing went wrong, and the user gets a silent partial failure. Instead, let the error propagate to your data-fetching layer's error state (React Query's `error` property, SWR's error return) so the UI can show an error state and the global error handler can report to Sentry.

**Rule of thumb:** If it helps you debug during development, it's a `console.log` that should be removed before merge. If it reports a failure in production, it should go to an error-tracking service — the recommendation for any app with real users. If it measures user behaviour, it should go to analytics. For a small internal tool without error tracking, the minimum bar still holds: don't swallow errors — surface them in the UI's error state, where both the user and you can see them. What never works is `console.log` as the *reporting* mechanism, because the user's browser console is invisible to you.

### What an error-tracking service captures

`console.error` gives you a string in one person's browser. An error-tracking SDK (Sentry is the common default; Datadog RUM is equivalent) captures what you actually need to debug a failure you'll never see live:

- **Unhandled errors and promise rejections**, caught automatically via `window.onerror` / `unhandledrejection` — no per-`catch` wiring.
- **Source-mapped stack traces.** Production JS is minified, so a raw stack reads `a.b is not a function at main.abc.js:1:4567`. You upload **source maps** at build time and the service un-minifies the trace back to real file, line, and function. Upload them to the service but don't ship them publicly — they expose your source.
- **Breadcrumbs** — the trail of clicks, navigations, and network calls leading up to the error.
- **User and release context** — which user (an ID, not raw PII) and which deployed version hit it.
- **Web Vitals** (LCP / CLS / INP) and optional **session replay** — client-perceived signals backend logs can't see.

**Privacy:** capture of personal data is opt-in — attach a user ID, not email or IP, and use a scrub hook (Sentry's `beforeSend`) to strip tokens or request bodies before the event leaves the browser. The client-side version of the secrets-scrubbing rule above.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| `console.log()` / `print()` in a deployed app | Use a structured logger (pino, structlog) | Unstructured text can't be searched, filtered, or aggregated (a CLI's `print` output is its interface — different thing) |
| Log strings: `logger.info("User " + userId + " signed up")` | Log structured: `logger.info({userId}, "User signed up")` | String concatenation loses structure — can't filter by userId |
| Log everything at ERROR level | Use warn for operational errors, error for bugs and for failures a human must act on | Alert fatigue — team ignores alerts, misses real incidents |
| Log secrets, passwords, tokens | Scrub at the call site and redact in the logger; serialise errors safely | Logs are stored, forwarded, and often accessible to many people, and a driver's error text carries the query's values |
| Log full request/response bodies at INFO | Log at DEBUG, or log only specific fields | Massive log volume, potential PII exposure |
| Pass the request ID through every function argument | Use AsyncLocalStorage / contextvars | Context propagation should be automatic, not manual plumbing |
| Log health check requests | Filter them out in middleware | Noise — every 5 seconds from the load balancer |

---

## Deciding for Your Project

1. **Which correlation header, and do you echo it?** One name for every service and queue hop (`x-request-id`, or `traceparent` once OTel owns propagation), validated on the way in and echoed on every response.
2. **What fields on every log entry?** At minimum: timestamp, level, message, service name, request ID (`request_id`), and the tenant ID in a multi-tenant app. Decide which names every language shares: at least `request_id`, plus any field you search across services.
3. **Where do logs go, and for how long?** In development: console (pretty-printed). In production: JSON to stdout, collected by your platform (Docker, Kubernetes, CloudWatch, etc.), with a retention period set on the store.
4. **What log level in production?** Typically `info`. Switch to `debug` temporarily when investigating issues.

---

## Related Topics

- **Error logging** — see [Error Handling](./error-handling.md) for the operational vs programming error distinction that determines log level, and the problem-details body that carries the request ID
- **Metrics and alerting** — see [Monitoring](./monitoring.md) for the aggregate view that logs can't provide
- **Distributed tracing** — see [Monitoring](./monitoring.md) for how correlation IDs evolve into full distributed traces, and the Collector that can scrub span attributes centrally
- **Audit logs** — see [Authentication & Authorization](./authentication-authorization.md#audit-logging) for the separate, long-retention stream that authorization events need
- **Log-based secrets exposure** — see [Security](./security.md) for why scrubbing secrets from logs matters
- **Log level configuration** — see [Configuration](./configuration.md) for making log level configurable per environment
- **Frontend failure states** — see [Frontend Development](./frontend-development.md) for treating a failed request as a failure, not an empty result, the UI side of the swallowed-catch rule
- **Behaviour events** — see [Product Analytics](./product-analytics.md) for the events that belong in analytics rather than logs, and the consent rules for them
