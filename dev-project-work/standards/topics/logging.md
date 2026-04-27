# Logging

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
  "email": "kasey@example.com",
  "traceId": "abc-456-def"
}
```

```json
{
  "timestamp": "2026-04-01T10:23:45.456Z",
  "level": "error",
  "message": "Payment failed",
  "service": "api",
  "userId": "user_123",
  "orderId": "order_789",
  "traceId": "abc-456-def",
  "error": "connection refused to stripe.com:443"
}
```

Now you can: search for `userId=user_123`, filter by `level=error`, correlate the signup and payment failure by `traceId`, build dashboards of error rates over time.

### TypeScript Logger Options

| | pino | Winston |
|--|------|---------|
| **Design** | JSON-first, minimal API | Flexible, multi-transport |
| **Performance** | Fastest Node.js logger (5-10x faster than Winston) | Acceptable, but slower — matters in Lambda where you pay per ms |
| **Structured output** | JSON by default, no configuration needed | Needs format configuration to produce JSON |
| **Child loggers** | Built-in — `logger.child({ handler: "name" })` adds fields to all entries | Possible but requires more setup |
| **Transports** (plugins for sending logs to different destinations) | Fewer — stdout is the expected output, your platform (CloudWatch, Datadog) collects from there | Many — file, database, cloud services, HTTP. Useful when you need to send logs to multiple places simultaneously |
| **Dev readability** | Needs `pino-pretty` companion package for human-readable local output | Configurable format per environment |
| **Dependency size** | ~150KB | ~1MB+ |
| **Best for** | APIs and serverless functions sending structured JSON to CloudWatch, Datadog, etc. | Complex applications that route logs to multiple destinations, or teams already using Winston |

**Recommended default: pino.** It does one thing well (structured JSON logging), it's fast, and the child logger API solves the "add context to every log call" problem cleanly. Winston is a reasonable choice if your team already uses it or you need its transport ecosystem.

### TypeScript — pino

```typescript
import pino from 'pino';

const logger = pino({
  level: env.LOG_LEVEL,  // from your config module — see Configuration topic
});

// Structured: pass context as an object, message as second argument
logger.info({ userId: user.id, email: user.email }, 'User signed up');
logger.error({ userId: user.id, orderId, err }, 'Payment failed');

// Child loggers — bind context that applies to all subsequent calls
const requestLogger = logger.child({ traceId, path: req.path });
requestLogger.info('Request received');  // traceId and path are included automatically
requestLogger.info({ userId }, 'Authenticated');  // traceId, path, AND userId
```

### TypeScript — Winston

```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: env.LOG_LEVEL,
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()   // must opt in to JSON — plain text is the default
  ),
  transports: [new winston.transports.Console()],
});

// Structured: pass context in a metadata object
logger.info('User signed up', { userId: user.id, email: user.email });
logger.error('Payment failed', { userId: user.id, orderId, error: err.message });

// Child loggers — Winston calls these "child" loggers too (added in v3.11)
const requestLogger = logger.child({ traceId, path: req.path });
requestLogger.info('Request received');
requestLogger.info('Authenticated', { userId });
```

Note the difference: pino outputs JSON with zero configuration. Winston requires `format.json()` — without it, you get plain text. Winston also has more setup (transports array, format pipeline) but that same flexibility lets you add file logging, HTTP transports, or custom formats later without changing call sites.

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
import structlog

logger = structlog.get_logger()

# Structured: pass context as keyword arguments
logger.info("User signed up", user_id=user.id, email=user.email)
logger.error("Payment failed", user_id=user.id, order_id=order_id, error=str(e))

# Bound loggers — like pino child loggers
request_logger = logger.bind(trace_id=trace_id, path=request.url.path)
request_logger.info("Request received")
request_logger.info("Authenticated", user_id=user.id)
```

### Python — python-json-logger

```python
import logging
from pythonjsonlogger import jsonlogger

# Configure the standard logger to output JSON
handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(message)s"
))
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Structured: pass context via the `extra` dict
logger.info("User signed up", extra={"user_id": user.id, "email": user.email})
logger.error("Payment failed", extra={"user_id": user.id, "order_id": order_id})

# No built-in context binding — you'd use logging.LoggerAdapter or pass fields manually
```

