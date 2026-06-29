# Triage Labels

The skills speak in terms of canonical triage roles. This repo's tracker is **Linear** (team `Cloud Assist`, key `CLO`), which combines workflow **states** with a `triage` **label group**, so each role maps to a state and/or a label.

| Canonical role    | In our Linear tracker                                    | Meaning                                  |
| ----------------- | -------------------------------------------------------- | ---------------------------------------- |
| `needs-triage`    | **Triage** state (no label)                              | Maintainer needs to evaluate this issue  |
| `needs-info`      | stays in **Triage** state + `needs-info` label          | Waiting on reporter for more information |
| `ready-for-agent` | **Todo** state + `ready-for-agent` label                | Fully specified, ready for an AFK agent  |
| `wontfix`         | **Canceled** state (or **Duplicate**)                   | Will not be actioned                     |

**`ready-for-human` is NOT used here** (removed from the workspace). Tickets that need a human to implement just go to **Todo** (or **Backlog** if still rough) with no special triage label — they sit in the normal queue.

There is also an `agent-blocked` label: an agent is mid-task but blocked on human input; remove the label to resume.

When a skill mentions a role, use the corresponding state/label from this table.
