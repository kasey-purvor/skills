<!--
WORKED EXAMPLE, 12 Nov 2026. What a repo's AGENTS.md could look like under the
new layout, filled in with Connect Assist's rules as they stand today so the
shape can be judged. It is not a template yet, and it changes no repo.
-->

# Agent instructions

Connect Assist is a multi-tenant web application that runs anonymous employee-feedback questionnaires.

## Skills

Load the skill when its moment comes. Each one holds its own procedure; nothing here repeats it.

| When | Skill | What it is for | Who uses it |
| --- | --- | --- | --- |
| Deciding what to build | `grill-with-docs` | Questions an idea against the project's vocabulary and past decisions until it is clear. | You, with the human |
| | `to-prd` | Writes the agreed idea up as a requirements document. | You |
| | `to-issues` | Breaks a plan into tickets that can each be picked up alone. | You |
| Building | `stream` | For two or more tickets: one session runs them all as a stream, recorded on a parent ticket. Also holds the check to make before starting any ticket. | You, as orchestrator |
| | `review-code-change` | Reviews a finished change with fresh reviewers. | Subagents you send |
| | `verify-frontend-change` | Checks a visible change by using the real app. | A subagent you send |
| Any time | `linear` | Everything about tickets: statuses, labels, what a good ticket holds. | Anyone who touches a ticket |
| | `session-wrap-up` | When the human is wrapping up: proposes what from the session is worth keeping. | You, with the human |
| | `handoff` | When a session ends with work unfinished: writes the note for the next one. | You |

## Context files

These are the files that explain the project. Read the ones your task touches.

| File | What it holds |
| --- | --- |
| `AGENTS.md` | This file: what every session needs before any task. |
| `CONTEXT.md` | The vocabulary: each term of the product and what it means. |
| `docs/adr/` | Architecture decision records (ADRs): one file per decision that is hard to reverse, with its reason and the options turned down. |
| `docs/decisions.md` | Rulings the human made that no ADR covers, one line each. |
| `docs/pitfalls.md` | Traps in this repo that cost time and will recur, one line each. |
| `docs/agents/domain.md` | The rules for all of the above: what belongs in each file and what does not. |
| `README.md` | What the project is and how to get it running. |

**Ask the human first, every time,** before you:
- add to, change or remove anything in any of these files, this one included;
- create a new context file, ADR, planning document or folder for them;
- start any new way of keeping context, such as a notes file, a log or a memory scheme.

The one exception is an ADR: when a ticket or plan the human approved carries the exact new wording, land it unchanged without asking again. Code files and folders need no permission.

## How work is done

### Two modes

| Mode | What happens | It ends with |
| --- | --- | --- |
| Deciding what to build | You and the human work out what is wanted and why. | Tickets, each ready to pick up. |
| Building | A ticket becomes a merged change, with evidence that it works. | A merged pull request and a finished ticket. |

### Who does the work

Deciding is done by you, with the human. How building is done depends on how much there is:

| | How it runs |
| --- | --- |
| One ticket | You build it yourself, or brief a builder to build it. |
| Two or more tickets | Suggest a stream. A stream is a parent ticket with the work's tickets beneath it, run by one session, the orchestrator. That is you. You split the tickets into lanes, hand each lane to a builder, send the reviews, and keep the parent ticket current. It is how one session finishes many tickets without supervision. |

A lane is one builder, one branch and one pull request. It may hold several tickets.

A review is always done by fresh subagents, never by whoever built the change. You stay responsible throughout: you brief the subagents, read what they report, and decide what happens to their findings.

| Subagent | What it does |
| --- | --- |
| Builder | Builds the tickets in its brief, with tests and evidence, in its own worktree. The brief may be a single ticket or one lane of a stream. |
| Code reviewers (two) | One checks the change against its ticket and the standards. One hunts for bugs. |
| Frontend verifier | Drives the real app through the journeys a change affects. |

### Tickets

