---
name: stream
description: How multi-ticket agent work is planned, run and recorded in Linear as streams - the stream ticket, the clash check with other running sessions, what happens to code-review findings, the team document, and the close checklist. Use before starting any ticket, when planning, starting, resuming or closing a stream, when a code review produces findings, or when reading or writing a team document.
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

Streams are optional. When you are handed two or more tickets, suggest one. A lone ticket runs without one.

## Suggest, don't act

On scope, plans, review findings and records, the human decides. You suggest, with your reason. You can do these without asking:

- **Bookkeeping:** comments on the stream ticket, its Session line, and status moves that follow work already done.
- **Messaging other sessions.**
- **Fixing review findings inside the stream,** and dropping trivial non-security ones with a line saying why.
- **Close bookkeeping,** once the human has settled the leftovers.

Building, pushing and merging follow `AGENTS.md` and the human's own instructions as before.

## Before starting a ticket

Check with the other sessions working in this repo so you don't collide. List the live sessions and the team's In Progress stream tickets (label `stream`), and message each session one line: "Starting VAN-123, will touch `<areas>`. Any clash?" Carry on reading while they answer. If one doesn't answer, its stream ticket's Touches section says what it is working on; if that overlaps with your ticket, raise it with the human.

Also worth reading: the last few status updates on the ticket's project, and the team document.

A ticket whose parent is a stream ticket is part of that stream. A lone ticket still gets this check and the review-findings rules.

## Who does what in a lane

The orchestrator runs the stream: the check above, the stream ticket, the pane pins and the close. Builder and reviewer subagents leave those alone and report to the orchestrator. (A reply to a subagent's message goes to its parent session, so a subagent running the check would wait forever.) A subagent reporting findings gives a ranked list, as [review-findings.md](review-findings.md) describes. The shared builder procedure is [lane-builder.md](lane-builder.md); reviewer procedures are [change-review](../change-review/SKILL.md) and [frontend-verify](../frontend-verify/SKILL.md). Harness-specific lane agents load these procedures rather than maintaining their own review checklists.

## Running a stream

- **Pin it.** Follow the Ticket Panel section of the shared global instructions (`CLAUDE.md`, also loaded by Codex), the one place the pane rules live: the stream ticket first, then each ticket as it is picked up, and nothing is detached unless the human asks.
- **Keep the Session line current.** It names the session running the stream, so other agents know who to message. A session picking up an existing stream sets it to its own name.
- **The description is the plan.** Update it when the plan changes, Touches included.
- **Comments are the log.** One short comment per event: a decision the human made, a pull request opened or merged, a change to the plan, a review's findings and what happened to them, a blocker. Routine progress gets no comment.
- **Reviews:** at a completed lane or pull request, follow the shared global review policy: dispatch `change-review` automatically and add `frontend-verify` for visible or interactive changes. Give each worker an exact target and scoped brief. The orchestrator owns findings and records; workers do not restart orchestration. The human can defer or narrow the routine reviews. Recommend extra specialists with a reason and obtain approval before dispatching them. After fixes, obtain verification against the new revision before treating the findings as resolved.
- **Ending a session mid-stream:** record anything unrecorded as a comment, then use the `handoff` skill as usual. The handoff file names the stream ticket and does not restate the plan.

The stream ticket's shape and the close checklist are in [stream-ticket.md](stream-ticket.md).

## Review findings

A stream cleans up after itself: it isn't finished until every review finding is fixed, dropped or settled by the human. The outcomes and the report format are in [review-findings.md](review-findings.md). They apply to lone tickets too.

## Team document

Each team has one team document, a jotting area for app-wide notes. See [team-document.md](team-document.md).

## Documents

Don't create other Linear documents unless the human asks for one. The stream ticket, the project status updates and the team document are the record.
