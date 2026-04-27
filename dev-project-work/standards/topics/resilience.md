# Resilience

## The Problem

Your app doesn't exist in isolation. It depends on external services — databases, payment APIs, email providers, cache servers, third-party APIs. Any of these can fail at any time: network blip, service overloaded, deployment in progress, DNS hiccup.

The question isn't "will external services fail?" — it's "what does your app do when they fail?"

Without resilience patterns:
- A slow database query makes every request hang
- A payment API outage crashes your checkout flow
- A deployment restarts drop in-flight requests
- A brief network blip causes permanent failures

Resilience is the discipline of designing your system to survive and recover from these failures gracefully.

---

## Retries with Exponential Backoff

When an external call fails, you retry — but not immediately and not forever.

**Naive retry (don't do this):**

```typescript
// BAD: hammers the service 3 times as fast as possible
for (let i = 0; i < 3; i++) {
  try { return await callService(); } catch {}
}
```

This makes a failing service worse — if it's struggling under load, you're tripling that load instantly.

**Exponential backoff with jitter:**

```
Attempt 1: fails
Wait 1 second
Attempt 2: fails
Wait 2 seconds
Attempt 3: fails
Wait 4 seconds
Attempt 4: fails
Give up, return error to caller
```

Each wait doubles. Add a small random jitter (±100ms) so that if 1000 clients all retry at the same time, they spread out instead of stampeding.

### What to Configure

Three parameters drive retry behaviour, regardless of which library you use:

- **`maxAttempts`** — typically 3 to 5. Beyond 5, the extra attempts rarely succeed and you're better off failing loudly so an alert fires.
- **Backoff schedule** — exponential base delay (1s → 2s → 4s → 8s) with added jitter. AWS's ["full jitter"](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) (`random(0, base × 2^attempt)`) spreads retries better than a fixed ±100ms window if many clients retry simultaneously.
- **Retry predicate** — which errors are retryable (see table below). Default should be *not* retrying; opt specific errors in. Many retry libraries default to retrying everything, which is a trap — validation errors, 401s, and 404s will never succeed on retry and just consume attempts.

### Libraries

In practice, use a library rather than hand-rolling the loop:

- **Python:** `tenacity` — the standard. Exponential backoff, jitter, conditional retries, async operations.
- **TypeScript:** `p-retry` or `cockatiel`. The AWS SDK (`@aws-sdk/middleware-retry`) and many HTTP clients have their own retry layer — check before adding a second one.
- **HTTP clients:** `axios-retry`, `got`'s built-in retry, `httpx` + tenacity.

### What's Retryable?

**Critical: only retry what's retryable.** Retrying a client error wastes time and resources.

| Response | Retryable? | Why |
|----------|-----------|-----|
| **400** Bad Request | No | The request is wrong — sending it again won't fix it |
| **401** Unauthorized | No | Authentication is invalid — retry won't help |
| **404** Not Found | No | Resource doesn't exist — retry won't create it |
| **409** Conflict | Maybe | If the conflict is transient (optimistic lock), retry might work |
| **429** Too Many Requests | Yes | Wait for the rate limit window to reset, then retry |
| **500** Internal Server Error | Maybe | Could be transient or permanent — retry with caution |
| **502** Bad Gateway | Yes | Upstream might recover |
| **503** Service Unavailable | Yes | Service might recover |
| **Connection timeout** | Yes | Network blip |
| **Connection refused** | Maybe | Service might be restarting |

---

## Circuit Breakers

Retries help with temporary blips. But what if a service is fully down? Retrying every request 3 times means you're tripling load on a dead service while making your users wait 7+ seconds per request.

A circuit breaker tracks failure rates and **stops trying** when failures exceed a threshold:

```
CLOSED (normal operation)
  → Requests pass through normally
  → Track success/failure count
  → If failures exceed threshold → switch to OPEN

OPEN (circuit tripped)
  → ALL requests fail immediately with a predefined error (no waiting)
  → After a timeout period (e.g., 30 seconds) → switch to HALF-OPEN

HALF-OPEN (testing recovery)
  → Allow ONE request through as a test
  → If it succeeds → switch to CLOSED (service recovered)
  → If it fails → switch back to OPEN (still down)
```

**Why this matters:**

Without a circuit breaker, 1000 users hitting your checkout page while the payment service is down means:
- 1000 requests × 3 retries × 10-second timeout = 30,000 seconds of wasted waiting
- Each user waits 30+ seconds before seeing an error
- The payment service gets hammered with 3000 requests when it's already struggling

With a circuit breaker:
- First few requests detect the failure, circuit opens
- Remaining 990+ requests fail immediately (< 1ms) with "Service temporarily unavailable"
- The payment service gets zero additional load while recovering
- Users see a fast, clean error message instead of a hanging page

**In practice**, you'd use a library. The concept is the important part — the implementation details vary by language and framework.

---

## Timeouts

Every external call needs a timeout. Without one, a single slow service can hang your entire application. If your database hangs and you have no timeout, every request that touches the database hangs too — and your connection pool fills up, and new requests can't get connections, and your entire service becomes unresponsive.

```typescript
// BAD: no timeout — if the service hangs, this request hangs forever
const result = await externalApi.fetch(data);

// GOOD: timeout after 10 seconds
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), 10_000);
try {
  const result = await fetch(url, { signal: controller.signal });
  return await result.json();
} finally {
  clearTimeout(timeout);
}
```

```python
import asyncio

# BAD: no timeout
result = await external_api.fetch(data)

# GOOD: timeout after 10 seconds
try:
    result = await asyncio.wait_for(external_api.fetch(data), timeout=10.0)
except asyncio.TimeoutError:
    raise ExternalServiceError("external_api")
```

### Timeout Values

There's no universal right answer, but these are reasonable starting points:

| Operation | Suggested timeout | Why |
|-----------|------------------|-----|
| Database query | 5-10 seconds | If a query takes longer, something is wrong (missing index, table lock) |
| External API call | 10-30 seconds | Depends on the service; payment APIs can be slow |
| Health check dependency check | 2-3 seconds | Health checks should be fast |
| Internal service-to-service call | 5-10 seconds | These should be fast if the network is healthy |

Set timeouts in your [Configuration](./configuration.md) so they can be tuned without code changes.

---

## Idempotency

If you retry a request, will it cause duplicate side effects? This is the idempotency problem.

**Scenario:** A user clicks "Pay." The request times out — but the payment actually went through on the server side. The client retries. Without idempotency, the user gets charged twice.

An **idempotent** operation produces the same result whether you execute it once or ten times.

### Naturally Idempotent Operations

- `GET /users/123` — reading data is always idempotent
- `PUT /users/123` with a full replacement body — writing the same state is idempotent
- `DELETE /users/123` — deleting something that's already deleted is fine

### Operations That Need Idempotency Keys

- `POST /payments` — creating a payment is NOT naturally idempotent
- `POST /orders` — creating an order is NOT naturally idempotent
- Any operation with side effects (sending emails, charging cards, incrementing counters)

### The Idempotency Key Pattern

The client sends a unique `Idempotency-Key` header with each request (e.g., `Idempotency-Key: order-abc-123-payment`). The server stores the key alongside the operation's result. On retry, the server returns the stored result instead of repeating the side effect.

**Key generation.** The client derives the key from (entity + operation): `order-{orderId}-payment`, `user-{userId}-signup-email`. Using the same derivation on every retry means the same logical operation always produces the same key.

**The implementation trap — check-then-act races.** The naive implementation (look up the key; if not found, do the work; then save) is subject to a race condition: two concurrent retries both observe the key as absent, both perform the side effect, and both save. That's exactly the duplicate charge the pattern is supposed to prevent.

**The correct implementation enforces uniqueness at the storage layer, not in application code.** Common shapes:

- **Insert-then-commit.** Write a row keyed on the idempotency key with a `UNIQUE` constraint *before* the side effect runs, inside a transaction that wraps the side effect. A retry attempting the same insert hits the conflict branch, which fetches the stored result and returns it.
- **Distributed lock on the key.** Acquire a lock (Redis `SET NX`, Postgres advisory lock) keyed on the idempotency key; release when the operation completes. Concurrent retries queue or fail fast.
- **Provider-native idempotency.** Stripe, Shopify, and most modern payment APIs accept an `Idempotency-Key` header on their side, so retries against them are safe without adding a second layer of keys in your app.

**Retention.** Store idempotency records long enough to cover realistic retry windows — typically 24 hours. Stripe keeps them for 24h; shorter windows leave a gap where a delayed retry creates a duplicate. Longer windows balloon storage without benefit.

**Edge cases to think about.** What does your server return if a retry arrives *while* the original is still in flight? What if the original succeeded but the stored-result write failed? What does "same result" mean if the original returned a non-deterministic payload (a generated ID)? These are the questions that make idempotency non-trivial — the pattern shape is simple; the edge cases are where production bugs live. Stripe's API reference is the most thorough public treatment of these cases.

---

## Graceful Shutdown

When you deploy new code, the platform sends your process a `SIGTERM` signal — "please stop." What happens next determines whether users see errors during deploys.

### Without Graceful Shutdown

1. Process dies immediately
2. In-flight HTTP requests get dropped — users see "connection reset" errors
3. Database connections left hanging — might cause connection pool exhaustion on the next startup
4. Queue messages being processed are lost — work needs to be redone

### With Graceful Shutdown — Ordering Matters

The correct sequence on SIGTERM:

1. **Stop accepting new connections.** Close the server socket so the load balancer sees the instance go unhealthy and routes new traffic away.
2. **Drain in-flight requests.** Wait for the requests already mid-flight to finish. Bound this with a hard timeout (typically 30s) so a hung request can't block shutdown forever.
3. **Close dependencies.** Only after all in-flight requests are done: disconnect the database pool, close queue consumers, flush buffered logs.
4. **Exit cleanly.** Exit code 0 signals to the process manager that shutdown was orderly.

**The common bug: closing dependencies before requests drain.** In Node.js, `server.close(callback)` is non-blocking — it returns immediately and fires the callback after draining. Calling `await db.disconnect()` right after `server.close(...)` disconnects the database while requests are still handling — those requests fail with connection errors. The fix is to promisify `server.close` (or `util.promisify(server.close.bind(server))()`) and `await` it before closing dependencies.

### Python (FastAPI with lifespan)

FastAPI's lifespan context manager handles the ordering for you — setup code runs before `yield`, teardown code after, and uvicorn coordinates signal handling and request draining around the lifespan. Put dependency open/close inside the lifespan context:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
```

Uvicorn will catch SIGTERM, stop accepting new connections, wait for in-flight requests, *then* run the post-yield shutdown code. If you run with a process manager (gunicorn + uvicorn workers, supervisord), tune its shutdown grace period to at least match the longest reasonable request duration.

### Node.js libraries worth using

Rather than hand-rolling the SIGTERM handler, libraries like [`stoppable`](https://github.com/hunterloftis/stoppable) or the built-in `server.closeAllConnections()` + `server.closeIdleConnections()` (Node 18.2+) handle the tricky parts (keep-alive sockets that would otherwise extend drain time indefinitely).

### Why This Matters in Practice

Every deployment triggers this code. If you deploy 5 times a day, that's 5 graceful shutdowns per day. Without graceful shutdown, some percentage of users see errors during every deploy. Multiply that over weeks and it adds up to noticeable unreliability.

---

## Health Checks

A health check is an HTTP endpoint that tells the platform "I'm alive and ready to serve traffic." There are three types:

### Liveness Probe — "Is the process alive?"

If this fails, the platform **restarts your container**. Should be lightweight — just return 200. Don't check dependencies here (if the DB is down, restarting your app won't fix the DB).

```typescript
app.get('/health/live', (req, res) => {
  res.json({ status: 'ok' });
});
```

```python
@app.get("/health/live")
async def liveness():
    return {"status": "ok"}
```

### Readiness Probe — "Can you handle requests right now?"

If this fails, traffic is **routed away from you** (but the process keeps running). Should check dependencies — can you reach the database? Is the cache connected?

```typescript
app.get('/health/ready', async (req, res) => {
  try {
    await db.query('SELECT 1');   // DB reachable?
    await cache.ping();            // Cache reachable?
    res.json({ status: 'ready' });
  } catch (err) {
    res.status(503).json({
      status: 'not ready',
      reason: err.message,
    });
  }
});
```

```python
@app.get("/health/ready")
async def readiness():
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": str(e)},
        )
