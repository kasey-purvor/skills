# Environment

Traps in the tools and machines every repo shares: Claude Code and its harness, Codex,
Linear, the scraping and search services, git and GitHub, and the machines. Read it
before the first command of a piece of work.

A trap about one repo belongs in that repo's `docs/pitfalls.md` (or the place its
`## Agent skills` block names), not here. The test: would it bite in a different repo
too? Then it lives here.

**One line per trap,** in the same shape as a repo's `docs/pitfalls.md`
(`setup-matt-pocock-skills/domain.md` gives it):

```
YYYY-MM-DD · <symptom, plainly> → <fix or rule> · seen: N · source: <measured | read in code | an agent's word | the human said>
```

The date is the date the trap was first seen. The same trap again bumps `seen`; it
never gets a second line.

**An inbox, not an archive.** Every line ends one of three ways:

1. **Fixed at the source.** A hook, a script or a preflight step now stops the trap.
   Delete the line.
2. **Moved into a how-to.** The skill or instructions that cover the tool now say it.
   Delete the line.
3. **Kept,** with its `seen` count, until one of those happens. A high count is the
   sign it is worth fixing at the source.

**Who writes it.** Only the `session-wrap-up` skill, and only lines (and deletions) the
human says yes to. They land as one commit in the skills repo, which the human makes and pushes from
their own profile. Builders and reviewers report traps; they never edit this file.

## Claude Code

Nothing yet.

## Codex

Nothing yet.

## Linear

Nothing yet.

## Scraping and search services (Scrapfly, Serper, Bright Data)

Nothing yet.

## Git and GitHub

Nothing yet.

## Machines (hal, kasey-lt, spark, hal-mini, Tailscale)

Nothing yet.
