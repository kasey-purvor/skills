---
name: dev-project-work
description: Use when designing or building software projects end-to-end across the full lifecycle — design, research, sprint planning, implementation, and review. Entry point that routes between three roles (Lead, Implementer, Junior Developer) and consults production standards on-demand. Start here when the user wants project work but hasn't picked a specific sub-skill.
---

# Project Work

A unified skill for designing and building software projects. Covers the full lifecycle from early design through implementation.

## Roles

| Role | Focus | Module |
|------|-------|--------|
| **Lead** | Design, research, chunk scoping, sprint management, durable truth ownership | `lead/lead.md` |
| **Implementer** | Detailed implementation plans, tactical gap-filling, post-chunk review | `sprint/implementer.md` |
| **Junior Developer** | Execute implementation plans exactly | `sprint/junior.md` |

## Standards & Decisions

Two layers carry engineering decision material:

- **Handbook** — `standards/topics/*.md` within this skill. Production engineering patterns (error handling, security, resilience, testing, etc.) as reference material. Project-independent. The Lead may consult a topic when grounding a design decision in established options
- **Project decisions** — `.context/decisions/NNNN-*.md` in each project. ADRs (Architecture Decision Records) — one decision per file, numbered sequentially, immutable. Each ADR captures *why* a non-obvious, hard-to-reverse choice was made. The handbook informs the discussion; the resulting decision is recorded as an ADR

See "Decisions Structure" below for when to write an ADR and the format.

---

## Sub-agents

Five sub-agent prompts live in `sub-agents/` at the skill root. Any role may invoke any sub-agent when needed; each role file describes role-specific guidance for when invocation is appropriate.

| Sub-agent | Purpose | Typical caller |
|---|---|---|
| `consistency-check-prompt.md` | Reads context files and verifies cross-references, boundary rules, no duplication, mandatory sections present, vocabulary adherence between context files, and ADR structural integrity (Date / Status / Context / Decision / Consequences). Reports findings only | Lead, at wrap-up or after significant doc changes across multiple files |
| `truthfulness-check-prompt.md` | Reads context files for concrete claims (paths, functions, schemas, libraries, routes) and verifies each against the actual codebase. Reports accuracy, staleness, and gaps | Lead, post-sprint or when docs may have drifted from reality |
| `code-review-prompt.md` | Reads a completed chunk's code for quality, correctness, edge cases, context-file consistency, and vocabulary adherence in code | Implementer, during post-chunk review |
| `spec-adherence-prompt.md` | Reads a completed chunk against the implementation plan. Reports what deviates and whether it's justified | Implementer, during post-chunk review |
| `vocabulary-audit-prompt.md` | Comprehensive sweep over docs + code together for vocabulary discipline. Reports misuse, drift, **gaps** (recurring concepts without canonical names), stale entries, and incomplete coverage. Distinct from inline discipline and other sub-agents in that it is *expected* to surface gaps | Lead, on-demand vocabulary sweep — Sprint Wrap-up or before a Sharpen Vocabulary session to gather evidence |

Sub-agents report findings only. Classification (fix-now, promote, backlog, defer, rule-out) is the Lead's responsibility with the user.

---

## Role Routing

On initialization:

1. Ask the user which role they need
2. Read the full entry point (this file), then the role's module
3. The Lead is the default — if the user describes work without specifying a role, suggest Lead

The Lead proposes its mode (design, sprint, or direct) based on context: existing `.context/` state, `ACTIVE-SPRINT`, `HANDOFF.md`, and the user's stated goal. It always confirms with the user before proceeding.

---

## Roles and Information Flow

### Lead

The Lead is the senior technical authority. It operates in three modes:

**Design mode** — exploring, researching, and recording durable project truth in context files. Used when figuring out *what* to build and *why*.

Activities: scaffolding `.context/`, researching domain and integrations, discussing design options, recording decisions in context files, running consistency checks, assessing production standards, preparing for sprint entry.

**Sprint mode** — organizing and overseeing implementation. Used when the project (or a slice of it) is designed enough to build.

