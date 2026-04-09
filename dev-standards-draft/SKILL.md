---
name: dev-standards-draft
description: DRAFT — Comprehensive production engineering standards covering data safety, error handling, resilience, security, observability, API design, deployment, concurrency, and testing. Teaches concepts from the ground up with TypeScript and Python examples. Use during project planning (design-time integration), design/code review (audit mode), or mid-sprint (implementation reference).
---

# Production Engineering Standards

An engineering handbook containing production engineering knowledge — concepts explained from the ground up, tradeoffs, code examples in TypeScript and Python, recommendations for common project types, and anti-patterns.

This skill is reference material that the agent internalises. It is not a checklist to be applied mechanically — it is knowledge that shapes decisions as they are being made.

## Scope

**This skill covers:** Data validation, configuration, schema evolution, error handling, resilience, security, observability, API design, deployment, concurrency, and testing — the core concerns of building production-grade web services in TypeScript and Python.

**This skill does NOT cover:** Infrastructure provisioning (Terraform, CloudFormation), framework-specific deep dives (use framework skills for those), project management or sprint planning (use the project-planning and sprint-development skills), or domain-specific business logic.

## Three Modes of Operation

### Mode 1: Design-Time Integration

**When:** During project planning, while design decisions are being made.

**How:** This knowledge is active while discussing architecture, data models, API design, etc. Bring relevant production concerns into design discussions as they naturally arise — don't force a sequential walkthrough.

**Context mapping — which topics are most relevant for which discussions:**

| If the discussion is about... | Consider these topics |
|------------------------------|---------------------|
| Data models, schemas, storage | [Data Integrity](./topics/data-integrity.md), [Schema Evolution](./topics/schema-evolution.md), [Configuration](./topics/configuration.md) |
| API endpoints, request/response | [API Design](./topics/api-design.md), [Error Handling](./topics/error-handling.md), [Security](./topics/security.md) |
| External service calls, third-party APIs | [Resilience](./topics/resilience.md), [Error Handling](./topics/error-handling.md), [Logging](./topics/logging.md) |
| Authentication, user data, permissions | [Security](./topics/security.md), [Error Handling](./topics/error-handling.md), [Data Integrity](./topics/data-integrity.md) |
| Deployment, environments, CI/CD | [Deployment](./topics/deployment.md), [Configuration](./topics/configuration.md), [Resilience](./topics/resilience.md) |
| How to know if the system is working | [Monitoring](./topics/monitoring.md), [Logging](./topics/logging.md), [Testing](./topics/testing.md) |

**What it produces:** Project decision files in `.context/standards/` (see Project-Specific Output below). Files are created as decisions are made — not all at once.

### Mode 2: Review / Audit

**When:** After design or implementation, to check completeness. Can be applied to design docs OR existing code.

**How:** Walk through each topic's "Deciding for Your Project" section systematically. For each topic:

1. Read the topic's "Deciding for Your Project" questions
2. Check whether the project has addressed them (in design docs or code)
3. Record the outcome: **decided**, **deferred** (with reason), or **not applicable** (with reason)

**Progress tracking:** Compare the skill's topic list against the project's `.context/standards/` folder. Any skill topic without a corresponding project file hasn't been considered yet. Any project file missing a "Decided" section has open questions.

**What it produces:** Updated project decision files. A review summary noting gaps found and how they were resolved.

### Mode 3: Implementation Reference

**When:** Mid-build, when a specific question comes up.

**How:** Check conventions first, then go deeper if needed:

1. Read `conventions.md` — does it have a rule for this? If yes, follow it. Done.
2. If not covered, read the project's decision file in `.context/standards/` — what was decided?
3. If you need the full pattern or code example, read the skill topic file.

Example: "How do I handle errors in this orchestrator?" → `conventions.md` says "Throw typed errors (ValidationError, NotFoundError, ExternalServiceError), never plain Error. Wrap AWS SDK errors with `{ cause }`." That's enough to write the code. Only go to the skill topic if you need to understand the pattern from scratch.

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

## Project-Specific Output

When this skill is used in Mode 1 or Mode 2, it produces **project decision files** — a mirror of the skill's topic structure containing only the decisions for this specific project.

### Where they live

```
.context/standards/
├── data-integrity.md
├── configuration.md
├── schema-evolution.md
├── error-handling.md
├── resilience.md
├── security.md
├── logging.md
├── monitoring.md
├── api-design.md
├── deployment.md
└── testing.md
```

Each file corresponds 1:1 to a skill topic file. The skill topic has the full reference (patterns, examples, tradeoffs). The project file has only what was decided for this project.

**Not every topic needs a project file.** If a topic isn't relevant (e.g., distributed tracing for a single-service app), either omit the file entirely or include a one-liner explaining why it was skipped.

### Project decision file template

Each project decision file uses this structure:

```markdown
# [Topic Name] — Project Decisions

## Decided
- [Concrete decisions with chosen tools, patterns, and project-specific details]
- [Reference skill topic for implementation patterns where helpful]

## Deferred
- [Decisions intentionally postponed, with reason and revisit trigger]
- Example: "Distributed tracing — not needed for v1 (single service). Revisit if we add a second service."

## Not Applicable
- [Topics considered but determined not relevant, with brief reason]
- Example: "Circuit breakers — no external service dependencies."
```

### Example project decision file

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

### How the three layers work together

| Need | Read |
|------|------|
| "How do I handle errors when writing code right now?" | `.context/project/implementation/conventions.md` — terse, actionable rules |
| "What did we decide for this project and why?" | Project file: `.context/standards/error-handling.md` |
| "What IS an error hierarchy? Show me the full pattern." | Skill topic: `topics/error-handling.md` |

**Skill topics** are the handbook — teach concepts, show patterns, explain tradeoffs. Project-independent. Permanent.

**Standards decision files** record what was chosen — tools, approaches, and what was explicitly deferred or ruled out. They prevent re-litigation ("why didn't we use Joi?") and track coverage ("have we considered security?"). Semi-permanent.

**Conventions** are the quick-reference card for writing code — actionable rules that tell you what to do, not why. This is what an agent or developer checks while building. Evolves with the codebase.

The three layers have a clear flow: skill topics inform decisions (recorded in standards files), decisions get implemented in code, and the patterns that emerge get recorded as conventions. Each layer is progressively more specific and more actionable.

### When to write conventions

Conventions are written **during any sprint** when a pattern worth recording is established or changed. Common triggers:

- **First implementation of a cross-cutting concern** — error handling, logging, validation, config. The sprint writes the code and writes the convention entry describing the pattern.
- **A new pattern emerges** — a sprint introduces a new repository, a new type of orchestrator, or a new frontend pattern. If future code should follow the same approach, record it.
- **An existing pattern changes** — a convention is updated or replaced based on new learning. Update the entry, don't append a second one.
- **A decision from a standards file gets implemented** — the decision file says "use pino". The sprint implements pino. The convention says "use `logger.info({ context }, 'message')`, never string concatenation."

**What makes a good convention entry:** one section heading, 3-5 terse rules, no teaching, no justification. If you need to explain why, reference the standards decision file. If you need to show a full pattern, reference the skill topic.

**What does NOT belong in conventions:**
- Decisions without implementations ("we plan to use Zod" — that's a standards decision, not a convention)
- Architecture ("we use orchestrators" — that's architecture.md)
- Teaching ("Zod is a schema validation library" — that's the skill topic)
- One-off implementation details that don't generalize to future code
