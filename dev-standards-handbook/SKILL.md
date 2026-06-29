---
name: dev-standards-handbook
description: >-
  Use when planning or making any non-trivial change to a codebase — a new project,
  feature, fix, refactor, live change, integration, or pre-launch hardening — to
  route you to the right chapters of a production-engineering handbook (API design,
  auth, data integrity, error handling, resilience, security, testing, deployment,
  monitoring, logging, configuration, schema evolution, product analytics). Not for
  pure research, Q&A, or one-line edits.
---

# Production Engineering Handbook

Reference material for production engineering. Each chapter lives in `topics/` —
one project-independent markdown per concern (patterns, tradeoffs, common mistakes).

This file is a **router** — it narrows 14 chapters down to the few your task most
likely needs. It's a starting point for your judgment, not a checklist to obey, and
not a substitute for thinking.

## Show your reasoning — don't run on confidence

Before you start reading, **tell the user your plan in plain language and check it
with them**: which chapters you'll read, which you'll skip, and why. Two failure
modes hurt equally — reading too little and missing something, or digging into
chapters that don't help. You guard against both by saying your reasoning *before*
you act on it, not after.

- **Justify every call, especially deviations.** Pulling in a chapter the router
  didn't flag, or skipping one it did — say so, and say why, in plain terms.
- **Don't assume — confirm.** Don't assume you've understood the task, and
  *especially* don't assume the user already knows the concepts or the tradeoffs.
  Explain them simply, so they can actually judge your plan. Unsure what they want?
  Ask — don't guess.
- **When you're genuinely torn** — skip something that might matter, or go deep on
  something the router didn't flag? — don't trust your own confidence. **Get a
  second opinion from a subagent, or stop and put the question to the user.**
- **Raise what the task doesn't force.** Something smart to handle now but not
  strictly required — structured logging before it grows, a metric worth emitting,
  an auth boundary starting to form — surface it as a suggestion or a question.
  Don't silently decide either way.
- **An agreed plan or spec wins.** If the work is already scoped, follow it —
  surface anything the handbook flags that it missed as a *suggestion*, and don't
  unilaterally expand scope.
- When you truly can't tell whether something applies, lean toward reading it over
  skipping — but still say why.

