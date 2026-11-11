# Consolidation, report and delivery

## `findings.json`

The merger writes one combined specification. The coordinator can build it progressively; unfinished coverage and evidence must be labelled in the draft rather than presented as final verification. Build from a consistent snapshot of completed worker packages and their matching manifests, not files another worker is still writing or unmerged candidate IDs. Selected report inputs may live in a separate directory; preserve the original worker evidence.

```json
{
  "title": "Acme experience review",
  "storage_key": "acme-review-1",
  "lede": "Rule on each finding: keep, drop or discuss.",
  "sections": [
    { "id": "main", "title": "Task and interpretation findings" },
    { "id": "minor", "title": "Smaller improvements", "layout": "grid" }
  ],
  "findings": [
    {
      "id": "F012", "section": "main",
      "title": "My tasks opens with Done outside the phone viewport",
      "classification": "defect",
      "confidence": "High: reproduced twice in the recorded phone journey.",
      "impact": "The person must discover horizontal scrolling to finish the task.",
      "recovery": "The action becomes visible after scrolling the table sideways.",
      "badges": ["Phone", "Account manager"],
      "wrong": "The action column is outside the initial viewport.",
      "who": "Account managers checking tasks at 390px wide.",
      "fix": "Keep the completion action reachable alongside the task name.",
      "already": "",
      "detail": "See the before/after interaction record in notes/tasks-journey.md."
    }
  ],
  "pieces": [
    { "id": "W1", "name": "Task completion on phone", "covers": "Keep actions reachable.", "findings": ["F012"] }
  ]
}
```

- Findings appear in listed order within their section. Rank by task impact, observed reach and recovery cost. A blocked action or misleading outcome usually outranks cosmetic discomfort; do not invent frequency or implementation effort.
- `classification`: `defect` for a reproduced failure or contradiction in the interface; `improvement` for a usable journey that could work better; `policy` for a tradeoff or meaning that needs an owner decision. This is separate from whether a picture proves the claim. Reclassify when ticket context reveals an intentional policy rather than assuming a regression.
- `confidence`, `impact`, `recovery`: plain strings explaining the evidence, consequence and working alternative. New retained findings supply these; older specifications remain compatible without them.
- `badges` are observed facts. `flags` are a few established conditions worth emphasising, not speculative urgency. Review ordering and impact are not permission to set tracker priorities.
- `already`: settled decisions or concise ticket context, rendered as escaped text. Use structured `reconciliation` below for clickable ticket links.
- `storage_key`: unique per review and stable through rebuilds, so feedback persists without mixing reviews. Do not change it to clear the owner's answers.
- `pieces`: optional candidate work groups, a menu rather than an implementation plan. Omit `size` unless there is an actual basis for an estimate.

Keep source finding IDs and a short merge record for duplicates, splits and rejected claims. Update both finding prose and evidence-status notes when verification changes a conclusion. A candidate rejected by a stable live check should not remain in the report as an established defect.

## Coverage, actions and ticket comparison

The HTML itself includes scope, roles, viewport coverage, completed journeys, meaningful gaps and all test changes left in the environment. For a compact review, `lede` and `footnote` may suffice. For larger reviews use the optional native fields below; custom local sections are also allowed when they preserve the evidence and feedback controls. A review with no findings still needs coverage and an action account.

```json
{
  "coverage": {
    "summary": "Review of the agreed test environment and populated test tenant.",
    "roles": ["Account manager"],
    "viewports": ["390 × 844", "1280 × 900"],
    "journeys": [
      { "role": "Account manager", "viewport": "390 × 844", "journey": "Complete a task", "outcome": "Completed after horizontal scroll", "evidence": "notes/tasks-journey.md" }
    ],
    "gaps": ["No physical touchscreen or screen-reader session."]
  },
  "actions": [
    { "role": "Account manager", "action": "Completed test task", "record": "REVIEW-Task-1", "outcome": "Completed status shown", "left_in_environment": "Task remains completed; no cleanup." }
  ],
  "reconciliation": [
    { "ticket": "APP-123", "url": "https://tracker.example/APP-123", "finding_ids": ["F012"], "match": "partial", "summary": "Existing mobile-table work lacks a criterion for action reachability.", "checked": "Current description and discussion; phone task journey." }
  ]
}
```

