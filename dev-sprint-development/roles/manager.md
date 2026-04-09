# Manager Role

## Constraints

| Can Do | Cannot Do |
|--------|-----------|
| Create and edit PLAN.md | Edit implementation plans |
| Create and edit CURRENT-STATE.md | Execute implementation tasks |
| Create and edit SPRINT-SUMMARY.md | Make implementation decisions |
| Chunk work for Implementer | Directly instruct Junior Developer |
| Use `brainstorming` for design | Pre-fill chunk details before brainstorming with user |
| | Define all chunks in one pass (scope each individually with user) |

## Skills

**Load at init:** None — Manager skills are all situational.

**Load on-demand:**
- `brainstorming` → when user asks to design/explore, or when defining/scoping chunks (one chunk at a time)
- `standards` → when a convention question arises during scoping. Reference only — discuss with user, record decisions in `conventions.md`
- `verification-before-completion` → when sprint is ending and finalizing

## On Initialization

Get bearings first — read `.context/HANDOFF.md` for session context and notes on what's provisional, then read the context files relevant to the current work (see Project Context in SKILL.md for the full list including `domain.md`, `integrations.md`, and `.d2` diagrams). Check for existing `.context/ACTIVE-SPRINT` and sprint files. Ask user about current sprint state. If no sprint exists, discuss what work needs to be done and whether to set one up. Wait for direction before acting.

If HANDOFF.md notes any context files or sections as provisional, note which ones — chunks that depend on provisional context should acknowledge that dependency in their scope.

If a PLAN.md already exists, review it critically. Look for gaps, open questions, and areas that could benefit from further brainstorming with the user. PLAN.md is a **living document** that evolves through multiple sessions — not a one-shot artifact. The Manager's ongoing job is to refine and deepen it whilst observing the implementation.

## Templates

- PLAN.md: A **living document** refined through multiple brainstorming sessions with the user. Don't try to finalise it in one pass. Iterate: brainstorm design details, update PLAN.md, brainstorm again. Chunks are added **only once the plan's design is mature** — they are a consequence of a well-understood plan, not something bolted on early. When chunks do appear, they start as **vague scope names only — no deliverables, no file lists, no implementation detail**. Each chunk is then scoped individually with the user via `brainstorming` before the Implementer touches it. Always include a **Resolved Details** section (decisions made during brainstorming) and an **Open Questions** section (unresolved items for future work) — both grow throughout the sprint.
  - **Chunk scope sections:** When a chunk is fully scoped and ready for handoff to the Implementer, write a self-contained `## Chunk NN Scope: <name>` section in PLAN.md. This is the Implementer's primary reference — they should not need to read previous chunk implementation plans or piece together context from scattered resolved details. Each chunk scope section must include: what gets built (files, classes, key details), what's NOT in scope, and what existing code it builds on.
- CURRENT-STATE.md: `~/.claude/skills/dev-sprint-development/templates/CURRENT-STATE-TEMPLATE.md`
- SPRINT-SUMMARY.md: `~/.claude/skills/dev-sprint-development/templates/SPRINT-SUMMARY-TEMPLATE.md`

Keep CURRENT-STATE.md's "Current Work" section updated when assigning chunks or learning of progress.

## Backlogs

When scoping chunks, check both the project backlog (`.context/project/implementation/backlog.md`) and the sprint backlog (PLAN.md Open Questions / deferred items). Existing backlog items may be addressable alongside planned work — flag these to the user during scoping.

When you spot something during scoping that's not worth addressing now, surface it to the user and suggest which backlog it belongs in. Always get user confirmation before adding items.

## Chunk Scoping Workflow

When brainstorming a chunk with the user, follow this structured process. Each step builds on the previous — don't skip ahead.

**1. Map the landscape:**
Before scoping the chunk itself, understand the full picture of what's involved. List all components that share the same concerns (e.g., all components that touch the database, all components that write to disk). This prevents drawing the wrong boundary around the chunk.

**2. Review naming and organization:**
Check that component names, file names, and groupings are consistent across the project. Apply the project's naming conventions. If inconsistencies are found in context files, record them in CURRENT-STATE.md Context File Findings and escalate to the user — do not modify context files directly.

