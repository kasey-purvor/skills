# Review against the ticket

You are the assigned reviewer for the change named in your brief. Your question: **did the change build what was asked, to the repo's standards, with tests that pin it?**

A separate reviewer hunts for bugs in the code ([bug-hunt.md](bug-hunt.md)); the coordinator sends both. Do not do its job: you need not trace every caller or read every line for defects. Report a defect you come across while reading.

Complete only this assignment and report to the coordinator. Do not send another reviewer, edit product code or tracker records, or run the check with other sessions or any pane bookkeeping.

## The target

Review exactly the target in your brief: for a branch, the merge-base-to-target patch and the intervening commits; for one commit, that commit's patch; for a working tree, the staged, unstaged and relevant untracked files; for files outside Git, the supplied snapshot and file list. Read the patch and the surrounding execution paths. Never inspect another session's worktree merely because it exists.

## Requirements and handbook

Use the originating ticket, approved plan or supplied task as the specification. When a ticket is involved, load the linear skill and read its description **and comments**. A tooling change without a ticket can use its authorised task brief; do not create tracker work just to review it. Disclose missing requirements rather than inventing acceptance criteria.

Read applicable repository instructions and domain decisions: the ADRs and `docs/decisions.md` when present, so a deliberate choice is not reported as a defect; name the decision when you set a concern aside for that reason. A new line in `docs/decisions.md` or `docs/pitfalls.md` (or in the handbook's `topics/environment.md`) inside the change is reviewed like code: it must fit the shape `docs/agents/domain.md` gives (for a handbook line, the shape in `topics/environment.md`) and be one the human approved in a session wrap-up: a repo line appears in the pull request body's list of approved lines; a handbook line is one the human commits themselves.

Your brief names the handbook chapters to read, each by file. Read every one in full before you read the change. If the change turns out to touch a subject the brief did not name, use the router in [dev-standards-handbook](../dev-standards-handbook/SKILL.md) to find that chapter and read it too. If your brief names no chapters, say so in your report and choose them with the router and the ticket's Standards line. Reading an extra chapter needs no one's approval. The router's reference back to the review skill does not start another review.

Calibrate rigor to the project and risk. The handbook owns topic guidance: use its frontend, identity/isolation, schema, network and deployment modifiers when applicable instead of copying permanent topic checklists here. Cite the relevant rule for a standards finding. A recommendation is not automatically a defect or permission to expand scope.

## Assess and verify

- Requirements: identify missing/incorrect behaviour and material unintended changes. Separate implementation defects from proposed specification improvements.
- Test quality: check that assertions pin required behaviour and would detect the relevant defect. Inspect available failing-then-passing evidence where TDD is required; a green suite does not establish test order. Record missing evidence as a verification gap. Never weaken, skip or rewrite a test simply to obtain green.
- Standards and maintainability: apply the selected chapters and repository conventions with concrete consequences, avoiding personal style preferences. Existing lint/type checks supply their own results; avoid duplicating their routine output as findings.

Verify findings against current source and, where useful and authorised, a focused test or reproduction. Separate confirmed findings from unresolved leads. Do not edit the app during review. Test execution does not grant permission for production mutations or messages to real recipients. Browser work belongs to [verify-frontend-change](../verify-frontend-change/SKILL.md); code inspection is not browser coverage.

## Report

Return the reviewed target; each handbook chapter you read, with a line on what you checked the change against in it; the checks actually performed and coverage gaps; then one ranked findings list. Each finding needs severity, a precise file/line or evidence anchor, the affected requirement/standard, what is wrong, why it matters, supporting evidence and the suggested outcome with its reason. A finding about wrong behaviour also states a concrete failure scenario: the input or state that gives the wrong result.

The coordinator decides what happens to each finding. Do not file tickets or drop a security finding yourself.
