---
name: dev-executing-plans
description: Use when partner provides a complete implementation plan to execute in controlled batches with review checkpoints - loads plan, reviews critically, executes tasks in batches, reports for review between batches
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks — either in supervised batches or autonomously.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## Execution Modes

**At session start, determine execution mode:**

| Mode | Behavior | Use When |
|------|----------|----------|
| **Supervised** | Execute 3 tasks → report → wait for feedback → repeat | Human is actively overseeing |
| **Autonomous** | Execute entire plan, only stop on blockers/deviations | Running as subagent or trusted to proceed |

**Ask if unclear:** "Should I run in supervised mode (checkpoints every 3 tasks) or autonomous mode (full plan, stop only on issues)?"

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically — identify any questions or concerns
3. If concerns: Raise them before starting
4. If no concerns: Proceed with execution

### Step 2: Execute Tasks

**Supervised mode:**
- Execute batch of 3 tasks
- After each batch: Report what was done, show verification output, say "Ready for feedback"
- Wait for feedback before continuing
- Apply any requested changes, then continue

**Autonomous mode:**
- Execute all tasks sequentially
- Commit after logical groupings (e.g., after each numbered task section)
- Only stop on blockers or deviations (see "When to Stop")
- At end: Report summary of all work completed

**For each task (both modes):**
1. Mark as in_progress
2. Follow each step exactly
3. Run verifications as specified
4. Mark as completed

### Step 3: Complete Plan

When all tasks are done:
- Commit all work with descriptive message
- Report completion summary (what was built, any deviations documented)
- Wait for next instructions

## When to Stop and Escalate

**STOP executing immediately when:**
- Structural deviation required (plan approach won't work)
- Missing information prevents continuing
- Would need to add, remove, or reorder tasks
- Verification fails repeatedly
- You don't understand an instruction

**Ask for clarification rather than guessing.**

## When to Document and Continue

**These do NOT require stopping:**
- Trivial corrections (typos, minor path adjustments)
- Equivalent substitutions (same outcome, slightly different method)

**Document these deviations in the plan** (add a note under the task) and continue.

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** — stop and ask.

## Document Access (Sprint Context)

**If working within a sprint:**
- ✅ Tick checkboxes in implementation plan
- ✅ Add step notes after each checkbox (using decimal notation: 1.1, 1.2, etc.)
- ✅ Add deviation notes under tasks
- ❌ Add/remove/restructure tasks
- ❌ Modify PLAN.md or CURRENT-STATE.md

## Step Notes

**Notation:** Tasks and Steps use decimal format — `1.1` = Task 1, Step 1; `1.2` = Task 1, Step 2.

Complete all steps within a task before updating the file. When task is done, tick all step checkboxes and add a summary note. One of these is required:
- `✓ Done as specified`
- `✓ Done — [brief justification, reference steps if needed]`
- `⚠️ Deviation — [what changed and why, reference steps]`

```markdown
- [x] **1.1:** Write failing test
- [x] **1.2:** Implement function
- [x] **1.3:** Add validation
  ✓ Done — 1.2 used utils.py helper; 1.3 added null check (edge case required)
```

Notes go after the last step of the task. These help the Implementer review efficiently.

## Never Do This

| Don't | Why It Fails |
|-------|--------------|
| Don't "improve" code beyond the plan | Scope creep, untested changes |
| Don't refactor surrounding code | Creates drift from plan, hides changes |
| Don't add error handling not in the plan | Assumptions about edge cases, untested |
| Don't guess file paths — verify they exist | Wrong files modified, silent failures |
| Don't skip verification steps to move faster | Broken code not caught |
| Don't assume what unclear instructions mean | Wrong implementation — **stop and ask** |
| Don't change approach when hitting difficulty | Should escalate, not improvise |
| Don't modify files not mentioned in the plan | Untracked changes, surprise side effects |
| Don't add comments/docstrings not requested | Noise, may be wrong |
| Don't omit step notes because change seems minor | Reviewer needs to know everything |

## Git Commands

**Always run git commands as separate tool calls, never chained with `&&` or `;`.**

Chaining (e.g., `git add ... && git commit ...`) creates a combined command string that may not match permission allow-list patterns. Instead:

1. Run `git add` as one Bash call
2. Run `git commit` as a separate Bash call

This applies to all git operations — staging, committing, pushing, etc.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Supervised mode: report and wait between batches
- Autonomous mode: only stop on blockers/deviations
- Stop when blocked, don't guess
- Git commands: one per tool call, never chain