Product work always has a ticket. Changes to agent tooling (skills, this file, hooks) have none. This repo's tickets are in the Linear team **Connect Assist**, prefix **CON**. For everything else about tickets, load the `linear` skill.

### Worktrees

A worktree is a second working folder on its own branch, sharing the repo's history. It is how several agents build at once without treading on each other.

- All building happens in a worktree, never in the main folder. The main folder stays on `main`.
- One branch, one worktree, one pull request.
- Worktrees live in `.claude/worktrees/`, named for the ticket: `.claude/worktrees/con-123`.
- A worktree you did not start in belongs to another session. Leave it alone.
- Run `pnpm install` in every new worktree, or the commit hook will not exist there.

## Git

| | Rule |
| --- | --- |
| Main branch | Protected. Every change arrives through a pull request. |
| Branches | Cut from `origin/main`. Named `<user>/<ticket-id>-<slug>`, main ticket first. |
| Commits | The commit hook runs formatting, lint and type checks on what changed. |
| Tests | No local test run is needed before a push. CI runs the full suite. |
| Pushing | Only when the human asks. |
| Before a merge | CI is green and the branch is up to date with `main`. |
| Who merges | The human. Open the pull request and stop. |

Never:
- skip the commit hook with `--no-verify`;
- commit, push or merge straight to `main`;
- force-push, or run `git reset --hard` or `git clean` on a shared branch;
- commit with no branch checked out;
- add a line crediting an AI to a commit.

## CI/CD and environments

**Stage: live, with real customers.** A project starts with one environment and adds more as there is more to protect.

| Environment | What it is for | What data it holds |
| --- | --- | --- |
| Local | Development and the test suites. | Made-up data from a seed script. Nothing leaves the machine. |
| UAT | Proving a change in the deployed app before customers get it. | Standing test organisations and logins. No customer data. |
| Production | Customers. | Customer data. No test accounts. |

| When | What runs |
| --- | --- |
| On every pull request | The full suite: type checks, lint, unit and integration tests, and browser tests against a production build. |
| On merge | Nothing. |
| On a deploy, started by hand | The deploy refuses any commit CI has not proved. It runs migrations, then rolls out the API, then the web app. |
| On a schedule | Nothing yet. |

**Releasing**
- A change goes to UAT first, then to production. Both deploys are started by hand.
- A feature ticket is not finished at merge. It stays In Review until the change is proved on UAT, with the evidence on the ticket.

**Test data and logins**
- Logins are in AWS Secrets Manager under `connect-assist/uat/`. Fetch one when you need it. Never print, log or paste one.
- Email from a test goes only to the shared agent inbox. Never sign up a made-up address.
- Never delete these standing fixtures. Each is rebuilt by its own command:

| Fixture | Command |
| --- | --- |
| UAT Test Org | `pnpm uat:fixture` |
| The vendor organisation | `pnpm vendor:bootstrap` |
| BOTS ONLY — UAT Load Org | `pnpm uat:load-org --target uat` |
| DEMO DATA — Northwind Utilities | `pnpm uat:demo-data --target uat` |

## About this repo

| | |
| --- | --- |
| Language | TypeScript |
| API | Fastify, serving JSON only |
| Web | Next.js, in `web/`. The browser talks only to Next, and Next calls the API. |
| Database | PostgreSQL. One shared schema, with each organisation's rows separated by row-level security. |
| Hosting | AWS, account region `eu-west-1`. Always name the region: the local default is a different one. |
| Package manager | pnpm |
| Full local check | `pnpm check` |

Rules that hold across all of the code:
- Every query runs inside `withOrganisation()`, which is what keeps one organisation from seeing another's rows (ADR-0004).
- Throw the typed `AppError` classes. One handler turns them into responses (ADR-0006).
- Log only through `logEvent`. An answer's content must never reach a log (ADR-0007).
- Call a model only through the Inference port (ADR-0028).
- Before any work in `web/`, read `web/README.md`.