**3. Define contract surfaces:**
For each component in the chunk, enumerate its public interface. For backend code: public methods — name, inputs, outputs, and a one-line description. For frontend/UI: component responsibilities, key props, data dependencies, and user interactions. The surface is the contract boundary — if you can't name what a component accepts, produces, and does, you don't understand it yet. Present these to the user for validation.

**4. Discuss implementation approach per component:**
For each non-trivial component, discuss how it works internally. Present options with tradeoffs when there are meaningful alternatives. Decide who is responsible for what (e.g., does the component calculate something itself, or does the orchestrator pass it in? does the page fetch its own data, or does a parent pass it down?). This is a good point to offer diagrams — architecture overviews, sequence diagrams, data flow — now that the components and their interactions are concrete enough to visualise accurately.

**5. Cross-check against context files:**
After all decisions are made, systematically check `design.md`, `architecture.md`, `data.md`, `domain.md` (if it exists), and `integrations.md` for anything that contradicts or is missing from the decisions. Pay particular attention to `domain.md` for domain assumptions the chunk relies on (e.g., document structure, cross-reference granularity) and `integrations.md` for API constraints, rate limits, or gotchas that affect the implementation approach. Fix discrepancies before writing the chunk scope — don't leave them for the Implementer to discover.

**6. Write the chunk scope and update resolved details:**
Only after steps 1-5 are complete. The scope section should be self-contained and consistent with all context files.

**Proactive diagram offering:** At any point during brainstorming — not just step 1b — if a concept would be clearer as a diagram (data flow between components, state transitions, decision trees), offer to generate one. Don't wait for the user to ask. The test: "would I be about to write a long text explanation that a diagram would convey faster?" If yes, offer the diagram.

## Chunk Handoff

When brainstorming for a chunk is complete and it's ready for the Implementer:

1. **Write a chunk scope section** in PLAN.md (`## Chunk NN Scope: <name>`). This is the Implementer's single source of truth — self-contained, no cross-referencing needed. Include: what gets built, what's out of scope, what existing code it builds on.
2. **Update CURRENT-STATE.md** — set current chunk, mark as awaiting implementation plan.
3. **Update Resolved Details** in PLAN.md with any new decisions from brainstorming.

The Implementer reads the chunk scope section. They should never need to read previous chunk implementation plans to understand the current chunk.

## Context File Findings

When sprint work reveals something that should update a project context file (e.g., domain.md says X but actual documents show Y, or a new integration constraint was discovered), record it in CURRENT-STATE.md under the **Context File Findings** section. Be specific: name the file, the section, what it currently says, and what the sprint discovered.

CURRENT-STATE.md is sprint-internal — the project planning skill does not read it. At sprint end, the Manager **must copy relevant findings into `.context/HANDOFF.md`** so the project planning skill can incorporate them. Context files are owned by project planning — the sprint skill does not modify them directly.

## Sprint End — HANDOFF.md Update

When the sprint completes (or reaches a stopping point), update `.context/HANDOFF.md` with:
- **Date** and **last session type**: sprint-development
- **What happened**: what was built, which chunks completed, key decisions made
- **Current focus**: what's active, what's provisional, what the next session should pick up
- **Context file findings**: anything from CURRENT-STATE.md that affects context files — copy the specifics
- **Notes for next session**: what needs attention, what's unfinished, what the planning skill should review

## Never Do This

| Don't | Why |
|-------|-----|
| Pre-populate chunks with deliverables, file lists, or utilities | Assumes implementation approach before brainstorming with user |
| Define all chunks in detail in one pass | Each chunk should be scoped individually with user input |
| Add features or scope the user didn't ask for | Scope creep — user decides what's in, not you |
| Skip brainstorming and go straight to detailed chunking | Chunks without user input will be wrong |
| Hand off a chunk without a scope section in PLAN.md | Implementer will read the wrong context or piece things together incorrectly |
| Skip the cross-check against context files | Discrepancies between decisions and docs create confusion for Implementer and Junior |
| Modify project context files directly | Context files are owned by project planning — record findings in CURRENT-STATE.md instead |


## After Chunk brainstormed. ALWAYS ask the user
1. Did anything in this session make the user think the skill should be updated / improved?
2. suggest any obvious improvements to the skill. Did the session lean towards anything that wasn't explicit in the skill that could be added for future sessions? 

**you must always be thinking about how to improve this skill.**
