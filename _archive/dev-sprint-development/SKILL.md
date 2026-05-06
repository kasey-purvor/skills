---
name: dev-sprint-development
description: Use at the start of every development session - establishes .context/ folder structure, enforces skill usage, tracks progress via CURRENT-STATE.md
---

# Sprint Development

## Overview

Entry point for all sprint development work. Defines three roles with clear constraints on what each can and cannot do. User supervises all roles and coordinates between them.

**On initialization, ask:** "What's my role, and what's the current state of the work?"

**Then read your role file** at `~/.claude/skills/dev-sprint-development/roles/{role}.md` before proceeding:
- Manager → `roles/manager.md`
- Implementer → `roles/implementer.md`
- Junior Developer → `roles/junior-developer.md`

---

## Roles

| Role | Focus | Persistence |
|------|-------|-------------|
| **Manager** | Design, chunking, oversight | Long-lived (whole sprint) |
| **Implementer** | Detailed plans, gap-filling, review | Medium (multiple chunks) |
| **Junior Developer** | Execute plans exactly | Ephemeral (single plan execution) |

### Skills by Role

Skills are either **Init** (load immediately on initialization, before any work) or **On-demand** (load when triggered by a specific situation). Init skills shape how the role thinks about all work. On-demand skills are procedures invoked at specific moments.

| Skill | Manager | Implementer | Junior Developer |
|-------|---------|-------------|------------------|
| `dev-writing-plans` | - | **Init** | - |
| `dev-executing-plans` | - | - | **Init** |
| `dev-test-driven-development` | - | **Init** | **Init** |
| `dev-systematic-debugging` | - | On-demand | **Init** |
| `dev-verification-before-completion` | On-demand | On-demand | **Init** |
| `dev-brainstorming` | On-demand | On-demand | - |

---

## Folder Structure

```
.context/
├── project/
│   ├── design.md
│   ├── architecture.md
│   ├── data.md
│   ├── domain.md                 (optional — for projects with non-trivial domains)
│   ├── integrations.md
│   └── implementation/           (not read on startup — accessed on demand)
│       ├── conventions.md
│       └── backlog.md
├── standards/                    (project-specific production engineering decisions)
├── sprints/
│   ├── YYYY-MM-DD-<sprint-name>/
│   │   ├── PLAN.md
│   │   ├── CURRENT-STATE.md
│   │   ├── implementation/
│   │   │   ├── 01-<chunk-name>.md
│   │   │   └── ...
│   │   ├── temp-diagrams/
│   │   │   └── (temporary D2 diagrams plus PNG renders — human aids only, not source of truth)
│   │   └── SPRINT-SUMMARY.md
│   └── ...
├── HANDOFF.md                    (inter-session/inter-skill context bridge)
└── ACTIVE-SPRINT
```

**ACTIVE-SPRINT:** Contains full path to current sprint from project root (e.g., `.context/sprints/2026-02-03-user-auth/`). Skills read this file and use the path directly without modification.

**ACTIVE-SPRINT lifecycle:**
- **Created** by the Manager when a new sprint starts (before any chunks are scoped)
- **Persists** throughout the sprint and after the sprint ends — it is NOT deleted when the sprint completes
- **Overwritten** when the next sprint starts (the Manager writes the new sprint path, replacing the old one)

This means ACTIVE-SPRINT always points to the most recent sprint. It is used by sprint roles to locate the current sprint folder.

## Sprint Startup

Only the **Manager** starts a sprint. Use this when there is no current sprint worth continuing, or when the user explicitly wants to start a new sprint.

1. Confirm whether the session is continuing the sprint named in `.context/ACTIVE-SPRINT` or starting a new one. Do not create a new sprint just because a new session started.
2. Read `.context/HANDOFF.md` and the relevant durable files to understand what is ready, what is provisional, and whether the sprint is entering as a **vertical-slice** or **broader sprint-ready** effort.
3. Agree with the user on the sprint name and the one-sentence sprint goal.
4. Create `.context/sprints/YYYY-MM-DD-<sprint-name>/` with:
   - `PLAN.md`
   - `CURRENT-STATE.md`
   - `implementation/`
   - `temp-diagrams/`
