# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. In multi-context repos, also check `src/<context>/docs/adr/` for context-scoped decisions.
- **`docs/decisions.md`** — settled decisions that didn't earn an ADR. Read it before proposing anything it covers, and before reporting a deliberate choice as a defect.
- **`docs/pitfalls.md`** — traps that have cost agents time in this repo. Read it before the first command of a piece of work.
- **The handbook's `topics/environment.md`** (in the `dev-standards-handbook` skill) — traps in the tools and machines, not this repo. Read it before the first command of a piece of work too.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The producer skills (`/grill-with-docs` for the glossary and ADRs, `session-review` for decision and pitfall lines) create them lazily when terms, decisions or traps actually turn up.

## File structure

Single-context repo (most repos):

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
├── docs/decisions.md
├── docs/pitfalls.md
└── src/
```

Multi-context repo (presence of `CONTEXT-MAP.md` at the root):

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← system-wide decisions
├── docs/decisions.md                  ← one pair at the repo root, never per context
├── docs/pitfalls.md
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/adr/                  ← context-specific decisions
    └── billing/
        ├── CONTEXT.md
        └── docs/adr/
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/grill-with-docs`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_

The same applies to a line in `docs/decisions.md`: name it, don't quietly go against it.

## Decisions and pitfalls

Two plain lists for what the glossary and the ADRs don't hold. One line per entry, newest last, created on the first entry. They live at `docs/decisions.md` and `docs/pitfalls.md` unless the `## Agent skills` block in `AGENTS.md` names another place.

**`docs/decisions.md`** — a decision the human made that is settled but fails the ADR test (easy to reverse, or unsurprising, or no real alternative). Product rules and taste live here: what is in scope, what is never built, thresholds, how a feature should feel.

```
YYYY-MM-DD · <decision> · why: <reason> · from: <ticket, ADR or "chat"> · superseded by: <date or —>
```

A reversed decision is not deleted: fill in `superseded by:` on the old line and add the new line at the end.

**`docs/pitfalls.md`** — a trap in this repo (its code, hooks, scripts, tests) that cost an agent more than about fifteen minutes: a hook that bites, a flaky test, a command that must run from a certain place.

Each trap has one home. A trap about this repo goes here. Any other trap (a tool, the harness, Codex, Linear, a scraping service, git and GitHub, the machines) goes in the `dev-standards-handbook` skill's `topics/environment.md`, in the same line shape.

```
YYYY-MM-DD · <symptom, plainly> → <fix or rule> · seen: N · source: <measured | read in code | an agent's word | the human said>
```

The date is the date the trap was first seen. Before adding a line, search the file for the same symptom; if it is there, bump `seen` instead of adding.

**`docs/pitfalls.md` is an inbox, not an archive.** Every line ends one of three ways: fixed at the source (a hook, a script or a preflight step now stops it), then deleted; moved into `AGENTS.md` as a how-to, then deleted; or kept, with its `seen` count, until one of those happens.

**Who writes them.** One route: the `session-review` skill, run at a stream's close, at the end of a grill session, before a handoff, or when the human wraps up a session and says yes to the offer. It proposes each line, and each deletion the inbox rule calls for; the human says yes or no to each, and the lines land where `session-review` says. Builders report traps in their final report rather than writing them. Nothing is written to or deleted from either file outside that route. Nothing goes in that the human didn't decide or an agent didn't actually hit.

**If a thing fits none of these files** (glossary, ADR, decisions, pitfalls), it stays in the ticket comment. Don't create another file for it.
