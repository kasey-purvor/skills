---
name: dev-project-planning
description: Use when starting a new project or picking up an existing design - guides collaborative design and architecture through user-directed brainstorming, production engineering expertise, and structured research before or between sprint work
---

# Project Planning & Design

## Overview

Guide project design from rough idea to sprint-ready specification, and reconcile durable docs as planning and sprint work alternate. This skill often starts before `dev-sprint-development`, but projects may move back and forth between the two.

The primary value of this skill is the **context files** it produces and maintains. These are living documents that evolve throughout the project lifecycle.

### How Design Evolves

Domain, Integrations, and Design are explored iteratively — each informs the others. You research the domain, which raises design questions, which send you to explore integrations, which reveal constraints that change the design, which sends you back to domain research. Follow the thread of understanding; don't force a sequence.

Architecture and Data solidify later, once design has enough substance to make structural decisions. The bridge is **entity lifecycles**: if `domain.md` can describe concrete state sequences (stages, participants, time constraints) for the key concepts, the project is ready for architecture and data model work. If it can only describe obligations or requirements without lifecycles, more domain work is needed first.

Not every project has a complex domain — simple tools may skip `domain.md` entirely. Start by framing the project in `design.md` at a high level: purpose, scope, user-visible workflow, and obvious constraints. Domain and integration research deepen that picture. Do not start architecture or data model work until the behaviour and constraints are concrete enough to support them.

---

## Session Flow

### First session (no `.context/project/` exists)

1. Create `.context/` folder structure and seed `design.md` from the template:
   ```bash
   mkdir -p .context/project .context/reference .context/wip && cp ~/.claude/skills/dev-project-planning/templates/design.md .context/project/
   ```
2. Create a `README.md` at the project root: 1-2 sentences describing what the project does, a status line (e.g., "Planning phase"), and links to the context files in `.context/project/`. Then forget about it — do not update the README unless the user explicitly asks.
3. Ask the user what they're building
4. Capture the project at a high level in `design.md` first: Purpose & Scope, Interface & Interactions, Configuration, and Core Workflow
5. Create additional context files from templates only when needed:
   - `domain.md` for non-trivial domains
   - `integrations.md` when external services or technical dependencies matter
   - `architecture.md` and `data.md` once design has enough substance to support structural and schema decisions

### Continuing session

1. Read existing context files and `.context/HANDOFF.md` (if it exists) silently for orientation
2. Ask: **"What are we working on this session?"**
3. Work: research, discuss, record decisions to the appropriate context files
4. Before ending: update HANDOFF.md, commit context files to current branch with a descriptive message. **mandatory**, always confirm with user before doing.  

**Do not** run a comprehensive review or gap analysis unless the user asks for one. Orient yourself from the files and follow the user's lead.

---

## Agent Posture

### Default (always on)

- **Follow the user's lead** on what to discuss and how deep to go
- **Research when asked**, record findings to the appropriate context file
- **Production engineering awareness** — when recommending patterns, explain WHY they're industry standard. What problem does it solve? What happens without it? How do production systems actually handle this? Bridge the gap between "works" and "production-grade" explicitly. Only raise concerns when they're genuinely important — not as a routine checklist
- **Ask clarifying questions** to ensure decisions are recorded precisely
- **Brainstorm one topic at a time** — one question per message, prefer multiple choice when possible, present 2-3 approaches with tradeoffs when there's a genuine choice. Lead with your recommendation and explain why
- **YAGNI** — don't add complexity for hypothetical future requirements. Be honest about what's needed now vs later. Three similar lines of code is better than a premature abstraction. When suggesting production patterns, clearly label what's "v1" vs "future enhancement"

### On-demand actions

These are triggered by the user, or **suggested by the agent when it seems appropriate**. When suggesting, be brief: "Want me to run a sprint prep check before we hand off?"