5. Write the new sprint path into `.context/ACTIVE-SPRINT`.
6. Initialize `CURRENT-STATE.md` from the template with the sprint goal, an accurate status, and no fake in-progress chunk.
7. Seed `PLAN.md` with the minimum shape below before defining any detailed chunk scopes.

### Minimum Shape of a New `PLAN.md`

A new sprint plan does **not** need fully scoped chunks yet. It is acceptable if it contains this minimum structure:

```markdown
# Sprint Plan: [Sprint Name]

**Sprint Goal:** [one sentence]
**Entry Mode:** vertical-slice | broader sprint-ready

## Current Active Sprint Focus

## Scope Guardrails / Do-Not-Expand Boundaries

## Durable Files / Sections This Sprint Depends On

## Planned Chunks Awaiting Detailed Scope
- Chunk 01: [name]

## Sprint-Resolved Execution-Relevant Details

## Sprint-Local Open Questions

## Sprint-Local Deferred Items
```

Rules:

- `Planned Chunks Awaiting Detailed Scope` starts as a short list of chunk names or very short scope labels only
- A chunk gets a full `## Chunk NN Scope: <name>` section only after the Manager scopes it with the user
- `Durable Files / Sections This Sprint Depends On` should point to the durable files or sections the sprint depends on; it should not restate all of their contents
- `Sprint-Local Deferred Items` is sprint-local. If an item needs to outlive the sprint, move it to `backlog.md` or the appropriate durable file

## Diagram Policy

- **Format:** D2 is the standard diagram source format
- **Outputs:** Save both the `.d2` source file and a `.png` render by default
- **Authority:** Diagrams are human aids only. Text context files and sprint docs remain the source of truth
- **When to create:** Only when the user explicitly asks for a diagram
- **Sprint location:** Save sprint-local diagrams in `temp-diagrams/`
- **Reading:** Roles should not rely on diagrams unless the user explicitly points them to one

---

## Project Context

The project's durable truth lives in two places:

- **Project context files** in `.context/project/`: `design.md`, `architecture.md`, `data.md`, `domain.md` (if it exists — optional, for projects with non-trivial domains), and `integrations.md`
- **Standards decision files** in `.context/standards/`: project-specific cross-cutting engineering decisions created via `dev-standards`

Sprint work must stay consistent with these durable files. Sprint roles must not silently override them or create competing truth in sprint docs.

Project planning remains the primary owner of durable truth, but sprint is where implementation often disproves assumptions. Because of that, the sprint workflow may **promote** durable findings during the sprint:

- **Manager** may update `.context/project/*.md` and `.context/standards/*.md` with user confirmation when implementation reveals the durable truth needs to change
- **Implementer** may surface and propose promotions, but does not edit durable truth directly
- **Junior Developer** may surface discrepancies in the implementation plan, but does not edit durable truth directly

Files in `.context/project/implementation/` (`conventions.md` and `backlog.md`) remain writable during sprint with user confirmation. These are durable implementation-support files, not sprint-local notes.

**Context files may be provisional.** Check `.context/HANDOFF.md` for notes on which files/sections are provisional. Provisional context may be updated by the project planning skill between sprints. If a chunk depends on provisional context, note the dependency in the chunk scope.

### Context File Maturity

Read maturity from the content itself: cited sources in `domain.md`, tested-behaviour dates in `integrations.md`, open-question count in `design.md`, rationale in `architecture.md`, and concrete examples in `data.md`.

**Access by role:**

Detailed access rules live in the role files. In summary: the **Manager** reads `HANDOFF.md` first and then the relevant durable files, the **Implementer** reads durable files only on demand from the chunk scope, and the **Junior Developer** does not read root-level context files.

## Artifact Roles

Sprint uses different kinds of artifacts for different jobs. The key distinction is whether an artifact owns durable truth, mirrors it for execution, or just tracks sprint state.

