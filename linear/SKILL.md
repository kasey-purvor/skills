---
name: linear
description: Operational conventions for the Cloud Assist Linear workspace — labels, statuses, priorities, common MCP recipes, known gotchas. Use when creating, updating, triaging, commenting on, or closing Linear issues, or running any `mcp__plugin_linear_linear__*` tool.
---

# Linear

Day-to-day operational skill for the Cloud Assist Linear workspace. Loaded on any Linear MCP operation.

**Workspace:** `cloud-assist` · **Team:** Cloud Assist (issue prefix `CLO-*`) · **Plan:** Free

## Cheat sheet

### Statuses (in workflow order)

| Status | Category | When |
|---|---|---|
| Triage | triage | New issues land here |
| Backlog | backlog | Acknowledged, not scheduled |
| Todo | unstarted | Scheduled for current/next cycle |
| In Progress | started | Active work; PR branch copied |
| In Review | started | PR open, awaiting review or CI |
| Done | completed | Shipped — PR merged |
| Canceled | canceled | Won't do |
| Duplicate | duplicate | Auto-applied when `duplicateOf` is set |

### Labels (4 mutex groups + 2 free-floating)

| Group | Values |
|---|---|
| `type/*` | `bug`, `feat`, `refactor`, `chore`, `spike` |
| `scope/*` | `api`, `web`, `infra` |
| `feature/*` | Workspace-specific — mirrors the codebase's feature directories. See the per-repo overlay (`docs/agents/issue-tracker.md`) or run `list_issue_labels` for the actual set. |
| `triage/*` | `needs-info`, `ready-for-agent` |
| `security` | free-floating; security-sensitive code or behaviour |
| `agent-blocked` | free-floating; agent paused mid-task, awaiting human resolution |

Mutex = mutually exclusive within a group; picking a second value drops the first. All labels live at **workspace level** — never pass `teamId`.

### Priorities

| Value | Meaning |
|---|---|
| Urgent (1) | Page-worthy fires only. Production blocking. 0–1 at a time. |
| High (2) | Reshuffle this cycle for it. |
| Medium (3) | Default for committed work. |
| Low (4) | Nice-to-have; often dead weight — prune. |
| No Priority (0) | Default for new/untriaged. Triage assigns priority. |

## Conventions

1. **One label per group max** — mutex is enforced.
2. **Free-floating labels (`security`, `agent-blocked`) apply alongside group labels** — they don't belong to any mutex group.
3. **`feature/*` only when work targets one feature directory** — cross-feature work skips it.
4. **Comment before state change** — when moving to Done/Canceled, post `save_comment` rationale *first*, then `save_issue` state change.
5. **Set `duplicateOf` — don't also set state.** Linear auto-transitions to Duplicate.
6. **Default state for new issues: Triage.** Override only when the issue is explicitly pre-spec'd (e.g., `to-issues` publishes vertical slices in Backlog with `triage/ready-for-agent` — well-defined but not yet scheduled).
7. **Priority is a triage output, not an input.** New issues come in at No Priority.
8. **Triage-state issues must carry a `triage/*` label *or* be re-evaluated.** An unlabeled Triage issue is the `needs-triage` role — *"awaiting maintainer evaluation"* — and should not linger. After evaluation, apply one of `triage/needs-info` / `triage/ready-for-agent` (with the matching state per the table below), or close as Duplicate / Canceled. See the `triage` skill for the state machine.
9. **Spec changes edit the description, not comments.** Mid-flight enrichment, scope changes, AC amendments, and deviations all amend the description in place; a one-line breadcrumb comment can point at the change. The description is what every downstream reader sees — spec content kept only in comments is invisible to them. For what comments *are* for, see *Reading a ticket for action* below.

## Reading a ticket for action

`get_issue` does NOT return comments. Anyone reading a ticket programmatically to take action (audit, implement, review, dispatch a subagent) MUST call `list_comments({issueId})` alongside `get_issue`. For tickets with linked work, pass `includeRelations: true` to `get_issue` as well. Treat "reading a Linear issue" as at minimum two API calls — description plus discussion — never one.

