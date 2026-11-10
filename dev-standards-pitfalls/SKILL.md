---
name: dev-standards-pitfalls
description: Compatibility entrypoint for the former pitfalls catalogue. When explicitly invoked or referenced by an older workflow, route to the Pitfalls chapter in dev-standards-handbook.
---

# Pitfalls — compatibility entrypoint

The named anti-patterns now live in
[Pitfalls](../dev-standards-handbook/topics/pitfalls.md), a chapter of the handbook.
There is one source of truth; this file is a link for older briefs.

- **Building new code or a module:** use the handbook router, and scan the chapter's section for what you are building.
- **Hitting a trap:** report it; do not write it yourself. A trap in one repo: the `session-review` skill proposes it for that repo's `docs/pitfalls.md`. A trap in a tool, the harness or a machine: the same, for the handbook's [Environment](../dev-standards-handbook/topics/environment.md) chapter.
- **Updating an anti-pattern:** edit its entry in the chapter directly. Keep its name, what goes wrong, the fix and the chapter it points to. Do not duplicate it here.