Note the difference: structlog's `.bind()` returns a new logger that carries context forward automatically. With python-json-logger, you pass `extra={}` on every call or set up a `LoggerAdapter` to hold context — more manual work for the same result.

---

## Correlation IDs

When a request flows through your system, you need to connect all log entries for that request. A **correlation ID** (the generic term — distributed tracing systems call a closely-related concept a "trace ID") is a unique identifier generated at the entry point and attached to every log entry for that request.

```
Request arrives → Generate ID: req_abc123
→ {"traceId": "req_abc123", "message": "Request received"}
→ {"traceId": "req_abc123", "message": "Fetching user from DB"}
→ {"traceId": "req_abc123", "message": "Payment failed"}
```

Search for `traceId=req_abc123` and you get the complete story.

### Relationship to distributed tracing

Before implementing correlation IDs from scratch, decide whether you're going to adopt OpenTelemetry (see [Monitoring](./monitoring.md)). If you are, **use OTel's trace ID as your log correlation ID** — OTel auto-instrumentation generates a trace ID per request and propagates it across services via the W3C `traceparent` header. Both `pino` and `structlog` can be wired to read the current OTel trace ID and include it in every log entry. That way, clicking a trace in Jaeger / Datadog / Grafana Tempo lands you on the matching logs for free.

If you're not using OTel (yet, or at all), run your own correlation ID — generate one per request, propagate it downstream, stamp it on every log line. The pattern below works regardless of which ID you're carrying, and swaps cleanly to OTel's trace ID later.

### Automatic Propagation

You don't want to pass the correlation ID to every function manually. Use language-level context storage:

**TypeScript — AsyncLocalStorage:**

```typescript
import { AsyncLocalStorage } from 'async_hooks';

// Create a context store. The key name (traceId) is arbitrary —
// the point is that it travels with the request automatically.
const requestContext = new AsyncLocalStorage<{ traceId: string }>();

// Middleware: pick up an incoming ID or generate one, then store in context.
// Choose the incoming header based on your stack: OTel uses `traceparent`;
// a custom setup might use `x-request-id` or `x-correlation-id`. Pick one
// and be consistent across your services.
app.use((req, res, next) => {
  const incoming = req.headers['x-request-id'] as string | undefined;
  const traceId = incoming ?? crypto.randomUUID();
  requestContext.run({ traceId }, () => next());
});

// Anywhere in your code — no need to pass traceId through every function
export function getTraceId(): string {
  return requestContext.getStore()?.traceId ?? 'no-trace';
}

// Your logger can use it automatically
const logger = pino({
  mixin() {
    return { traceId: getTraceId() };
  },
});
```

`AsyncLocalStorage` stores context that automatically follows async operations — when an `await` resumes, it's still in the same context. This is how Node.js solves the "pass context everywhere" problem.

**Python — contextvars:**

```python
import contextvars
import uuid

# Create a context variable
trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('trace_id', default='no-trace')

# Middleware: pick up an incoming header or generate one.
# As above, the header name is a project decision — align it with whatever
# your other services send, or adopt OTel and let it own propagation.
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    token = trace_id_var.set(trace_id)
    response = await call_next(request)
    trace_id_var.reset(token)
    return response

# Anywhere — access without passing through function arguments
def get_trace_id() -> str:
    return trace_id_var.get()

# Custom processor that adds trace_id to every log entry
def add_trace_id(logger, method_name, event_dict):
    event_dict["trace_id"] = trace_id_var.get()
    return event_dict

# Configure structlog to include it automatically
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        add_trace_id,
        structlog.dev.ConsoleRenderer(),  # use JSONRenderer in production
    ]
)
```

`contextvars` is Python's built-in equivalent of AsyncLocalStorage — context that follows async operations.

### Cross-Service Propagation

When Service A calls Service B, include the correlation ID in a request header and have Service B's middleware pick it up. The specific header name is a project choice — use the same one consistently across services. If you go OTel, its SDKs inject and extract `traceparent` automatically; you don't write the propagation code yourself.

---

## Log Levels

| Level | When to use | Example |
|-------|------------|---------|
| **debug** | Detailed info for development, too noisy for production | "Parsed request body: {fields}", "Cache miss for key X" |
| **info** | Normal operations worth recording | "User signed up", "Order created", "Deploy started" |
| **warn** | Something unexpected but handled — operational errors | "Rate limit hit for user", "Retry attempt 2/3", "Deprecated API called" |
| **error** | Something failed that shouldn't have — programming errors | "Unhandled exception", "Database schema mismatch" |
| **fatal** | System is going down | "Cannot connect to database, shutting down" |

