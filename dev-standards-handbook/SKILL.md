---
name: dev-standards-handbook
description: >-
  Use when planning or making any non-trivial change to a codebase — a new project,
  feature, fix, refactor, live change, integration, or pre-launch hardening — to
  route you to the right chapters of a production-engineering handbook (API design,
  auth, multi-tenant isolation, data integrity, error handling, resilience, security,
  testing, deployment, monitoring, logging, configuration, schema evolution, product
  analytics, module design, front-end development, code pitfalls, and traps in shared tools and
  machines). Not for pure research, Q&A, or trivial edits such as a typo or a rename.
---

# Production Engineering Handbook

Each chapter in `topics/` covers one concern, independent of any project: patterns,
tradeoffs, common mistakes. This file is a **router**: it narrows the chapters to the few
your task most likely needs. It is a starting point for your judgment, not a checklist.
When the user points you at a specific chapter or concern, read it directly.

## First: calibrate rigor to the context

The chapters describe the **thorough** version of each concern — the shape a pattern
takes on a public, high-traffic, multi-client, long-lived system. **Most work is not
that.** Before applying any chapter, name what you're actually building, because that
sets how much of the chapter applies:

- **Who calls it?** A public API with third-party clients you don't control earns
  strict versioning, response-shape discipline, and rate limiting. An internal tool
  with a handful of known callers usually does not — you can change the contract by
  editing both sides in one commit.
- **What's the blast radius if it's wrong?** A payment path or a system-of-record
  justifies belt-and-braces. A dashboard, a batch job, an internal admin screen, or a
  prototype usually justifies the simplest thing that works.
- **What scale?** Pagination, percentiles, circuit breakers, and expand-and-contract
  migrations earn their keep at scale. Small scale, they're often premature.
- **How long does it live?** A throwaway or a greenfield app still finding its shape
  tolerates shortcuts a decade-old system-of-record does not.

Match the rigor to the answers. Applying public-API discipline to an internal CRUD
tool isn't "being thorough" — it's cost with no return, and it's the most common way
this handbook gets misread. When a chapter states something as an absolute ("always",
"every", "never"), read it as *the default for the demanding case* and ask whether
your case is that case.

**The exception — security, auth, and tenant isolation.** For those three, the *core*
protections hold even for a small internal tool: a real vulnerability, an unverified
permission, or a cross-tenant leak doesn't care how few users you have. Calibrate how
much you *invest* there (how many roles, which isolation strategy, how elaborate the CSP),
but don't calibrate the core rules away. On a shared-schema multi-tenant system the
database backstop (RLS on Postgres) is core, not optional defence-in-depth.

## Show your reasoning — don't run on confidence

Before you start reading, **tell the user your plan in plain language and check it
with them**: which chapters you'll read, which you'll skip, and why. Saying it *before*
you act guards against both failures: reading too little, and digging into chapters that
don't help. A small change gets one sentence; a big one gets a real check-in.

**Delegated work:** under a coordinator's standing authorisation (a review, a browser
verification, a lane build), give the plan and its reasons to the coordinator and proceed.
Questions go to the coordinator, only for a material scope change or genuine uncertainty,
and you dispatch no agent your brief does not allow.

- **Justify deviations.** Say why you pulled in a chapter the router didn't flag, or
  skipped one it did. When you can't tell whether one applies, lean toward reading it.
- **Don't assume — confirm.** Don't assume you've understood the task, or that the user
  knows the concepts and tradeoffs; explain them simply so they can judge your plan.
  Unsure what they want? Ask.
- **When you're genuinely torn**, don't trust your own confidence: get a second opinion
  from a subagent, or put the question to the user.
- **Raise what the task doesn't force** — structured logging before it grows, a metric
  worth emitting, an auth boundary starting to form — as a suggestion or a question.
  Don't silently decide either way.
- **An agreed plan or spec wins.** Follow it; surface anything the handbook flags that it
  missed as a *suggestion*, without expanding scope.

## Start here — what are you doing?

Pick the **one** row closest to what you're fundamentally doing, then add any
**modifiers** below that the task involves.

**Whatever the row, two chapters ride along:** read `environment` before the first
command of a piece of work (known traps in the tools, the harness and the machines), and
scan `pitfalls` alongside any new code or module (named anti-patterns to catch before
they become embedded).

