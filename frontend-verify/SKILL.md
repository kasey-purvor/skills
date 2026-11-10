---
name: frontend-verify
description: Verify a frontend change by driving the actual app through affected journeys and inspecting behaviour, screenshots, relevant browser errors, responsive layouts and keyboard interaction. Use after visible or interactive changes or for an assigned browser verification. Broader usability audits belong to frontend-audit; this does not install test-generation or healing agents.
---

# Frontend verification

Produce evidence that the delivered interface satisfies the assigned change, using the existing app and browser tools. This focused verification does not start frontend-audit or require an HTML report.

## Ownership and preparation

The coordinator supplies requirements, checkout/revision, environment, affected journeys and roles, operational setup and permitted test actions. It dispatches a fresh browser verifier by default when the shared review policy calls for one. Assigned verifiers do only their portion and report to the coordinator; do not dispatch agents, fix code or manage tracker states. Disclose when independent delegation is unavailable.

Read applicable project instructions, frontend conventions and operational setup. Load [dev-standards-handbook](../dev-standards-handbook/SKILL.md) and use its router: frontend-development, the relevant groups of [Front-end Patterns](../dev-standards-handbook/topics/frontend-patterns.md) (the observable-fault catalogue, with its probe sizes) and relevant testing guidance are usual starting points; add identity, contracts or other chapters when the change concerns them. State the selection and reason within the authorised assignment. Do not recursively launch code review from the router. Source inspection can aid setup or diagnosis, but verification claims require the running interface.

Identify the running build: checkout/commit plus a dirty-tree fingerprint when needed, or deployed version. Local success is not deployment evidence. Report a coverage gap if the build cannot be matched to the change. Coordinate a stable revision; a server changed during the run may invalidate evidence.

## Browser and data boundaries

- Prefer the project's existing Playwright runner or documented browser tooling. Load the relevant browser skill before using its tools when available. Use the actual dev server, existing end-to-end harness or agreed deployment; describe fixture/mock boundaries honestly.
- Verify browser isolation. Separate tabs may share a profile. Prefer isolated contexts/profiles and distinguishable test records; if only a shared signed-in browser is available, assign one owner at a time with explicit handoff. Never interfere with another agent's browser.
- Honour project restrictions on shared Playwright tools. Reuse documented sign-in or approved accounts; never extract/copy a person's credentials, print secrets or include them in evidence. Missing access is a blocker or coverage gap, not permission to bypass authentication.
- Exercise writes only within authorised environment/test-data boundaries. Follow project test-inbox rules and load mailbox-agents for mail journeys. Preserve protected fixtures, record changes and follow the project's cleanup policy. Without a cleanup policy or explicit instruction, do not delete records as routine cleanup. A verification assignment does not authorise production mutations.
- Reach states through supported actions and documented fixtures. Do not substitute a hand-built interface or fabricate a successful state to fill coverage gaps.

## Drive and inspect

Choose checks from the affected requirements and handbook rather than extending a local change into a whole-app audit:

1. Complete the changed journey, checking expected outcomes, persistence and return navigation where relevant. Check related regressions affected by the change.
2. Exercise meaningful ordinary, empty, validation/error, loading and success states as applicable and reachable. Cover roles whose behaviour changed. Record inaccessible states and why they were not exercised.
3. Inspect desktop and narrow layouts for visible changes, including relevant long content, wrapping, clipping and control reach. Exercise keyboard navigation and focus for changed interactions. Describe accessibility coverage accurately; limited keyboard checks do not establish full compliance.
4. Inspect relevant console errors and failed requests produced during the journey. Distinguish reproduced, pre-existing and unresolved problems without exposing credentials or sensitive content.
5. Capture important rendered states and **open and inspect the images**. Record actions and before/after outcomes supporting behavioural claims: a screenshot alone does not prove an interaction worked. Wait for observable settled conditions rather than arbitrary delays.

Keep screenshots/traces local unless the project explicitly requires authorised tracker attachments. Do not publish previews externally or commit evidence artifacts into the product repository. The coordinator posts evidence unless uploads are explicitly assigned to the verifier.

Use existing tests or a small disposable browser driver when useful. Do not install Playwright planner/generator/healer agents, generate a new regression suite or auto-heal assertions in this workflow. Confirmed defects can go to a fixer following the ordinary TDD and regression-test requirements; those existing requirements still apply.

## Return evidence

Return:

- Tested revision/build, environment, roles and viewports, including limits on matching them to the change.
- Requirements/journeys checked with observed outcomes: passed, failed or not verified.
- Screenshot/trace paths, meaningful browser errors, reproduction steps, data changes and records left behind. Exclude credentials, session files and raw action-link tokens.
- Confirmed findings ranked by impact using [stream/review-findings.md](../stream/review-findings.md), plus coverage gaps and blockers. Report to the coordinator; do not create tracker work yourself.

Claim completion only to the extent supported by the evidence. A material unverified prerequisite/state yields a partial or blocked result rather than a full pass. After fixes, rerun affected journeys against the new revision with fresh evidence. Recheck wider behaviour only when the fix invalidates earlier coverage.
