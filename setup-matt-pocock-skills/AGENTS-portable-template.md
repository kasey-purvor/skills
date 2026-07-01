<!--
Portable AGENTS.md workflow block — a reusable TEMPLATE.
Copy everything above the `═══ REPO-SPECIFIC ═══` divider into a new repo's
AGENTS.md verbatim; write that repo's own sections below the divider
(and relocate the package-manager / env / check-command details into them).
-->

# Agent instructions

> **Two parts.** Everything above the `═══ REPO-SPECIFIC ═══` divider is the **portable workflow** — generic, copied into every repo's `AGENTS.md` unchanged. Everything below it is specific to *this* repo and rewritten per project.

## CRITICAL

This codebase will outlive you. Every shortcut becomes someone else's burden; every hack compounds into technical debt. You are shaping the project — the patterns you establish get copied, the corners you cut get cut again. Fight entropy. Leave the codebase better than you found it.

## Per-repo agent config

Where this repo's specifics live, so this block never has to name them:

- **Issue tracker, label/domain vocab** — scaffolded by `setup-matt-pocock-skills` into `docs/agents/*.md` (`issue-tracker.md`, `domain.md`). Read `issue-tracker.md` for this repo's team name and issue prefix.
- **Linear conventions** (labels, states, ticket body, recipes) — the `linear` skill, auto-loaded on any Linear MCP call.
- **Session hand-off** — the `handoff` skill (manual, invoked at session boundaries).

## Work lifecycle — tickets, branches & PRs

**Read this before starting any piece of work.** It defines the unit of work, *when* to cut a branch, and *when* to record state to Linear. It does not restate what's owned elsewhere (ticket shape → `linear` skill; worktree mechanics → next section). It only sequences them.

### When this applies — product work vs. plumbing

This lifecycle governs **product work**: changes to the shipped product or its infrastructure. **Product work always gets a ticket.** It does **not** govern **agent/tooling plumbing** — the skills, agent-workflow docs like this file, hooks, CI tweaks. That's rare and gets **no ticket**; but where it lives in a branch-protected repo it still rides a branch + PR like anything else. The test: **a ticket means product work.** Changing how the *agent or tooling* behaves rather than what the *product* does → no ticket.

### Three artifacts, three lifespans, no overlap

| Artifact | Lives | Source of truth for | Never holds |
| --- | --- | --- | --- |
| **Linear ticket** | Durable — outlives the PR | The *what & why*: goal, scope, AC, verification, decisions | Branch names, session mechanics |
| **Branch = worktree = PR** | One delivery — pickup → merge | The *change*: commits, diff, the thing that ships | — |
| **Handoff doc** | Ephemeral — one session → next | *Where we are now*: done / in-flight / next / gotchas, **linking** tickets + PR | Spec content — that's the ticket's job |

Spec content always lives in the **ticket**, never a handoff. Thin ticket → enrich the *ticket description* (step 1), not a handoff.

### The unit of work

**One branch ⇒ one worktree ⇒ one PR** — that pairing is firm; it's just where the branch lives. **How many *tickets* ride in a PR is a judgment call, not a rule:** fold several in when they're small or land together, split when they don't. Not "one ticket per PR." Name the branch/worktree for the PR, carrying its ticket id(s), primary first.

### Lifecycle — do these in order