### The Operational vs Programming Error Distinction

This connects directly to [Error Handling](./error-handling.md):

- **Operational errors** (expected failures) → log at **warn**. A user sending invalid data is normal. A rate limit being hit is normal. These aren't bugs.
- **Programming errors** (bugs) → log at **error**. An unhandled exception is a bug. A null reference is a bug. These need attention.

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
- **Business events** — user signed up, order placed, payment processed
- **Errors with context** — the error, plus what the system was trying to do, for whom, with what data
- **State transitions** — circuit breaker opened, feature flag changed, config reloaded
- **Retry attempts** — which attempt, what failed, how long until next retry

### Don't Log

- **Secrets** — API keys, passwords, tokens. Scrub these from log output. A common mistake: logging an entire config object that contains secrets.
- **Personal data carelessly** — Depending on jurisdiction (GDPR, CCPA), logging full email addresses or IP addresses may have legal implications. Log user IDs instead.
- **Request/response bodies at INFO level** — Full bodies create massive log volume. Use DEBUG level, and never in production unless actively investigating.
- **Health check requests** — Your load balancer hits `/health` every 5 seconds. That's noise, not signal. Filter these out.

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
# BAD: logs request body which might contain passwords
logger.info("Login attempt", body=request.body)

# GOOD: log only what you need
logger.info("Login attempt", email=body.email)  # no password
```

---

## Request Logging Middleware

A common pattern — log every request automatically:

### TypeScript (Express + pino)

```typescript
app.use((req, res, next) => {
  const start = Date.now();
  const traceId = crypto.randomUUID();

  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info({
      traceId,
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      durationMs: duration,
    }, 'Request completed');
  });

  next();
});
```

### Python (FastAPI)

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    duration = (time.monotonic() - start) * 1000

    logger.info(
        "Request completed",
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        duration_ms=round(duration, 2),
    )
    return response
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

**Rule of thumb:** If it helps you debug during development, it's a `console.log` that should be removed before merge. If it reports a failure in production, it should go to Sentry. If it measures user behaviour, it should go to analytics. There is almost no case where `console.log` in committed production code is the right choice.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| `console.log()` / `print()` in production code | Use a structured logger (pino, structlog) | Unstructured text can't be searched, filtered, or aggregated |
| Log strings: `logger.info("User " + userId + " signed up")` | Log structured: `logger.info({userId}, "User signed up")` | String concatenation loses structure — can't filter by userId |
| Log everything at ERROR level | Use warn for operational errors, error for bugs | Alert fatigue — team ignores alerts, misses real incidents |
| Log secrets, passwords, tokens | Scrub sensitive fields before logging | Logs are stored, forwarded, and often accessible to many people |
| Log full request/response bodies at INFO | Log at DEBUG, or log only specific fields | Massive log volume, potential PII exposure |
| Pass traceId through every function argument | Use AsyncLocalStorage / contextvars | Context propagation should be automatic, not manual plumbing |
| Log health check requests | Filter them out in middleware | Noise — every 5 seconds from the load balancer |

---

## Deciding for Your Project

1. **Which logger?** pino for TypeScript, structlog for Python — these are the recommended defaults.
2. **What fields on every log entry?** At minimum: timestamp, level, message, service name, trace ID.
3. **Where do logs go?** In development: console (pretty-printed). In production: JSON to stdout, collected by your platform (Docker, Kubernetes, CloudWatch, etc.).
4. **What log level in production?** Typically `info`. Switch to `debug` temporarily when investigating issues.
5. **Do you need cross-service correlation?** If you have multiple services, propagate trace IDs in HTTP headers.

---

## Related Topics

- **Error logging** — see [Error Handling](./error-handling.md) for the operational vs programming error distinction that determines log level
- **Metrics and alerting** — see [Monitoring](./monitoring.md) for the aggregate view that logs can't provide
- **Distributed tracing** — see [Monitoring](./monitoring.md) for how correlation IDs evolve into full distributed traces
- **Log-based secrets exposure** — see [Security](./security.md) for why scrubbing secrets from logs matters
- **Log level configuration** — see [Configuration](./configuration.md) for making log level configurable per environment
