# Error Handling Standards

**Status:** Draft

## Core Principle

Error handling strategy depends on context. This document provides the approaches — the agent and user select what fits the situation.

---

## Related Topics

- **Retries, timeouts, circuit breakers**: See [Reliability Standards](./reliability.md) — error categorisation (this file) determines what's retryable; reliability patterns handle the retry mechanics
- **Structured logging with trace IDs**: See [Logging Standards](./logging.md) — production error handling requires structured logging for debugging
- **Error leaking to clients**: See `dev-standards-pitfalls` skill — "Error Leaking" anti-pattern

---

## Error Handling Approaches

### Fail Fast

**Mantra:** Crash immediately when something's wrong. Don't continue with bad state.

**When to use:**
- Programming bugs (null reference, assertion failures)
- Invariants that should never be violated
- Unrecoverable situations

**Example:**
```python
def process_order(order):
    if order.total < 0:
        raise ValueError("Order total cannot be negative")
```

---

### Let It Crash

**Mantra:** Don't handle every error. Let the process crash and restart fresh.

**When to use:**
- Systems with supervisors (Kubernetes, process managers)
- When restart returns to known-good state
- Errors that are genuinely unrecoverable

**Requires:** External supervision to restart the process.

---

### Errors as Values

**Mantra:** Errors are data. Return them explicitly, handle them explicitly.

**When to use:**
- Expected failures (file not found, validation errors)
- When callers need to make decisions based on error type
- Languages that support this well (Go, Rust, or explicit Result types)

**Example:**
```python
def get_user(id) -> tuple[User | None, Error | None]:
    user = db.find(id)
    if not user:
        return None, NotFoundError(f"User {id}")
    return user, None
```

---

### Graceful Degradation

**Mantra:** When something fails, provide reduced functionality rather than failing entirely.

**When to use:**
- Non-critical features
- User-facing systems
- When partial function is better than total failure

**Example:** Image service down → show placeholder image.

---

### Retry with Backoff

**Mantra:** Transient failures (network, rate limits) often resolve on retry.

**When to use:**
- External API calls
- Network operations
- Rate-limited services
- Data pipelines with external dependencies

**Pattern:**
```
Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 2s
Attempt 4: wait 4s
(give up after N attempts)
```

Add jitter (random offset) to prevent thundering herd.

---

## Error Categories

| Category | Example | Typical Approach |
|----------|---------|------------------|
| **Programming bug** | Null reference, assertion | Fail fast |
| **Invalid user input** | Bad email format | Return error, inform user |
| **Not found** | User ID doesn't exist | Return error (expected case) |
| **External service failure** | API timeout | Retry with backoff |
| **Rate limited** | 429 response | Retry with backoff |
| **Resource exhausted** | Disk full, OOM | Fail fast |
| **Business rule violation** | Insufficient balance | Return error |
| **Transient failure** | Network blip | Retry |
| **Permanent failure** | Invalid API key | Fail fast, alert |

---

## Error Information

What an error should contain:

| Field | Purpose | Example |
|-------|---------|---------|
| **Type/Code** | Machine-readable classification | `ValidationError`, `E_NOT_FOUND` |
| **Message** | Developer-readable explanation | "User 123 not found in database" |
| **User message** | Safe to display to end users | "User not found" |
| **Context** | What was being attempted | `{"user_id": 123, "operation": "lookup"}` |
| **Timestamp** | When it occurred | ISO 8601 |
| **Trace ID** | Correlation across services | UUID |

---

## Tier Requirements

### Exploratory

**Minimal error handling.**

- Let errors crash (fail fast)
- Console output for debugging
- No retry logic required
- No user-friendly messages required

### Internal

**Basic error handling.**

- Catch and log errors with context
- Distinguish expected vs unexpected errors
- Retry logic for external calls (3 attempts, simple backoff)
- Graceful messages for known failure modes

### Production

**Comprehensive error handling.**

- All errors categorized and handled appropriately
- Retry with exponential backoff + jitter for external services
- User-friendly messages (no stack traces, no internal details)
- Structured error logging with trace IDs
- Dead letter queues or fallback paths for pipeline failures
- Alerting on unexpected error rates

---

## Data Pipeline Considerations

For pipelines with external APIs and AI transformations:

| Scenario | Approach |
|----------|----------|
| API rate limit (429) | Retry with backoff, respect Retry-After header |
| API timeout | Retry 2-3 times, then fail the item |
| API auth failure | Fail fast, alert (won't resolve on retry) |
| Malformed response | Log, fail the item, continue pipeline |
| AI model error | Retry once, then fail the item with context |
| Batch partially fails | Continue with successful items, report failures |

**Key pattern:** Fail individual items, not the whole pipeline. Collect failures for review.

---

## Anti-Patterns

| Don't | Why |
|-------|-----|
| Catch and ignore (`except: pass`) | Hides bugs, causes silent corruption |
| Log and re-raise without adding context | Duplicate logs, no new information |
| Expose stack traces to users | Security risk, poor UX |
| Retry infinitely | Wastes resources, never resolves permanent failures |
| Treat all errors the same | Different errors need different handling |

---

## Open Questions

- Specific retry configurations per tier?
- Alerting thresholds?