| What you're doing | Core chapters (start here, then adjust) | Read them for |
|---|---|---|
| **Start a new project** (greenfield) | module-design · configuration · data-integrity · api-design · error-handling · testing · deployment | Each **Deciding for Your Project** section: the choices painful to retrofit. Name the project's kind first (below). |
| **Build a feature** in an existing app | module-design · data-integrity · error-handling · testing | The established patterns; each **Anti-Patterns** table before you finish. |
| **Fix a bug or make a small change** | error-handling · testing, plus the chapter that owns the concern | The rule the defect broke; a test that fails without the fix. |
| **Refactor** without changing behaviour | module-design · testing | Interfaces and seams; tests on the interface stay green. |
| **Change how a live system behaves** | deployment · resilience · monitoring · testing | Not breaking what runs (migrations, rollout, shutdown); watch the metrics after. |
| **Debug an incident** or chase a perf/latency regression | error-handling · logging · monitoring · resilience | Process: the `diagnose` skill. |
| **Review or audit** a change | testing, plus the row and modifiers the change itself triggers | Anti-Patterns against the diff. Process: the `change-review` skill. |

**Starting a new project? First name what *kind* it is** — the greenfield list leans
toward a web app/service, and the right set shifts with the shape. Say which you picked
and what you changed:

- **Web app / service** → fits as written; `api-design` (contracts) and `auth` (users, via the identity modifier) carry real weight.
- **Browser client** (for example, standalone React) → start with `frontend-development` · `module-design` · `configuration` · `testing`; add backend contract, data, and identity chapters only when those concerns are involved.
- **Data workflow / pipeline / batch job** → `data-integrity` + `resilience` become the heart of it — runs get retried and re-run, so idempotency and partial-failure handling matter most; `api-design` usually drops out (no HTTP contract, though an output schema is its own kind of contract); read `deployment`/`monitoring` as *"how does it get scheduled, and how do I know a run succeeded?"* — not web rollout and dashboards.
- **Library / CLI / something else** → keep `configuration` · `error-handling` · `testing`; pull the rest in only as it applies.

**Modifiers — add the chapters for any that apply:**

| If the task… | also read |
|---|---|
| …builds, changes, or reviews front-end code: a rendered interface, React components, client state, or front-end structure | frontend-development; module-design when changing boundaries, testing for behaviour changes; no backend chapters unless a contract or backend behaviour changes. A browser review reads the relevant groups of frontend-patterns |
| …changes the database schema | schema-evolution · data-integrity |
| …calls another service over the network (third-party API, payment provider, internal service, queue) | resilience · error-handling · configuration · testing, for timeouts, retries, error mapping and mocking the boundary |
| …handles identity or sensitive data (auth, payments, PII, admin actions) | authentication-authorization · security |
| …serves multiple customer orgs from one system (multi-tenant SaaS) | multi-tenant-isolation · authentication-authorization · security |
| …adds or changes an API contract (public ones most of all) | api-design |
| …creates a new module, or reshapes how code is split into modules (new service/package/layer, extracting or merging modules) | module-design |
| …is being deployed / going live | deployment · monitoring · resilience · logging · security, for the security pass, alerts with runbooks, and recovery |

If your task matches no row, pick chapters by keyword from the **Topic index** below
— and say which you picked and why.

## Topic index

| Chapter | Covers |
|---|---|
| `topics/api-design.md` | REST conventions, response shapes, pagination, versioning and breaking changes, field casing, type-safe contracts |
| `topics/authentication-authorization.md` | OIDC, JWT verification, token storage and backend-for-frontend, sessions, account flows, RBAC/ABAC, audit logging |
| `topics/configuration.md` | Env var validation, `.env`, multi-layer config, build-time vs runtime config, secret delivery and rotation, where clients are built, serverless config |
| `topics/data-integrity.md` | Zod/Pydantic, three-layer integrity model, validation boundaries, transactions, locking and deadlocks, transactional outbox, poolers |
| `topics/deployment.md` | Rolling deploys and the mixed-version window, release patterns, rollback, migrations in the pipeline, lockfiles and supply chain, CI/CD and promotion, infrastructure as code |
| `topics/environment.md` | Traps in shared tools and machines: Claude Code, Codex, Linear, scraping and search services, git/GitHub, the machines. Read before the first command of a piece of work |
| `topics/error-handling.md` | Error hierarchies, global handlers, RFC 9457, error chaining |
| `topics/frontend-development.md` | Component boundaries, state ownership, data changes, forms, navigation, accessibility, layout, React/framework decisions |
| `topics/frontend-patterns.md` | Observable interface faults by review lens (fit, first screen, controls, tasks, consistency, wording, states, accessibility), with browser checks and probe sizes; read the relevant group for a browser review |
| `topics/logging.md` | Structured logging, correlation IDs echoed to clients, redaction and personal data in telemetry, retention, frontend logging |
| `topics/module-design.md` | Deep vs shallow modules, interfaces, seams, adapters, design-it-twice, dependency categories |
| `topics/monitoring.md` | Metric types, RED/USE, job and queue monitoring, SLOs and burn-rate alerts, distributed tracing, OTel |
| `topics/multi-tenant-isolation.md` | Isolation strategies, scoped data layers, the RLS database backstop, elevated cross-tenant access, tenant scope beyond the database (caches, jobs, storage, search) |
| `topics/pitfalls.md` | Named anti-patterns from real codebases, grouped by what you're building. Scan alongside any new code or module |
| `topics/product-analytics.md` | Event tracking and naming, server-side capture, identity (not in anonymity products), groups, consent |
| `topics/resilience.md` | Retries, circuit breakers, timeouts, fan-out and connection pools, idempotency, background jobs, graceful shutdown, health checks |
| `topics/schema-evolution.md` | Migrations, expand-and-contract, backfills, lock timeouts, adding constraints to big tables, which release each migration rides in |
| `topics/security.md` | Access-control core rules, injection, SSRF and path traversal, XSS, CSRF and session cookies, CORS, headers and CSP, supply-chain trust, secrets, rate limiting |
| `topics/testing.md` | Test types and the pyramid, per-concern negatives linking each owner, harness parity, proving a test can fail, test DBs and reset strategies, mocking, factories |

