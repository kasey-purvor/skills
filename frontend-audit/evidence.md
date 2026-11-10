# Screenshot evidence and handoff

Finding pictures, manifests, statuses and candidate findings go in the review's `evidence/` folder. Journey, coverage and changes notes go in `notes/`.

## Pictures

Named `<finding id>-<width>-<n>.png`: `F012-390-1.png`. Width is the screen width it was taken at; `n` counts from 1 per finding and width. Each agent takes its ids from a block the lead gives it (fit F001 to F099, controls C001 to C099, and so on), so agents never collide.

- A picture is an unchanged capture or a **crop** with enough surrounding context to orient the owner. Prefer a readable region over a tiny reduction of a very long page. Around 1,200px tall is a useful crop target, not a correctness limit; the overlay must stay aligned at every displayed size.
- For "this is three screens down", use a reduced whole page with the thing ringed, and give the distance in the caption.
- **Keep the original unchanged.** The ring is recorded as a box and drawn by the review page. Any necessary redaction must be disclosed; do not conceal or recreate the part supporting the finding.
- **How the fault is highlighted.** Every picture the owner sees has the part that matters outlined with a bright ring, and everything outside the ring dimmed to about half brightness, so the eye goes straight to the fault. The page draws both from the recorded box (`scripts/build_review.py`, `scripts/ring.py`: a 3px pink ring, the rest dimmed by half). A picture with no box is shown undimmed: use that only when the whole picture is the point.
- The same rule holds for every later picture: on a before and after pair, ring the same region in both, so the owner sees what changed without hunting for it.
- Usually one to three pictures are sufficient. Add more when they establish distinct roles, states or recovery; remove redundant shots. A comparison ("these two screens disagree") needs both sides at comparable widths.
- A behaviour needs a before and an after.

## The manifest: `manifest-<agent>.json`

A list with one object per picture:

```json
{
  "id": "F012",
  "file": "F012-390-1.png",
  "width": 390,
  "caption": "My tasks on a phone. The company and note columns have no width, and Done is off the right edge.",
  "boxes": [[0, 212, 390, 96]],
  "kind": "seen",
  "from": "shots/run1/tasks--390.png, cropped to 390 × 660px starting 1,240px down",
  "capture": {
    "original": "shots/run1/tasks--390.png",
    "viewport": { "width": 390, "height": 844 },
    "crop": [0, 1240, 390, 660],
    "output": { "width": 390, "height": 660 },
    "role": "Account manager",
    "state": "Loaded tasks after opening My tasks",
    "observed_at": "2026-10-05T10:00:00Z"
  },
  "made_note": "",
  "shows_fault": "yes",
  "note": ""
}
```

- `caption`: one or two plain sentences: what the picture shows and what is wrong in it. The owner reads only this and the picture.
- `boxes`: what to ring, each `[x, y, width, height]` **in the final image's own pixels**, after any crop or resize. Ring the relevant region tightly. Coordinates must be finite, dimensions positive, and every box inside the image; do not silently clamp a bad measurement. Empty means the whole picture is the point.
- `kind`: `seen` for the actual app reached through normal interface actions, including test data entered through the app. Note the test-data context in the caption or `note`. The legacy `made` value is retained only for importing older, explicitly labelled synthetic evidence; this workflow never manufactures inaccessible states.
- `made_note`: for legacy `made` evidence, exactly what was invented or switched on. Do not treat it as evidence that the current deployed journey is reachable.
- `shows_fault`: `yes`, `partly` or `no`. A comparison picture that shows the good case is `no`, with a note saying so.
- `capture`: recommended structured provenance for new captures. `crop` uses original pixels; `output` is the final image size and must match the file. `viewport` describes the browser, not the full-page image. Omit `crop` when no crop was made. Keep originals outside report inputs when sensitive. Legacy `from` notes remain supported.
- `finding`: optional; set it when the picture belongs to a finding whose id differs from `id` (after the merger splits or renames a finding).

## The status file: `status-<agent>.json`

One object per finding: `{"id", "status", "note"}`.

| Status | Means |
|---|---|
| `shown` | The picture shows the fault as described |
| `partly shown` | Some of the claim is visible; the behaviour or state is incompletely evidenced or reproduced |
| `not shown` | No picture could be made. The finding is only a lead; say what would be needed |
| `contradicted` | The picture shows the claim is wrong, or much smaller than claimed |

`contradicted` and `not shown` are good results. A review that reports them is trusted; one that never does is not.

## Handoff contract

Return one package per assigned journey or evidence group, using the assigned files rather than a separate HTML report:

- **Task:** the goal the explorer chose, expected outcome, discovery path and reproduction steps.
- **Context:** role, environment, safe state/record identifiers, viewport and capture time. Record touch emulation or keyboard testing separately from viewport resizing.
- **Evidence:** unchanged originals, selected image paths, crop/resize provenance and final-pixel boxes. Behaviour includes before/after observations and elapsed time.
- **Consequence:** observed task impact, any working alternative and recovery attempted. Separate inference from observation.
- **Uncertainty:** confidence with a reason, contradictory observations, unvisited states and what a targeted follow-up would resolve.
- **Actions:** records created or changed, sends, submissions, intentional deletions and what remains, including uncertain outcomes.

Capture-only workers may return observations without inventing findings or a classification. New retained findings use `classification`, `confidence`, `impact` and `recovery` as described in [findings.md](findings.md). The coordinator tracks missing parts and assigns targeted follow-up; a gap is not permission to inspect source or fabricate the state.

## Checking a box

The commonest mistake is a box that is off: measured on the full page and applied to the crop. Draw every ring on a preview and look at it before listing the picture:

```
python3 scripts/ring.py <crop.png> <preview.png> "x,y,w,h" ["x,y,w,h" ...]
```

Evidence previews and scratch files go in `evidence/_work/<agent>/`, never beside the pictures. Preview alignment is only the first check: also inspect the overlay on the rendered report at phone and desktop widths and in the enlarged view. A correct source box can still be distorted by the report layout.

## Writing a finding

Beside its pictures, each finding needs these, in plain words, in the agent's own `findings-<agent>.json` (same fields as `findings.md` describes):

- **title**: the fault in one line, as the owner would say it. "Rep Assignments: the Save button is off screen."
- **wrong**: two or three sentences. What you see, with the measured numbers.
- **who**: which observed role, tenant or feature setting meets it. Include frequency only when established; do not invent usage patterns.
- **fix**: the proposed layout or behaviour, in one or two sentences. Use relevant settled decisions (when supplied) or the handbook pattern catalogue where they fit. Explorers need not know prior design decisions to record an observation.
- **detail**: reproduction steps, expected and observed outcomes, role, viewport, measurements, and remaining uncertainty. Do not infer a source-code cause. Include safe references to the corresponding journey and changes notes.

## Journey and changes notes

Alongside evidence, keep per-agent notes under `notes/` for coverage and actions. For each data-changing action record the role, journey, action, safe record name or identifier, observed outcome, and what remains. Include sends and submissions as well as newly created records. Report uncertain outcomes. **Leave changes in place by default; these notes are an account of the work, not a cleanup checklist.** The coordinator includes this account in the final HTML.

For a behaviour finding, include the triggering action, before/after images, elapsed observation time where relevant, and any recovery attempted. A screenshot pair alone does not establish the internal cause.
