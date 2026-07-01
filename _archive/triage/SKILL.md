---
name: triage
description: Use when triaging tickets in Linear — either picking one to work on from the Triage bucket or assessing and enriching a named ticket toward a ready state. Anchored to the `linear` skill for ticket shape.
---

# Triage

Lightweight workflow for moving Linear tickets out of Triage. The shape of a "ready" ticket lives in the `linear` skill — not here.

## What "in triage" means

A ticket needs triage if its **status** is `Triage`. No label required.

## Invocation

`/triage` with one of:

- **No argument** — pull the Triage bucket, summarize, propose one to focus on. Oldest first, with a one-liner per ticket. Let the user pick.
- **A ticket reference** (e.g., `CLO-119`) — fetch it. Per the `linear` skill's *Reading a ticket for action*, fetch both `get_issue` and `list_comments`.

## The flow

1. **Read everything that's there first.** Description, comments, labels, prior triage notes. Don't re-ask resolved questions. Don't propose work that's already specified.

2. **Assess against the agent-ready shape** (Goal, Scope, Acceptance Criteria, Verification — per the `linear` skill). Tell the user concretely what's present, missing, or weak. Example: *Goal is clear; Scope > Out is missing; the second acceptance criterion reads as soft ("should feel fast")*. Not vague summaries.

3. **For bugs, attempt reproduction before enrichment.** Read the steps, trace the code, run the relevant command or test. Report what happened — successful repro with the code path, failed repro, or insufficient detail. A confirmed repro makes the rest of the triage much stronger. A failed repro is itself a useful signal — flag it.

4. **Enrich interactively.** If the ticket needs work, run `/grill-with-docs` to pull out the missing pieces. **The output edits the description in place** (Convention #9, `linear` skill). Comments are for status, blockers, and discussion — not spec content.

5. **Move to ready when it's solid.** Apply `triage/ready-for-agent` or `triage/ready-for-human` based on the intended executor, and move state to Backlog (or Todo if it's next-up). The two labels share the same description shape — they differ only in who picks the ticket up next.

6. **If it won't be done, close as Canceled** with a one-line reason in a comment. No paperwork.

## Things deliberately not here

- **No `needs-triage` label** — the Triage status is the signal.
- **No bug/enhancement category role separate from `type/*` labels** — Linear's labels already cover that.
- **No prescribed "needs-info" comment template** — you're usually the reporter; use natural language when you genuinely need input from someone else.
- **No parallel agent-brief template** — the description shape is in the `linear` skill, full stop.
- **No AI-generated disclaimer rule.**

## Related

- `linear` — ticket shape, label and state semantics, Convention #9
- `to-prd` — when triage uncovers a feature too big for one ticket, escalate to a PRD
- `to-issues` — when a PRD or a thicker triage outcome needs slicing into multiple tickets
- `grill-with-docs` — invoked during step 4 to enrich thin tickets
