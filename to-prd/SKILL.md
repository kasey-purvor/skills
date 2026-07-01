---
name: to-prd
description: Turn the current conversation context into a PRD and write it to docs/PRD/ as a markdown file. Use when user wants to create a PRD from the current context.
---

This skill takes the current conversation context and codebase understanding and produces a PRD. Do NOT interview the user — just synthesize what you already know.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. Sketch out the major modules you will need to build or modify. Actively look for opportunities to extract **deep modules** that can be tested in isolation.

   **Deep vs shallow modules** — from John Ousterhout's *A Philosophy of Software Design*. Think of a module's worth as the ratio of the functionality it provides to the complexity of its interface. That ratio is its **depth**.

   - A **deep module** hides a lot of implementation behind a small, simple interface — powerful functionality, minimal surface area. The classic example is Unix file I/O: `open` / `read` / `write` / `close` is a tiny interface over enormous hidden complexity (disk layout, buffering, scheduling, permissions). The interface is far simpler than the implementation, so callers get leverage without paying for the complexity.
   - A **shallow module** has an interface nearly as complex as its implementation — it hides little. Symptoms: rows of thin pass-through methods, or a class whose signature already tells you everything it does. Each shallow module still charges an interface cost (one more thing to learn and wire up) while buying almost no abstraction; enough of them and the interfaces cost more than they save.
   - Design for interfaces **much simpler than** their implementations. That gap is also what makes a module testable in isolation — the interface becomes a genuine seam.
   - **Deletion test:** imagine deleting the module. If the complexity simply vanishes, it was a pass-through and shouldn't exist. If the same complexity reappears, duplicated across its callers, the module was earning its keep.

   Check with the user that these modules match their expectations. Check with the user which modules they want tests written for.

3. Write the PRD using the template below, then save it as `docs/PRD/YYYY-MM-DD-<feature-slug>.md` in the repo. Use today's date (YYYY-MM-DD) and a kebab-case feature slug. Example: `docs/PRD/2026-05-27-tenant-invite-quota.md`.

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
