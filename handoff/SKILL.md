---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

The handoff is the home for **transient session state** — branch/push state, commits ahead, what's left to do, known-flaky tests, parked stashes, "where the cursor is." That's exactly the bookkeeping that must **not** clutter the ticket (which records decisions + state transitions, not session status — see AGENTS.md § Lifecycle, step 4). Durable decisions belong in the ticket and are *referenced* here by id/URL; transient status belongs **here** and nowhere else.

State the continuation model explicitly, up front: whether the next session **continues the same pull request** — so it *resumes the existing branch and worktree* (name both, and give the worktree path) — or **starts a new pull request** — so it *cuts a new branch and worktree*. This single line removes the ambiguity that otherwise makes a picking-up agent stop and ask which worktree it should be working in.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