| Artifact | Role in the workflow |
|----------|----------------------|
| **`.context/project/*.md`** | Durable project truth. Enduring behavior, structure, data, domain, and integration truth live here. |
| **`.context/standards/*.md`** | Durable cross-cutting engineering decisions. These record what the project decided for topics like error handling, testing, security, and resilience. |
| **`.context/project/implementation/conventions.md`** | Durable implementation truth. Terse, implemented coding rules and recurring patterns live here. |
| **`.context/project/implementation/backlog.md`** | Durable future work. Concrete items worth doing later live here. |
| **`PLAN.md`** | Execution mirror. It may restate durable truth for sprint clarity, but it does not own that truth. |
| **`implementation/*.md`** | Exact execution instructions for the Junior Developer. These are executable plans, not design authority. |
| **`CURRENT-STATE.md`** | Sprint working memory. It tracks progress, blockers, deviations, and pending promotions during the current sprint. |
| **`.context/HANDOFF.md`** | Session bridge. It summarizes what the next planning or sprint session needs to know quickly. |
| **`SPRINT-SUMMARY.md`** | Retrospective summary. It records the sprint outcome and carry-forward items. |

Rules:

- `PLAN.md` may restate important design, architecture, data, integration, or standards decisions when that makes execution clearer
- `PLAN.md` must never become the only place a durable fact exists
- `CURRENT-STATE.md` and `HANDOFF.md` are bridges and working memory, not authoritative truth containers
- `backlog.md` is for concrete future work only — not unresolved truth discrepancies

## Production Engineering Mindset

Applies to **Manager and Implementer** roles. When making or evaluating technical decisions during the sprint:

- **Explain the "why"** behind patterns — "do X because without it, Y happens"
- **Reference real-world practice** — how production systems and open-source projects actually handle it
- **Name the tradeoff** between simple and professional approaches — be explicit about what matters at this project's scale
- **Challenge skipped fundamentals** — error handling, logging, data integrity, testability
- **YAGNI** — don't gold-plate, but don't skip what production code needs

This does NOT apply to the Junior Developer role. Juniors execute plans, not engineering judgments.

---

## File Ownership Matrix

