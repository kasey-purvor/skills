---
name: change-review
description: Independently review a completed change, branch, commit or working tree for correctness, requirements, test quality and applicable handbook standards. Use at a delivery boundary or when asked to review changes. Browser journeys belong to frontend-verify; a requested usability audit belongs to frontend-audit.
---

# Change review

Assess the change against its requirements and applicable standards. The shared review policy in the current global instructions controls when to run this skill. Use this procedure in Claude Code and Codex; a native review command can help but must satisfy the same contract.

## Ownership

- The coordinator establishes the scope and dispatches one fresh reviewer by default. Supply the requirements, exact review target, applicable instructions, existing verification evidence and access constraints. Give a focused brief rather than the builder's conversation or proposed verdict. Follow the user's model and effort policy.
- An assigned reviewer completes only that assignment and reports to the coordinator. Do not dispatch another review, edit product code or tracker records, or run the stream's clash check and pane bookkeeping. Loading this skill inside a reviewer does not make it a coordinator.
- Suggest additional specialists when risk or size warrants them; follow the global policy for approval. Multiple reviewers are not a quota. If delegation is unavailable, disclose that independence is missing; do not claim an independent pass.

## Establish the target

Use the supplied base and target. For an automatic branch review, infer the integration branch from repository instructions or the remote default; ask only if the comparison remains ambiguous. Resolve references to commit ids and record the checkout.

- Branch: review the merge-base-to-target patch, for example git diff BASE...TARGET, and the intervening commits.
- One commit: inspect that commit's patch, not the whole branch.
- Working tree: include staged, unstaged and relevant untracked files. Record the base commit and a diff/content fingerprint; committed changes alone do not cover this target.
- Explicit files outside Git: use the supplied before/after snapshot and bounded file list. Do not invent history or include unrelated pre-existing edits.

Read the patch and surrounding execution paths. Coordinate a stable review interval. If the target changes, identify what needs rechecking. Never inspect another session's worktree merely because it exists.

## Requirements and handbook

Use the originating ticket, approved plan or supplied task as the specification. When a ticket is involved, load the linear skill and read its description **and comments**. A tooling change without a ticket can use its authorised task brief; do not create tracker work just to review it. Disclose missing requirements rather than inventing acceptance criteria.

Read applicable repository instructions and domain decisions: the ADRs and `docs/decisions.md` when present, so a deliberate choice is not reported as a defect; name the decision when you set a concern aside for that reason. A new line in `docs/decisions.md` or `docs/pitfalls.md` (or in the handbook's `topics/environment.md`) inside the change is reviewed like code: it must fit the shape `docs/agents/domain.md` gives (for a handbook line, the shape in `topics/environment.md`) and be one the human approved in a session review: a repo line appears in the pull request body's list of approved lines; a handbook line is one the human commits themselves. Load [dev-standards-handbook](../dev-standards-handbook/SKILL.md), use its router and the ticket's Standards line, and read the relevant chapters before reviewing. State the chapter selection and reason to the coordinator; add concerns revealed by the actual change. Routine chapter selection is inside the authorised review, not a fresh approval request. The router's reference back to this skill does not start another review.

Calibrate rigor to the project and risk. The handbook owns topic guidance: use its frontend, identity/isolation, schema, network and deployment modifiers when applicable instead of copying permanent topic checklists here. Cite the relevant rule for a standards finding. A recommendation is not automatically a defect or permission to expand scope.

## Assess and verify

Cover these concerns together unless the coordinator has split the assignment:

- Correctness and regressions: trace behaviour, callers, failures, state transitions and relevant boundaries.
- Requirements: identify missing/incorrect behaviour and material unintended changes. Separate implementation defects from proposed specification improvements.
- Test quality: check that assertions pin required behaviour and would detect the relevant defect. Inspect available failing-then-passing evidence where TDD is required; a green suite does not establish test order. Record missing evidence as a verification gap. Never weaken, skip or rewrite a test simply to obtain green.
- Standards and maintainability: apply the selected chapters and repository conventions with concrete consequences, avoiding personal style preferences. Existing lint/type checks supply their own results; avoid duplicating their routine output as findings.

Verify findings against current source and, where useful and authorised, a focused test or reproduction. Separate confirmed findings from unresolved leads. Do not edit the app during review. Test execution does not grant permission for production mutations or messages to real recipients. Assign browser work through [frontend-verify](../frontend-verify/SKILL.md); code inspection is not browser coverage.

## Report and fixes

Return the reviewed target, selected handbook chapters, checks actually performed and coverage gaps, followed by one ranked findings list. Each finding needs severity, a precise file/line or evidence anchor, the affected requirement/standard, what is wrong, why it matters, supporting evidence and the suggested outcome with its reason.

Use [stream/review-findings.md](../stream/review-findings.md) for findings disposition and the user-facing report. The coordinator owns fixes, records and decisions. Reviewers do not file tickets or drop security findings themselves. A standalone local review need not invent a ticket or stream.

After fixes, the prior reviewer rechecks the changed code and affected assumptions; the coordinator obtains relevant checks and browser reruns. Record the new reviewed revision. Reopen broader review only when a fix invalidates earlier coverage. Report blockers, material disagreements and unverifiable claims instead of claiming a clean pass or starting an unbounded loop. Review reports do not themselves trigger another automatic review.
