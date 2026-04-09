# Reliability Standards

**Status:** Draft (concepts overview — specifics determined during brainstorming)

## Core Principle

Design for failure. External calls will fail, timeouts will happen, APIs will be down. Decide in advance what happens when they do.

---

## Related Topics

- **Error categorisation**: See [Error Handling Standards](./error-handling.md) — which errors are retryable vs. fatal determines when reliability patterns (retries, circuit breakers) apply
- **Idempotency and data safety**: See [Data Integrity Standards](./data-integrity.md) — idempotency protects data integrity during retries

---

## Context Matters

The right reliability approach depends on your data flow:

| Pattern | Example | On Failure |
|---------|---------|------------|
| **Independent items** | Processing 1000 documents | Log failure, continue to next |
| **Dependent chain** | Step B needs Step A's output | Fail fast, don't proceed |
| **Idempotent operations** | Updating a record | Safe to retry |
| **Non-idempotent operations** | Sending an email, charging a card | Dangerous to retry blindly |

**These must be determined per-project during brainstorming.**

---

## Concepts Reference

### Retries

Re-attempt failed operations. Use exponential backoff to avoid hammering.

```
Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 2s
Attempt 4: wait 4s
(give up)
```

Add **jitter** (random offset) to prevent thundering herd when many clients retry simultaneously.

**Discuss:** How many retries? What backoff multiplier? Which errors are retryable?

---

### Timeouts

Don't wait forever. Set limits on external calls.

| Timeout Type | Purpose |
|--------------|---------|
| **Connect timeout** | How long to establish connection |
| **Read timeout** | How long to wait for response |
| **Total timeout** | Overall operation limit |

**Discuss:** What timeouts are appropriate for each external service?

---

### Circuit Breakers

Stop calling a failing service temporarily. Prevents wasting resources on a dead API.

```
CLOSED (normal) → failures exceed threshold → OPEN (reject calls)
    ↑                                              ↓
    └─── success ← HALF-OPEN (test with one call) ←┘
                        after cooldown period
```

**Discuss:** Is this needed? What failure threshold triggers opening?

---

### Fallbacks

What to return when the primary path fails completely.

| Strategy | Example |
|----------|---------|
| **Default value** | Return cached data, empty result |
| **Degraded response** | Return partial data |
| **Error response** | Return clear error to caller |
| **Skip** | Log and continue (for independent items) |

**Discuss:** What's acceptable when this operation fails?

---

### Idempotency

Ensure retrying an operation doesn't cause duplicate effects.

| Operation | Naturally Idempotent? |
|-----------|----------------------|
| Read data | Yes |
| Update to fixed value | Yes |
| Insert new record | No (may duplicate) |
| Increment counter | No |
| Send email | No |
| Charge payment | No |

**Mitigation:** Use idempotency keys, check-before-write, upserts.

**Discuss:** Which operations need idempotency protection?

---

### Rate Limiting

Respect external API limits. Back off when throttled.

**Discuss:** What are the rate limits? How to handle 429 responses?

---

### Dead Letter Handling

What happens to items that fail permanently (after all retries exhausted)?

| Approach | Use When |
|----------|----------|
| **Log and continue** | Low-value items, can be manually reviewed |
| **Dead letter queue** | Need to reprocess later |
| **Alert and halt** | Critical items that can't be skipped |

**Discuss:** Where do permanently failed items go? Who reviews them?

---

### Checkpointing

For long-running batch jobs, save progress so crashes don't restart from zero.

**Discuss:** How often to checkpoint? Where to store progress?

---

## Tier Requirements

### Exploratory

- Basic try/catch
- Log errors
- No retry logic required

### Internal

- Retry with backoff for external calls
- Timeouts on all external calls
- Log failed items for review

### Production

- All Internal requirements
- Idempotency for non-safe operations
- Dead letter handling
- Checkpointing for long batches
- Consider circuit breakers for critical dependencies

---

## Expand During Brainstorming

For each project, determine:

1. Which operations are independent vs dependent?
2. Which operations are idempotent vs non-idempotent?
3. What retry counts and backoff make sense?
4. What happens to permanently failed items?
5. Is checkpointing needed for batch size/duration?
6. Are circuit breakers warranted?
