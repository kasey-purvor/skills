---
name: dev-standards-handbook
description: Production Engineering Handbook
---

# Production Engineering Handbook

Reference material for production engineering patterns. The actual content lives in `topics/` alongside this file — one chapter-style markdown per concern, written to be project-independent.

## Topics folder

Each topic covers one production concern with enough depth to ground a design conversation or code review. Topics describe patterns, tradeoffs, and common mistakes — they are not mandates.

| Topic | Covers |
|---|---|
| `topics/api-design.md` | REST conventions, response shapes, pagination, versioning, type-safe contracts |
| `topics/authentication-authorization.md` | OIDC, JWT, tokens, RBAC/ABAC, common vulnerabilities |
| `topics/configuration.md` | Env var validation, `.env`, multi-layer config, serverless config |
| `topics/data-integrity.md` | Zod/Pydantic, three-layer integrity model, transactions, validation boundaries |
| `topics/deployment.md` | Release patterns, lockfiles, concurrency, CI/CD |
| `topics/error-handling.md` | Error hierarchies, global handlers, RFC 9457, error chaining |
| `topics/logging.md` | Structured logging, correlation IDs, frontend logging |
| `topics/monitoring.md` | Metric types, RED/USE, SLOs, distributed tracing, OTel |
| `topics/multi-tenant-isolation.md` | Isolation strategies, scoped data layers, the RLS database backstop, elevated cross-tenant access |
| `topics/product-analytics.md` | Event tracking, identity, groups, privacy |
| `topics/resilience.md` | Retries, circuit breakers, timeouts, idempotency, graceful shutdown, health checks |
| `topics/schema-evolution.md` | Migrations, expand-and-contract, backfills |
| `topics/security.md` | Injection, XSS, CSRF, CORS, headers, secrets, rate limiting |
| `topics/testing.md` | Test pyramid, contract tests, test DBs, mocking, factories |

Read the topic the user points you to, or the one that matches the concern at hand. Follow the user's guidance for what to do with it.

---

## Cross-cutting scenarios

Some work spans several topics at once and the synthesis lives in none of them. If the task matches a scenario below, the integrating idea is here; the **recruits** are the topics to open.

- **Multi-tenant isolation** — one system serving many customer orgs. Isolation is structural, not per-query vigilance: enforce the tenant filter in a scoped data layer *and* back it with the database engine, and take tenant identity only from the verified session. Full treatment in [multi-tenant-isolation.md](./topics/multi-tenant-isolation.md); recruits [security.md](./topics/security.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Request correlation / tracing** — reconstructing one request across logs and services. Mint a correlation id at the edge, thread it through every log line and outbound call, and surface it in error responses — that one id ties the trail together. Recruits [logging.md](./topics/logging.md), [error-handling.md](./topics/error-handling.md), [monitoring.md](./topics/monitoring.md).
- **Idempotent side-effects** — an external effect (payment, email, webhook) that may be retried. Guard it with an idempotency key and a stored result so a retry returns the original outcome, not a second effect — and the guard must hold under *concurrent* retries, not just sequential ones. Recruits [resilience.md](./topics/resilience.md), [testing.md](./topics/testing.md).
- **Server-projected capabilities** — the client needs to know which actions a user may take, to render or enable UI. The server is the authority: derive the permitted-action set from the same rules the endpoints enforce and project it into the response, so the client shows affordances without re-deriving authorization. One source, or the UI hint and the real check drift apart. Recruits [api-design.md](./topics/api-design.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Validation at trust boundaries** — data arriving from anywhere untrusted (API input, third-party responses, queue messages, files). Parse it through a schema at the boundary and trust the typed result inside; the boundary is the one place to establish the data is what you think it is. Recruits [data-integrity.md](./topics/data-integrity.md) (owner), [security.md](./topics/security.md).
