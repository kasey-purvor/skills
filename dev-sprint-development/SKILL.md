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
| `writing-plans` | - | **Init** | - |
| `executing-plans` | - | - | **Init** |
| `test-driven-development` | - | **Init** | **Init** |
| `systematic-debugging` | - | On-demand | **Init** |
| `verification-before-completion` | On-demand | On-demand | **Init** |
| `brainstorming` | On-demand | On-demand | - |

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
├── sprints/
│   ├── YYYY-MM-DD-<sprint-name>/
│   │   ├── PLAN.md
│   │   ├── CURRENT-STATE.md
│   │   ├── implementation/
│   │   │   ├── 01-<chunk-name>.md
│   │   │   └── ...
│   │   ├── temp-diagrams/
│   │   │   └── (temporary context diagrams — brainstorming aids, not maintained)
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

---

## Project Context

Project context files in `.context/project/` are the project's source of truth: `design.md`, `architecture.md`, `data.md`, `domain.md` (if it exists — optional, for projects with non-trivial domains), and `integrations.md`. Sprint work must be consistent with them. If a sprint decision would conflict with a context file, escalate to the user — don't silently override the design.

Context files are owned by the project planning skill. The sprint development skill **reads** them but does **not modify** them — with one exception: files in `.context/project/implementation/` (`conventions.md` and `backlog.md`) can be written by any sprint role with user confirmation. If sprint work reveals that any other context file is wrong or incomplete, record the finding in CURRENT-STATE.md (see Context File Findings below) — findings are then copied to HANDOFF.md at sprint end for the project planning skill to incorporate.

**Context files may be provisional.** Check `.context/HANDOFF.md` for notes on which files/sections are provisional. Provisional context may be updated by the project planning skill between sprints. If a chunk depends on provisional context, note the dependency in the chunk scope.

### Context File Maturity

Each file carries its own maturity signals — read maturity from the content itself:

| File | How to read maturity | How it evolves |
|------|---------------------|----------------|
| `domain.md` | Sections with cited sources = researched. Empty/missing = unresearched | Iterative — revisited as different project areas need domain understanding |
| `integrations.md` | Per-service: "Tested behaviour" dates = reliable. No dates = assumed from docs | Services mature individually as they're tested during implementation |
| `design.md` | Open Questions count = maturity indicator. Content sections = decided | Constantly evolving. Never "done" |
| `architecture.md` | Sections with rationale = resolved. Empty/missing = not yet decided | Stabilises once implementation begins. Revisited for fundamental changes |
| `data.md` | Schemas with concrete examples = solid. TBD fields = provisional | Lags behind design. Fills in during implementation |

**Access by role:**

| Role | Context file access |
|------|-------------------|
| **Manager** | Read `.context/HANDOFF.md` first (for session context and provisional notes), then the context files relevant to the current work. The Manager is responsible for ensuring chunk scopes and decisions are consistent with these files. |
| **Implementer** | Read on-demand only, when the chunk scope section references a specific section (e.g., "see `data.md` Config Model for the config schema"). The chunk scope is the Implementer's primary input — context files fill in referenced details. |
| **Junior Developer** | Never reads context files. The implementation plan contains everything needed for execution. |

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
| **`.context/HANDOFF.md`** | Read, Edit (sprint end) | — | — |
| **`.context/project/*.md`** (context files) | Read | Read (on-demand) | — |
| **`.context/project/implementation/conventions.md`** | Read, Edit | Read, Edit | Read (via plan) |
| **`.context/project/implementation/backlog.md`** | Read, Edit | Read, Edit | Read, Edit |

---

## Task and Step Notation

Implementation plans use Tasks (logical units) containing Steps (individual actions).

**Decimal notation:** `Task.Step` — e.g., `1.1` = Task 1, Step 1; `2.3` = Task 2, Step 3

**Progress notation for CURRENT-STATE.md:** `✅1.1 ✅1.2 🔄1.3 ⬜1.4`

---

## Deviation Tracking

Deviations recorded in two places:

1. **Implementation Plan** (Junior records): Detailed note under the task — what changed, why, file references
2. **CURRENT-STATE.md** (Implementer summarizes): Task ID + brief summary in Deviations table

---

## Backlogs

Two locations for deferred work:

- **Project backlog** (`.context/project/implementation/backlog.md`) — items that outlive the current sprint. Grouped by priority: before-production, next-time-we-touch-this, nice-to-have.
- **Sprint backlog** (PLAN.md Open Questions / deferred items) — items that could be addressed in a later chunk of the current sprint.

All roles should be aware of both locations. When any role spots something not worth fixing now, surface it to the user and suggest which backlog it belongs in. Always get user confirmation before adding items.

The **Manager** should check both backlogs when scoping chunks — existing backlog items may be addressable alongside planned work.

## Post-Chunk Review

After the Junior finishes a chunk, the user dispatches code review and spec adherence sub-agents. The **Implementer** then runs a consolidated review:

1. Read the Junior's deviation notes from the implementation plan
2. Read the sub-agent findings (code review + spec adherence)
3. Summarise in CURRENT-STATE.md: what deviated, what needs fixing
4. Batch any backlog candidates and present them to the user for approval

This is a single step — not separate deviation review and sub-agent review. The Implementer processes all post-chunk findings together.

## Sub-Agent Prompts

The user dispatches these after the Junior completes a chunk. The Implementer processes the findings during Post-Chunk Review.

- `sub-agents/code-review-prompt.md` — Quality, correctness, edge cases, backlog candidates
- `sub-agents/spec-adherence-prompt.md` — Plan compliance, deviation detection
