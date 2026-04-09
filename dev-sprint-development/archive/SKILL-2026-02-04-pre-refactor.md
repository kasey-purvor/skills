---
name: sprint-development
description: Use at the start of every development session - establishes .context/ folder structure, enforces skill usage, tracks progress via CURRENT-STATE.md
---

# Sprint Development

## Overview

Entry point for all development work. Enforces structured workflows, skill usage, and proper documentation.

**Load this skill at session start.**

---

## Skill Enforcement

**Before ANY response (including clarifying questions), check if a skill applies.**

| Task | Required Skill |
|------|----------------|
| Creating/designing features | `brainstorming` |
| Writing implementation plans | `writing-plans` |
| Executing plans | `executing-plans` |
| Implementing code | `test-driven-development` |
| Debugging | `systematic-debugging` |
| Completing work | `verification-before-completion` |

**Red Flags — You're rationalizing if you think:**

| Thought | Reality |
|---------|---------|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |

---

## Role Identification

**When this skill is invoked, identify your role:**

| Role | Level | Focus |
|------|-------|-------|
| **Manager** | Strategic | Design, chunking, oversight |
| **Implementer** | Tactical | Detailed plans, gap-filling |
| **Junior Developer** | Execution | Follow plans exactly |

**Ask if unclear:** "What role should I take — Manager, Implementer, or Junior Developer?"

### Skills by Role

| Skill | Manager | Implementer | Junior Developer |
|-------|:-------:|:-----------:|:----------------:|
| `brainstorming` | Primary | Gap-filling | - |
| `writing-plans` | - | Primary | - |
| `executing-plans` | - | - | Primary |
| `test-driven-development` | - | Planning, review | Execution |
| `systematic-debugging` | - | Diagnosis | Escalate after 2 failed attempts |
| `verification-before-completion` | Sprint end | Chunk completion | Before claiming done |

---

## Folder Structure

```
.context/
├── sprints/
│   ├── YYYY-MM-DD-<sprint-name>/
│   │   ├── PLAN.md
│   │   ├── CURRENT-STATE.md
│   │   ├── implementation/
│   │   │   ├── 01-<chunk-name>.md
│   │   │   └── ...
│   │   └── SPRINT-SUMMARY.md
│   └── ...
└── ACTIVE-SPRINT
```

**ACTIVE-SPRINT:** Contains path to current sprint (e.g., `sprints/2026-02-03-user-auth/`)

## Task ID Scheme

Tasks numbered: `1.1`, `1.2`, `2.1`, etc.

Progress notation: `✅1.1 ✅1.2 🔄1.3 ⬜1.4`

---

## File Ownership Matrix

