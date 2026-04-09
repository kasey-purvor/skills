# Standards Matrix

Quick reference for what production requires and what can be relaxed for exploratory or internal-only work.

**Production is the default.** If the system is intended for production, the Production column is the baseline — not a stretch goal. The Exploratory and Internal columns show what you can consciously skip when the code genuinely might not survive, and the cost of each relaxation if it does.

| Topic | Exploratory (might be thrown away) | Internal (team tools, no external users) | Production (the default) |
|-------|-----------|----------|------------|
| Testing & Testability | TDD, pure functions for core logic | TDD + explicit edge cases, dependency injection for external services | TDD + edge cases + templates + spec-grounded testing + mutation testing, no singletons in business logic |
| Error Handling | Fail fast, console output | Catch + log, basic retry | Categorized handling, retry + backoff, user-friendly messages |
| Logging | Console summary + progress | Console + file logging, configurable verbosity | Structured (JSON), full context, correlation IDs, queryable |
| Security | .env secrets, basic validation | + parameterized queries, encryption at rest | + secret manager, auth/authz, audit logging, dependency scanning |
| Configuration | .env + env access with defaults | + config file, typed models (Pydantic / Zod), cached singleton | + startup validation, clear error messages |
| Monitoring | Console output, manual checks | Persistent logs, post-run summaries | Metrics, alerting, dashboards, log aggregation |
| Reliability | Basic try/catch, log errors | Retry + backoff, timeouts, log failures | + idempotency, dead letter handling, checkpointing |
| Data Integrity | Basic type hints, ad-hoc validation | Typed schemas for external data, type hints, DB constraints on key columns | Runtime schemas for all entities, boundary contracts, runtime validation at every entry/exit, strict typing, schema verification against real data |
| Documentation | README with setup instructions | + Docstrings, architecture diagram | + API docs, runbooks, decision records |

**How to use this matrix:** If you're consciously building below production standard, scan the relevant column to understand what you're skipping. Track every relaxation (e.g., in a backlog) so it's visible when the system matures. If the system was always intended for production, this matrix shouldn't be needed — build to the Production column from the start.
