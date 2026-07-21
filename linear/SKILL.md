---
name: linear
description: Operational conventions for the Linear workspace — label scheme, statuses, common MCP recipes, and known gotchas. Use when creating, updating, commenting on, or closing Linear issues, or running any `mcp__plugin_linear_linear__*` tool.
---

# Linear

Day-to-day operational skill for the team's Linear workspace. Loaded on any Linear MCP operation.

**The workspace is organized `team = product`, `project = epic`.** Each repo maps to exactly one product **team** (`repo = team` — a fixed, one-time binding); a **project** is a delivery epic within that team. Team name + issue prefix are per-repo — read them from `AGENTS.md` (`## Agent skills` → `### Issue tracker`). Examples below use `CLO-123` illustratively.

## Cheat sheet

### Statuses (in workflow order)

| Status | Category | When |
|---|---|---|
| Triage | triage | Native landing for externally-filed issues; agents create into Backlog |
| Backlog | backlog | Where agent-created tickets land (scoped or not); awaits your go |
| Todo | unstarted | Greenlit to start — momentary; agent sets it at pickup, then starts |
| In Progress | started | Active work; PR branch cut |
| In Review | started | PR open, awaiting review or CI |
| Done | completed | Shipped — PR merged |
| Canceled | canceled | Won't do |
| Duplicate | duplicate | Auto-applied when `duplicateOf` is set |

### Labels (4 mutex groups + 3 free-floating)

| Group | Values |
|---|---|
| `type/*` | `bug`, `chore`, `feature`, `refactor`, `spike` |
| `quality/*` | `drive-by`, `scoped`, `audited` — spec maturity; `audited` = passed the pre-work re-audit |
| `blocked/*` | `needs-decision`, `needs-info`, `blocked-by-work` |
| `kickback/*` | `for-ben`, `for-kasey` — **human-only; agents never set these** (attention hand-off between colleagues) |
| `security` | free-floating; security-sensitive code or behaviour |
| `ai-added` | free-floating; ticket was created by an AI agent |
| `nit` | free-floating; small hardening/cleanup deliberately deferred at discovery (see *Review-finding disposition*) |

Mutex = mutually exclusive within a group; picking a second value drops the first. All labels live at **workspace level** — never pass `teamId`.

Priority is the **native Linear Priority field**, set by humans only. It is deliberately absent from this skill; agents never set or reason about it.

## Conventions

1. **One label per group max** — mutex is enforced.
2. **Free-floating labels (`security`, `ai-added`, `nit`) apply alongside group labels** — they don't belong to any mutex group.
3. **Comment before state change** — when moving to Done/Canceled, post a `save_comment` rationale *first*, then the `save_issue` state change.
4. **Set `duplicateOf` — don't also set state.** Linear auto-transitions to Duplicate.
5. **Spec changes edit the description, not comments.** Mid-flight enrichment, scope changes, AC amendments, and deviations all amend the description in place; a one-line breadcrumb comment can point at the change. The description is what every downstream reader sees — spec content kept only in comments is invisible to them. For what comments *are* for, see *Reading a ticket for action* below.
6. **`quality/*` signals spec maturity, not schedule.** `drive-by` = an unscoped dump; `scoped` = has a real spec (see *Ticket body*); `audited` = re-audited and ready to pick up. It does **not** gate status — every ticket lands in Backlog regardless of `quality/*`, and scheduling (Backlog → Todo) is your call (see *Status lifecycle*).
7. **`kickback/*` is human-only.** Agents never set or remove it — but must preserve it when updating other labels (replace-only API, see recipes).
8. **Agents label their own tickets `ai-added`.** Any ticket an agent creates gets the free-floating `ai-added` label.
9. **Every ticket homes in its team; homing in an epic (project) is the strong default.** The team is mandatory — it's simply where the ticket lives. Beyond that, **strongly prefer** the epic whose area the ticket touches — the cross-epic view is how work is navigated, and there is deliberately no junk-drawer project. **Exceptions, by judgment (not a hard gate):** a `quality/drive-by` ticket (too raw to know its epic) and a `nit` not clearly tied to any epic may sit projectless — home them once scoped / once the owning epic is clear. Nits usually *do* spring from an epic; place them there when they do. A *scoped* ticket with no obvious epic → ask, don't invent a holding project.
10. **Agent-created tickets are assigned to the operating human.** Pass `assignee: "me"` on creation — the MCP session is signed in as its human, so `"me"` resolves to Kasey on Kasey's machines and Ben on Ben's, with nothing hardcoded. Override only when explicitly told the ticket is for the other person (email works: `ben.ward@` / `kasey.purvor@thecloudassist.com`). Assignment is ownership, not attention — `kickback/*` (human-only) remains the attention hand-off.