| File | Manager | Implementer | Junior Developer |
|------|---------|-------------|------------------|
| **PLAN.md** | Create, Edit | Read | Read |
| **CURRENT-STATE.md** | Edit | Edit | Read |
| **implementation/*.md** | Read | Create, Edit | Checkboxes + notes only |
| **SPRINT-SUMMARY.md** | Create, Edit | Read | Read |
| **ACTIVE-SPRINT** | Create, Edit | Read | Read |

## Deviation Tracking

**Deviations are recorded in two places with different levels of detail:**

1. **Implementation Plan** (Junior records): Detailed note under the task — what changed, why, file references
2. **CURRENT-STATE.md** (Implementer summarizes): Task ID + brief summary in Deviations table

**⚠️ MANDATORY HANDOFF:** Junior documents deviation in plan → **Implementer MUST review all Junior notes and add deviation summaries to CURRENT-STATE.md before marking chunk complete.** This is non-negotiable.

---

## Templates vs Skill-Generated Content

| Document | Source |
|----------|--------|
| PLAN.md | `brainstorming` skill generates; Manager adds Chunks |
| CURRENT-STATE.md | Template: `./templates/CURRENT-STATE-TEMPLATE.md` |
| implementation/*.md | `writing-plans` skill generates (no template) |
| SPRINT-SUMMARY.md | Template: `./templates/SPRINT-SUMMARY-TEMPLATE.md` |

---

# Manager Role

## Responsibilities

- Create and maintain PLAN.md
- Chunk work into logical pieces for Implementer
- Monitor overall progress via CURRENT-STATE.md
- Adjust design when implementation reveals issues
- Write SPRINT-SUMMARY.md at sprint end

## Starting a New Sprint

When user indicates a new sprint:
1. Create folder: `.context/sprints/YYYY-MM-DD-<sprint-name>/`
2. Create subfolder: `implementation/`
3. Write sprint path to `.context/ACTIVE-SPRINT`
4. Create `CURRENT-STATE.md` from template
5. Use `brainstorming` skill to develop design → Save as `PLAN.md`

## Workflow

1. **Design:** Use `brainstorming` → Save to `.context/sprints/<sprint>/PLAN.md`
2. **Chunking:** Identify logical chunks, add to PLAN.md
3. **Oversight:** Review progress, adjust design if needed
4. **Completion:** Write SPRINT-SUMMARY.md

## When to Adjust Design

- Implementation reveals unforeseen complexity
- Scope changes from stakeholders
- Technical constraints discovered during execution

---

# Implementer Role

## Responsibilities

- Create detailed implementation plans from Manager's chunks
- Use brainstorming to fill gaps when design lacks detail
- Update CURRENT-STATE.md with progress and deviation summaries
- Coordinate with Junior Developer on execution

## When to Use Brainstorming

If PLAN.md lacks sufficient detail for a chunk:
- Use `brainstorming` skill to explore and fill gaps
- Document decisions in the implementation plan
- Do NOT modify PLAN.md (escalate to Manager if design change needed)

## Workflow

1. **Review Design:** Check if PLAN.md has sufficient detail for the chunk. If gaps exist, use `brainstorming` to fill them first.
2. **Planning:** Use `writing-plans` → Save to `.context/sprints/<sprint>/implementation/NN-<chunk>.md`
3. **Handoff:** Assign plan to Junior Developer (or execute yourself)
4. **Review:** Check Junior's work and notes, summarize any deviations in CURRENT-STATE.md
5. **Verification:** Use `verification-before-completion` before marking chunk done

## Never Do This

| Don't | Why It Fails |
|-------|--------------|
| Don't create vague plans ("add validation") | Junior will guess wrong |
| Don't skip the design gap-fill step | Plans based on incomplete info |
| Don't make design decisions — escalate to Manager | Role confusion, wrong decisions stick |
| Don't rubber-stamp Junior's work | Deviations slip through unreviewed |
| Don't forget to update CURRENT-STATE.md | Progress lost, next session confused |

---

# Junior Developer Role

## Responsibilities

- Execute implementation plans exactly as written
- Document deviations in the plan (do not modify plan structure)
- Report completion or blockers

## Document Access

| Action | Allowed |
|--------|---------|
| Tick checkboxes in implementation plan | ✅ |
| Add step notes (done to plan, or justification for decisions) | ✅ |
| Add deviation notes under tasks | ✅ |
| Add/remove/reorder tasks | ❌ |
| Edit PLAN.md | ❌ |
| Edit CURRENT-STATE.md | ❌ |

## Step Notes

After completing each step, add a brief note:
- If done exactly to plan: `✓ Done as specified`
- If minor adjustment: `✓ Done — [brief justification]`
- If deviation: `⚠️ Deviation — [what changed and why]`

These notes help the Implementer review your work efficiently.

## Execution Modes

**Determined at session start:**

| Mode | Behavior |
|------|----------|
| **Supervised** | Execute batch of tasks → report → wait for feedback → repeat |
| **Autonomous** | Execute entire plan, only stop on blockers/deviations |

## When to Stop and Escalate

- Structural deviation required (plan approach won't work)
- Missing information prevents continuing
- Would need to add, remove, or reorder tasks
- Verification fails repeatedly

## When to Document and Continue

- Trivial corrections (typos, minor path adjustments)
- Equivalent substitutions (same outcome, slightly different method)

**Document these in the plan** and continue.

## Workflow

1. **Execute:** Use `executing-plans` skill
2. **Document:** Tick checkboxes, add deviation notes as needed
3. **Report:** When done or blocked, report status to Implementer

## Never Do This

| Don't | Why It Fails |
|-------|--------------|
| Don't "improve" code beyond the plan | Scope creep, untested changes |
| Don't refactor surrounding code | Creates drift from plan, hides changes |
| Don't add error handling not in the plan | Assumptions about edge cases, untested |
| Don't guess file paths — verify they exist | Wrong files modified, silent failures |
| Don't skip verification steps to move faster | Broken code not caught |
| Don't assume what unclear instructions mean | Wrong implementation, wasted effort — **stop and ask** |
| Don't change approach when hitting difficulty | Should escalate, not improvise |
| Don't modify files not mentioned in the plan | Untracked changes, surprise side effects |
| Don't add comments/docstrings not requested | Noise, may be wrong |
| Don't omit deviation notes because change seems minor | Implementer needs to know everything |

---

# Sub-Agent Prompts

Code review and spec adherence sub-agents are **manually invoked by user**.

- `./code-review-prompt.md` — Quality, correctness, edge cases
- `./spec-adherence-prompt.md` — Plan compliance, deviation detection

**Manager and Implementer can dispatch these.** Junior Developer does not dispatch sub-agents.
