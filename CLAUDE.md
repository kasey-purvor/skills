# ~/.claude/skills — authorship and sync

This directory is the runtime view of skills Claude Code loads. It is also the working tree of the **`kasey-purvor/skills`** GitHub repo (used for cross-machine sync). Skills come from two sources, which are managed differently.

## Two layers

```
~/.claude/skills/
├── <skill>/              ← runtime: what Claude Code actually loads
└── skills/               ← nested git repo: full mattpocock/skills clone, kept as a reference + update mechanism
    └── skills/<category>/<skill>/   ← upstream versions of the Matt-authored skills
```

The outer repo (`kasey-purvor/skills`) tracks **both layers as files** — no git submodule. The inner clone (`skills/`) is its own repo for `git pull` access to upstream, but its files are also tracked by the outer repo. This means a pull from Matt's upstream surfaces in the outer repo as a set of file modifications under `skills/`, which then need committing to the outer fork to propagate to other machines.

## Authorship inventory

### Matt-authored skills (vendored from mattpocock/skills)

These have a 1:1 counterpart at `skills/skills/<category>/<name>/`. When Matt ships updates, these may need re-syncing.

| Skill | Upstream path (under skills/skills/) |
|---|---|
| `caveman` | `productivity/caveman/` |
| `diagnose` | `engineering/diagnose/` |
| `git-guardrails-claude-code` | `misc/git-guardrails-claude-code/` |
| `grill-me` | `productivity/grill-me/` |
| `grill-with-docs` | `engineering/grill-with-docs/` |
| `handoff` | `productivity/handoff/` |
| `improve-codebase-architecture` | `engineering/improve-codebase-architecture/` |
| `prototype` | `engineering/prototype/` |
| `review` | `in-progress/review/` |
| `setup-matt-pocock-skills` | `engineering/setup-matt-pocock-skills/` ⚠ local customizations |
| `setup-pre-commit` | `misc/setup-pre-commit/` |
| `tdd` | `engineering/tdd/` |
| `to-issues` | `engineering/to-issues/` ⚠ local customizations |
| `to-prd` | `engineering/to-prd/` |
| `triage` | `engineering/triage/` ⚠ local customizations |
| `write-a-skill` | `productivity/write-a-skill/` |
| `zoom-out` | `engineering/zoom-out/` |

### User-authored skills (no upstream)

These are original work or forks. Edit freely; nothing to sync.

| Skill | Notes |
|---|---|
| `dev-condition-based-waiting` | Flaky-test fixing via condition polling |
| `dev-design-an-interface` | Generate multiple interface designs via parallel sub-agents |
| `dev-request-refactor-plan` | Refactor plan as GitHub issue |
| `dev-standards-handbook/` | Reference library of production engineering topics |
| `dev-standards-pitfalls` | Named anti-pattern catalogue |
| `dev-writing-skills` | TDD-for-skills methodology (different scope from Matt's `write-a-skill`) |
| `learn` | End-of-conversation knowledge extraction |
| `permission-reviwer` | Claude Code permission allowlist helper *(typo in dir name — frontmatter `name: util-permission-helper`)* |
| `spark` | Local vLLM inference helper |
| `mcp-confluence`, `mcp-diagrams*`, `mcp-markdown-to-pdf` | MCP integration helpers |

## Local customizations (divergence from upstream)

These are the only places we've modified Matt-authored content. **Watch for conflicts when pulling upstream.**

### `setup-matt-pocock-skills/`

| File | Change |
|---|---|
| `issue-tracker-linear.md` | NEW — entire file is local. Adds Linear as a tracker option using `mcp__plugin_linear_linear__*` MCP tools and a hybrid status+label triage mapping |
| `SKILL.md` | EDITED — added Linear as 4th first-class option in Section A, removed Linear from "Other" examples, added `issue-tracker-linear.md` to Section 4 seed templates list, expanded frontmatter description to mention all four trackers |

Linear triage labels live in the **Cloud Assist** team in Linear, under the `triage` label group (`needs-info`, `ready-for-agent`, `ready-for-human`). `needs-triage` and `wontfix` use Linear's native Status (Triage, Canceled) — no labels needed.

### `triage/`

| File | Change |
|---|---|
| `SKILL.md` | REPLACED — full rewrite as a Linear-anchored lightweight workflow. Drops the `needs-triage` label, bug/enhancement category roles, AI-generated disclaimer, parallel agent-brief template, and the `.out-of-scope/` knowledge base. Spec edits land in the description (per `linear` Convention #9), not comments. The two `ready-for-*` labels share the same template, differing only by intended executor. |
| `AGENT-BRIEF.md` | DELETED — divergent template; absorbed by anchoring to the `linear` skill's agent-ready shape. |
| `OUT-OF-SCOPE.md` | DELETED — feature-rejection knowledge base no longer in use. |

### `to-issues/`

| File | Change |
|---|---|
| `SKILL.md` | EDITED — removed `Constraints` from the two parenthetical references to the agent-ready template, matching the slimmed template in the `linear` skill (which no longer has a Constraints section). |

## Sync workflow — pulling Matt's updates

```bash
cd ~/.claude/skills/skills
git fetch origin
git log --oneline HEAD..origin/main           # preview what's incoming
git pull --ff-only origin main                # fast-forward the clone
```

This updates the inner clone. The outer repo (`~/.claude/skills/`) will now show modifications under `skills/`. For each modified upstream skill, decide what to do with the corresponding **root-level** copy:

```bash
cd ~/.claude/skills
# For each Matt-authored skill at root, diff against upstream:
diff -ruN <skill>/ skills/skills/<category>/<skill>/
```

**Three outcomes per skill:**

1. **Root copy is unmodified from upstream** (most common case) → replace root copy with upstream:
   ```bash
   rm -rf <skill> && cp -r skills/skills/<category>/<skill> <skill>
   ```
2. **Root copy has local customizations** (`setup-matt-pocock-skills/` today) → manual three-way merge: apply upstream changes while preserving local edits. The "Local customizations" section above lists current divergences.
3. **Upstream change isn't wanted** → leave root copy alone, document why here.

Finally commit both layers to the outer repo:

```bash
cd ~/.claude/skills
git add -A
git commit -m "Sync upstream mattpocock/skills @ <new-commit>"
git push
```

## Conventions for future authorship

- **Adding a new user-original skill:** put it at root with a `dev-` prefix (or no prefix for non-developer tools like `learn`, `spark`). Add a row to the User-authored inventory above.
- **Forking a Matt skill to customize:** rename to `dev-<name>` so it's clear it's diverged, delete the upstream-mirrored copy at root, document the fork in Local customizations.
- **Modifying a Matt skill in-place** (rare — usually you'd fork instead): add an entry to Local customizations describing what changed and why, so the next sync knows to merge carefully.

## Profile

This repo is on the **personal** GitHub account (`kasey-purvor`). Pushing requires `gh` to be authed as `kasey-purvor` — open a terminal in the `personal` profile, or run `gh auth switch --user kasey-purvor` for a one-off.