Activities: creating sprints, scoping chunks, tracking progress via CURRENT-STATE.md, overseeing post-chunk review, promoting discoveries back to durable truth, wrapping up sprints.

**Direct mode** — the Lead acts as a senior developer, making changes hands-on without sprint machinery. Used for focused work that doesn't warrant chunk scoping.

Activities: bug fixes, tooling setup, infrastructure admin, small refactors, context file maintenance, CI/CD configuration, dependency updates.

**Mode switching:** The Lead moves fluidly between modes within a session. The litmus test: if the answer creates or changes durable truth, that's design work. If it needs chunk scoping and handoff to an implementer, that's sprint work. If it's focused, bounded work the Lead can do directly, that's direct mode.

### Implementer

Writes detailed implementation plans from the Lead's chunk scopes. Fills tactical gaps, structures test-first development, and reviews the Junior Developer's work after execution. Does not make design decisions — escalates gaps to the Lead or user.

### Junior Developer

Executes implementation plans exactly. Records deviations and discoveries in the plan. Does not read context files directly — the implementation plan contains everything needed. Stops and asks when anything is ambiguous.

### Information Flow

```
Design Mode                          Sprint Mode
───────────                          ───────────
Lead explores & researches           Lead scopes chunks from durable truth
         │                                    │
         ▼                                    ▼
Context files (durable truth)        PLAN.md chunk scopes (execution mirror)
  vocabulary.md                               │
  design.md                                   ▼
  architecture.md                    Implementer writes implementation plans
  data.md                                     │
  domain.md                                   ▼
  integrations.md                    Junior Developer executes
  backlog.md
  .context/decisions/*.md (ADRs)
                                              │
         ▲                                    ▼
         │                           Discoveries & deviations
         │                                    │
         └────────────────────────────────────┘
              Promotion back to durable truth
              (Lead confirms with user)
```

### Truth Hierarchy

Information flows downward from durable truth into execution artifacts. Discoveries flow upward through promotion.

- **Durable truth** (context files) is authoritative. Sprint artifacts consume it but do not own it.
- **Execution artifacts** (PLAN.md, implementation plans, CURRENT-STATE.md) may restate durable truth for clarity, but must never become the only place a fact exists.
- **Bridges** (HANDOFF.md) carry context between sessions — not just between sprints; HANDOFF is written at any session end, regardless of sprint boundary. They point to truth but do not contain it. **The previous Lead's "expected next session" notes are proposals, not mandates** — the current Lead validates them against the backlog and current circumstances before committing.
- **Retrospectives** (SPRINT-SUMMARY.md) record what happened during a sprint. They are not read on startup and do not drive decisions — they exist for historical reference only.

### Entry Modes

When the Lead transitions from design to sprint, it uses one of two entry modes:

- **Vertical-slice entry** — enough clarity exists to build one thin slice safely. Core workflow is described, the touched area has enough structure to avoid guessing, and any major assumptions are explicitly marked provisional.
- **Broader sprint-ready entry** — the target area is mostly settled. Workflows, structure, contracts, and relevant ADRs are recorded or consciously deferred.

The Lead records the entry mode in HANDOFF.md when transitioning to sprint mode, along with which context files or sections are still provisional.

### Promotion Flow

When implementation reveals that durable truth is wrong, incomplete, or missing:

1. **Junior Developer** records the discovery as a deviation in the implementation plan
2. **Implementer** summarizes findings during post-chunk review into CURRENT-STATE.md (does not classify — that's the Lead's job)
3. **Lead** classifies each finding with the user: fix now, promote to owning file, defer, add to backlog, or rule out

If current work depends on the correction, promote before continuing. If the change affects meaning or makes a new decision, get user confirmation first. Update the owning durable file first, then update execution artifacts as needed.

---

## The Context File System

### Folder Structure

