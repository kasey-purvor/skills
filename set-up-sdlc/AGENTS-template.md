<!--
THE TEMPLATE for a repo's agent instructions file. Read by the setup agent.

How it is marked:
- Text written out in full is fixed. Copy it word for word. Do not reword, trim or improve it.
- [Square brackets] mark a blank. Fill each one as section-guide.md says.
- A comment starting "setup:" marks a section that is worked out with the repo's owner.
  Follow the file it names, write the section, and delete the comment.
The finished file has no brackets and no comments, this one included.
-->

# Agent instructions

[One sentence saying what the product is.]

## House rules

This codebase will outlive you. Every shortcut becomes someone else's burden; every hack compounds into technical debt. You are shaping the project — the patterns you establish get copied, the corners you cut get cut again. Fight entropy. Leave the codebase better than you found it.

These rules are the same in every repo that uses this setup.

| | Rule |
| --- | --- |
| Models | Subagents doing code work run on Opus at extra-high effort (on Codex, Sol at extra-high). Research and other work that is not about code runs on Sonnet (on Codex, Luna). A different model only when the human asks. |
| Reviews | When a change is ready, the routine reviews start without asking. Anything heavier is suggested with a reason and waits for a yes. |
| Fix rounds | A builder that has finished is never resumed. Each round of review fixes, and any later work, goes to a fresh builder. A builder that is still running can be told of a change of plan. A reviewer is different: the same reviewer is resumed to check the fix. |
| Credit | Nothing you write credits an AI: not a commit, a pull request or a ticket. |
| Naming | Every name follows these rules. Prefixes are consistent across the project. The thing comes first and its role second: `course.repository.ts`, not `repository-course.ts`. TypeScript: kebab-case for files and folders, PascalCase for React component files, camelCase for variables and functions. Python: snake_case for files, folders, variables and functions, PascalCase for classes. |
| Decisions | Record a decision, a change of scope or a blocker on its ticket when it happens, and before any handoff. One that lives only in the chat is lost when the session ends. |
| Secrets | Never print, log or paste a credential. Fetch it at the moment you use it. |
| Other sessions | Before starting a ticket, tell the other sessions working in this repo what you are about to touch, and ask whether it clashes. If one does not answer and the work may overlap, raise it with the human. Only the agent the human is talking to does this. A subagent never does. |
| This file | If something you learn or change makes a line in this file untrue, or the setup stops fitting the project, tell the human. Do not change the file yourself. |

## Skills

Load the skill when its moment comes. Each one holds its own procedure; nothing here repeats it.

| When | Skill | What it is for | Who uses it |
| --- | --- | --- | --- |
| Deciding what to build | `grill-with-docs` | Questions an idea against the project's vocabulary and past decisions until it is clear. | You, with the human |
| | `to-prd` | Writes the agreed idea up as a requirements document. | You |
| | `to-issues` | Breaks a plan into tickets that can each be picked up alone. | You |
| Building | `stream` | Optional. For several tickets planned as one piece of work: a parent ticket that gives one session a place to coordinate and record them. | You, as orchestrator |
| | `review-code-change` | Reviews a finished change with fresh reviewers. | Subagents you send |
| | `verify-frontend-change` | Checks a visible change by using the real app. | A subagent you send |
| Any time | `linear` | Everything about tickets: statuses, labels, what a good ticket holds. | Anyone who touches a ticket |
| | `session-wrap-up` | When the human is wrapping up: proposes what from the session is worth keeping. | You, with the human |
| | `handoff` | When a session ends with work unfinished: writes the note for the next one. | You |
| | `dev-standards-handbook` | The house engineering standards, by chapter. Read the chapters a change touches before planning or building it. | You, builders and the ticket reviewer |

## Subagents

A subagent is a separate agent you send to do one job and report back. You send all of them; none of them sends another.

| Subagent | What it does | What it works from |
| --- | --- | --- |
| Builder | Builds the tickets in its brief, tests first, in its own worktree. The brief may be one ticket or one lane of a stream. | Its own definition. Test-driven development. `diagnose` when something fails unexpectedly. The handbook chapters you name in its brief. |
| Ticket reviewer | Checks a finished change against its ticket, its tests and the standards. | `review-code-change`. The handbook chapters you name in its brief. |
| Bug hunter | Reads only the code of a finished change, looking for bugs. | `review-code-change`. |
| Frontend verifier | Drives the real app through the journeys a change affects. | `verify-frontend-change`. |

In every brief to a builder or a ticket reviewer, name the handbook chapters it must read, each by file. Take them from the ticket's Standards line and add any the work plainly touches. Its report says which it read.

