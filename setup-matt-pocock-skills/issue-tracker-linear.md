# Issue tracker: Linear

Issues and PRDs for this repo live as Linear issues. Use the `mcp__plugin_linear_linear__*` MCP tools for all operations — there is no first-party Linear CLI.

Workspace-wide conventions (label taxonomy, status workflow, triage mapping, MCP gotchas) live in the `linear` skill, which auto-loads on any Linear MCP call. Don't duplicate that detail here.

The team for this repo is named in `AGENTS.md` (or `CLAUDE.md`) under `## Agent skills`. Discover available teams with `list_teams` if unsure.

## When a skill says "publish to the issue tracker"

Create a Linear issue with `save_issue` in this repo's team. The `linear` skill defines the default state for new issues.

## When a skill says "fetch the relevant ticket"

Call `get_issue` with the team-prefixed identifier (e.g., `ABC-42`). The user will normally pass this directly.
