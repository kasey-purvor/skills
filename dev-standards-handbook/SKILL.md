---
name: dev-standards-handbook
description: >-
  Use when planning or making any non-trivial change to a codebase — a new project,
  feature, fix, refactor, live change, integration, or pre-launch hardening — to
  route you to the right chapters of a production-engineering handbook (API design,
  auth, multi-tenant isolation, data integrity, error handling, resilience, security,
  testing, deployment, monitoring, logging, configuration, schema evolution, product
  analytics, module design, front-end development, code pitfalls, and traps in shared tools and
  machines). Not for pure research, Q&A, or one-line edits.
---

# Production Engineering Handbook

Reference material for production engineering. Each chapter lives in `topics/` —
one project-independent markdown per concern (patterns, tradeoffs, common mistakes).

This file is a **router** — it narrows the chapters down to the few your task most
likely needs. It's a starting point for your judgment, not a checklist to obey, and
not a substitute for thinking.

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

**Whatever the row, two chapters ride along:** read `environment` before the first
command of a piece of work (known traps in the tools, the harness and the machines), and
scan `pitfalls` alongside any new code or module (named anti-patterns to catch before
they become embedded).

**Primary — pick the closest:**

| What you're doing | Core chapters (start here, then adjust) |
|---|---|
| **Start a new project** (greenfield) | module-design · configuration · data-integrity · api-design · error-handling · testing · deployment |
| **Build a feature** in an existing app | module-design · api-design · data-integrity · error-handling · testing |
| **Change how a live system behaves** | deployment · resilience · monitoring · testing |

**Starting a new project? First name what *kind* it is** — the greenfield list leans
toward a web app/service, and the right set shifts with the shape. Say which you picked
and what you changed:

- **Web app / service** → fits as written; `api-design` (contracts) and `auth` (users, via the identity modifier) carry real weight.
- **Browser client** (for example, standalone React) → start with `frontend-development` · `module-design` · `configuration` · `testing`; add backend contract, data, and identity chapters only when those concerns are involved.
- **Data workflow / pipeline / batch job** → `data-integrity` + `resilience` become the heart of it — runs get retried and re-run, so idempotency and partial-failure handling matter most; `api-design` usually drops out (no HTTP contract, though an output schema is its own kind of contract); read `deployment`/`monitoring` as *"how does it get scheduled, and how do I know a run succeeded?"* — not web rollout and dashboards.
- **Library / CLI / something else** → keep `configuration` · `error-handling` · `testing`; pull the rest in only as it applies.

Don't inherit the list on autopilot.

**Working with existing or running code** — lean on the dedicated skill for the *process*:

| Situation | Chapters | Skill |
|---|---|---|
| **Debug an incident** or chase a perf/latency regression | error-handling · logging · monitoring · resilience | `diagnose` |
| **Review or audit** code | testing · security · data-integrity | `change-review` |

**Modifiers — add the chapters for any that apply:**

| If the task… | also read |
|---|---|
| …builds, changes, or reviews front-end code: a rendered interface, React components, client state, or front-end structure | frontend-development; add module-design when changing boundaries, and testing for behaviour changes |
| …changes the database schema | schema-evolution · data-integrity |
| …calls another service over the network (third-party API, payment provider, internal service, queue) | resilience · error-handling · configuration · testing |
| …handles identity or sensitive data (auth, payments, PII, admin actions) | authentication-authorization · security |
| …serves multiple customer orgs from one system (multi-tenant SaaS) | multi-tenant-isolation · authentication-authorization · security |
| …changes a public API contract | api-design |
| …creates a new module, or reshapes how code is split into modules (new service/package/layer, extracting or merging modules) | module-design |
| …is being deployed / going live | deployment · monitoring · resilience · logging · security |

**Front-end work:** for a local layout or interaction change, start with `frontend-development` and the relevant testing guidance; the generic feature row does not require backend chapters when no backend contract or behaviour changes. Add contracts, identity, or isolation chapters only when those concerns are involved. Framework names select short sections within the chapter, not a separate framework manual.

**Authorised review assignments:** chapter selection within the shared review workflow is already authorised. State the chapters and reasons to the coordinator without reopening routine approval; ask about material scope changes or genuine uncertainty. When you are already a reviewer, the process link to `change-review` does not dispatch another review.

**Browser-only review:** an experience review (frontend-audit) or a browser verification (frontend-verify) reads only the relevant groups of `frontend-patterns`, the catalogue of observable interface faults with its probe sizes, within the workflow's and the user's assigned scope. Loading it does not authorise code inspection or start a code review.

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
- **Failure & Robustness** — `error-handling` · `resilience` (the error hierarchy tells retry predicates and circuit breakers which failures are upstream ones; the operation decides whether a retry is safe)
- **Observability** — `logging` · `monitoring` · `product-analytics` (one request · whole system · are users using it)
- **Identity & Protection** — `authentication-authorization` · `security` · `multi-tenant-isolation` (auth is the canonical reference for identity, sessions and authorization; security the web attack surface and the access-control rules a review checks; multi-tenant-isolation the tenant boundary)
- **User Interfaces** — `frontend-development` · `module-design` · `testing` (keep behaviour understandable, boundaries useful, and journeys verified; recruit contracts and identity chapters when needed) · `frontend-patterns` for browser review
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

If you're **planning** work (especially alongside the user), record in the plan **which chapters/rows above apply** to it. The agent that implements should read the plan **and reload those chapters** — not the plan alone, which can't capture every standard. (Small task → the same agent can plan and implement. Larger task → a fresh implementing agent is fine, as long as the plan names the chapters for it to reload.)

When the user points you at a specific chapter or concern, read it directly. Otherwise use the router above.