These fields are optional and text is plain text, not arbitrary HTML. `coverage.journeys[].evidence` and `reconciliation[].checked` are strings. A reconciliation row may omit `ticket` and `url` for a new unmatched finding; use `finding_ids` to identify it. A ticket-only row may omit `finding_ids`.

Read existing ticket descriptions **and discussion** after independent discovery; keep expectations out of explorer briefs. Match each retained finding as `exact`, `partial` or `new`. Distinguish an existing acceptance criterion from a proposed scope extension. Completed origin tickets can be provenance without implying an active fix exists. Record ticket-only results as `apparently-resolved` or `not-verified`, with the exact journey, role, state/version and limitations checked. A successful sub-item does not close a multi-item ticket, and non-reproduction is not proof of resolution. Apply the owner's existing tracker authorisation; do not create duplicates or silently close, expand or reprioritise work.

Keep every worker's action record, with safe identifiers and observed outcomes, including uncertain sends. **No automatic cleanup.** These are changes left in place, not a teardown checklist.

## Building and checking

```sh
python3 scripts/build_review.py findings.json evidence review.html
NODE_PATH=<playwright-module-parent> node scripts/check_review.cjs review.html F012
```

The builder validates evidence references and highlight geometry. The checker uses an isolated browser, loads images and checks the report at desktop and phone sizes, including feedback and rendered highlight geometry. Named findings are captured into `check/` for visual inspection. Automated checks do not decide whether the selected region actually supports a claim: inspect every selected highlight independently for a full delegated review, and have the coordinator inspect a representative rendered sample.

Use targeted live verification while sessions are available. Once consolidation and material corrections are complete, freeze the retained evidence set. Reconciliation can add policy context or trigger a specific correction, but it is not a reason to repeat every journey. Finish with the following gate:

- Claims match their interaction records and pictures; contradictory evidence and limits are explicit.
- Originals are preserved; boxes fit the final images and remain aligned in inline and enlarged views.
- Scope, gaps, action logs and any requested ticket mapping are present and consistent.
- Images and links work; desktop and phone rendering is readable without accidental page overflow. Tables remain readable through their intended scroll area.
- Keep / Drop / Discuss, clearing a choice, notes, persistence, filtering, highlights and export work. Test feedback is isolated from the owner's feedback.
- The owner receives a verified clickable local web link and the file location.

After a correction, verify only the affected claims, images, sections or controls. Reopen broader review only when new evidence invalidates an earlier conclusion or a material coverage gap changes the result. Do not keep adding independent final sweeps after the gate passes. Independent-review limits must be disclosed when delegation is unavailable or outside the assignment.

## Serve and hand over

Start a local server in a managed session that stays alive for the owner's review:

```sh
python3 scripts/serve_review.py /absolute/path/to/review.html
```

The helper serves only the chosen report by default. If a report uses local galleries or later feedback pages, explicitly allow just the required assets with repeated `--allow-asset` arguments, for example `--allow-asset shots --allow-asset gallery-thumbs`. A later feedback page can explicitly allow its `review-input.js` file; do not serve the whole review workspace, private authentication files or raw mail. It binds only to loopback and prints a normal `http://localhost:…/…` link. Omitting `--port` selects a free port on first start; record it and reuse it with `--port` on later starts. Verify the printed URL returns the report and opens correctly before delivery. Keep the serving process available, and report any access limitation rather than claiming a filesystem path is a working hyperlink.

Keep the same port, hostname and review `storage_key` during the owner's feedback cycle: browser storage is tied to the origin, so switching between file URLs, ports or `localhost` and `127.0.0.1` does not carry answers automatically. Before an unavoidable move, have the owner export existing rulings; preserve those exports. Do not replace or clear their feedback during checks.

Give the clickable web link first, the file path as a fallback, counts and important verification limits. Keep all evidence local; do not publish the report to an external service. The owner can Keep, Drop or Discuss each entry, add notes and use Copy or Save:

```text
F012 keep
C004 drop: not worth it until the redesign
F020 discuss: what would cards look like here?
```