| Action | What it does | When to suggest |
|--------|-------------|-----------------|
| **Challenge mode** | Actively push back on decisions, propose alternatives, question assumptions, suggest simplifications | When the user seems unsure, says "what do you think?", "be honest", "be critical", "push back on this", or asks for your opinion on a decision |
| **Sprint prep** | Readiness check for transitioning to sprint work. Reviews context files for sufficiency: are they complete enough to build from? What's provisional? What open questions would block implementation? Determines whether the next handoff is a **vertical-slice entry** (enough clarity to build one thin slice safely) or a **broader sprint-ready entry** (the target area is mostly settled and can support wider chunking). Checks whether the upcoming work touches areas covered by `.context/standards/` decision files — if decisions exist but conventions.md doesn't yet have corresponding rules, notes that the sprint should establish those patterns and write convention entries as it goes. If no standards decisions exist for relevant areas, loads `dev-standards` to discuss with the user first | When the user mentions wanting to start implementation, or when most open questions are resolved and sprint work seems near |
| **Consistency check** | Dispatched as a **sub-agent** that reads all context files and verifies: cross-references between files are valid, boundary rules are followed (each fact stated once in its owning file), no duplication across files, content matches the rules defined in this skill (what belongs where, mandatory sections present, no guidance/meta-commentary in context files). Reports findings only — does not fix issues | When the user says "let's wrap up", at the end of any session, or after significant changes across multiple files |
| **Standards assessment** | Loads `dev-standards` and uses whichever mode fits the current state of the project (design-time if planning is in progress, audit if design or code already exists). The standards skill drives the assessment — this action just triggers it and ensures outputs land in `.context/standards/`. Does not need to cover all topics in one session | When the user asks about production concerns, hardening, or "what are we missing?". When design discussions naturally raise production questions (error handling, security, data validation). During sprint prep if `.context/standards/` is empty or incomplete for the upcoming work |
| **Source review** | Re-read primary source material (requirements docs, CSVs, specs, stakeholder notes) independently of existing context files. Compare what the source says against what's been captured. Identify concepts, signals, or structural intent that prior analysis missed or flattened | When the user questions whether context files fully represent the source material, when a new agent picks up someone else's analysis, or when the user says something feels incomplete |

---

## Folder Structure

```
.context/
├── project/          ← living documentation (agent reads project/*.md on startup)
│   ├── design.md, architecture.md, data.md, domain.md, integrations.md
│   └── implementation/   ← NOT read on startup (conventions.md, backlog.md)
├── standards/        ← production engineering decisions (read on demand, written during standards assessment)
├── reference/        ← source material: CSVs, meeting notes, stakeholder docs (read on demand)
├── wip/              ← draft D2 diagrams plus PNG renders, exploratory notes, visual aids (read on demand)
└── HANDOFF.md        ← inter-session/inter-skill context bridge
```

- **`project/`** — the authoritative context files. On startup, read `project/*.md` only (the root-level files). **Do NOT read** `project/implementation/`, `reference/`, `standards/`, or `wip/` on startup — these are accessed on demand only.
- **`project/implementation/`** — files that support sprint work: `conventions.md` (coding standards and patterns established during sprints) and `backlog.md` (deferred items from sprints). Read during sprint prep or when explicitly asked.
- **`standards/`** — production engineering decision files, one per topic (error handling, configuration, data integrity, etc.). Created during a standards assessment using the `dev-standards` skill. Records what was decided, deferred, and ruled out. Read during sprint prep or when a production concern comes up. See the `dev-standards` skill for the three-layer model (skill topics → decision files → conventions).
- **`reference/`** — static input material that informed the planning. Does not change. Read on demand (e.g., during a "source review" action), not on startup.
- **`wip/`** — work-in-progress artifacts produced during sessions that aren't documentation-quality. Draft D2 diagrams plus PNG renders, scratch analysis, exploratory notes. Human aids only — never authoritative. Items either get promoted to `project/` when mature, or discarded.

### Diagram Policy

- **Format:** D2 is the standard diagram source format
- **Outputs:** Save both the `.d2` source file and a `.png` render by default
- **Authority:** Diagrams are human aids only. Text context files remain the source of truth
- **When to create:** Only when the user explicitly asks for a diagram
- **Default location:** Save planning diagrams in `.context/wip/`
- **Reading:** Do not consult diagrams on startup. Only look at them when the user explicitly points you to one

---

## Context Files

### General Principles

