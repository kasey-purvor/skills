# The team document

Each team has one team document: a Linear document on the team, named in the repo's `AGENTS.md` under `## Agent skills` → `### Team document`. It is a jotting area for app-wide notes that have no other home, and it should stay short enough to read in one go.

```markdown
## Notes
Anything app-wide worth jotting down.

## Blockers
Things blocking more than one stream.

## Open decisions
Decisions the human has not made that more than one stream is waiting on.

## Recurring findings
Review findings that were not fixed, counted by theme, with the tickets where they came up.
- Test fixtures copied between files: 2 (VAN-160, VAN-171)
```

Work in flight is not listed here: In Progress tickets already show it. Standing rules live in `AGENTS.md` and skills, settled product decisions in `docs/decisions.md`, repo traps in `docs/pitfalls.md`, a stream's plan and log on its stream ticket, and an epic's history in its project status updates.

- **Read it** when a stream is planned or started, and before starting a ticket.
- **Update it** when a stream closes.
- **Every write is also a tidy-up.** Reread the whole page and suggest to the human what should come out, so it doesn't grow.
- **Edit one part at a time** rather than resending the whole page, so two agents writing at once don't overwrite each other.