```

### Startup Probe — "Have you finished initializing?"

Gives slow-starting apps time to boot without being killed. Only runs during startup, then liveness takes over. Useful when your app needs to load a large model, warm a cache, or run migrations before it's ready.

### Why the Liveness/Readiness Split Matters

A process can be "running" (liveness = ok) but unable to serve requests (readiness = not ok) because the database connection died. Without the split:
- Platform sees "liveness failed" and restarts your container
- This doesn't help because the DB is the problem, not your process
- Container restarts, DB is still down, restart loop

With the split:
- Liveness = ok (process is fine)
- Readiness = not ok (DB connection lost)
- Platform routes traffic to other healthy instances
- Your instance keeps running and recovers when the DB comes back

### Where Health Checks Are Configured

The endpoints are just HTTP routes in your app — framework-agnostic. Where they're consumed:

| Platform | Configuration |
|----------|--------------|
| **Kubernetes** | `livenessProbe`, `readinessProbe`, `startupProbe` in pod spec |
| **Docker Compose** | `healthcheck` directive |
| **AWS ECS** | Health check path + grace period in task definition |
| **Load balancers (ALB, nginx)** | Target group health check path |

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Retry client errors (400, 401, 404) | Only retry server errors and timeouts | Client errors won't succeed on retry |
| Retry immediately without backoff | Use exponential backoff with jitter | Immediate retries overwhelm struggling services |
| Retry indefinitely | Set a max attempt count | Infinite retries waste resources and delay error responses |
| No timeout on external calls | Set a timeout on every external call | One slow service can hang your entire application |
| Kill process immediately on SIGTERM | Graceful shutdown: stop accepting, drain, close, exit | Immediate kill drops in-flight requests |
| Check dependencies in liveness probe | Only check dependencies in readiness probe | Failed dependency doesn't mean your process needs a restart |
| Skip idempotency on payment/creation endpoints | Use idempotency keys for non-idempotent operations | Retries without idempotency cause duplicate charges, orders, emails |
| Hardcode timeout values | Put timeouts in configuration | Different environments and services need different timeouts |

---

## Deciding for Your Project

When starting a new project, determine:

1. **What external services do you depend on?** Each one needs timeout + retry strategy.
2. **Which operations have side effects?** These need idempotency keys (payments, emails, order creation).
3. **What's your deployment model?** Containers need graceful shutdown + health checks. Serverless (Lambda, Vercel functions) handles this for you.
4. **Do you need circuit breakers?** Usually not for simple apps with 1-2 external dependencies. More valuable when you have many external services or high traffic.
5. **What are your timeout budgets?** If your API has a 30-second SLO, and it calls 3 services sequentially, each service gets at most ~8 seconds.

---

## Related Topics

- **Error classification** — see [Error Handling](./error-handling.md) for how to classify failures using custom error hierarchies
- **Logging failures** — see [Logging](./logging.md) for how to log retries, circuit breaker state changes, and timeout events with proper context
- **Monitoring resilience** — see [Monitoring](./monitoring.md) for metrics to track: retry rates, circuit breaker trips, timeout frequency, error budgets
- **Config for timeouts** — see [Configuration](./configuration.md) for making timeouts and retry counts configurable
- **Deployment patterns** — see [Deployment](./deployment.md) for how graceful shutdown fits into deploy pipelines
