# Project Work

A unified skill for designing and building software projects. Covers the full lifecycle from early design through implementation.

## Roles

| Role | Focus | Module |
|------|-------|--------|
| **Lead** | Design, research, chunk scoping, sprint management, durable truth ownership | `lead/lead.md` |
| **Implementer** | Detailed implementation plans, tactical gap-filling, post-chunk review | `sprint/implementer.md` |
| **Junior Developer** | Execute implementation plans exactly | `sprint/junior.md` |

## Standards

Production engineering standards (`standards/`) are not a role. They are a handbook consulted on-demand when production engineering questions arise — error handling, security, resilience, testing, etc. See "Standards as Handbook" below.

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
  design.md                                   │
  architecture.md                             ▼
  data.md                            Implementer writes implementation plans
  domain.md                                   │
  integrations.md                             ▼
  .context/standards/*.md            Junior Developer executes
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
- **Bridges** (HANDOFF.md) carry context between sessions. They point to truth but do not contain it.
- **Retrospectives** (SPRINT-SUMMARY.md) record what happened during a sprint. They are not read on startup and do not drive decisions — they exist for historical reference only.

### Entry Modes

When the Lead transitions from design to sprint, it uses one of two entry modes:

- **Vertical-slice entry** — enough clarity exists to build one thin slice safely. Core workflow is described, the touched area has enough structure to avoid guessing, and any major assumptions are explicitly marked provisional.
- **Broader sprint-ready entry** — the target area is mostly settled. Workflows, structure, contracts, and relevant standards decisions are documented or consciously deferred.

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
│   ├── design.md
│   ├── architecture.md
│   ├── data.md
│   ├── domain.md                    (optional)
│   ├── integrations.md
│   └── implementation/
│       ├── conventions.md
│       └── backlog.md
├── standards/
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
| `design.md` | What we're building and why — behaviour, workflows, business rules, user experience | Durable truth |
| `architecture.md` | How it's built — patterns, libraries, structure, naming conventions | Durable truth |
| `data.md` | What the data looks like — schemas, models, contracts, concrete examples | Durable truth |
| `domain.md` | What the real world looks like — entities, lifecycles, terminology *(optional)* | Durable truth |
| `integrations.md` | What we connect to — external APIs, auth, tested behaviour, constraints | Durable truth |
| `conventions.md` | How we write code — terse actionable rules for implemented patterns | Durable truth |
| `backlog.md` | Future work — concrete items deferred during sprints, grouped by priority | Durable truth |
| `.context/standards/*.md` | Cross-cutting engineering decisions — one file per topic (error handling, security, etc.) | Durable truth |
| `PLAN.md` | Sprint execution plan — chunk scopes, sprint goal, guardrails | Execution artifact |
| `CURRENT-STATE.md` | Sprint working memory — progress, blockers, deviations, promotion queue | Execution artifact |
| `implementation/*.md` | Chunk implementation plans — exact tasks and steps for the Junior Developer | Execution artifact |
| `SPRINT-SUMMARY.md` | Sprint retrospective — outcomes, what was built, carry-forward items | Execution artifact |
| `ACTIVE-SPRINT` | Pointer to current sprint folder | Execution artifact |
| `HANDOFF.md` | Session bridge between Lead sessions — what changed, what's next, what's provisional | Bridge (Lead-only) |
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

#### architecture.md — How it's built and with what

**Boundary:** Design patterns and rationale, concurrency model, library/technology choices, structural constraints.
**Not here:** User workflows/business rules (-> design.md) . Schemas/examples (-> data.md) . External API details (-> integrations.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| System Overview | System type, language, packaging, entry point | Yes |
| Component Map | Components with responsibilities, dependency tree, rationale subsections | Yes |

**Optional sections:** Concurrency Model . Data Flow . External Dependencies . Key Constraints . Resolved Architectural Questions . Any project-specific topic

**Notes:**
- **Only resolved decisions** — if it's not settled, it stays in `design.md` Open Questions even if the topic is architectural
- Stabilises once implementation begins; revisited when fundamental changes are needed or new components are added
- **Naming conventions are mandatory.** When discussing file layout or component structure, establish explicit naming rules before naming any files. The convention should cover: file casing (language-appropriate defaults), prefix pattern (what comes before the suffix — typically an entity noun), suffix inventory (the complete list of role suffixes used in the project, e.g., `.model.ts`, `.repository.ts`), and folder grouping rationale (by feature, by layer, or hybrid — and the threshold for when to split). Record the agreed convention in a dedicated section of architecture.md. All subsequent file naming must follow it. If a new file doesn't fit the convention, that's a signal to revisit the convention, not to invent a one-off name

**Example — WRONG in architecture.md:**
> "Output at `output/{key}/run_{N}/` containing `config.yaml`, `results/{doc_id}.json`, `aggregation.json`."

**Example — RIGHT in architecture.md:**
> "Result Writer generates disk output in the structure defined in `data.md` Output Schemas."

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

**Boundary:** Real-world systems, entity types, relationships, lifecycles, terminology. Independent of the software.
**Not here:** How the software uses domain knowledge (-> design.md) . Technical API access details (-> integrations.md) . Data schemas for modelling domain entities (-> data.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Domain Overview | What real-world system, why it matters for this project | Yes (if file exists) |
| Terminology & Glossary | Domain-specific terms with precise meanings | Yes (if file exists) |

**Optional sections:** Entity Types & Relationships . Lifecycle & Processes . Cross-References & Linkages . Any domain-specific topic

**Notes:**
- **Optional file** — only create for projects with non-trivial domains
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

#### conventions.md — How we write code *(implementation support)*

**Location:** `.context/project/implementation/conventions.md`

Actionable rules for writing code in this codebase. Terse entries (section heading + 3-5 rules) covering patterns like error handling, validation, logging, config access. Written during sprints when a pattern is established or changed — not populated upfront during design.

**Not here:** Project-level decisions about which approach to use (-> `.context/standards/`) . Architecture or component structure (-> architecture.md) . Teaching or justification (-> standards topic files)

#### backlog.md — Future work *(implementation support)*

**Location:** `.context/project/implementation/backlog.md`

Concrete items surfaced during sprint work that aren't worth fixing now. Grouped by priority: before-production, next-time-we-touch-this, nice-to-have.

**Not here:** Unresolved truth discrepancies (-> `design.md` Open Questions or the appropriate owning file) . Raw questions or open decisions (-> `design.md` Open Questions)

#### .context/standards/*.md — Cross-cutting engineering decisions

**Boundary:** Project-wide decisions about how to handle cross-cutting concerns — error handling strategy, logging approach, security posture, testing philosophy. These answer: "How does this project handle [X] across the board?"

**Not here:** Component-specific structure decisions (-> architecture.md) . Feature behaviour or business rules (-> design.md) . Data shapes (-> data.md) . Code patterns already implemented (-> conventions.md)

One file per topic, mirroring the standards handbook structure. Each file uses: Decided / Deferred / Not Applicable sections. See "Standards as Handbook" for the full three-layer model.

### The Boundary Rule

> **If you changed it, would the user experience change, the code structure change, the shape of data change, is it about an external service, or does it describe how the real world works?**
>
> - User experience -> `design.md`
> - Code structure -> `architecture.md`
> - Data shape -> `data.md`
> - External service details -> `integrations.md`
> - Real-world domain knowledge -> `domain.md`

When in doubt, apply this test.

### Cross-File Overlaps

When a topic spans multiple files, one file **owns** the detail and others **reference** it:

| Overlap | How to split |
|---------|-------------|
| Domain + Design | `domain.md` owns how the real world works . `design.md` owns how the software uses that knowledge |
| Domain + Integrations | `domain.md` owns what an entity IS . `integrations.md` owns how to technically access it |
| Design + Data | `design.md` owns the behavioural rule . `data.md` owns the schema |
| Architecture + Data | `architecture.md` owns the pattern/library choice . `data.md` owns the data contract |
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
| `domain.md` | Sections with cited sources = researched. Empty/missing sections = unresearched | Iterative — revisited as different project areas need domain understanding |
| `integrations.md` | Per-service: "Tested behaviour" dates = reliable. No dates = assumed from docs | Services mature individually as they're tested during implementation |
| `design.md` | Open Questions count = maturity indicator. Content sections = decided | Constantly evolving. The living document. Never "done" |
| `architecture.md` | Sections with rationale = resolved. Empty/missing sections = not yet decided | Stabilises once implementation begins. Revisited for fundamental changes or new components |
| `data.md` | Schemas with concrete examples = solid. Schemas with TBD fields = provisional | Lags behind design. Fills in during implementation as real data shapes emerge |

---

## Standards as Handbook

The standards skill is a reference handbook — not a role, not a phase. It contains production engineering knowledge organised by topic: error handling, security, resilience, testing, data integrity, and others. Each topic teaches the concept from the ground up, explains tradeoffs, and shows code examples.

It is consulted on-demand when production engineering questions arise during design or sprint work. It is never loaded in bulk — read only the topic relevant to the current discussion.

### The Three-Layer Model

| Layer | Location | Purpose | When written |
|-------|----------|---------|-------------|
| **Handbook topics** | `standards/topics/*.md` | Teach concepts, show patterns, explain tradeoffs. Project-independent | Permanent reference — part of the skill |
| **Project decision files** | `.context/standards/*.md` | Record what was decided, deferred, or ruled not applicable for this project | During design or sprint scoping, when a cross-cutting concern is discussed |
| **Conventions** | `.context/project/implementation/conventions.md` | Terse actionable rules for how decisions look in code | During sprints, when a pattern is first implemented or changed |

Each layer is progressively more specific and more actionable. Handbook topics inform decisions (recorded in project decision files). Decisions get implemented in code. The patterns that emerge get recorded as conventions.

### When to Consult Standards

- During design when the discussion naturally raises a production concern ("how should we handle errors?", "what about retries?")
- During sprint scoping when the Lead or Implementer hits a question about how to handle a cross-cutting concern
- During sprint prep to check whether upcoming work touches areas without decisions yet
- When the user asks about production hardening, security, or "what are we missing?"

### Project Decision File Format

Each project decision file in `.context/standards/` uses:

```markdown
# [Topic Name] — Project Decisions

## Decided
- [Concrete decisions with chosen tools, patterns, and project-specific details]

## Deferred
- [Decisions intentionally postponed, with reason and revisit trigger]

## Not Applicable
- [Topics considered but determined not relevant, with brief reason]
```

Not every topic needs a project file. If a topic isn't relevant, either omit the file entirely or include a one-liner explaining why it was skipped.

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
