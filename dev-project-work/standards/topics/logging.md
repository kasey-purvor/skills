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

Why pino? Fastest Node.js logger — outputs JSON natively with minimal overhead. Alternatives:
- **winston** — more features (transports, formatting), slower
- **bunyan** — older, similar to pino

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

Why structlog? Produces structured JSON, integrates with Python's standard logging, supports context binding. Alternatives:
- **python-json-logger** — lighter weight, wraps standard logging
- **loguru** — more features, less structured, popular for scripts

---

## Correlation IDs

When a request flows through your system, you need to connect all log entries for that request. A **correlation ID** (also called trace ID or request ID) is a unique identifier generated at the entry point and attached to every log entry for that request.

```
Request arrives → Generate ID: req_abc123
→ {"traceId": "req_abc123", "message": "Request received"}
→ {"traceId": "req_abc123", "message": "Fetching user from DB"}
→ {"traceId": "req_abc123", "message": "Payment failed"}
```

Search for `traceId=req_abc123` and you get the complete story.

### Automatic Propagation

You don't want to pass the trace ID to every function manually. Use language-level context storage:

**TypeScript — AsyncLocalStorage:**

```typescript
import { AsyncLocalStorage } from 'async_hooks';

// Create a context store
const requestContext = new AsyncLocalStorage<{ traceId: string }>();

// Middleware: generate ID and store in async-local context
app.use((req, res, next) => {
  const traceId = req.headers['x-trace-id'] as string || crypto.randomUUID();
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

# Middleware: generate ID and store in context
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
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

When Service A calls Service B, include the trace ID in the HTTP request header:

```typescript
// Service A — outgoing request
const response = await fetch('https://service-b/api/data', {
  headers: { 'x-trace-id': getTraceId() },
});

// Service B — incoming request (the middleware above reads x-trace-id)
```

This way, logs from both services share the same trace ID. Search for one ID and you see the full cross-service story. This concept is formalized in distributed tracing (see [Monitoring](./monitoring.md)).

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