```
.context/
├── project/
│   ├── vocabulary.md
│   ├── design.md
│   ├── architecture.md
│   ├── data.md
│   ├── domain.md                    (optional)
│   ├── integrations.md
│   └── backlog.md
├── decisions/
│   └── NNNN-<slug>.md               (ADRs — sequential, immutable)
├── reference/
├── wip/
├── sprints/
│   └── YYYY-MM-DD-<sprint-name>/
│       ├── PLAN.md
│       ├── CURRENT-STATE.md
│       ├── implementation/
│       │   └── 01-<chunk-name>.md
│       ├── temp-diagrams/
│       └── SPRINT-SUMMARY.md
├── ACTIVE-SPRINT
└── HANDOFF.md
```

### File Purposes

| File | Purpose | Authority |
|------|---------|-----------|
| `vocabulary.md` | What we call things — canonical terms with definitions, aliases to avoid, and term relationships | Durable truth |
| `design.md` | What we're building and why — behaviour, workflows, business rules, user experience | Durable truth |
| `architecture.md` | The shape of the system — system overview and component map. *Description, not decisions* — rationale lives in ADRs | Durable truth |
| `data.md` | What the data looks like — schemas, models, contracts, concrete examples | Durable truth |
| `domain.md` | What the real world looks like — entities, lifecycles, processes *(optional)* | Durable truth |
| `integrations.md` | What we connect to — external APIs, auth, tested behaviour, constraints | Durable truth |
| `backlog.md` | Future work — concrete items deferred during sprints, grouped by priority | Durable truth |
| `.context/decisions/NNNN-*.md` | ADRs — one decision per file, numbered sequentially, immutable. Context, decision, consequences. Captures *why* a non-obvious, hard-to-reverse choice was made | Durable truth |
| `PLAN.md` | Sprint execution plan — chunk scopes, sprint goal, guardrails | Execution artifact |
| `CURRENT-STATE.md` | Sprint working memory — progress, blockers, deviations, promotion queue | Execution artifact |
| `sprints/<sprint>/implementation/*.md` | Chunk implementation plans — exact tasks and steps for the Junior Developer | Execution artifact |
| `SPRINT-SUMMARY.md` | Sprint retrospective — outcomes, what was built, carry-forward items | Execution artifact |
| `ACTIVE-SPRINT` | Pointer to current sprint folder | Execution artifact |
| `HANDOFF.md` | **Inter-session bridge** (written at any session end, not just sprint boundaries) — what changed, what's *proposed* next, what's provisional. Proposals not mandates | Bridge (Lead-only) |
| `reference/` | Source material — CSVs, meeting notes, specs. Static input, not modified | Reference |
| `wip/` | Work-in-progress — draft diagrams, exploratory notes. Human aids, not authoritative | Temporary |
| `temp-diagrams/` | Sprint-local diagrams. Human aids, not authoritative | Temporary |

Execution artifacts may restate durable truth for clarity, but must never become the only place a fact exists.

### Context File Definitions

#### General Principles

- **One fact, one owner** — a fact is stated once in its owning file. Other files reference it but don't restate it. Minor contextual overlap is normal and acceptable — naming a technology while describing behaviour, or briefly mentioning a concept that another file owns in detail, is not a violation. The rule targets full restatements, not passing references
- **Sections are created when there's content**, not pre-emptively. Don't create empty sections
- **Section menus are not exhaustive** — suggest new sections not on the menu if the project needs them, with user approval
- **Context files are pure content** — no guidance blocks, no HTML comments, no meta-commentary. All guidance lives in skill files
- **Nothing is permanently locked** — all decisions can be revisited as the project evolves

#### vocabulary.md — What we call things