A builder moves each of its tickets to In Progress when it starts, and records its decisions on them as it goes. Check both when it reports. No other subagent changes a ticket. None of them writes to a context file, except a builder landing an ADR change carried in its brief. They report to you, and you decide what happens next.

## Context files

These are the files that explain the project. Read the ones your task touches.

| File | What it holds |
| --- | --- |
| `AGENTS.md` | This file: what every session needs before any task. |
| `CONTEXT.md` | The vocabulary: each term of the product and what it means. |
| `docs/adr/` | Architecture decision records (ADRs): one file per decision that is hard to reverse, with its reason and the options turned down. |
| `docs/decisions.md` | Rulings the human made that no ADR covers, one line each. |
| `docs/pitfalls.md` | Traps in this repo that cost time and will recur, one line each. |
| `docs/PRD/` | Requirements documents, one for each agreed idea, written with `to-prd`. |
| `docs/agents/domain.md` | The rules for all of the above: what belongs in each file and what does not. |
| `README.md` | What the project is and how to get it running. |

**Ask the human first, every time,** before you:
- add to, change or remove anything in any of these files, this one included;
- create a new context file, ADR, planning document or folder for them;
- start any new way of keeping context, such as a notes file, a log or a memory scheme.

The one exception is an ADR: when a ticket or plan the human approved carries the exact new wording, land it unchanged without asking again. Code files and folders need no permission.

## How work is done

Work is in one of two modes. Each is a short path, and each step names the skill or subagent from the tables above.

### Tickets

Product work always has a ticket. Changes to agent tooling (skills, this file, hooks) have none. This repo's tickets are in the Linear team **[team name]**, prefix **[PREFIX]**. For everything else about tickets, load the `linear` skill.

### Worktrees

A worktree is a second working folder on its own branch, sharing the repo's history. It is how several agents build at once without treading on each other.

- All building happens in a worktree, never in the main folder. The main folder stays on `main`.
- One branch, one worktree, one pull request. Branches are cut from `origin/main` and named `<user>/<ticket-id>-<slug>`, main ticket first.
- Worktrees live in `.claude/worktrees/`, named for the ticket: `.claude/worktrees/[prefix]-123`.
- A worktree you did not start in belongs to another session. Leave it alone.
- Run `[install command]` in every new worktree before working there. A new worktree starts without the installed packages and without a working commit hook.

### Deciding what to build

| Step | What happens | Skill |
| --- | --- | --- |
| 1. Question it | You and the human question the idea until it is clear. The vocabulary and the ADRs are updated as decisions are made, with the human there. | `grill-with-docs` |
| 2. Write it up | The agreed idea becomes a requirements document. | `to-prd` |
| 3. Break it down | The plan becomes tickets, which wait in Backlog. | `to-issues`, `linear` |
| 4. Choose | The human picks what to start. Nothing starts without that. | |

### Building

<!-- setup: word steps 4, 7 and 8 from the Git and CI/CD answers. Do this after that section is agreed. -->

| Step | What happens | Who | Skill |
| --- | --- | --- | --- |
| 1. Check | Check with the other sessions (a house rule), and re-audit the ticket. | You | `linear` |
| 2. Set up | A worktree and a branch for the work. | You | |
| 3. Build | Tests first, then the code, with evidence that it works. The full local check passes before the work is handed on. | You, or a builder | |
| 4. Pull request | [When the pull request is pushed and opened.] CI runs. | You | |
| 5. Review | The ticket reviewer and the bug hunter, at the same time. The frontend verifier too, for a visible change. | Subagents | `review-code-change`, `verify-frontend-change` |
| 6. Fix | Each round of fixes goes to a fresh builder, and the same reviewer checks the fix. | A builder | `review-code-change` |
| 7. Merge | Once CI is green and the review is clean. | [Who merges] | |
| 8. Prove | [Where the change is proved], with the evidence on the ticket. Then the ticket is finished. | You | `linear` |

**A ticket goes through those steps by itself.** That is the normal case. If the human gives you another ticket when one is finished, carry on with it the same way.

**A stream is optional.** Offer one when the human plans several tickets as one piece of work, or hands you several at once. Do not start one just because a second ticket follows the first.

A stream is a parent ticket with the work's tickets beneath it. It gives one session, the orchestrator, a place to coordinate and record the work, and it is how one session finishes many tickets without supervision. As orchestrator you split the tickets into lanes, and each lane goes through steps 2 to 6 with its own builder. A lane is one builder, one branch and one pull request, and may hold several tickets. The stream is finished when every review finding is fixed, dropped or settled by the human.

## Git and CI/CD

<!-- setup: the whole section. Follow git-and-cicd.md. -->

## About this repo

<!-- setup: the stack table, then the rules that hold across the code. Follow "About this repo" in section-guide.md. -->
