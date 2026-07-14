---
name: to-prd
description: Turn the current conversation context into a PRD and write it to docs/PRD/ as a markdown file. Use when user wants to create a PRD from the current context.
---

This skill takes the current conversation context and codebase understanding and produces a PRD. Do NOT interview the user — just synthesize what you already know.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. Invoke the `dev-standards-handbook` skill and use its router to decide which chapters apply to this feature. These get recorded in the PRD's **Applicable Standards** section so `/to-issues` can carry them onto each issue and implementing agents can reload them. This comes before the module sketch because a flagged chapter can change which modules you propose (e.g. multi-tenant-isolation puts tenant filtering in a scoped data layer; schema-evolution may make a migration its own piece of work).

3. Sketch out the major modules you will need to build or modify. Actively look for opportunities to extract **deep modules** that can be tested in isolation — a lot of behaviour hidden behind a small interface. Before proposing any module, read `topics/module-design.md` in the `dev-standards-handbook` skill and design to it: answer its "Before Proposing a Module" questions, apply the deletion test to every proposed module, and sketch the interface twice before committing.

   Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

4. Write the PRD using the template below, then save it as `docs/PRD/YYYY-MM-DD-<feature-slug>.md` in the repo. Use today's date (YYYY-MM-DD) and a kebab-case feature slug. Example: `docs/PRD/2026-05-27-tenant-invite-quota.md`.

The PRD is a planning artifact, not an implementable issue — do not create a Linear issue for it. The follow-up `/to-issues` skill breaks the PRD into implementable issues that reference back to this file.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified (and why each is a deep module — see above)
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Applicable Standards

The `dev-standards-handbook` chapters that apply to this feature (from step 2), one line each on what it governs here. Example:

- `module-design` — the two new modules proposed under Implementation Decisions
- `api-design` — the new endpoints' response shapes
- `schema-evolution` — the migration adding the invite-quota column

`/to-issues` carries these onto each issue; implementing agents reload the named chapters rather than working from the PRD alone.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
