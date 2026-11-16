---
name: review-code-change
description: Review a completed code change with independent reviewers. One checks it against its ticket, its tests and the handbook standards; one hunts for bugs in the code. Use at a delivery boundary (a finished lane, pull request or standalone change), or when asked to review a change or hunt for bugs in one. Also holds what happens to each finding: fixed, dropped or made a ticket. Browser journeys belong to verify-frontend-change; a requested usability audit belongs to audit-frontend.
---

# Review a code change

A change is reviewed by separate reviewers, each with one question. The session the human talks to is the coordinator: it sends every reviewer and owns what comes back. The repo's agent instructions say when to run this skill. Use this procedure in Claude Code and Codex; a native review command can help but must satisfy the same contract.

**Dispatched as a reviewer?** This file is for the coordinator. Load the procedure file your brief names and follow only that. If the brief names none, use [against-ticket.md](against-ticket.md).

## The reviews

| Review | Its question | Procedure | The brief gives it |
|---|---|---|---|
| Against the ticket | Did the change build what was asked, to the repo's standards, with tests that pin it? | [against-ticket.md](against-ticket.md) | The requirements (ticket or task brief), the target, applicable instructions, existing verification evidence, access limits |
| Bug hunt | Does the code that was written break? | [bug-hunt.md](bug-hunt.md) | The target, and one or two sentences on what the change is meant to do |
| Frontend check | Does it work in the running app? | the [verify-frontend-change](../verify-frontend-change/SKILL.md) skill | See that skill. Visible or interactive changes only |

The two code reviews read different things and do not repeat each other. The ticket reviewer needs the ticket and the handbook; the bug hunter needs only the code, plus enough of the intent to tell a deliberate change from a regression.

## Sending the reviewers

- Send one ticket reviewer and one bug hunter by default, each a fresh subagent, at the same time. Add the frontend check for a visible or interactive change.
- Give each a focused brief with what the table lists, and the name of its procedure file. Do not pass the builder's conversation or a proposed verdict. Use the model and effort the repo's agent instructions give for review work.
- A reviewer completes only its own assignment and reports to the coordinator. It does not send other reviewers, edit product code or tracker records, or run the check with other sessions or any pane bookkeeping.
- For a large change, suggest a second bug hunter or a specialist, with the reason, and wait for the human's yes. More reviewers are not a quota.
- If delegation is unavailable, work through both procedures yourself, one after the other, and say that the review was not independent. Do not claim an independent pass.

## Establish the target

Resolve the target before sending anyone, and put the result in every brief: the base and target commit ids, the checkout, and which kind of target it is. For an automatic branch review, infer the integration branch from repository instructions or the remote default; ask only if the comparison remains ambiguous.

- Branch: the merge-base-to-target patch, for example git diff BASE...TARGET, and the intervening commits.
- One commit: that commit's patch, not the whole branch.
- Working tree: staged, unstaged and relevant untracked files. Record the base commit and a diff/content fingerprint; committed changes alone do not cover this target.
- Explicit files outside Git: the supplied before/after snapshot and bounded file list. Do not invent history or include unrelated pre-existing edits.

Coordinate a stable review interval. If the target changes, identify what needs rechecking. Never inspect another session's worktree merely because it exists.

## When the reports come back

Merge the reports into one ranked list. Where two reviewers report the same defect, keep one entry and note both saw it. Use [review-findings.md](review-findings.md) for what happens to each finding and for the report the human gets. The coordinator owns fixes, records and decisions. A standalone local review need not invent a ticket or stream.

After fixes, the reviewer that raised a finding rechecks the changed code and the assumptions it affects; the coordinator obtains relevant checks and browser reruns. Record the new reviewed revision. Reopen a broader review only when a fix invalidates earlier coverage. Report blockers, material disagreements and unverifiable claims instead of claiming a clean pass or starting an unbounded loop. Review reports do not themselves trigger another automatic review.
