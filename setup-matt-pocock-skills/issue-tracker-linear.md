# Issue tracker: Linear

Issues and PRDs for this repo live as Linear issues. Use the `mcp__plugin_linear_linear__*` MCP tools for all operations — there is no first-party Linear CLI.

## Default team

This Linear workspace's default team is **`Cloud Assist`**. Pass `team: "Cloud Assist"` when creating issues, or override per-repo if a different team applies. All Linear MCP tools accept team by name, ID, or slug.

## Conventions

- **Create an issue**: `save_issue` with `team`, `title`, `description`. New issues default to `state: "Triage"` unless the skill explicitly sets a different role (see Triage Mapping below).
- **Read an issue**: `get_issue` with the team-prefixed identifier (e.g., `CAS-42`). Pass `includeRelations: true` for blocking/related/duplicate info.
- **List issues**: `list_issues` with `team`, optionally filtered by `state`, `label`, `assignee`. Use `query` for full-text search of title/description. Use `state: "Triage"` to see what needs triage; `state: "Todo"` + `label: "ready-for-agent"` for the AFK queue.
- **Comment on an issue**: `save_comment` with `issueId` and `body`. To reply within an existing thread, pass `parentId` instead of `issueId`.
- **List comments**: `list_comments` with `issueId`.
- **Apply / remove labels**: `save_issue` with `id` and `labels` (array of label names). Linear's MCP **replaces the full label set on update** — to add a label, fetch existing labels first and include them in the new array.
- **Change status**: `save_issue` with `id` and `state` (status name: `"Triage"`, `"Backlog"`, `"Todo"`, `"In Progress"`, `"Done"`, `"Canceled"`, `"Duplicate"`).
- **Close**: `save_issue` with `id` and `state: "Done"` (work shipped) or `state: "Canceled"` (won't fix). Post a closing rationale first with `save_comment`.

Issues are referenced by team-prefixed identifiers (e.g., `CAS-42` for Cloud Assist). Discover the prefix by running `list_issues` once if unsure.

## Triage Mapping (Linear-specific)

Unlike GitHub/GitLab where everything is labels, Linear has both **Status** and **Labels**. This tracker uses a hybrid mapping that leverages Linear's primitives:

| Canonical role     | Status        | Triage label         |
| ------------------ | ------------- | -------------------- |
| `needs-triage`     | **Triage**    | *(no label needed)*  |
| `needs-info`       | **Triage**    | `needs-info`         |
| `ready-for-agent`  | **Todo**      | `ready-for-agent`    |
| `ready-for-human`  | **Todo**      | `ready-for-human`    |
| `wontfix`          | **Canceled**  | *(no label needed)*  |

The three triage labels (`needs-info`, `ready-for-agent`, `ready-for-human`) live under the `triage` label group, alongside the existing `type:`, `scope:`, `concern:`, `initiative:`, `workflow:` groups.

**Important:** when `triage-labels.md` says "apply label X for role Y", interpret it via the table above for Linear — some roles set status only, some set status + label.

## When a skill says "publish to the issue tracker"

Create a Linear issue with `save_issue` in the `Cloud Assist` team. Default `state: "Triage"` unless the skill explicitly sets a different role (e.g., `to-prd` sets `state: "Todo"` + `label: "ready-for-agent"` because PRDs are pre-triaged by definition).

## When a skill says "fetch the relevant ticket"

Call `get_issue` with the team-prefixed identifier (`CAS-42`). The user will normally pass this directly.
