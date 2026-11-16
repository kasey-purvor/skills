# Environment

Traps in the tools and machines every repo shares: Claude Code and its harness, Codex,
Linear, the scraping and search services, git and GitHub, and the machines. Read it
before the first command of a piece of work.

A trap about one repo belongs in that repo's `docs/pitfalls.md`, not here. The test: would it bite in a different repo
too? Then it lives here.

**One line per trap,** in the same shape as a repo's `docs/pitfalls.md`
(`set-up-sdlc/domain.md` gives it):

```
YYYY-MM-DD · <symptom, plainly> → <fix or rule> · seen: N · source: <measured | read in code | an agent's word | the human said>
```

The date is the date the trap was first seen. The same trap again bumps `seen`; it
never gets a second line.

**An inbox, not an archive.** A line stays, with its `seen` count, until the trap is
fixed at its source: a hook, a script, a preflight step or the skill that covers the
tool now stops it. Then the line is deleted. A high count is the sign it is worth fixing.

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
