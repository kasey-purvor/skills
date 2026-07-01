---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the tracker using tracer-bullet vertical slices. Use when converting a plan into issues, creating implementation tickets, or breaking work down into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

The issue tracker and label vocabulary come from the repo overlay (`docs/agents/issue-tracker.md`) and the `linear` skill — run `/setup-matt-pocock-skills` first if the repo isn't configured yet.

## Process

### 1. Gather context

Work from whatever is already in the conversation. If the user passes an issue reference (id, URL, or path) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state. Issue titles and descriptions should use the project's domain-glossary vocabulary and respect ADRs in the area you're touching.

### 3. Draft vertical slices

**CRITICAL** For all work regarding code you must load the /dev-standards-handbook & /dev-standards-pitfalls skills.

Break the plan into **tracer-bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end (schema, API, UI, tests), NOT a horizontal slice of one layer.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice show:

- **Title** — short descriptive name
- **Blocked by** — which other slices (if any) must complete first
- **User stories covered** — which the slice addresses (if the source material has them)

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?

Iterate until the user approves. Then confirm you have the inputs for the **Ticket body** template in the `linear` skill (TL;DR / Goal / Scope / AC / Verification) — ask the user for any missing fields before publishing.

### 5. Publish the issues

For each approved slice, publish a Linear issue:

- **Body:** the **Ticket body** template from the `linear` skill (TL;DR / Goal / Scope / Acceptance criteria / Verification). Don't redefine it here.
- **Labels:** `type/*`, `quality/scoped`, and `ai-added` (these tickets are agent-created).
- **Project:** assign one — never leave a ticket projectless (`linear` Convention #9). Ask which project if it isn't obvious.
- **State: Backlog** — well-defined but not yet scheduled. Promotion to Todo (scheduling) and `quality/audited` (the pre-work re-audit) are separate, later steps — `/to-issues` does not do them.

Publish in dependency order (blockers first) so you can reference real issue ids in the "Blocked by" field.

All slices sit inside the universal frame:

<universal-frame>
## Parent

A reference to the parent issue (if the source was an existing issue; otherwise omit this section).

## <ticket body — see the `linear` skill>

## Blocked by

- A reference to the blocking ticket(s), or "None — can start immediately".

</universal-frame>

Do NOT close or modify any parent issue.