| File | Manager | Implementer | Junior Developer |
|------|---------|-------------|------------------|
| **PLAN.md** | Create, Edit | Read | Read |
| **CURRENT-STATE.md** | Create, Edit | Edit | Read |
| **implementation/*.md** | Read | Create, Edit | Checkboxes + notes only |
| **SPRINT-SUMMARY.md** | Create, Edit | Read | Read |
| **ACTIVE-SPRINT** | Create, Edit | Read | Read |
| **`.context/HANDOFF.md`** | Read, Edit | — | — |
| **`.context/project/*.md`** (durable project truth) | Read, Edit (promotion with user confirmation) | Read (on-demand) | — |
| **`.context/standards/*.md`** (durable standards decisions) | Read, Edit (promotion with user confirmation) | Read (on-demand) | — |
| **`.context/project/implementation/conventions.md`** | Read, Edit | Read, Edit | Read (via plan) |
| **`.context/project/implementation/backlog.md`** | Read, Edit | Read, Edit | Read |

---

## Task and Step Notation

Implementation plans use Tasks (logical units) containing Steps (individual actions).

**Decimal notation:** `Task.Step` — e.g., `1.1` = Task 1, Step 1; `2.3` = Task 2, Step 3

**Progress notation for CURRENT-STATE.md:** `✅1.1 ✅1.2 🔄1.3 ⬜1.4`

---

## Deviation Tracking

Deviations recorded in two places:

1. **Implementation Plan** (Junior records): Detailed note under the task — what changed, why, file references
2. **CURRENT-STATE.md** (Implementer summarizes): Task ID + brief summary in `Execution Deviations / Post-Review Summary`

If a deviation changes or disproves durable truth, it must also enter the promotion/reconciliation flow below — not remain only as a deviation note.

---

## Promotion & Reconciliation

Sprint is allowed to discover that earlier planning was incomplete or wrong. When that happens, the workflow must reconcile the durable truth instead of leaving it stale.

**Who does what:**

- **Junior Developer** records discrepancies and discoveries in the implementation plan
- **Implementer** summarizes them in `CURRENT-STATE.md`, identifies likely destination artifacts, and escalates
- **Manager** decides with the user whether the finding changes durable truth, and performs the promotion when needed

Use the routing table below to choose the owner. In practice: durable project truth goes to `.context/project/*.md`, cross-cutting engineering decisions to `.context/standards/*.md`, implemented recurring code rules to `conventions.md`, concrete future work to `backlog.md`, and sprint-local coordination to `PLAN.md` or `CURRENT-STATE.md`.

**Promotion order:**

1. Record the discovery in the implementation plan or `CURRENT-STATE.md`
2. Decide whether it is sprint-local, future work, or durable truth
3. If current work depends on the change, promote it before continuing
4. If the change affects meaning or makes a new decision, get user confirmation
5. Update the owning durable artifact first
6. Then update sprint mirrors as needed: `PLAN.md`, `CURRENT-STATE.md`, and `.context/HANDOFF.md`

`CURRENT-STATE.md` is the sprint's promotion queue, not the final home of those findings. By chunk end or session end, each finding should be either promoted, explicitly deferred, awaiting user decision, or ruled out.

---

## Unresolved Item Routing

An unresolved item should have **one owner**. `CURRENT-STATE.md` and `.context/HANDOFF.md` may mirror an item while it is active or being handed over, but they do not own it.

| If the unresolved item is... | Put it here | Why / how to use it |
|------------------------------|-------------|----------------------|
| A project-level question whose answer changes durable behavior, structure, data, domain, or integration truth | `design.md` Open Questions | This is the durable home for undecided project truth. If sprint discovers it, capture it in the implementation plan or `CURRENT-STATE.md` first, then promote it into `design.md` once the Manager and user agree it is a real project-level open question. |
| A sprint-local scoping or sequencing question about the remaining chunks | `PLAN.md` `Sprint-Local Open Questions` | Use this only for questions inside the current sprint. Do not let `PLAN.md` become a second project-wide design-question list. If the answer changes durable truth, promote that truth to its owning file. |
| Confirmed non-blocking work intentionally postponed but still plausible for this sprint | `PLAN.md` `Sprint-Local Deferred Items` | This is the sprint-local "not now" list. If the sprint ends and the item still matters, move it to `backlog.md` or the appropriate durable file. |
| Concrete future work that should outlive the current sprint | `.context/project/implementation/backlog.md` | Use for actionable follow-up work, not raw questions or unresolved truth discrepancies. If the next session needs to notice it quickly, HANDOFF may point to it briefly, but backlog remains the owner. |
| A cross-cutting engineering decision intentionally postponed, with reason and revisit trigger | Relevant `.context/standards/<topic>.md` `Deferred` section | Use when the project has already considered the standards topic and deliberately decided "later". This is a durable decision record, not a generic TODO list. |
| The exact record of what execution changed, discovered, or could not follow in the plan | Implementation plan deviation notes | The Junior records the full detail here first. This captures what happened during execution, but does not own final classification. |
| An active sprint finding that still needs classification, user decision, promotion, or follow-up during this sprint | `CURRENT-STATE.md` | This is the sprint working queue. Summarize the finding, likely owner, and current status until it is promoted, deferred to the right home, ruled out, or handed off. |
| Concise carry-forward context the next session must see quickly | `.context/HANDOFF.md` | Bridge only. Copy unresolved or newly important items here when the session or sprint ends, but do not let HANDOFF become the only place the item exists long-term. If an item already lives in `PLAN.md` or `backlog.md`, HANDOFF should point to it briefly rather than duplicate it in full. |

- Common sprint flow for newly discovered issues: implementation plan deviation note → `CURRENT-STATE.md` → owning durable file (`design.md`, `.context/standards/*.md`, `backlog.md`, or `PLAN.md`) → `.context/HANDOFF.md` only if the item is still unresolved at handoff time.
- Avoid duplicate unresolved-item lists. Once an item has reached its owner, keep only the minimal mirror needed in `PLAN.md`, `CURRENT-STATE.md`, or `HANDOFF.md` for execution and continuity.
- All roles may surface backlog candidates, but additions to either backlog still require user confirmation.

---

## Post-Chunk Review

After the Junior finishes a chunk, the user dispatches code review and spec adherence sub-agents. The **Implementer** then runs a consolidated review:

1. Read the Junior's deviation notes from the implementation plan
2. Read the sub-agent findings (code review + spec adherence)
3. Classify each finding: fix now, Manager promotion candidate, convention update, backlog candidate, or ruled out
4. Summarise in CURRENT-STATE.md: what deviated, what needs fixing, and which findings may need promotion
5. If a finding changes or disproves durable truth, flag it for Manager promotion instead of leaving it only in CURRENT-STATE.md or the implementation plan
6. Batch any backlog candidates and present them to the user for approval. Only use backlog for concrete future work, not unresolved truth discrepancies.

This is a single step — not separate deviation review and sub-agent review. The Implementer processes all post-chunk findings together.

## Chunk Completion

A chunk is only ready to hand off to the next chunk when:

1. Junior execution is complete and deviations are recorded in the implementation plan
2. Post-chunk review is complete
3. Any `fix now` findings are fixed or explicitly accepted by the user
4. Any promotion candidates in `CURRENT-STATE.md` are no longer ambiguous — they are promoted, explicitly deferred, awaiting user decision, or ruled out
5. `CURRENT-STATE.md` is updated to reflect the final state of the chunk

**Update responsibilities:**

- **Implementer** updates `CURRENT-STATE.md` after post-chunk review: final chunk status, progress, deviation summary, and promotion candidates
- **Manager** decides with the user whether the chunk is complete enough to move on, performs any needed durable-truth promotions, and only then advances sprint focus to the next chunk

Do not start the next chunk while the previous chunk still has unresolved `fix now` work or unclassified promotion candidates.

## Sprint Wrap-Up

When the sprint completes or pauses for a meaningful handoff:

1. Review `CURRENT-STATE.md` and make sure every promotion candidate is promoted, explicitly deferred, awaiting user decision, or ruled out
2. Review the sprint backlog in `PLAN.md` (`Sprint-Local Open Questions` and `Sprint-Local Deferred Items`) and classify each item: resolved, intentionally staying in the sprint because the sprint is continuing, promoted to `.context/project/implementation/backlog.md`, promoted to a durable truth file, or copied into `.context/HANDOFF.md` as a carry-forward pointer for the next session
3. Finalize chunk statuses and update `Current Active Chunk / Task / Execution State` so the sprint does not appear to be mid-chunk accidentally
4. Write `SPRINT-SUMMARY.md`: overall sprint outcome, per-chunk outcomes, what was built or changed, what was promoted into durable owning files during sprint, and what is still unreconciled or pointed to from `HANDOFF.md`
5. Update `.context/HANDOFF.md` using the shared handoff schema so the next planning or sprint session can resume quickly

**Wrap-up responsibilities:**

- **Implementer** may help summarize final chunk outcomes and ensure `CURRENT-STATE.md` reflects the final sprint state
- **Manager** owns the final wrap-up: any remaining durable-truth promotions with user confirmation, `SPRINT-SUMMARY.md`, and `.context/HANDOFF.md`

`SPRINT-SUMMARY.md` is retrospective only. It records what happened during the sprint, but it does not replace durable project docs, standards decision files, `conventions.md`, or `backlog.md`.

## Sub-Agent Prompts

The user dispatches these after the Junior completes a chunk. The Implementer processes the findings during Post-Chunk Review.

- `sub-agents/code-review-prompt.md` — Quality, correctness, edge cases, promotion candidates, backlog candidates
- `sub-agents/spec-adherence-prompt.md` — Plan compliance, deviation detection, promotion candidates
