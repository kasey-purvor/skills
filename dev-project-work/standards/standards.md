# Production Engineering Standards

An engineering handbook containing production engineering knowledge — concepts explained from the ground up, tradeoffs, code examples in TypeScript and Python, recommendations for common project types, and anti-patterns.

This is reference material that the agent internalises. It is not a checklist to be applied mechanically — it is knowledge that shapes decisions as they are being made.

For how this handbook fits into the broader system (three-layer model, when to consult, project decision file format), see the entry point skill's "Standards as Handbook" section.

## Scope

**Covers:** Data validation, configuration, schema evolution, error handling, resilience, security, observability, API design, deployment, concurrency, and testing — the core concerns of building production-grade web services in TypeScript and Python.

**Does NOT cover:** Infrastructure provisioning (Terraform, CloudFormation), framework-specific deep dives (use framework skills for those), project management or sprint workflows, or domain-specific business logic.

## Modes of Operation

### Mode 1: Design-Time Integration

**When:** During design, while decisions are being made.

**How:** Bring relevant production concerns into design discussions as they naturally arise — don't force a sequential walkthrough. Use the context mapping below to find relevant topics.

**What it produces:** Project decision files in `.context/standards/`, created as decisions are made — not all at once.

### Mode 2: Review / Audit

**When:** After design or implementation, to check completeness. Can be applied to design docs OR existing code.

**How:** Walk through each topic's "Deciding for Your Project" section systematically. For each topic:

1. Read the topic's "Deciding for Your Project" questions
2. Check whether the project has addressed them (in design docs or code)
3. Record the outcome: **decided**, **deferred** (with reason), or **not applicable** (with reason)

**Progress tracking:** Compare the topic list below against the project's `.context/standards/` folder. Any topic without a corresponding project file hasn't been considered yet. Any project file missing a "Decided" section has open questions.

**What it produces:** Updated project decision files. A review summary noting gaps found and how they were resolved.

### Mode 3: Implementation Reference

**When:** Mid-build, when a specific question comes up.

**How:** Check conventions first, then go deeper if needed:

1. Read `conventions.md` — does it have a rule for this? If yes, follow it. Done.
2. If not covered, read the project's decision file in `.context/standards/` — what was decided?
3. If you need the full pattern or code example, read the skill topic file.

## Context Mapping

Which topics are most relevant for which discussions:

| If the discussion is about... | Consider these topics |
|------------------------------|---------------------|
| Data models, schemas, storage | Data Integrity, Schema Evolution, Configuration |
| API endpoints, request/response | API Design, Error Handling, Security |
| External service calls, third-party APIs | Resilience, Error Handling, Logging |
| Authentication, user data, permissions | Security, Error Handling, Data Integrity |
| Deployment, environments, CI/CD | Deployment, Configuration, Resilience |
| How to know if the system is working | Monitoring, Logging, Testing |

## Topics

### Data & Validation
- **[Data Integrity](./topics/data-integrity.md)** — Schema validation (Zod, Pydantic), validation boundaries, the three-layer model, runtime vs compile-time safety, testing data pipelines
- **[Configuration](./topics/configuration.md)** — Treating app config as validated data, pydantic-settings, env schemas, .env files, startup fail-fast
- **[Schema Evolution](./topics/schema-evolution.md)** — Database migrations (Alembic, Prisma, Drizzle), expand-and-contract, zero-downtime changes, backfills

### Error Handling & Resilience
- **[Error Handling](./topics/error-handling.md)** — Custom error hierarchies, error chaining, global error handlers, RFC 9457 HTTP error responses, status code selection
- **[Resilience](./topics/resilience.md)** — Retries with backoff, circuit breakers, timeouts, idempotency keys, graceful shutdown, health checks (liveness/readiness/startup)

### Security
- **[Security](./topics/security.md)** — Injection attacks (SQL, NoSQL, command), XSS, CSRF, CORS, security headers, password hashing (bcrypt/argon2), dependency scanning, authentication vs authorization

### Observability
- **[Logging](./topics/logging.md)** — Structured logging (pino, structlog), correlation IDs, AsyncLocalStorage/contextvars, log levels, request logging middleware, secret scrubbing
- **[Monitoring](./topics/monitoring.md)** — Metric types (counter/gauge/histogram), RED and USE methods, percentiles, SLIs/SLOs/error budgets, alerting, distributed tracing, OpenTelemetry

### API & Contracts
- **[API Design](./topics/api-design.md)** — REST conventions, response shapes, pagination (offset/cursor), versioning strategies, type-safe contracts (tRPC, OpenAPI/FastAPI)

### Deployment & Operations
- **[Deployment](./topics/deployment.md)** — Release patterns (blue-green, canary, feature flags), rollback strategy, dependency management (lockfiles, npm ci, vulnerability scanning), concurrency (race conditions, locking, Promise.allSettled, connection pooling), CI/CD basics

### Cross-Cutting
- **[Testing](./topics/testing.md)** — Testing pyramid (unit/integration/E2E/contract), what to test per production concern, test infrastructure (real DBs not mocks, factories, organization), systems-level testing checklist

## Project Decision Files

Each project decision file in `.context/standards/` corresponds 1:1 to a skill topic file. The skill topic has the full reference (patterns, examples, tradeoffs). The project file has only what was decided for this project.

Not every topic needs a project file. If a topic isn't relevant, either omit the file entirely or include a one-liner explaining why it was skipped.

### Example

```markdown
# Error Handling — Project Decisions

## Decided
- Custom error hierarchy with AppError base class (see skill topic for pattern)
- ValidationError (400), NotFoundError (404), AuthorizationError (403), ExternalServiceError (502)
- RFC 9457 Problem Details format for all API error responses
- FastAPI @app.exception_handler for global error handling
- Operational errors logged at WARN, programming errors at ERROR

## Deferred
- Error tracking service (Sentry vs Datadog) — choose after v1 launch based on observability needs

## Not Applicable
- Next.js error.tsx — this project is API-only, no frontend
```

## When to Write Conventions

Conventions are written **during sprints** when a pattern worth recording is established or changed. Common triggers:

- **First implementation of a cross-cutting concern** — error handling, logging, validation, config
- **A new pattern emerges** — a new repository type, orchestrator, or frontend pattern that future code should follow
- **An existing pattern changes** — update the entry, don't append a second one
- **A decision from a standards file gets implemented** — the decision file says "use pino", the sprint implements pino, the convention says "use `logger.info({ context }, 'message')`, never string concatenation"

**What makes a good convention entry:** one section heading, 3-5 terse rules, no teaching, no justification. Reference the standards decision file for why. Reference the skill topic for the full pattern.

**What does NOT belong in conventions:**
- Decisions without implementations (that's a standards decision)
- Architecture (that's architecture.md)
- Teaching (that's the skill topic)
- One-off implementation details that don't generalize
