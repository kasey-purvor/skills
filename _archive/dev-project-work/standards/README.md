# Production Engineering Handbook

Reference material for production engineering patterns — error handling, security, resilience, testing, and the rest. Lives alongside the `dev-project-work` skill and is consulted on demand.

## What this handbook is (and isn't)

**It is** a collection of chapter-style topic files under `topics/`, each covering one production concern with enough depth to ground a design conversation or code review. Topics are written to be project-independent — they describe patterns, tradeoffs, and common mistakes, not mandates for any specific project.

**It is not** a specification. It does not dictate that every project must adopt every pattern. Some topics will not apply to a given project, some will apply with different tooling, and some will be overridden by project-specific decisions.

## How to use it

**During design or planning:** read the topic that's relevant to the decision you're making. Cite the concepts in your project's own docs (`.context/project/design.md`, `architecture.md`, or — when the choice passes the three-question filter — a new ADR in `.context/decisions/`) — don't copy whole sections in.

**During implementation:** treat the code examples as documentation for the pattern, not as copy-paste sources. Library APIs change; verify against the current library docs before pasting into code. The handbook tries to keep code short, focused on the pattern, and correct — but the canonical source for any library is the library itself.

**During review:** if a topic comes up that isn't covered here, or is covered in a way that doesn't fit the project, that's a signal — see "Iterative nature" below.

## The two-layer decisions model

This handbook is the top layer of a two-layer system described in the parent skill's `SKILL.md`:

| Layer | Location | Purpose |
|---|---|---|
| **Handbook** (reference) | `standards/topics/*.md` | Production patterns with tradeoffs — this folder |
| **Project decisions (ADRs)** | `.context/decisions/NNNN-*.md` (per project) | One decision per file, immutable. Captures *why* a non-obvious, hard-to-reverse choice was made |

The handbook informs decisions; the resulting decision — when it passes the three-question filter (hard to reverse / surprising / real trade-off) — is recorded as an ADR. Patterns enforced automatically (linter, types, code-review sub-agent) don't get a separate doc.

## Iterative nature

The handbook is not finished. Topics get added, trimmed, corrected, and reshaped as projects expose gaps and inaccuracies. The current state is a snapshot — expect changes.

Two folders hold the *meta* of that process:

- **`Internal skill review/`** — dated review artifacts. Each file is a point-in-time review: what felt wrong, what felt missing, what was out of scope. These are atomic — they don't get consolidated or rewritten. Over time they form a history of what the handbook has been through.
- **`findings-and-additions.md`** (legacy) — earlier consolidation of findings. Now superseded by the dated-review pattern in `Internal skill review/`.

## The post-session review loop

At the end of a project or significant phase, consider whether anything in the handbook felt wrong, missing, or over-specified for the work you just did. Findings sort into four buckets, each with a different destination:

| Bucket | What it means | Goes to |
|---|---|---|
| **Fix** | The handbook was wrong — buggy code, misleading prose, out-of-date pattern | Inline edit to the topic file |
| **Preference** | This project prefers X over Y, but Y is still a valid handbook default | An ADR in `.context/decisions/` (if it passes the three-question filter) — not the handbook |
| **Gap** | A pattern exists and should be in the handbook but isn't yet | Entry in the latest `Internal skill review/` file |
| **Scope** | The handbook covers something that isn't generally useful, or over-covers something | Note in the latest `Internal skill review/` file |

Inline edits to the handbook are reserved for the Fix bucket. Preferences stay in the project. Gaps and scope concerns accumulate in the review file and get triaged later — they aren't action items until someone picks them up.

## Current topic index

| Topic | Covers |
|---|---|
| `api-design.md` | REST conventions, response shapes, pagination, versioning, type-safe contracts |
| `authentication-authorization.md` | OIDC, JWT, tokens, RBAC/ABAC, multi-tenant isolation, RLS, common vulnerabilities |
| `configuration.md` | Env var validation, `.env`, multi-layer config, serverless config |
| `data-integrity.md` | Zod/Pydantic, three-layer integrity model, transactions, validation boundaries |
| `deployment.md` | Release patterns, lockfiles, concurrency, CI/CD |
| `error-handling.md` | Error hierarchies, global handlers, RFC 9457, error chaining |
| `logging.md` | Structured logging, correlation IDs, frontend logging |
| `monitoring.md` | Metric types, RED/USE, SLOs, distributed tracing, OTel |
| `product-analytics.md` | Event tracking, identity, groups, privacy |
| `resilience.md` | Retries, circuit breakers, timeouts, idempotency, graceful shutdown, health checks |
| `schema-evolution.md` | Migrations, expand-and-contract, backfills |
| `security.md` | Injection, XSS, CSRF, CORS, headers, secrets, rate limiting |
| `testing.md` | Test pyramid, contract tests, test DBs, mocking, factories |

The list is current at the time of the most recent review under `Internal skill review/`. For the latest proposed additions or subtractions, see the newest dated review file.