- **Nothing is permanently locked** — all decisions can be revisited as the project evolves
- **Sections are created when there's content**, not pre-emptively. Don't create empty sections
- **Section menus are not exhaustive** — suggest new sections not on the menu if the project needs them, with user approval
- **Cross-reference by section name**: ``See `design.md` Configuration for [what's there]``
- **One fact, one owner** — a fact is stated once in its owning file. Other files reference it but don't restate it
- **Context files are pure content** — no guidance blocks, no HTML comments, no meta-commentary. All guidance lives in this skill file

### design.md — What we're building and why

**Boundary:** Behaviour, workflows, business rules, config effects, user experience.
**Not here:** Library/pattern/class names (→ architecture.md) · JSON/schemas/examples (→ data.md) · External API details (→ integrations.md) · Domain knowledge (→ domain.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Purpose & Scope | What we're building, why, use cases, out-of-scope | Yes |
| Interface & Interactions | What the user types and sees — CLI, API, library surface | Yes |
| Configuration | What each config key DOES (types/defaults in data.md) | Yes |
| Core Workflow | Happy path end-to-end | Yes |
| Open Questions | Unresolved decisions with context and options | Yes (always second-to-last) |
| Deferred Items | Confirmed non-blocking, with reasoning | Yes (always last) |

**Optional sections** (create when relevant): Error handling · Resume/repeat behaviour · Console output/UX · Cost/resource management · Any project-specific topic

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

### architecture.md — How it's built and with what

**Boundary:** Design patterns and rationale, concurrency model, library/technology choices, structural constraints.
**Not here:** User workflows/business rules (→ design.md) · Schemas/examples (→ data.md) · External API details (→ integrations.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| System Overview | System type, language, packaging, entry point | Yes |
| Component Map | Components with responsibilities, dependency tree, rationale subsections | Yes |

**Optional sections:** Concurrency Model · Data Flow · External Dependencies · Key Constraints · Resolved Architectural Questions · Any project-specific topic

**Notes:**
- **Only resolved decisions** — if it's not settled, it stays in `design.md` Open Questions even if the topic is architectural
- Stabilises once implementation begins; revisited when fundamental changes are needed or new components are added
- **Naming conventions are mandatory.** When discussing file layout or component structure, establish explicit naming rules before naming any files. The convention should cover: file casing (language-appropriate defaults — see global CLAUDE.md), prefix pattern (what comes before the suffix — typically an entity noun), suffix inventory (the complete list of role suffixes used in the project, e.g., `.model.ts`, `.repository.ts`), and folder grouping rationale (by feature, by layer, or hybrid — and the threshold for when to split). Record the agreed convention in a dedicated section of architecture.md. All subsequent file naming in sprint work must follow it. If a new file doesn't fit the convention, that's a signal to revisit the convention, not to invent a one-off name

**Example — WRONG in architecture.md:**
> "Output at `output/{key}/run_{N}/` containing `config.yaml`, `results/{doc_id}.json`, `aggregation.json`."

**Example — RIGHT in architecture.md:**
> "Result Writer generates disk output in the structure defined in `data.md` Output Schemas."

### data.md — What the data looks like

**Boundary:** Schemas, models, data contracts, concrete examples (actual JSON/YAML).
**Not here:** Behavioural rules using data (→ design.md) · Data flow direction (→ architecture.md) · Library choices (→ architecture.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| *(none)* | All sections are project-specific | — |

**Optional sections:** Config Model (types, defaults, constraints) · Output/Storage Schemas · Inter-Component Data Contracts · API request/response shapes · Database schemas · Any project-specific schema

**Notes:**
- Include concrete examples (actual JSON, actual YAML) for every schema
- This file lags behind design — schemas solidify during implementation
- Types and defaults here; behavioural effects in `design.md`
- Only add schemas when they're resolved — provisional schemas live as open questions in `design.md`
- Data models can't be designed directly from requirements or obligations. The bridge is entity lifecycles: `domain.md` describes how things work in the real world (stages, participants, time constraints), then `design.md` translates those into what the software tracks. If `domain.md` only describes obligations without concrete lifecycles, the domain research is incomplete — re-dispatch before attempting data model design

**Example — WRONG in data.md:**
> "The `status` field is used by resume logic to skip successful documents."

**Example — RIGHT in data.md:**
> `status`: string, enum `["success", "error", "pending"]` — see `design.md` Resume Behaviour for how this field is used.

### implementation/ subfolder — Implementation support files

**Location:** `.context/project/implementation/`
**Not read on startup.** Only accessed on demand — during sprint prep or when explicitly asked.

Contains files that support sprint work but aren't needed for planning sessions:

- **conventions.md** — Actionable rules for writing code in this codebase. Terse entries (section heading + 3-5 rules) covering patterns like error handling, validation, logging, config access. Written during any sprint when a pattern is established or changed — not populated upfront. The `dev-standards` skill topics are the reference material; standards decision files in `.context/standards/` record what was chosen; conventions.md records how those choices look in practice. See the `dev-standards` skill for the full three-layer model (skill topics → decision files → conventions).
- **backlog.md** — Items surfaced during sprint work that aren't worth fixing now. Grouped by priority: before-production, next-time-we-touch-this, nice-to-have. Primarily written by sprint roles; the project planner reads it when planning future sprints.

### domain.md — What the real world looks like *(optional file)*

**Boundary:** Real-world systems, entity types, relationships, lifecycles, terminology. Independent of the software.
**Not here:** How the software uses domain knowledge (→ design.md) · Technical API access details (→ integrations.md) · Data schemas for modelling domain entities (→ data.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Domain Overview | What real-world system, why it matters for this project | Yes (if file exists) |
| Terminology & Glossary | Domain-specific terms with precise meanings | Yes (if file exists) |

**Optional sections:** Entity Types & Relationships · Lifecycle & Processes · Cross-References & Linkages · Any domain-specific topic

**Notes:**
- **Optional file** — only create for projects with non-trivial domains
- Researched iteratively as different project areas need domain understanding
- Can be revisited when new features touch new domain concepts
- Only verified domain knowledge goes here — uncertain claims live in `design.md` Open Questions

### integrations.md — What we connect to

**Boundary:** External service APIs, auth models, tested behaviour, constraints, gotchas.
**Not here:** How your code connects to services (→ architecture.md) · Data schemas for API responses (→ data.md) · Implementation status (→ design.md)

| Section | Purpose | Mandatory? |
|---------|---------|-----------|
| Open Integration Questions | Unresolved questions that may affect design | Yes |

**Optional sections:** One section per external service, added as services are identified

**Per-service, consider:** Auth (dev vs production) · API version/endpoints/regional constraints · Tested behaviour (with dates) · Constraints/limits · Pricing if design-relevant

**Notes:**
- Only confirmed behaviour goes here — assumptions live in `design.md` Open Questions until verified
- Per-service maturity: services with "Tested behaviour" dates are reliable; services documented only from official docs need verification during implementation
- A local database might be 3 lines. A complex cloud API might need a full page. Document what matters

### HANDOFF.md — Session context bridge

**Location:** `.context/HANDOFF.md`
**Written by:** Whichever skill ran last (project planning or sprint development)
**Read by:** Whichever skill runs next

**Contents — write these sections each time:**
- **Handoff written on / last session type** — date plus `project-planning` or `sprint-development`
- **Completed this session / durable changes made** — decisions made, files updated, research completed, promotions performed
- **Expected next session / entry mode** — planning continuation, vertical-slice sprint entry, or broader sprint-ready entry
- **Current active area / provisional areas to treat carefully** — what's active, what's provisional (e.g., "architecture.md Data Flow is provisional, depends on auth approach resolution")
- **Unreconciled durable-file updates / carry-forward pointers** — durable-truth changes that still need reconciliation, plus brief pointers to owned items that the next session must notice
- **Immediate next-session pickup notes** — what to pick up next, what needs attention first

No template file — the agent writes HANDOFF.md from these instructions each session. This is the dedicated inter-session and inter-skill bridge. Both project planning and sprint development read and write it for continuity, but it is **not** a source-of-truth file. Durable truth must live in its owning `project/*.md`, `.context/standards/*.md`, or `project/implementation/*.md` file. If an item already lives in `PLAN.md`, `backlog.md`, or another owning file, HANDOFF.md should point to it briefly rather than duplicating it as a second owner.

---

## Context File Maturity

Each file carries its own maturity signals. No external tracking is needed — the agent reads maturity from the content itself.

| File | How to read maturity | How it evolves |
|------|---------------------|----------------|
| `domain.md` | Sections with cited sources = researched. Empty/missing sections = unresearched | Iterative — revisited as different project areas need domain understanding |
| `integrations.md` | Per-service: "Tested behaviour" dates = reliable. No dates = assumed from docs | Services mature individually as they're tested during implementation |
| `design.md` | Open Questions count = maturity indicator. Content sections = decided | Constantly evolving. The living document. Never "done" |
| `architecture.md` | Sections with rationale = resolved. Empty/missing sections = not yet decided | Stabilises once implementation begins. Revisited for fundamental changes or new components |
| `data.md` | Schemas with concrete examples = solid. Schemas with TBD fields = provisional | Lags behind design. Fills in during implementation as real data shapes emerge |

---

## The Boundary Rule

> **If you changed it, would the user experience change, the code structure change, the shape of data change, is it about an external service, or does it describe how the real world works?**
>
> - User experience → `design.md`
> - Code structure → `architecture.md`
> - Data shape → `data.md`
> - External service details → `integrations.md`
> - Real-world domain knowledge → `domain.md`

This is the single most important rule for maintaining context files. When in doubt, apply this test.

### Cross-File Overlaps

When a topic spans multiple files, one file **owns** the detail and others **reference** it:

| Overlap | How to split |
|---------|-------------|
| Domain + Design | `domain.md` owns how the real world works · `design.md` owns how the software uses that knowledge |
| Domain + Integrations | `domain.md` owns what an entity IS · `integrations.md` owns how to technically access it |
| Design + Data | `design.md` owns the behavioural rule · `data.md` owns the schema |
| Architecture + Data | `architecture.md` owns the pattern/library choice · `data.md` owns the data contract |
| Architecture + Integrations | `architecture.md` owns how your code connects · `integrations.md` owns what the service requires |

### Cross-Reference Format

Always use: ``See `filename.md` Section Name for [brief description].``

Always include: backtick filename, section name, and "for [what]" suffix. The suffix tells the reader whether the reference is worth following.

**Examples:**
- "Resume logic skips documents with status `success` — see `data.md` Result Schema for the full model."
- "STT Client wraps Google Cloud Speech V2 — see `integrations.md` Google Cloud Speech for API constraints."
- `status`: string, enum `["success", "error", "pending"]`. See `design.md` Resume Behaviour for how this field drives retry logic.

### Avoiding Duplication

A fact should be stated **once** in its owning file. Other files may reference it but must not restate it. If you find yourself writing the same information in multiple files, stop and apply the boundary rule.

**Acceptable:** Stating a core principle once in each file with different framing (design: "what the user relies on", architecture: "what the code must enforce", data: "what the schema guarantees").

**Not acceptable:** Restating the same specification, schema, or policy across files.

---

## Research

Research instructions and pattern files live in `research/` within this skill's directory:

```
research/
├── instructions.md           ← source tiering, verification tagging, output format, when to skip patterns
└── patterns/
    ├── domain-research.md    ← investigating real-world systems and regulations
    ├── api-exploration.md    ← testing API behaviour and reading official docs
    ├── library-evaluation.md ← assessing library fitness and maintenance
    └── standards-research.md ← investigating formal standards and specifications (W3C, ISO, industry consortiums)
```

**How to research:** Read `research/instructions.md` first. If a pattern fits, read **only the single relevant pattern file**. If the research doesn't fit any pattern — a quick lookup, a straightforward question — just follow the core rules (source tiering, verification tags) and use common sense. The patterns are guides, not gates.

**Inline vs sub-agent:** For quick lookups (1-2 web fetches), follow the instructions directly. For deeper investigation, ask the user: "Should I research this myself or use a sub-agent? Sub-agent keeps the context cleaner but takes a moment." Default to sub-agent for anything requiring more than two web fetches. When dispatching a sub-agent, point it at the same two files (instructions.md + the relevant pattern).

**Recording findings:** The agent doing the research (whether inline or sub-agent) returns structured, tagged findings. The planning agent always reviews findings and writes to context files per the boundary rule:
- Verified domain facts → `domain.md`
- Verified API/service behaviour → `integrations.md`
- Design decisions informed by research → `design.md`
- Architecture decisions informed by research → `architecture.md`
- Unverified claims → `design.md` Open Questions (never record unverified claims as facts in `domain.md` or `integrations.md`)

---

## Git

At the end of each session, after updating HANDOFF.md and context files, commit the changes to the current branch with a descriptive message. Example:

```
planning: resolved auth approach, updated design + architecture
```

Don't create branches for context-only changes. Don't push unless the user asks.

---

## Handoff to Sprint Development

The user decides when to start sprint work. This skill does not gate that decision — the user may want to build before all context files are mature, and that's expected. Projects often alternate between planning and building as implementation reveals new information.

Use one of these entry modes when handing off:

- **Vertical-slice entry** — enough clarity exists to build one thin slice safely. `design.md` describes the slice's purpose and workflow, the touched area has enough naming/structure to avoid random invention, and any major assumptions are explicitly marked provisional.
- **Broader sprint-ready entry** — the target area is mostly settled. The workflows, structure, contracts, and relevant standards decisions for the upcoming work are documented or consciously deferred, so sprint can scope larger chunks with less design churn.

When the user decides to move to sprint work, update HANDOFF.md:

1. Set **Expected next session / entry mode** so it clearly says sprint work and which entry mode applies
2. Update **Current active area / provisional areas to treat carefully** with any context files/sections that are still provisional (e.g., "architecture.md Data Flow is provisional — depends on how the batch endpoint behaves")
3. Include any open questions that the sprint might resolve through implementation in **Immediate next-session pickup notes**
4. Include any durable-truth changes or promotions that are still pending in **Unreconciled durable-file updates / carry-forward pointers** so sprint can reconcile them deliberately

The Sprint Development Manager reads HANDOFF.md first, then the authoritative context files as needed. HANDOFF.md tells the Manager what's reliable, what's provisional, and what still needs reconciliation. Context files should be self-contained — the Manager should not need to read planning session history to understand what's being built.

### Returning from sprint

When the user returns from sprint work, read HANDOFF.md (which the sprint Manager updated at sprint end). Sprint may already have promoted durable truth directly into the appropriate project or standards files with user confirmation. Use HANDOFF.md to see what changed, what remains provisional, and what still needs reconciliation. Incorporate unresolved findings into the appropriate owning files rather than letting HANDOFF.md become the place where truth lives.

---

## What This Skill Does NOT Do

| Don't | Why |
|-------|-----|
| Create sprint files, PLAN.md, or ACTIVE-SPRINT | That's `dev-sprint-development` |
| Write implementation plans or code | This is design phase |
| Run gap analysis automatically | On-demand only, when user requests or agent suggests |
| Assume what the user wants to discuss | Ask first, every session |
| Add features the user didn't ask about | YAGNI — user decides scope |
| Accept "it's fine" without thinking critically | Your job is to find problems before implementation does |
| Record unverified claims as facts | Unverified → `design.md` Open Questions |
| Put guidance or meta-commentary in context files | All guidance lives in this skill file |
| Update the README unless explicitly asked | Created once during first session, then left alone |
| Generate diagrams automatically | Diagrams are on-demand only — user must ask for them |

---

## Skills

**Load on-demand:**
- `dev-brainstorming` → for structured design conversations (one topic at a time, options with tradeoffs)
- `dev-standards` → when production engineering concerns arise. The standards skill has its own modes (design-time, audit, implementation reference) and determines how to apply itself based on context. Its outputs go to `.context/standards/` (decision files). Conventions.md is written during sprints as patterns are implemented, not during planning. The planning skill's role is to know the standards skill exists and suggest loading it when production concerns come up — not to prescribe how or when standards are applied.
- `dev-diagrams` → only when the user explicitly asks for a diagram. Use D2 and save both `.d2` and `.png` outputs by default. Output goes to `.context/wip/` by default. Diagrams are human aids and never replace the text context files as source of truth. Never generate diagrams automatically
