---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Before writing, offer the user a session wrap-up (the `session-wrap-up` skill), unless one was just run or declined in this session. If they say no or not now, carry on.

Include a "suggested skills" section in the document, which suggests skills that the agent should invoke.

Do not duplicate content already captured in other artifacts (PRDs, plans, ADRs, issues/tickets, commits, diffs). Reference them by path or URL instead.

The handoff is the home for **transient session state** — branch/push state, commits ahead, what's left to do, known-flaky tests, parked stashes, "where the cursor is." That's exactly the bookkeeping that must **not** clutter the ticket (which records decisions + state transitions, not session status — see AGENTS.md § Lifecycle, step 4). Durable decisions belong in the ticket and are *referenced* here by id/URL; transient status belongs **here** and nowhere else.

State the continuation model explicitly, up front: whether the next session **continues the same pull request** — so it *resumes the existing branch and worktree* (name both, and give the worktree path) — or **starts a new pull request** — so it *cuts a new branch and worktree*. This single line removes the ambiguity that otherwise makes a picking-up agent stop and ask which worktree it should be working in.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

**Exception — app login credentials are passed on, not redacted** (Kasey's standing instruction, 2026-10-02). If Kasey gave login credentials for the app being worked on during the session (email and password for the live app, a test account, and so on), put them in the handoff in a clearly headed section near the top, with what the login is (role, tenant, anything it cannot reach), so the next agent never has to ask for them again. Because the file then holds a password: keep it outside any repository and set it to mode 600. This exception covers app logins Kasey supplied; API keys, service-role keys, tokens and database URLs are still redacted.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.