1. **Orient on fresh `main`, scope the PR, and re-audit every ticket to ready — *even one that already looks well-specified*.** Reading/grepping/planning on an up-to-date `main` is fine. Decide which ticket(s) this PR closes and give each the `linear` skill's Ticket-body shape (TL;DR / Goal / Scope / AC / Verification). A thin, just-in-time, or not-yet-existing ticket gets written/enriched **now, into the Linear description** — not a comment, not a handoff. Mark it `quality/audited` once it passes this re-audit. *→ records: audited ticket description.*
2. **Cut the worktree + branch off fresh `origin/main`** once the ticket(s) are audited — before you edit. Move every ticket in the PR → **In Progress**. *→ records: state = In Progress.*
3. **Work.** The Linear ticket — not the chat log — is the record of decisions. **As work progresses, update status and drop decision / scope-change / deviation comments as they happen** (amend the *description* for spec changes; `linear` Convention #5). On a blocker, apply the relevant `blocked/*` label + a comment. Record visible-change proof as you go (see *Evidence*). *→ records: decisions + state as they happen.*
4. **At a session boundary or low context:** record any unrecorded decision / scope change / blocker in Linear **first** (a handoff is throwaway — an unrecorded decision dies with it), **then** invoke the `handoff` skill. *→ records: decisions before the throwaway doc.*
5. **Open the PR (when asked to push).** Body lists `Closes <ID>` for **every** ticket it resolves. **Keep the cross-reference consistent both ways — the PR names the ticket id(s), the ticket carries the PR number.** Move every ticket → **In Review**, then stop — a human reviews and merges. *→ records: state = In Review.*
6. **After merge.** `Closes` lines move tickets to **Done** automatically. *→ records: state = Done.*

### Evidence — before/after

When work produces a **visible** change (UI, layout, a Playwright screenshot), record before/after proof on the ticket — in a **comment** by default (promote the headline shot into the description's `## Verification` when it's the definitive proof). Upload via the `linear` skill's 2-phase image recipe → Linear's asset store; **never commit screenshots as repo files** (local Playwright shots are disposable once uploaded). Format:

```
## Evidence — <what changed>
**Before:** ![before](assetUrl)
**After:**  ![after](assetUrl)
```

## Parallel work via git worktrees

Work several branches at once with worktrees rather than one clone you keep switching. A worktree shares the repo's single `.git`; one branch per worktree, and a branch can be checked out in only one worktree at a time.

- **Worktrees live in `.claude/worktrees/`**, named for the **ticket id(s) only** (`.claude/worktrees/clo-342`, multi-ticket `…/clo-342-clo-343`) — a tmux `ticket` panel reads the id from the directory name, so never use generic `wt1`/`wt2` names. This is also where the Claude Code harness creates them, so manual and harness slots agree.
- **Create off `origin/main`:** `git worktree add .claude/worktrees/<id> -b <user>/<id>-<slug> origin/main`. `main` can't be checked out twice, so always branch from the remote ref.
- **Never *develop* in the main clone** — keep it on `main` as the fresh base you branch from. Reading/orienting there is fine; edits and commits belong in a worktree.

**Worktree preflight — run before editing a worktree you didn't just create** (a PR often spans sessions; resume the *same* worktree, don't cut a second):

1. `pwd` — confirm you're under `.claude/worktrees/`, not the main clone.
2. `git branch --show-current` — must print your branch. Empty = detached HEAD → STOP, cut the branch first.
3. **Update from `main` before you orient or edit:** `git fetch origin && git merge origin/main`. Resolve conflicts now.
4. **Re-sync dependencies** for your repo's package manager (see repo-specific section).
5. `git status` — expect a clean tree.

**Mislocated worktree:** if the branch is checked out in a *sibling* of the repo instead of `.claude/worktrees/<id>`, relocate it from the main clone (or another worktree) with `git worktree move`, then resume preflight. If your session is *inside* the misplaced slot, finish and relocate cold at the boundary — don't block the work on it.

## Checks, PRs & CI — the discipline

- `main` is **protected**: every change lands via a PR, the required status check must pass, and the branch must be up to date with `main` before merge.
- **Always run the repo's full check before pushing** (command in the repo-specific section) — it should mirror CI exactly.
- PRs touching only non-product files (docs, agent config) may skip the heavy CI jobs (repo-configured).

## Hard constraints

- **Never use `--no-verify`** to skip the pre-commit hook. Fix the failing check instead.
- **Each commit must pass the repo's full check** before push.
- **Never include `Co-Authored-By` or any AI-attribution lines** in commits (global rule).
- **Never commit, push, or merge to `main` directly.** All work lands via a branch and a PR.
- **Never `git push` unless explicitly asked, and never push `main`.**
- **Never merge a PR yourself.** Open it and stop — a human reviews and merges. No auto-merge unless told.
- **One branch per PR, cut from `origin/main`**, named `<user>/<ticket-id>-<slug>` (primary id first; append secondary ids). Keep the id so Linear auto-links the PR.
- **Never commit on a detached HEAD** — `git branch --show-current` must print a branch name first.
- **Never force-push, and never `git reset --hard` / `git clean` on shared branches.**

═══════════════════════════ REPO-SPECIFIC ═══════════════════════════

<!-- Below this divider: this repo's own sections — overview, environments,
     deploy, package layout, local dev loop, infrastructure, data layer,
     architecture — plus the package-manager / env / check-command details
     the portable block defers to. Written fresh per repo. -->
