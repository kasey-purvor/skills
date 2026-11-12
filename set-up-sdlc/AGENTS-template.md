<!--
DRAFT, 12 Nov 2026. The new skeleton for a repo's AGENTS.md, replacing
AGENTS-portable-template.md once it is complete.

Written so far: the one group below ("How a change is made and shipped here").
Not written yet: what this repo is; the skills this workflow uses; the context
files; what every session needs to know about this repo.

How to read it: a plain line is the same in every repo. A `<slot>` is this
repo's answer, which setup fills by asking. Nothing here restates a procedure:
the procedure lives in the skill the line names.
-->

## How a change is made and shipped here

### The path of a change

The steps are the same in every repo. Each line is either a pointer to the
skill that holds the procedure, or this repo's answer.

**1. Starting work**

- Product work always has a ticket. Changes to agent tooling (skills, this file, hooks) have none.
- Before starting a ticket: the `stream` skill (check no other session is on it) and the `linear` skill (re-audit the ticket).
- Branches are cut from `<base branch>` and named `<pattern>`.
- Worktrees: `<used, kept in <folder> | not used>`.

**2. While working**

- A ticket's `Standards:` line names the `dev-standards-handbook` chapters to read before starting.
- Each commit runs `<what the commit hook runs>`.
- Run before handing work back: `<command | nothing, CI runs the tests>`.
- Subagents that write code: `<used | not used>`. Their rules are in the `stream` skill's builder file.

**3. Review**

- When a change is ready, these start without asking: `<reviews, such as review-code-change, and verify-frontend-change for a visible change>`.
- Anything heavier is suggested with a reason and waits for a yes.
- Review findings: `<a fresh agent fixes each round | the builder fixes them>`, and the same reviewer checks the fix.
- Evidence this repo expects on a ticket: `<what proves a change here>`.

**4. Pull request and merge**

- An agent pushes `<only when asked | when the branch is ready>`, `<once | as often as needed>`.
- Before a merge, these must pass: `<checks>`.
- Approvals needed: `<how many, and from whom>`.
- Who merges: `<the human | the agent, once <conditions>>`.
- A ticket is Done when it is `<merged | merged and proven in <environment>>`.
- Never: `<this repo's git never-do rules, one line each>`.

### This repo's setup

**Environments**

| Environment | What it is for | Where it runs | What data it holds |
| --- | --- | --- | --- |
| `<name>` | `<purpose>` | `<pointer>` | `<its own records | a masked copy | test data from a script>` |

A project nobody depends on yet may have one row.

**What runs when**

| When | What runs |
| --- | --- |
| On every pull request | `<checks>` |
| On merge | `<checks, and any deploy>` |
| On release to production | `<checks and gates>` |
| On a schedule | `<jobs>`. When one fails or does not run, `<who is told, and how>`. |

**Releasing**

- A change reaches each environment by `<how>`.
- A release to production is started by `<who>`.
- An agent never `<this repo's release never-do rules, one line each>`.

**Test data and logins**

- Test data comes from `<script>`, which refuses to run against production.
- Test logins are kept in `<where: a pointer, never a value>`.
- Never delete: `<each standing fixture by name, one line each>`.
- A test environment cannot `<send real email | take real payments>` because `<how that is prevented here>`.
