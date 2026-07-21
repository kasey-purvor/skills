---
name: setup-matt-pocock-skills
description: Scaffold a repo's `## Agent skills` block and `docs/agents/` so the engineering skills know this repo's Linear tracker and domain-doc layout. Run once per repo before first use of `to-issues`, or any skill that needs the issue tracker or domain docs.
disable-model-invocation: true
---

# Setup

Scaffold the per-repo configuration the engineering skills assume:

- **Issue tracker** — this repo's Linear team + issue prefix, recorded in the `## Agent skills` block (`repo = team`).
- **Domain docs** — where `CONTEXT.md` and ADRs live, and the consumer rules for reading them.

Prompt-driven, not a script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. Explore

Read whatever exists; don't assume:

- `git remote -v` — confirm the repo.
- `AGENTS.md` at the root — does it exist? Is there already an `## Agent skills` section? (This workspace uses `AGENTS.md`, never `CLAUDE.md`.)
- `CONTEXT.md` / `CONTEXT-MAP.md` at the root.
- `docs/adr/` and any `src/*/docs/adr/` directories.
- `docs/agents/` — does this skill's prior output already exist?

### 2. Present findings and ask

Summarise what's present and what's missing, then walk the user through the two decisions **one at a time**.

**A — Linear tracker.**

> Which Linear team owns this repo's issues, and what's its issue prefix? Because **`repo = team`** (one product per repo), this is a fixed, one-time binding — recorded in `AGENTS.md`'s `## Agent skills` block, not a separate file. Workspace-wide Linear conventions (labels, states, recipes) live in the `linear` skill — this only records the per-repo **team name** and **prefix**. Discover teams with `list_teams` if unsure.

**B — Domain docs.**

> Some skills read `CONTEXT.md` for the project's domain language and `docs/adr/` for past decisions. Confirm the layout:
>
> - **Single-context** — one `CONTEXT.md` + `docs/adr/` at the repo root. Most repos.
> - **Multi-context** — `CONTEXT-MAP.md` at the root pointing to per-context `CONTEXT.md` files (typically a monorepo).

### 3. Confirm and edit

Show the user a draft of:

- The `## Agent skills` block to add to `AGENTS.md` (step 4).
- The contents of `docs/agents/domain.md`.

Let them edit before writing.

### 4. Write

**Edit `AGENTS.md`** — this workspace uses `AGENTS.md` as the agent-instructions file, never `CLAUDE.md`. Create it if absent (seed from the portable template — see below). Add the `## Agent skills` block near the top (right after the title) so the portable block's references to it resolve. If an `## Agent skills` block already exists, update it in place rather than appending a duplicate.

The block:

```markdown
## Agent skills

### Issue tracker

Linear team **<Team>**, issue prefix **<PREFIX>** (`repo = team`). Workspace conventions: the `linear` skill.

### Domain docs

[one-line: single- or multi-context]. See `docs/agents/domain.md`.
```

Then write `docs/agents/domain.md` using the seed in this skill folder:

- [domain.md](./domain.md) — domain-doc consumer rules + layout

There is **no separate issue-tracker doc** — the team + prefix live in the `## Agent skills` block above (single source; `repo = team`), and all workspace-wide Linear conventions live in the `linear` skill (auto-loads on any Linear MCP call).

**Portable AGENTS.md block.** If the repo has no `AGENTS.md` yet (or you're standardising one), seed it from [AGENTS-portable-template.md](./AGENTS-portable-template.md): copy the portable workflow block (everything above the `═══ REPO-SPECIFIC ═══` divider) verbatim, then write the repo's own sections below the divider. If an `AGENTS.md` already exists, don't re-seed the portable block over it — step 4's `## Agent skills` update is still the edit to make; touch the rest only if the user asks.

### 5. Done

Tell the user setup is complete and which skills now read from these files. They can edit `docs/agents/*.md` directly later; re-run only to reconfigure.