## Status lifecycle

Agents drive the **forward flow** of statuses; the **human decisions** are scheduling (Backlog → Todo) and cancellation (→ Canceled) — every move between them is agent bookkeeping. In order:

| From → To | Trigger | Who |
|---|---|---|
| *(create)* → **Backlog** | any agent-created ticket, `scoped` or `drive-by` | agent — bookkeeping |
| **Backlog → Todo** | you decide to do it (epic or standalone) | agent, **on your go** — never self-scheduled |
| **Todo → In Progress** | work starts / branch cut | agent — bookkeeping |
| **In Progress → In Review** | PR opened / review underway | agent — bookkeeping |
| **In Review → Done** | PR merged | `Closes` auto-transitions *if it fires*; else the agent sets Done (Conv #3) |

- **Two moves are your call: scheduling (Backlog → Todo) and cancellation (→ Canceled).** Every forward move between them follows mechanically from work already in motion — the agent keeps the tracker honest, it does not decide.
- **Todo is a momentary green-light, not a staging queue** — set at pickup, the instant before starting; never ahead-of-time grooming.
- **`quality/*` does not gate status** — everything lands in Backlog regardless of spec maturity; your go is what promotes it (Convention #6).
- **Agents set `state: Backlog` explicitly on create** — a projectless ticket (e.g. a `drive-by`) would otherwise default to Triage natively (gotcha #13).
- **`Canceled` (won't-do) is a human decision**, same gate as scheduling — comment first (Convention #3).
- The **In Review** step may be handled by you *or* an agent (Playwright or otherwise); the review + evidence process lives in the `AGENTS.md` work lifecycle.

## Review-finding disposition

When a review (agent, handbook, or human) produces findings, **every finding is surfaced and recorded — the agent never silently drops one.** The agent proposes a disposition for each; **the human is notified and has the last word on how it's recorded.** Three dispositions:

1. **Fix in the PR** — defects in code the PR introduces (correctness, security, data-loss), or anything cheap that touches files already in the diff. New code merges clean; deferring defects on brand-new code is how quality erodes.
2. **Becomes a ticket** — work beyond the PR's scope: needs its own decision (`blocked/needs-decision`), touches code outside the diff, or the human decides it shouldn't hold up the merge. Small deferred hardening gets the `nit` label, sized to one coherent ticket (one "hardening pass over X", not one ticket per one-liner). Home it in the epic whose area it touches when it clearly belongs to one (nits usually do); a nit spanning no single epic may sit projectless — Convention #9. There is deliberately NO junk-drawer project; the cross-epic `nit` **label** view — not project membership — IS the debt register.
3. **Declined** — a considered rejection the **human signs off on**: comment on the driving ticket ("considered, declined because X"), no ticket. The agent may *recommend* declining but records the finding for your decision — it is never an agent assumption.

**Security-relevant findings are never declined** — they ride the PR or get a ticket carrying `security`.

**PR timing is the human's call, never a ticket count.** The agent surfaces findings and may advise that a hardening pass is warranted; it does not trigger or batch a PR based on how many `nit`s are open. An agent already opening a PR in an area may fold in adjacent open `nit` tickets (`Closes CLO-x`) as a convenience — that rides an existing PR, it doesn't decide when one happens.

## Projects

- **A project = a delivery epic** — a coherent outcome with an end (a phase/journey slice), not a category.
- **Agents may create (open) and close projects.** Creating one is a planning-boundary act — do it deliberately for a real epic, not a catch-all and not reflexively mid-session. Closing = marking the epic Completed (or Canceled) when its work is done. This is a *permission*, not a chore: no completion-hygiene obligation, and the human can create/close projects too. (Ticket-status authority lives in *Status lifecycle* above.)
- **Home every ticket in the epic whose area it touches** — review findings and post-completion bugs included (a finished epic still homes its trailing work). Strong default, not an absolute — see Convention #9 for the `drive-by` / loosely-related-`nit` exceptions. No obvious epic for a scoped ticket → ask (Convention #9); never create a holding project.

## Sub-issues (parent/child)

A **project (epic)** groups many *independent* tickets toward one outcome. A **parent/sub-issue** link is different: it's for *one* body of work big enough to coordinate as children — a tracking issue whose sub-issues are its slices, or a ticket that splits mid-flight. Reach for sub-issues only on genuinely complex, multi-slice work; most tickets need just team + project + labels, not a hierarchy.

- Set on create/update via `save_issue({ parentId: "CLO-100" })` (`null` removes it); read children with `list_issues({ parentId })`. Both verified 2026-07-20.
- A sub-issue keeps its own team, project, labels, and state; a parent and its children normally share the same project.

## Reading a ticket for action

`get_issue` does NOT return comments. Anyone reading a ticket programmatically to take action (audit, implement, review, dispatch a subagent) MUST call `list_comments({issueId})` alongside `get_issue`. For tickets with linked work, pass `includeRelations: true` to `get_issue` as well. Treat "reading a Linear issue" as at minimum two API calls — description plus discussion — never one.

**Legitimate things comments contain** (and that downstream readers therefore need):

- Implementer follow-up sweeps documenting scope-deferral decisions (e.g., "ran a value-level grep, found X / Y / Z, deferred them because…")
- Code-review findings against an in-review ticket
- Blocker discussions (paired with a `blocked/*` label per *Blocked & kickback*)
- Status updates ("implementation complete, awaiting review", "shipped in #142")
- Post-merge notes (verification on staging, follow-up surprises)
- Threaded discussion among reviewers

**What does NOT belong in comments** — see Convention #5:

- Enrichment of a thin spec into a scoped/audited spec — edits the description.
- Scope changes, AC additions/removals, constraint changes — edit the description.
- Spec deviations discovered during implementation — amend the description, then leave a breadcrumb comment if helpful.

**When dispatching a subagent against a ticket, the orchestrator fetches both `get_issue` and `list_comments` and passes both into the briefing.** Do not assume the subagent will fetch comments itself unless explicitly instructed.

## Ticket body

The standard shape for a well-formed ticket. A ticket earns `quality/scoped` once it carries this; `quality/audited` after the pre-work re-audit.

<ticket-body-template>

## TL;DR
Plain-English, jargon-free — what this ticket is and why, in 2–3 sentences a non-technical reader could follow. The structured spec below is for whoever implements it.

## Goal
One sentence: what user-visible behavior changes and why.

## Scope
- In: what this issue covers
- Out / Non-goals: what it explicitly does not

## Acceptance criteria (AC)
- [ ] Binary checkboxes — each independently verifiable
- [ ] Avoid soft criteria like "should be fast" or "code should be clean"

## Verification
How to prove it works. Exact command, URL, or observable result — never "make sure it works."

</ticket-body-template>

**File paths and code snippets stay out of the body** — they go stale fast. Exception: prototype snippets that encode a decision more precisely than prose can (state machine, schema, type shape).

**Time estimates and file-count limits are guidance, never rules.** They are useful signals about whether an issue is well-sized; they are not targets the implementation must hit. If an issue feels too big, decompose it; too small, merge it.

**Retrofitting a thin existing ticket?** Same template — fill it into the description in place (Convention #5).

## Blocked & kickback

When work is blocked, apply the relevant `blocked/*` label (`needs-decision` / `needs-info` / `blocked-by-work`) with a comment explaining the blocker; leave the issue in its current state. To resume: resolve the blocker, remove the `blocked/*` label.

```
issue = get_issue({ id: "CLO-123" })   // fetch current labels first
save_comment({ issueId: "CLO-123", body: "Blocked on: <specific question/decision>" })
save_issue({ id: "CLO-123", labels: [...issue.labels.map(l => l.name), "needs-decision"] })
```

**Kickback is the human hand-off, not a blocker signal.** A human applies `kickback/for-ben` or `kickback/for-kasey` to grab that colleague's attention — for information, a review, or a decision. Agents never set it, and preserve it on label updates.

## Common recipes

### Create
```
save_issue({ team: "<team>", title, description, project: "<project>", labels: ["feature", "scoped", "ai-added"], assignee: "me", state: "Backlog" })
```
**Labels are sent as bare names** (`feature`, `scoped`) — the group is determined by each label's own `parent` field in Linear, not by passing a compound string like `"type/feature"`.

### Update labels (replace-only — fetch first!)
The MCP **overwrites** the label array. To add one without losing others:
```
issue = get_issue({ id: "CLO-123" })
save_issue({ id: "CLO-123", labels: [...issue.labels.map(l => l.name), "security"] })
```

### Close
```
save_comment({ issueId: "CLO-123", body: "Shipped in #142. Verified on staging." })
save_issue({ id: "CLO-123", state: "Done" })  // or "Canceled"
```

### Mark duplicate
```
save_issue({ id: "CLO-123", duplicateOf: "CLO-90" })  // state auto-becomes Duplicate
```

### Add a milestone, then attach an issue
```
save_milestone({ project: "Project Name", name: "M1", targetDate: "2026-06-15" })
save_issue({ id: "CLO-123", milestone: "M1" })   // accepts name OR id
```
On create, `save_milestone` returns a stripped object (no `targetDate`/`description` when unset); on update it returns the full object. The issue response field is **`projectMilestone`** (not `milestone`).

### Create a document (4 possible parents)
```
save_document({ title: "Spec", project: "Project Name", content: "# Spec\n..." })
save_document({ title: "Notes", issue: "CLO-123", content: "..." })
save_document({ id: docId, content: "Updated..." })   // update
```
Exactly one parent: `project`, `issue`, `initiative`, or `cycle`. `content` is rewritten on save — bare issue refs (`CLO-123`) become issue-mention markup.

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
issue = get_issue({ id: "CLO-123" })            // fetch the CURRENT description — there is NO append API
prep  = prepare_attachment_upload({ issue: "CLO-123", filename, contentType, size })
// PUT raw bytes to prep.uploadRequest.url with prep.uploadRequest.headers VERBATIM (60s expiry!)
save_issue({ id: "CLO-123",
  description: issue.description + "\n\n## Verification evidence\n\n![alt text](" + prep.assetUrl + ")" })
// optional: also create_attachment_from_upload({ issue, assetUrl: prep.assetUrl }) to add the panel row too
```
- **`![alt](url)` is an image; `[alt](url)` is a link** — the leading `!` is what makes it render inline.
- **One upload, two homes.** The same `prep.assetUrl` works for both the inline embed AND `create_attachment_from_upload` — for headline proof (e.g. a UAT verification shot), do both from a single PUT.
- **`save_issue` overwrites the whole description** (no append API) — fetch it first and concatenate, keeping real newlines. On save Linear **re-signs** the asset URL (`?signature=…`, short-lived) and **re-linkifies bare issue refs** (`CLO-123` → markup), so send bare refs, not `<issue …>` markup.
- **Scoped per issue:** `prepare_attachment_upload` ties the asset to the `issue` you pass — re-upload (don't reuse an `assetUrl`) when embedding the same image into another ticket.

**Inline vs panel:** inline for anything worth *seeing at a glance* (screenshots, diagrams, stylistic before/after); panel for supplementary files (logs, larger artifacts); both for headline verification evidence.

### Threaded comment reply
```
save_comment({ parentId: rootCommentId, body: "Reply..." })   // no issueId needed
```
Replies inherit the root's entity automatically. `list_comments` returns the thread flat — `parentId` encodes nesting.

## MCP capabilities (verified)

Verified end-to-end against a live workspace on **2026-05-27**. This table is canonical for the tools it lists — defer to it before falling back to "the schema looks like…". When in doubt, the underlying tool exists for every ✅; a ❌ means it didn't exist as of the verification date — the staleness note below applies to ❌ cells too.

**Staleness note (2026-07-21):** the live server has since grown beyond this verified set (~47 tools live vs the 35 below — releases, status updates, agent skills are unlisted). Absence from this table means **unverified, not nonexistent** — re-verify before relying on an unlisted tool. Full matrix re-verification is parked as its own task.

### Resource × operation matrix

| Resource              | List | Get | Create | Update | Delete | Notes |
|-----------------------|:----:|:---:|:------:|:------:|:------:|---|
| Issues                | ✅   | ✅  | ✅     | ✅     | ❌     | `save_issue` does both (id present = update). No MCP delete. Sub-issues via `parentId`. |
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

### Tool inventory (35 verified tools — live server exposes more; see staleness note)

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
13. **Creation state depends on what you pass: `project` + `assignee` lands in `Backlog`; a projectless ticket natively defaults to `Triage`.** Don't rely on either — agents always pass `state: "Backlog"` explicitly on create (see *Status lifecycle*).
14. **`duplicateOf` auto-transitions state AND sets `canceledAt`** — don't set state separately (Convention #4).
15. **`save_issue.links` auto-populates `subtitle` from the URL's page metadata** — Linear fetches the page and extracts the meta description. Not documented anywhere.
16. **`save_document.content` is rewritten on save** — bare issue refs (`CLO-130`) become `<issue id="…">CLO-130</issue>` markup; `@displayName` mentions get linkified.
17. **Project status NAMES are workspace-customized**, but `type` values are canonical (`canceled`, `started`, `completed`, etc.). Filter on `type`, not `name` — names vary per workspace. Same applies in part to issue status names.
18. **Linear has no manual archive verb anywhere.** Archive is auto-only at the team-settings level. That's why the MCP has no `archive_*` tool — the operation doesn't exist in the product.
19. **`get_issue` does not include comments, relations, or sub-issues by default.** Use `list_comments({issueId})` for the discussion, `includeRelations: true` on `get_issue` for blocking/related/duplicate links, and `list_issues({parentId})` for sub-issues. Treat "a Linear issue" as multiple API calls, not one. See *Reading a ticket for action* above.

### From earlier sessions (still true)
20. **"Duplicate label name" error may not mean the write failed.** Re-list with `list_issue_labels` before retrying.
21. **Flat labels with `/` in the name look grouped but aren't** (`name: "workflow/blocked"` with `parent: null`). Check the `parent` field.
22. **Workspace vs team-scoped labels live in different UI pages.** Pass no `teamId` for workspace-level (the convention here).
23. **`type/spike` is its own type, not a `chore`.** A spike succeeds when it produces an answer.
24. **Reserved label names blocked**: `assignee`, `cycle`, `effort`, `estimate`, `hours`, `priority`, `project`, `state`, `status` — they'd duplicate first-class issue properties. (This is why Priority and Project/hierarchy are native fields here, not labels.)

## Pointers

- **Per-repo binding:** `AGENTS.md` → `## Agent skills` → `### Issue tracker` (team name + issue prefix; `repo = team`, so this is fixed)
- **Work lifecycle (ticket → branch → PR):** `AGENTS.md`