**Boundary:** Canonical terms (domain and software-internal), one-line definitions, aliases to avoid, term relationships, resolved ambiguities.
**Not here:** Real-world entity structure, lifecycles, or processes (-> domain.md) . Behavioural rules using terms (-> design.md) . Schemas modelling terms (-> data.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Glossary | Canonical terms with one-line definitions and aliases to avoid | Yes |
| Relationships | Light cardinality between terms (e.g., a Sprint contains one or more Chunks) | Optional |
| Recently Resolved Ambiguities | Terms previously ambiguous, with how they were resolved | Optional |

**Notes:**
- **Reading is mandatory.** Lead and Implementer read this file at startup. The file itself is created lazily — the first canonical term resolved triggers creation
- **Inline discipline is always on.** The Lead calls out terminology drift the moment it appears in conversation and updates `vocabulary.md` as canonical terms resolve. This is ambient Lead behaviour, not an action
- **Sharpen Vocabulary** is the on-demand Lead action for a focused grilling pass — see `lead.md` Actions
- **Be opinionated.** When multiple words exist for one concept, pick one canonical term and list the rest as `_Avoid_` aliases
- **Definitions are one sentence.** What it IS, not what it does
- **Both domain and software-internal terms belong here.** "Customer" sits next to "Chunk". `domain.md` owns *structural* domain knowledge (entities, lifecycles, processes); `vocabulary.md` owns *naming*
- **Code review enforces vocabulary always-on when this file exists.** It flags misuse of *defined* terms (e.g., `task` used where `chunk` is canonical) and aliases that should be replaced. It does NOT flag undefined identifiers or absence of coverage — the file documents what's been decided, not everything that exists

**Example entry:**

```markdown
**Chunk**: a unit of work scoped by the Lead and handed to the Implementer.
_Avoid_: task, ticket, slice
```

#### design.md — What we're building and why

**Boundary:** Behaviour, workflows, business rules, config effects, user experience.
**Not here:** Architectural wiring and component structure (-> architecture.md) . JSON/schemas/examples (-> data.md) . External API details (-> integrations.md) . Domain knowledge (-> domain.md)

Naming technologies or libraries in passing while describing behaviour is fine. The boundary is about not putting *how components are wired together* in design.md, not about avoiding technology names.

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Purpose & Scope | What we're building, why, use cases, out-of-scope | Yes |
| Interface & Interactions | What the user types and sees — CLI, API, library surface | Yes |
| Configuration | What each config key DOES (types/defaults in data.md) | Yes |
| Core Workflow | Happy path end-to-end | Yes |
| Open Questions | Unresolved decisions with context and options | Yes (always second-to-last) |
| Deferred Items | Confirmed non-blocking, with reasoning | Yes (always last) |

**Optional sections** (create when relevant): Error handling . Resume/repeat behaviour . Console output/UX . Cost/resource management . Any project-specific topic

**Notes:**
- The Design Status header (open questions count, deferred items count, last updated) gives instant orientation — update it every session
- Config keys: describe what they DO here; types, defaults, and constraints live in `data.md`
- Open Questions and Deferred Items are always the last two sections regardless of how many sections are added
- Even if config is minimal, document it. Even if the interface is a simple CLI, document it
- All open questions live here, even if the topic is architectural or data-related — they move to the appropriate file once resolved

**Example — WRONG in design.md:**
> "Enforced by a token bucket rate limiter module that sits between the orchestrator and LLM client."

**Example — RIGHT in design.md:**
> "Rate limited to a configurable RPM. Requests exceeding the limit are queued, not dropped. 429 responses are retried with backoff."

#### architecture.md — The shape of the system

**Boundary:** *Description only* — system overview, component map. What exists, not why it exists that way. Rationale and trade-offs live in ADRs (`.context/decisions/`).
**Not here:** Why we chose X over Y (-> ADR) . User workflows/business rules (-> design.md) . Schemas/examples (-> data.md) . External API details (-> integrations.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| System Overview | System type, language, packaging, entry point. One short paragraph | Yes |
| Component Map | Components with one-line responsibilities and a dependency tree. **No rationale subsections** — link to ADRs instead | Yes |

**Optional sections:** Concurrency Model (description) . Data Flow (description) . Naming Conventions (description of *what* the convention is, with link to the ADR that decided it) . Any project-specific descriptive topic

**Notes:**
- **Description, not decisions.** If you find yourself writing "we chose X because Y" in architecture.md, stop, write an ADR, and link to it from architecture.md. Re-bloating with rationale is the failure mode this structure exists to prevent
- **Stabilises once implementation begins**; revisited when fundamental components are added or removed
- **Cross-reference ADRs liberally.** Each component or pattern in the map can link to the ADRs that drove its existence. Architecture.md is the snapshot; ADRs are the log
- **Naming conventions are descriptive here, decisional in an ADR.** Record the *current* convention in architecture.md (file casing, prefix pattern, suffix inventory, folder grouping). The *reasoning* behind it lives in an ADR — link from architecture.md

**Example — WRONG in architecture.md:**
> "We use a token bucket rate limiter because constant-rate limiting amplified outages during the 2026-01 incident."

**Example — RIGHT in architecture.md:**
> "Rate Limiter sits between the Orchestrator and the LLM Client. Token bucket strategy — see [ADR-0007](../decisions/0007-token-bucket-rate-limiter.md)."

#### .context/decisions/NNNN-*.md — ADRs

**Boundary:** A single architectural or cross-cutting engineering decision per file. Captures *what* was decided and *why*, at the moment it was made. Immutable once written.
**Not here:** Description of the current shape (-> architecture.md) . Behavioural rules (-> design.md) . Schemas (-> data.md) . Naming definitions (-> vocabulary.md)

**Format** (minimum — most ADRs need only this):

```markdown
# NNNN: [Short title of the decision]

**Date:** YYYY-MM-DD
**Status:** Accepted

## Context
[1-2 sentences: what was the situation that forced a choice?]

## Decision
[1-2 sentences: what we decided.]

## Consequences
[1-3 bullets: what follows from this — what we accept, what we lose.]
```

**The three-question filter — write an ADR only when ALL THREE are true:**

1. **Hard to reverse?** Cost of changing your mind later is meaningful (quarter+ to swap, not a few-line change)
2. **Surprising without context?** A future reader looking at the code would wonder "why on earth did we do it this way?"
3. **Result of a real trade-off?** Genuine alternatives existed and were rejected for specific reasons

If any of the three is missing, skip. The bar is intentionally high. ADRs that don't pass the filter are exactly what creates dumping grounds.

**What qualifies:** Architectural shape ("event-sourced write model"). Integration patterns between subsystems. Technology choices that carry lock-in (database, message bus, auth). Boundary decisions ("Customer data owned by Customer subsystem"). Deliberate deviations from the obvious path. Constraints not visible in the code (compliance, partner SLAs).

**What doesn't qualify:** Library choices that are easily swapped. Coding patterns within a module. Configuration values (timeouts, retries). Conventions enforced automatically by linter or types.

**Status values:**
- `Accepted` — active state when written
- `Superseded by ADR-NNNN` — replaced; old ADR stays in place for history
- `Deprecated` — no longer relevant, no replacement (rare)

When superseding, write a new ADR referencing the old, then edit *only the status line* of the old. Never edit other content of an ADR after it's accepted.

**Numbering:** Sequential. Scan `.context/decisions/` for the highest existing number, increment by one. Never reuse numbers.

**Cross-references:** Other context files reference ADRs by short link rather than restating reasoning. Example in design.md or architecture.md:

> "Errors propagate via Result, never thrown. See [ADR-0007](../decisions/0007-result-pattern.md)."

See `lead/record-decision.md` for the full ADR playbook (loaded on demand when the Lead's Record Decision action fires).

#### data.md — What the data looks like

**Boundary:** Schemas, models, data contracts, concrete examples (actual JSON/YAML).
**Not here:** Behavioural rules using data (-> design.md) . Data flow direction (-> architecture.md) . Library choices (-> architecture.md)

All sections are project-specific — no mandatory sections. Create when relevant: Config Model (types, defaults, constraints) . Output/Storage Schemas . Inter-Component Data Contracts . API request/response shapes . Database schemas . Any project-specific schema.

**Notes:**
- Include concrete examples (actual JSON, actual YAML) for every schema
- This file lags behind design — schemas solidify during implementation
- Types and defaults here; behavioural effects in `design.md`
- Only add schemas when they're resolved — provisional schemas live as open questions in `design.md`
- Data models can't be designed directly from requirements or obligations. The bridge is entity lifecycles: `domain.md` describes how things work in the real world (stages, participants, time constraints), then `design.md` translates those into what the software tracks. If `domain.md` only describes obligations without concrete lifecycles, the domain research is incomplete

**Example — WRONG in data.md:**
> "The `status` field is used by resume logic to skip successful documents."

**Example — RIGHT in data.md:**
> `status`: string, enum `["success", "error", "pending"]` — see `design.md` Resume Behaviour for how this field is used.

#### domain.md — What the real world looks like *(optional file)*

**Boundary:** Real-world systems, entity types, relationships, lifecycles, processes. Independent of the software.
**Not here:** Canonical names and definitions of domain terms (-> vocabulary.md) . How the software uses domain knowledge (-> design.md) . Technical API access details (-> integrations.md) . Data schemas for modelling domain entities (-> data.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Domain Overview | What real-world system, why it matters for this project | Yes (if file exists) |

**Optional sections:** Entity Types & Relationships . Lifecycle & Processes . Cross-References & Linkages . Any domain-specific topic

**Notes:**
- **Optional file** — only create for projects with non-trivial domains
- **Naming and definitions live in `vocabulary.md`, not here.** This file owns *structural* knowledge — how entities work, how processes unfold, how things relate in the real world. When introducing a domain entity, define the canonical name in `vocabulary.md` first, then describe its structure here using that canonical name
- Researched iteratively as different project areas need domain understanding
- Can be revisited when new features touch new domain concepts
- Only verified domain knowledge goes here — uncertain claims live in `design.md` Open Questions

#### integrations.md — What we connect to

**Boundary:** External service APIs, auth models, tested behaviour, constraints, gotchas.
**Not here:** How your code connects to services (-> architecture.md) . Data schemas for API responses (-> data.md) . Implementation status (-> design.md)

**Optional sections:** One section per external service, added as services are identified

**Per-service, consider:** Auth (dev vs production) . API version/endpoints/regional constraints . Tested behaviour (with dates) . Constraints/limits . Pricing if design-relevant

**No mandatory sections.** All unresolved integration questions live in `design.md` Open Questions — integrations.md holds only confirmed behaviour.

**Notes:**
- Only confirmed behaviour goes here — assumptions and unresolved questions live in `design.md` Open Questions until verified
- Per-service maturity: services with "Tested behaviour" dates are reliable; services documented only from official docs need verification during implementation
- A local database might be 3 lines. A complex cloud API might need a full page. Document what matters

#### backlog.md — Future work

**Location:** `.context/project/backlog.md`

Concrete items surfaced during sprint work that aren't worth fixing now. Grouped by priority: before-production, next-time-we-touch-this, nice-to-have.

**Not here:** Unresolved truth discrepancies (-> `design.md` Open Questions or the appropriate owning file) . Raw questions or open decisions (-> `design.md` Open Questions)

### The Boundary Rule

> **If you changed it, would the user experience change, the code shape change, the shape of data change, is it about an external service, does it describe how the real world works, does it define what we *call* something, or does it record *why* a non-obvious choice was made?**
>
> - User experience -> `design.md`
> - Code shape (description) -> `architecture.md`
> - Data shape -> `data.md`
> - External service details -> `integrations.md`
> - Real-world domain knowledge -> `domain.md`
> - What we call something -> `vocabulary.md`
> - Why we chose X over Y (decision provenance) -> ADR in `.context/decisions/`

When in doubt, apply this test.

### Cross-File Overlaps

When a topic spans multiple files, one file **owns** the detail and others **reference** it:

| Overlap | How to split |
|---------|-------------|
| Vocabulary + Domain | `vocabulary.md` owns canonical names and one-line definitions . `domain.md` owns *structural* knowledge — how the entity works, its lifecycle, how it relates to other entities — using the canonical names |
| Vocabulary + everywhere else | `vocabulary.md` owns the term . Other files use the canonical name when describing behaviour, structure, schemas, etc. — they do not redefine it |
| Architecture + ADRs | `architecture.md` owns the *description* of the current shape (component map, layout, naming) . ADRs own the *reasoning* for why each significant piece exists or was chosen. Architecture cross-references ADRs; it does not restate their reasoning |
| ADRs + everywhere | An ADR captures a single decision with provenance. Other files cross-reference the ADR by short link rather than restating context, alternatives, or rationale |
| Domain + Design | `domain.md` owns how the real world works . `design.md` owns how the software uses that knowledge |
| Domain + Integrations | `domain.md` owns what an entity IS . `integrations.md` owns how to technically access it |
| Design + Data | `design.md` owns the behavioural rule . `data.md` owns the schema |
| Architecture + Data | `architecture.md` owns the component-shape description . `data.md` owns the data contract |
| Architecture + Integrations | `architecture.md` owns how your code connects . `integrations.md` owns what the service requires |

### Cross-Reference Format

Always use: `See design.md Section Name for [brief description].`

Always include: backtick filename, section name, and "for [what]" suffix. The suffix tells the reader whether the reference is worth following.

**Examples:**
- "Resume logic skips documents with status `success` — see `data.md` Result Schema for the full model."
- "STT Client wraps Google Cloud Speech V2 — see `integrations.md` Google Cloud Speech for API constraints."
- `status`: string, enum `["success", "error", "pending"]`. See `design.md` Resume Behaviour for how this field drives retry logic.

### Avoiding Duplication

Each fact has one owning file. Other files may reference it and include brief contextual mentions without restating the full detail. Some overlap between files is natural — the goal is to avoid *maintaining the same information in two places*, not to eliminate every passing mention.

**Acceptable:** Naming a technology while describing behaviour in design.md. Briefly noting what a domain concept means in data.md when describing a schema. Stating a core principle in each file with different framing.

**Not acceptable:** Fully restating the same specification, schema, or detailed explanation across files. If two files contain paragraphs covering the same topic in equal depth, one should own it and the other should cross-reference.

### Context File Maturity

Each file carries its own maturity signals. Read maturity from the content itself — no external tracking needed.

| File | How to read maturity | How it evolves |
|------|---------------------|----------------|
| `vocabulary.md` | Number of canonical terms with definitions = coverage. Recently Resolved Ambiguities entries = signs of active vocabulary work. Empty or missing file = no terminology discipline yet | Grows iteratively as terms are resolved during design, sprint, or Sharpen Vocabulary actions |
| `domain.md` | Sections with cited sources = researched. Empty/missing sections = unresearched | Iterative — revisited as different project areas need domain understanding |
| `integrations.md` | Per-service: "Tested behaviour" dates = reliable. No dates = assumed from docs | Services mature individually as they're tested during implementation |
| `design.md` | Open Questions count = maturity indicator. Content sections = decided | Constantly evolving. The living document. Never "done" |
| `architecture.md` | Component map populated with one-line responsibilities = current shape known. Cross-references to ADRs = decisions are recorded. Empty Component Map = structure not yet shaped | Stabilises once implementation begins. Revisited for fundamental changes or new components. Re-bloating with rationale is the failure mode — decisions belong in ADRs |
| `.context/decisions/*.md` | Number of accepted ADRs = decisions captured. Superseded chains = areas that have evolved. Empty `decisions/` early in a project is normal — ADRs are sparse | Grows as decisions arise that pass the three-question filter. Append-only — old ADRs remain as historical record even when superseded |
| `data.md` | Schemas with concrete examples = solid. Schemas with TBD fields = provisional | Lags behind design. Fills in during implementation as real data shapes emerge |

---

## Decisions Structure

Two layers — reference material and project record. There is no third "conventions" layer; patterns enforced automatically by linter, types, or sub-agent prompts don't need a separate doc.

### The Two-Layer Model

| Layer | Location | Purpose | When written |
|-------|----------|---------|-------------|
| **Handbook** | `standards/topics/*.md` within this skill | Production engineering patterns with tradeoffs and examples. Reference material. Project-independent | Maintained at the skill level — not edited during project work |
| **Project decisions (ADRs)** | `.context/decisions/NNNN-*.md` | One decision per file, numbered sequentially, immutable. Captures *why* a non-obvious, hard-to-reverse choice was made | When a decision arises that meets the three-question filter (see ADR section above) |

The handbook informs the discussion; the resulting decision — if it passes the filter — is recorded as an ADR. The Lead may reference handbook topics when grounding a design discussion, but nothing mandates when.

### When to write an ADR

When all three are true:

1. **Hard to reverse** — meaningful cost to change later
2. **Surprising without context** — a future reader would wonder "why did we do it this way?"
3. **Result of a real trade-off** — alternatives existed and were rejected

Naturally arising during:

- Design discussions that resolve a production concern with a non-obvious choice
- Sprint scoping when a cross-cutting question forces a project-level commitment
- Architectural shifts (component boundaries, technology lock-in)

If a topic comes up and **doesn't** pass the filter, don't write an ADR. Note the choice inline in the relevant context file (architecture.md component description, design.md behaviour, etc.) without ceremony. The filter is the whole point — bypassing it recreates the dumping-ground problem.

### Why one decision per file

Recording each decision as its own immutable file (rather than appending to a per-topic doc) gives every decision its own provenance — context, alternatives considered, date, status — and prevents the dumping-ground problem where a multi-decision doc loses the *why* behind individual entries as it gets edited over time. Code-level patterns enforced automatically (by linter, types, code-review sub-agent) don't get a separate doc.

---

## Diagram Policy

- **Format:** D2 is the standard diagram source format
- **Outputs:** Save both the `.d2` source file and a `.png` render
- **Authority:** Diagrams are human aids only. Text files remain the source of truth
- **When to create:** Only when the user explicitly asks — never generate diagrams automatically
- **Location:** Design diagrams go in `.context/wip/`. Sprint-local diagrams go in the sprint's `temp-diagrams/`
- **Reading:** Do not consult diagrams on startup. Only reference them when the user explicitly points to one
- **Skill:** Load `dev-diagrams` when doing any diagram work. It routes to the appropriate diagram skill (e.g., `dev-diagrams-d2` for D2)

---

## Research System

Research instructions and patterns live in `research/` within this skill:

```
research/
├── instructions.md           ← source tiering, verification tagging, output format
└── patterns/
    ├── domain-research.md    ← investigating real-world systems and regulations
    ├── api-exploration.md    ← testing API behaviour and reading official docs
    ├── library-evaluation.md ← assessing library fitness and maintenance
    └── standards-research.md ← investigating formal standards and specifications
```

**How to research:** Read `research/instructions.md` first. If a research pattern fits, read only the single relevant pattern file. If the research is a quick lookup that doesn't fit any pattern, follow the core rules (source tiering, verification tags) and use common sense.

**Inline vs sub-agent:** For quick lookups (1-2 web fetches), do the research directly. For deeper investigation, ask the user: "Should I research this myself or use a sub-agent? Sub-agent keeps the context cleaner but takes a moment." Default to sub-agent for anything requiring more than two web fetches. When dispatching a sub-agent, point it at instructions.md and the relevant pattern file.

**Recording findings:** Research returns structured, tagged findings. The Lead reviews findings and writes to context files per the boundary rule:
- Verified domain facts -> `domain.md`
- Verified API/service behaviour -> `integrations.md`
- Design decisions informed by research -> `design.md`
- Architecture decisions informed by research -> `architecture.md`
- Unverified claims -> `design.md` Open Questions (never record unverified claims as facts)

---

## Git Conventions

At the end of each session, after updating context files (and HANDOFF.md if Lead), commit changes to the current branch with a descriptive message. Examples:

```
planning: resolved auth approach, updated design + architecture
sprint: completed chunk 01, promoted integrations correction
```

- Don't create branches for context-only changes
- Don't push unless the user asks
