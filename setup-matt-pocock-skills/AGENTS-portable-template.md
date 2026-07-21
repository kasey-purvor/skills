<!--
Portable AGENTS.md workflow block — a reusable TEMPLATE.
Copy everything above the `═══ REPO-SPECIFIC ═══` divider into a new repo's
AGENTS.md verbatim; write that repo's own sections below the divider
(and relocate the package-manager / env / check-command details into them).
-->

# Agent instructions

<!-- setup-matt-pocock-skills REPLACES this comment with this repo's `## Agent skills` block (team + prefix) — the one per-repo section above the divider. -->

> **Two parts.** Everything above the `═══ REPO-SPECIFIC ═══` divider is the **portable workflow** — generic, copied into every repo's `AGENTS.md` unchanged, **except the `## Agent skills` block at the top, which setup fills with this repo's team + prefix**. Everything below the divider is specific to *this* repo and rewritten per project.

## CRITICAL

This codebase will outlive you. Every shortcut becomes someone else's burden; every hack compounds into technical debt. You are shaping the project — the patterns you establish get copied, the corners you cut get cut again. Fight entropy. Leave the codebase better than you found it.

## Per-repo agent config

Where this repo's specifics live, so this block never has to name them:

- **Issue tracker binding** — this repo's Linear **team + issue prefix** live in the `## Agent skills` → `### Issue tracker` block near the top of this file (`repo = team`, fixed). **Domain vocab** — `docs/agents/domain.md` (scaffolded by `setup-matt-pocock-skills`).
- **Linear conventions** (labels, states, ticket body, recipes) — the `linear` skill, auto-loaded on any Linear MCP call.
- **Session hand-off** — the `handoff` skill (manual, invoked at session boundaries).

## Engineering standards

The `dev-standards-handbook` skill is the house production-engineering reference (chapters on API design, auth, testing, module design, and more). Two rules make it land:

- **Implementing a ticket?** If its body carries a `Standards:` line, read those handbook chapters *before starting work* — the ticket can't capture every standard, the chapters can. If a non-trivial ticket names none, invoke `dev-standards-handbook` and route yourself via its SKILL.md.
- **Proposing a new module, or reshaping how code is split?** Read the handbook's `topics/module-design.md` first and design to it (deletion test, deep-over-shallow, design it twice). This applies to plans and PRDs, not just code.

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

*The status moves below follow `linear`'s **Status lifecycle** — the single source for who moves a ticket to which status. A ticket enters this flow only once the human greenlights it: **Backlog → Todo is the human's decision, never the agent's**, then the steps below carry it Todo → In Progress → In Review → Done.*