**Legitimate things comments contain** (and that downstream readers therefore need):

- Implementer follow-up sweeps documenting scope-deferral decisions (e.g., "ran a value-level grep, found X / Y / Z, deferred them because…")
- Code-review findings against an in-review ticket
- Blocker discussions (paired with the `agent-blocked` label per the workflow above)
- Status updates ("implementation complete, awaiting review", "shipped in #142")
- Post-merge notes (verification on staging, follow-up surprises)
- Threaded discussion among reviewers

**What does NOT belong in comments** — see Convention #9:

- Enrichment of a thin spec into a ready-for-agent spec — edits the description.
- Scope changes, AC additions/removals, constraint changes — edit the description.
- Spec deviations discovered during implementation — amend the description, then leave a breadcrumb comment if helpful.

**When dispatching a subagent against a ticket, the orchestrator fetches both `get_issue` and `list_comments` and passes both into the briefing.** Do not assume the subagent will fetch comments itself unless explicitly instructed.

## Agent-ready issue body

The `triage/ready-for-agent` label promises *"an agent can pick this up with no human context"* (verbatim from the label's own description). The body template below is what makes that promise true. **Mandatory at the `ready-for-agent` transition.** Issues earlier in the workflow (Triage, Backlog, `needs-info`) do not need to conform.

<agent-ready-template>

## Goal
One sentence: what user-visible behavior changes and why.

## Scope
- In: what this issue covers
- Out / Non-goals: what it explicitly does not

## Acceptance criteria (AC)
- [ ] Binary checkboxes — each independently verifiable
- [ ] Avoid soft criteria like "should be fast" or "code should be clean"

## Verification
How the agent proves it works. Exact command, URL, or observable result — never "make sure it works."

</agent-ready-template>

**File paths and code snippets stay out of the body** — they go stale fast. Exception: prototype snippets that encode a decision more precisely than prose can (state machine, schema, type shape).

**Time estimates and file-count limits are guidance, never rules.** They are useful signals about whether an issue is well-sized; they are not targets the implementation must hit. Agents are poor estimators, and hard file-count constraints push them into contrived avoidance. If an issue feels too big, decompose it; too small, merge it.

**Retrofitting a spec onto an existing poorly-written issue?** Use the `AGENT-BRIEF.md` template in the `triage` skill instead. Its "Current behavior / Desired behavior" framing is built for patching existing tickets, whereas this template assumes greenfield (born-as-spec) issues from the `to-issues` flow. Both serve the same audience (the AFK agent); they differ by input quality, not output goal.

## Agent-blocked workflow

When an in-progress agent hits a blocker (decision needed, missing info, unknown), it **stays in `In Progress`** and adds the free-floating `agent-blocked` label, with a comment explaining the blocker.

Recipe:
```
issue = get_issue({ id: "CLO-119" })   // fetch current labels first
save_comment({ issueId: "CLO-119", body: "Blocked on: <specific question/decision>" })
save_issue({ id: "CLO-119", labels: [...issue.labels.map(l => l.name), "agent-blocked"] })
```

To resume: human addresses the blocker (reply or decision), removes the `agent-blocked` label. The agent picks back up.

Distinct from:
- **`triage/needs-info` + Triage state** — for *new* issues awaiting reporter info, not committed work.

## Common recipes

### Create
```
save_issue({ team: "Cloud Assist", title, description, labels: ["feat", "api"] })
```
**Labels are sent as bare names** (`feat`, `api`) — the group is determined by each label's own `parent` field in Linear, not by passing a compound string like `"type/feat"`.

### Update labels (replace-only — fetch first!)
The MCP **overwrites** the label array. To add one without losing others:
```
issue = get_issue({ id: "CLO-119" })
save_issue({ id: "CLO-119", labels: [...issue.labels.map(l => l.name), "security"] })
```

### Close
```
save_comment({ issueId: "CLO-119", body: "Shipped in #142. Verified on staging." })
save_issue({ id: "CLO-119", state: "Done" })  // or "Canceled"
```

### Mark duplicate
```
save_issue({ id: "CLO-119", duplicateOf: "CLO-90" })  // state auto-becomes Duplicate
```

### Add a milestone, then attach an issue
```
save_milestone({ project: "Project Name", name: "M1", targetDate: "2026-06-15" })
save_issue({ id: "CLO-119", milestone: "M1" })   // accepts name OR id
```
On create, `save_milestone` returns a stripped object (no `targetDate`/`description` when unset); on update it returns the full object. The issue response field is **`projectMilestone`** (not `milestone`).

### Create a document (4 possible parents)
```
save_document({ title: "Spec", project: "Project Name", content: "# Spec\n..." })
save_document({ title: "Notes", issue: "CLO-119", content: "..." })
save_document({ id: docId, content: "Updated..." })   // update
```
Exactly one parent: `project`, `issue`, `initiative`, or `cycle`. `content` is rewritten on save — bare issue refs (`CLO-119`) become issue-mention markup.

### Upload a file attachment (2-phase, preferred)
```
prep = prepare_attachment_upload({ issue, filename, contentType, size })
// PUT raw bytes to prep.uploadRequest.url with prep.uploadRequest.headers VERBATIM (60s expiry!)
create_attachment_from_upload({ issue, assetUrl: prep.assetUrl, title: filename })
```
The `prep.finalize` field literally returns the next tool name + pre-filled inputs. Use the deprecated `create_attachment` (base64 body) only for tiny files — it consumes agent context.

### Embed an image inline in a description (renders in-line, not just a panel attachment)

For **visual evidence** — UI screenshots, before/after, stylistic changes — put the image *in the description body* so it renders automatically, instead of (or as well as) the attachments panel. Same 2-phase upload; the `assetUrl` doubles as the markdown image source.
```
issue = get_issue({ id: "CLO-119" })            // fetch the CURRENT description — there is NO append API
prep  = prepare_attachment_upload({ issue: "CLO-119", filename, contentType, size })
// PUT raw bytes to prep.uploadRequest.url with prep.uploadRequest.headers VERBATIM (60s expiry!)
save_issue({ id: "CLO-119",
  description: issue.description + "\n\n## Verification evidence\n\n![alt text](" + prep.assetUrl + ")" })
// optional: also create_attachment_from_upload({ issue, assetUrl: prep.assetUrl }) to add the panel row too
```
- **`![alt](url)` is an image; `[alt](url)` is a link** — the leading `!` is what makes it render inline.
- **One upload, two homes.** The same `prep.assetUrl` works for both the inline embed AND `create_attachment_from_upload` — for headline proof (e.g. a UAT verification shot), do both from a single PUT.
- **`save_issue` overwrites the whole description** (no append API) — fetch it first and concatenate, keeping real newlines. On save Linear **re-signs** the asset URL (`?signature=…`, short-lived) and **re-linkifies bare issue refs** (`CLO-119` → markup), so send bare refs, not `<issue …>` markup.
- **Scoped per issue:** `prepare_attachment_upload` ties the asset to the `issue` you pass — re-upload (don't reuse an `assetUrl`) when embedding the same image into another ticket.

**Inline vs panel:** inline for anything worth *seeing at a glance* (screenshots, diagrams, stylistic before/after); panel for supplementary files (logs, larger artifacts); both for headline verification evidence.

### Threaded comment reply
```
save_comment({ parentId: rootCommentId, body: "Reply..." })   // no issueId needed
```
Replies inherit the root's entity automatically. `list_comments` returns the thread flat — `parentId` encodes nesting.

### Triage role → Linear primitives

| Triage role | State | Label |
|---|---|---|
| `needs-triage` | Triage | *(none — "awaiting evaluation")* |
| `needs-info` | Triage | `triage/needs-info` |
| `ready-for-agent` | Backlog or Todo | `triage/ready-for-agent` |
| `wontfix` | Canceled | *(none — close reason in comment)* |

**State and label encode different facts.** State = scheduling position (Backlog = acknowledged but not next-up; Todo = scheduled for current/next cycle). Label = readiness quality (well-defined enough for the named audience). The two are orthogonal: apply the label as soon as the issue is well-defined; promote the state when you're ready for it to be picked up. `/to-issues` produces Backlog + `ready-for-agent` issues by default — promotion to Todo is a separate scheduling decision.

The two "no-label" rows are distinguishable by state: a label-less Triage-state issue means *not yet evaluated*; a label-less Canceled-state issue is `wontfix`. Don't leave issues stuck in the *needs-triage* (label-less Triage) row — Convention 8 above.

## MCP capabilities (verified)

Verified end-to-end against the live workspace on **2026-05-27**. This table is canonical — defer to it before falling back to "the schema looks like…". When in doubt, the underlying tool exists for every ✅; for ❌ the tool genuinely isn't there.

### Resource × operation matrix

| Resource              | List | Get | Create | Update | Delete | Notes |
|-----------------------|:----:|:---:|:------:|:------:|:------:|---|
| Issues                | ✅   | ✅  | ✅     | ✅     | ❌     | `save_issue` does both (id present = update). No MCP delete. |
| Issue statuses        | ✅   | ✅  | ❌     | ❌     | ❌     | UI only — workflow config |
| Issue labels          | ✅   | —   | ✅     | ❌     | ❌     | UI only for rename/delete |
| Comments              | ✅   | —   | ✅     | ✅     | ✅     | `save_comment` overloaded. Threaded via `parentId`. |
| Projects              | ✅   | ✅  | ✅     | ✅     | ❌     | "Cancel" via `state: "canceled"`; no MCP delete |
| Project labels        | ✅   | —   | ❌     | ❌     | ❌     | Read-only via MCP |
| Project milestones    | ✅   | ✅  | ✅     | ✅     | ❌     | Scoped per project; no MCP delete |
| Documents             | ✅   | ✅  | ✅     | ✅     | ❌     | 4 parent types (project/issue/initiative/cycle); no MCP delete |
| Cycles                | ✅   | —   | ❌     | ❌     | ❌     | UI only — team workflow |
| Teams                 | ✅   | ✅  | ❌     | ❌     | ❌     | Workspace-admin operations only |
| Users                 | ✅   | ✅  | ❌     | ❌     | ❌     | Workspace-admin operations only |
| Attachments           | —    | ✅  | ✅     | ❌     | ✅     | 2-phase upload preferred. `get_attachment` returns **file contents**, only on Linear-hosted uploads. |
| Diffs (Linear Reviews)| ✅   | ✅  | ❌     | ❌     | ❌     | Read-only; threads via `get_diff_threads` |
| Linear docs           | search| —  | —      | —      | —      | `search_documentation` queries linear.app/docs |

✅ supported · ❌ not supported · — n/a (no such operation in Linear)

### Tool inventory (35 tools)

| Group | Tools |
|---|---|
| Issues | `list_issues`, `get_issue`, `save_issue`, `list_issue_statuses`, `get_issue_status` |
| Comments | `list_comments`, `save_comment`, `delete_comment` |
| Labels | `list_issue_labels`, `create_issue_label`, `list_project_labels` |
| Projects | `list_projects`, `get_project`, `save_project` |
| Milestones | `list_milestones`, `get_milestone`, `save_milestone` |
| Documents | `list_documents`, `get_document`, `save_document` |
| Attachments | `get_attachment`, `prepare_attachment_upload`, `create_attachment_from_upload`, `create_attachment` (deprecated), `delete_attachment` |
| Diffs (Reviews) | `list_diffs`, `get_diff`, `get_diff_threads` |
| Teams/Users/Cycles | `list_teams`, `get_team`, `list_users`, `get_user`, `list_cycles` |
| Utility | `extract_images`, `search_documentation` |

**`save_*` tools all double as create+update** via the id-or-no-id pattern: pass `id` to update, omit to create. Applies to `save_issue`, `save_comment`, `save_document`, `save_milestone`, `save_project`. Schemas don't always spell this out.

**Polymorphic save_comment**: a comment's parent is any of `issueId`, `projectId`, `initiativeId`, `documentId`, `milestoneId` — exactly one. For replies, only `parentId` is needed (parent type inherited).

## Known gotchas

### Schema vs reality
1. **`list_projects` rejects `includeMembers` and `includeMilestones`** with HTTP 400 — despite the schema documenting them. Use `get_project` (which accepts them) or `list_milestones` separately for hydrated data.
2. **`extract_images` only finds Linear-hosted images** (`uploads.linear.app/...`), not arbitrary markdown image URLs. Schema description is misleadingly general.
3. **`get_attachment` returns decoded file CONTENT, not metadata** — and only works on Linear-uploaded files. On link attachments it errors *"Cannot fetch external URL"*. `delete_attachment`, conversely, works on both.
4. **`list_issues.includeArchived` defaults to `true`** but `list_projects/teams/documents/issue_labels` default to `false`. Pass `false` explicitly when you don't want archived issues.
5. **`list_issue_statuses` and `list_cycles` return bare arrays** — no `{items:[…], hasNextPage}` envelope like every other list tool.
6. **Signed upload URLs expire in 60 seconds.** PUT immediately after `prepare_attachment_upload`; chain the calls in one message.
7. **Icons require emoji shortcode format** (`:test_tube:`, not 🧪) for `save_project` and `save_document`. Literal unicode → "Argument Validation Error".
8. **`get_issue_status` schema marks `id`, `name`, AND `team` as required** even though `id` is a UUID and would be sufficient. Pass all three.

### Input/output shape mismatches
9. **`save_issue.estimate` input is a number; response is `{value, name}`** (e.g., `{value: 3, name: "3 Points"}`).
10. **`save_issue.milestone` input ⇄ `projectMilestone` response** — different field names for the same concept.
11. **Fields are omitted, not nulled, when unset.** Unassigned issues simply lack `assignee`/`assigneeId` keys — use existence checks (`?.` / `'assignee' in obj`), not null checks.
12. **`save_milestone` create returns a stripped shape** (`{id, name, progress, sortOrder}`); update returns the full object. Targetdate/description are absent when unset, not null.

### Behavior surprises
13. **`save_issue` with `project` + `assignee` on creation lands in `Backlog`, not `Triage`.** Convention #6's "default Triage" is for genuinely unscoped new issues. Set `state` explicitly if you need Triage.
14. **`duplicateOf` auto-transitions state AND sets `canceledAt`** — don't set state separately (Convention #5).
15. **`save_issue.links` auto-populates `subtitle` from the URL's page metadata** — Linear fetches the page and extracts the meta description. Not documented anywhere.
16. **`save_document.content` is rewritten on save** — bare issue refs (`CLO-130`) become `<issue id="…">CLO-130</issue>` markup; `@displayName` mentions get linkified.
17. **Project status NAMES are workspace-customized**, but `type` values are canonical (`canceled`, `started`, `completed`, etc.). Filter on `type`, not `name` — names vary per workspace. Same applies in part to issue status names, though our team's are stable.
18. **Linear has no manual archive verb anywhere.** Archive is auto-only at the team-settings level. That's why the MCP has no `archive_*` tool — the operation doesn't exist in the product.
19. **`get_issue` does not include comments, relations, or sub-issues by default.** Use `list_comments({issueId})` for the discussion, `includeRelations: true` on `get_issue` for blocking/related/duplicate links, and `list_issues({parentId})` for sub-issues. Treat "a Linear issue" as multiple API calls, not one. See *Reading a ticket for action* above.

### From earlier sessions (still true)
20. **"Duplicate label name" error may not mean the write failed.** Re-list with `list_issue_labels` before retrying.
21. **Flat labels with `/` in the name look grouped but aren't** (`name: "workflow/blocked"` with `parent: null`). Check the `parent` field.
22. **Workspace vs team-scoped labels live in different UI pages.** Pass no `teamId` for workspace-level (the convention here).
23. **`type/spike` is its own type, not a `chore`.** A spike succeeds when it produces an answer.
24. **Reserved label names blocked**: `assignee`, `cycle`, `effort`, `estimate`, `hours`, `priority`, `project`, `state`, `status` — they'd duplicate first-class issue properties.

## Pointers

- **Per-repo overlay:** `docs/agents/issue-tracker.md` (in each repo — may add repo-specific overrides)
- **Triage state machine:** `triage` skill
