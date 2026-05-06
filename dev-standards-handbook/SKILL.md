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
| `topics/authentication-authorization.md` | OIDC, JWT, tokens, RBAC/ABAC, multi-tenant isolation, RLS, common vulnerabilities |
| `topics/configuration.md` | Env var validation, `.env`, multi-layer config, serverless config |
| `topics/data-integrity.md` | Zod/Pydantic, three-layer integrity model, transactions, validation boundaries |
| `topics/deployment.md` | Release patterns, lockfiles, concurrency, CI/CD |
| `topics/error-handling.md` | Error hierarchies, global handlers, RFC 9457, error chaining |
| `topics/logging.md` | Structured logging, correlation IDs, frontend logging |
| `topics/monitoring.md` | Metric types, RED/USE, SLOs, distributed tracing, OTel |
| `topics/product-analytics.md` | Event tracking, identity, groups, privacy |
| `topics/resilience.md` | Retries, circuit breakers, timeouts, idempotency, graceful shutdown, health checks |
| `topics/schema-evolution.md` | Migrations, expand-and-contract, backfills |
| `topics/security.md` | Injection, XSS, CSRF, CORS, headers, secrets, rate limiting |
| `topics/testing.md` | Test pyramid, contract tests, test DBs, mocking, factories |

Read the topic the user points you to, or the one that matches the concern at hand. Follow the user's guidance for what to do with it.