1. **Orient on fresh `main`, scope the PR, and re-audit every ticket to ready — *even one that already looks well-specified*.** Reading/grepping/planning on an up-to-date `main` is fine. Decide which ticket(s) this PR closes and give each the `linear` skill's Ticket-body shape (TL;DR / Goal / Scope / AC / Verification). A thin, just-in-time, or not-yet-existing ticket gets written/enriched **now, into the Linear description** — not a comment, not a handoff. Mark it `quality/audited` once it passes this re-audit. *→ records: audited ticket description.*
2. **Cut the worktree + branch off fresh `origin/main`** once the ticket(s) are audited — before you edit. At pickup (the human's greenlight — see preamble) set every ticket in the PR → **Todo**, then → **In Progress** once the branch is cut. *→ records: state = Todo → In Progress.*
3. **Work.** The Linear ticket — not the chat log — is the record of decisions. **As work progresses, update status and drop decision / scope-change / deviation comments as they happen** (amend the *description* for spec changes; `linear` Convention #5). On a blocker, apply the relevant `blocked/*` label + a comment. Record evidence as you go (see *Evidence*). *→ records: decisions + state as they happen.*
4. **At a session boundary or low context:** record any unrecorded decision / scope change / blocker in Linear **first** (a handoff is throwaway — an unrecorded decision dies with it), **then** invoke the `handoff` skill. *→ records: decisions before the throwaway doc.*
5. **Open the PR (when asked to push).** Body lists `Closes <ID>` for **every** ticket it resolves. **Keep the cross-reference consistent both ways — the PR names the ticket id(s), the ticket carries the PR number.** Move every ticket → **In Review**, then stop — the review may be run by the human or an agent (see *Evidence*); **merge is the human's call**. *→ records: state = In Review.*
6. **After merge.** `Closes` lines *should* move tickets to **Done**; if the integration doesn't fire, set Done explicitly (comment first, `linear` Convention #3). *→ records: state = Done.*

### Evidence — proof it works

**Every ticket carries evidence it did what it claimed** — that's the one firm rule, independent of *who* reviewed. The reviewer may be **the human or an agent** (driving Playwright, running the test suite, hitting an endpoint — whatever fits); the review *method* is flexible, evidence-on-the-ticket is not.

Evidence takes whatever form fits the change:
- **Visible change** (UI, layout) — before/after screenshots, or a Playwright shot.
- **Behavioural / backend change** — test output, a Playwright trace, a command's result, or a relevant log excerpt.

Record it on the ticket — a **comment** by default (promote the headline proof into the description's `## Verification` when it's definitive). Upload images/files via the `linear` skill's 2-phase recipe → Linear's asset store; **never commit screenshots or trace artifacts as repo files** (local output is disposable once uploaded). For a visible change, the before/after shape:

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
- **A worktree you *discover* rather than start in probably belongs to another live session — default to leaving it alone.** Sessions run in parallel, so a slot under `.claude/worktrees/` that shows up in `git worktree list` but isn't the one you were launched into is most likely a concurrent session's. As a rule: orientation may note it exists and stop there — don't `cd` into, read, `cat`, grep, or modify it — and new work normally cuts a fresh worktree/branch off `origin/main` rather than reusing someone else's slot. The legitimate exception is a worktree you're **already operating inside** when the session begins: you were handed off into it to continue the previous agent's PR, so carry on there (see the preflight below). Treat this as a strong default, not an iron rule — when your workflow genuinely calls for something else, use judgment.

**Worktree preflight — run before editing a worktree you didn't just create** (a PR often spans sessions; resume the *same* worktree, don't cut a second):

1. `pwd` — confirm you're under `.claude/worktrees/`, not the main clone.
2. `git branch --show-current` — must print your branch. Empty = detached HEAD → STOP, cut the branch first.
3. **Update from `main` before you orient or edit:** `git fetch origin && git merge origin/main`. Resolve conflicts now.
4. **Re-sync dependencies** for your repo's package manager (see repo-specific section).
5. `git status` — expect a clean tree.

**Mislocated worktree:** if the branch is checked out in a *sibling* of the repo instead of `.claude/worktrees/<id>`, relocate it from the main clone (or another worktree) with `git worktree move`, then resume preflight. If your session is *inside* the misplaced slot, finish and relocate cold at the boundary — don't block the work on it.

## Checks, PRs & CI — the discipline

- `main` is **protected**: every change lands via a PR with CI green and the branch up to date with `main` before merge. Where the repo's plan supports branch protection/rulesets, that's enforced mechanically; where it doesn't (e.g. free-plan private repos), the rule binds by discipline anyway — the repo-specific half says which applies.
- **Always run the repo's full check before pushing** (command in the repo-specific section) — it should mirror CI exactly.
- PRs touching only non-product files (docs, agent config) may skip the heavy CI jobs (repo-configured).

## Hard constraints

- **Never use `--no-verify`** to skip the pre-commit hook. Fix the failing check instead.
- **Each commit must pass the repo's full check** before push.
- **Never include `Co-Authored-By` or any AI-attribution lines** in commits (global rule).
- **Never commit, push, or merge to `main` directly.** All work lands via a branch and a PR.
- **Never `git push` unless explicitly asked, and never push `main`.**
- **Never merge a PR yourself.** Open it and stop — merge is the human's call. No auto-merge unless told.
- **One branch per PR, cut from `origin/main`**, named `<user>/<ticket-id>-<slug>` (primary id first; append secondary ids). Keep the id so Linear auto-links the PR.
- **Never commit on a detached HEAD** — `git branch --show-current` must print a branch name first.
- **Never force-push, and never `git reset --hard` / `git clean` on shared branches.**

═══════════════════════════ REPO-SPECIFIC ═══════════════════════════

<!-- Below this divider: this repo's own sections — overview, environments,
     deploy, package layout, local dev loop, infrastructure, data layer,
     architecture — plus the package-manager / env / check-command details
     the portable block defers to. Written fresh per repo. -->
