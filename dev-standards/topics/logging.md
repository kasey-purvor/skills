# Logging Standards

**Status:** Work in Progress

## Purpose

Logs answer questions you haven't thought of yet. When something fails, logs are your window into what happened. Good logging separates "what's happening now" (console) from "what happened" (persistent).

---

## Key Principles

- **Console output** is for real-time monitoring (summary stats, progress)
- **Persistent logs** are for post-mortem debugging (detailed records)
- **Verbosity is configurable** via runtime argument — verbose in dev, quieter in production
- These are discussion points — specifics depend on project and framework

---

## Log Levels

Four levels recommended (can vary by framework/project):

| Level | Purpose | Example |
|-------|---------|---------|
| **DEBUG** | Detailed diagnostic info (dev only) | "Processing item 47: payload={...}" |
| **INFO** | Normal operations worth noting | "Batch started: 1000 items" |
| **WARN** | Unexpected but handled | "Retry 2/3 for API call" |
| **ERROR** | Something failed | "Item 47 failed after 3 retries" |

Some frameworks add CRITICAL/FATAL for "system cannot continue." Adapt to your framework's conventions.

---

## Output Types

### Console Output (All Tiers)

Real-time monitoring while workflow runs:
- Summary statistics
- Progress indicators (bars, counts)
- Current stage/step
- Error counts

**What to show is task-specific** — discuss per project. Example elements:
- Items processed / total
- Current stage
- Errors encountered
- Elapsed time
- Estimated time remaining

### Persistent Logging

Detailed records for debugging:

| Tier | Persistent Logging |
|------|-------------------|
| **Exploratory** | Optional, console may suffice |
| **Internal** | File logging, configurable verbosity |
| **Production** | Structured (JSON), full context, queryable |

---

## Configurable Verbosity

Logging verbosity should be controllable via entry point argument:

```
--log-level DEBUG    # Everything (development)
--log-level INFO     # Normal operations
--log-level WARN     # Only warnings and errors
--log-level ERROR    # Only errors
```

**Typical usage:**
- Early development: DEBUG (see everything)
- Stable/production: INFO or WARN (reduce noise)
- Troubleshooting: Temporarily increase verbosity

---

## What to Log

| Do Log | Don't Log |
|--------|-----------|
| Operation start/end with context | Passwords, tokens, API keys |
| Error details with trace ID | Full credit card numbers |
| Processing times | High-volume success at DEBUG in production |
| Retry attempts | Personal data beyond what's needed |

---

## Structured Logging (Production)

For production, structured logs (JSON) enable querying:

```json
{
  "timestamp": "2026-02-04T10:30:00Z",
  "level": "ERROR",
  "message": "Item processing failed",
  "item_id": 47,
  "batch_id": "abc123",
  "error": "API timeout",
  "retry_count": 3,
  "trace_id": "xyz789"
}
```

Plain text is fine for prototype/internal if not using log aggregation.

---

## Recommended Tools

**Python:**
- `logging` (standard library) — reliable, configurable
- `structlog` — structured logging made easy
- `loguru` — simpler API, good defaults
- `rich` — beautiful console output, progress bars

**JavaScript:**
- `winston` — flexible, multiple transports
- `pino` — fast, JSON-native

**Output destinations:**
- Files (with rotation for long-running processes)
- Stdout (container-friendly)
- Database (if queryability needed)
- Log aggregators (ELK, Datadog, Loki) for production scale

---

## Discussion Points

When setting up logging for a project, discuss:
- What summary info is useful on console?
- What verbosity level for each environment?
- Structured vs plain text?
- Log retention and rotation needs?
- Need for trace IDs across operations?
