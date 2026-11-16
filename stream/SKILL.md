---
name: stream
description: How multi-ticket agent work is planned, run and recorded in Linear as streams - the stream ticket, what happens to code-review findings, and the close checklist. Use when planning, starting, resuming or closing a stream, or when a code review produces findings.
---

# Stream

How multi-ticket work is planned, run and recorded in Linear. These are defaults, not hard rules: the human steers, and what they say in the session wins. Linear mechanics (labels, statuses, tool recipes) are in the `linear` skill.

## Vocabulary

| Term | Meaning |
|---|---|
| **Team** | One app. One repo maps to one Linear team. |
| **Epic** | A Linear project: an outcome with an end. |
| **Stream** | A set of tickets handed to one orchestrator session, recorded as a stream ticket. It may take tickets from several epics. It ends when its work is finished, not on a date, and it does not use Linear Cycles. |
| **Lane** | One builder, one branch and one pull request inside a stream. A stream has one or more lanes. |

"Cluster" and "batch" are retired: say epic and lane.

Streams are optional. Suggest one when the human plans several tickets as one piece of work, or hands you several at once: a stream gives the session one place to coordinate and record them. When tickets simply come one after another in a session, carry on without one. A lone ticket runs without one.

## Suggest, don't act

On scope, plans, review findings and records, the human decides. You suggest, with your reason. You can do these without asking:

- **Bookkeeping:** comments on the stream ticket, its Session line, and status moves that follow work already done.
- **Messaging other sessions.**
- **Fixing review findings inside the stream,** and dropping trivial non-security ones with a line saying why.
- **Close bookkeeping,** once the human has settled the leftovers.

Building, pushing and merging follow the repo's agent instructions and the human's own instructions as before.

## Tickets in a stream

A ticket whose parent is a stream ticket is part of that stream. Worth reading before starting one: the last few status updates on the ticket's project.

Other sessions read a stream ticket's Touches section to see what the stream is working on, so keep it current.

## Who does what in a lane

The orchestrator runs the stream: the stream ticket, the pane pins and the close. Builder and reviewer subagents leave those alone and report to the orchestrator. Nor do they run the check with other sessions, which the repo's agent instructions give to the agent the human is talking to. (A reply to a subagent's message goes to its parent session, so a subagent running the check would wait forever.) A subagent reporting findings gives a ranked list, as [review-findings.md](review-findings.md) describes. The shared builder procedure is [builder.md](builder.md); reviewer procedures are [review-code-change](../review-code-change/SKILL.md) and [verify-frontend-change](../verify-frontend-change/SKILL.md). Harness-specific lane agents load these procedures rather than maintaining their own review checklists.

## Running a stream

- **Pin it.** Follow the Ticket Panel section of the shared global instructions (`CLAUDE.md`, also loaded by Codex), the one place the pane rules live: the stream ticket first, then each ticket as it is picked up, and nothing is detached unless the human asks.
- **Keep the Session line current.** It names the session running the stream, so other agents know who to message. A session picking up an existing stream sets it to its own name.
- **The description is the plan.** Update it when the plan changes, Touches included.
- **Comments are the log.** One short comment per event: a decision the human made, a pull request opened or merged, a change to the plan, a review's findings and what happened to them, a blocker. Routine progress gets no comment.
- **Reviews:** at a completed lane or pull request, the routine reviews start without asking: dispatch `review-code-change` and add `verify-frontend-change` for visible or interactive changes. Give each worker an exact target and scoped brief. The orchestrator owns findings and records; workers do not restart orchestration. The human can defer or narrow the routine reviews. Recommend extra specialists with a reason and obtain approval before dispatching them. After fixes, obtain verification against the new revision before treating the findings as resolved.
- **Ending a session mid-stream:** record anything unrecorded as a comment, then use the `handoff` skill as usual. The handoff file names the stream ticket and does not restate the plan.

The stream ticket's shape and the close checklist are in [stream-ticket.md](stream-ticket.md).

## Review findings

A stream cleans up after itself: it isn't finished until every review finding is fixed, dropped or settled by the human. The outcomes and the report format are in [review-findings.md](review-findings.md). They apply to lone tickets too.

## Documents

Don't create other Linear documents unless the human asks for one. The stream ticket and the project status updates are the record.