Scale this to the task: a one-line change gets a one-sentence plan ("reading
error-handling and data-integrity, skipping the rest — here's why"); a big one gets
a real check-in. Always say it; never assume.

## Start here — what are you doing?

Pick the **one** row closest to what you're fundamentally doing, then add any
**modifiers** below that the task involves.

**Primary — pick the closest:**

| What you're doing | Core chapters (start here, then adjust) |
|---|---|
| **Start a new project** (greenfield) | configuration · data-integrity · api-design · error-handling · testing · deployment |
| **Build a feature** in an existing app | api-design · data-integrity · error-handling · testing |
| **Change how a live system behaves** | deployment · resilience · monitoring · testing |

**Starting a new project? First name what *kind* it is** — the greenfield list leans
toward a web app/service, and the right set shifts with the shape. Say which you picked
and what you changed:

- **Web app / service** → fits as written; `api-design` (contracts) and `auth` (users, via the identity modifier) carry real weight.
- **Data workflow / pipeline / batch job** → `data-integrity` + `resilience` become the heart of it — runs get retried and re-run, so idempotency and partial-failure handling matter most; `api-design` usually drops out (no HTTP contract, though an output schema is its own kind of contract); read `deployment`/`monitoring` as *"how does it get scheduled, and how do I know a run succeeded?"* — not web rollout and dashboards.
- **Library / CLI / something else** → keep `configuration` · `error-handling` · `testing`; pull the rest in only as it applies.

Don't inherit the list on autopilot.

**Working with existing or running code** — lean on the dedicated skill for the *process*:

| Situation | Chapters | Skill |
|---|---|---|
| **Debug an incident** or chase a perf/latency regression | error-handling · logging · monitoring · resilience | `diagnose` |
| **Review or audit** code | testing · security · data-integrity | `review` |

**Modifiers — add the chapters for any that apply:**

| If the task… | also read |
|---|---|
| …changes the database schema | schema-evolution · data-integrity |
| …calls another service over the network (third-party API, payment provider, internal service, queue) | resilience · error-handling · configuration · testing |
| …handles identity or sensitive data (auth, payments, PII, admin actions) | authentication-authorization · security |
| …serves multiple customer orgs from one system (multi-tenant SaaS) | multi-tenant-isolation · authentication-authorization · security |
| …changes a public API contract | api-design |
| …is being deployed / going live | deployment · monitoring · resilience · logging · security |

If your task matches no row, pick chapters by keyword from the **Topic index** below
— and say which you picked and why.

## Topic index

| Chapter | Covers |
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

## How to read them, per situation

- **New project** — these are the decisions painful to retrofit. Start from each chapter's **"Deciding for Your Project"** section.
- **Building a feature** — apply the established patterns and scan each chapter's **"Anti-Patterns"** table before you finish.
- **Changing a live system** — read through the lens of *don't break what's running* (migrations, rollout, graceful shutdown), and watch your metrics after.
- **Calling another service** (third-party or internal) — read for the timeout / retry / error-mapping / mock-the-boundary patterns.
- **Going live / hardening** — read for the security pass, observability (alerts + runbooks), and recovery patterns.

## Topic map — how the chapters relate

**Hub chapters** — almost everything connects to these; expect to touch them whatever you're doing:
`error-handling` · `security` · `configuration` · `data-integrity`

**Clusters** — chapters that travel together:

- **Data & Contracts** — `data-integrity` · `api-design` · `schema-evolution` (a schema change ripples through all three; keep DB, app schema, and API shape in sync)
- **Failure & Robustness** — `error-handling` · `resilience` (the error hierarchy feeds retry predicates, circuit breakers, and graceful shutdown)
- **Observability** — `logging` · `monitoring` · `product-analytics` (one request · whole system · are users using it)
- **Identity & Protection** — `authentication-authorization` · `security` · `multi-tenant-isolation` (overlapping; auth is the deep implementation reference, multi-tenant-isolation the tenant-boundary treatment)
- **Foundation** — `configuration` · `deployment`
- **`testing`** cross-cuts all of the above.

Each chapter ends with a **Related Topics** list — follow those when a concern pulls in a neighbour.

## Cross-cutting scenarios

Some work spans several topics at once and the synthesis lives in none of them. If the task matches a scenario below, the integrating idea is here; the **recruits** are the topics to open.

- **Multi-tenant isolation** — one system serving many customer orgs. Isolation is structural, not per-query vigilance: enforce the tenant filter in a scoped data layer *and* back it with the database engine, and take tenant identity only from the verified session. Full treatment in [multi-tenant-isolation.md](./topics/multi-tenant-isolation.md); recruits [security.md](./topics/security.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Request correlation / tracing** — reconstructing one request across logs and services. Mint a correlation id at the edge, thread it through every log line and outbound call, and surface it in error responses — that one id ties the trail together. Recruits [logging.md](./topics/logging.md), [error-handling.md](./topics/error-handling.md), [monitoring.md](./topics/monitoring.md).
- **Idempotent side-effects** — an external effect (payment, email, webhook) that may be retried. Guard it with an idempotency key and a stored result so a retry returns the original outcome, not a second effect — and the guard must hold under *concurrent* retries, not just sequential ones. Recruits [resilience.md](./topics/resilience.md), [testing.md](./topics/testing.md).
- **Server-projected capabilities** — the client needs to know which actions a user may take, to render or enable UI. The server is the authority: derive the permitted-action set from the same rules the endpoints enforce and project it into the response, so the client shows affordances without re-deriving authorization. One source, or the UI hint and the real check drift apart. Recruits [api-design.md](./topics/api-design.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Validation at trust boundaries** — data arriving from anywhere untrusted (API input, third-party responses, queue messages, files). Parse it through a schema at the boundary and trust the typed result inside; the boundary is the one place to establish the data is what you think it is. Recruits [data-integrity.md](./topics/data-integrity.md) (owner), [security.md](./topics/security.md).

## Planning vs implementing

If you're **planning** work (especially alongside the user), record in the plan **which chapters/rows above apply** to it. The agent that implements should read the plan **and reload those chapters** — not the plan alone, which can't capture every standard. (Small task → the same agent can plan and implement. Larger task → a fresh implementing agent is fine, as long as the plan names the chapters for it to reload.)

When the user points you at a specific chapter or concern, read it directly. Otherwise use the router above.