## Topic map — how the chapters relate

**Hub chapters** — almost everything connects to these; expect to touch them whatever you're doing:
`error-handling` · `security` · `configuration` · `data-integrity`

**Clusters** — chapters that travel together:

- **Data & Contracts** — `data-integrity` · `api-design` · `schema-evolution` (a schema change ripples through all three; keep DB, app schema, and API shape in sync)
- **Failure & Robustness** — `error-handling` · `resilience` (the error hierarchy tells retry predicates and circuit breakers which failures are upstream ones; the operation decides whether a retry is safe)
- **Observability** — `logging` · `monitoring` · `product-analytics` (one request · whole system · are users using it)
- **Identity & Protection** — `authentication-authorization` · `security` · `multi-tenant-isolation` (auth is the canonical reference for identity, sessions and authorization; security the web attack surface and the access-control rules a review checks; multi-tenant-isolation the tenant boundary)
- **User Interfaces** — `frontend-development` · `frontend-patterns` (how to build the interface · the observable faults a browser review checks)
- **Foundation** — `configuration` · `deployment`
- **`testing`** and **`module-design`** cross-cut all of the above (every module has an interface, and the interface is the test surface).

Each chapter ends with a **Related Topics** list — follow those when a concern pulls in a neighbour.

## Cross-cutting scenarios

Some work spans several topics at once and the synthesis lives in none of them. If the task matches a scenario below, the integrating idea is here; the **recruits** are the topics to open.

- **Multi-tenant isolation** — one system serving many customer orgs. Isolation is structural, not per-query vigilance: enforce the tenant filter in a scoped data layer *and* back it with the database engine, and take tenant identity only from the verified session. Full treatment in [multi-tenant-isolation.md](./topics/multi-tenant-isolation.md); recruits [security.md](./topics/security.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Request correlation / tracing** — reconstructing one request across logs and services. Mint a correlation id at the edge, thread it through every log line and outbound call, and surface it in error responses — that one id ties the trail together. Recruits [logging.md](./topics/logging.md), [error-handling.md](./topics/error-handling.md), [monitoring.md](./topics/monitoring.md).
- **Idempotent side-effects** — an external effect (payment, email, webhook) that may be retried. Guard it with a per-tenant (or per-caller) idempotency key, a request fingerprint and a stored result so a retry returns the original outcome, not a second effect — and the guard must hold under *concurrent* retries, not just sequential ones. Recruits [resilience.md](./topics/resilience.md), [testing.md](./topics/testing.md).
- **Front-end state across a user journey** — a route, cached server record, and unsaved form draft can all describe the same entity while owning different facts. Make those owners and the save/refresh transitions explicit. Recruits [frontend-development.md](./topics/frontend-development.md), [testing.md](./topics/testing.md); add [api-design.md](./topics/api-design.md) if the wire contract changes.
- **Server-projected capabilities** — the client needs to know which actions a user may take, to render or enable UI. The server is the authority: derive the permitted-action set from the same rules the endpoints enforce and project it into the response, so the client shows affordances without re-deriving authorization. One source, or the UI hint and the real check drift apart. Recruits [api-design.md](./topics/api-design.md), [authentication-authorization.md](./topics/authentication-authorization.md).
- **Validation at trust boundaries** — data arriving from anywhere untrusted (API input, third-party responses, queue messages, files). Parse it through a schema at the boundary and trust the typed result inside; the boundary is the one place to establish the data is what you think it is. Recruits [data-integrity.md](./topics/data-integrity.md) (owner), [security.md](./topics/security.md).

## Planning vs implementing

If you're **planning** work, record which chapters apply: in a PRD's **Applicable
Standards** section, a ticket's `Standards:` line, or the plan itself. The implementing
agent reloads those chapters, not the plan alone, which can't capture every standard. A
fresh implementer is fine for a larger task, provided the plan names the chapters.
