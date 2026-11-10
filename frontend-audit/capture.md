# Discovering and capturing real screens

Discover screens through role exploration; do not build an inventory from application routes or internal documents. Capture transient states during exploration rather than expecting a later capture worker to recreate everything.

## Screen inventory

Use one entry per screen state, not just per route. The batch tool accepts:

```json
[
  { "slug": "customers", "path": "/customers", "ready": "h1" },
  { "slug": "customer-orders", "path": "/customer/ACME", "ready": "[role=tablist]",
    "steps": [{ "click": "text=Orders" }] },
  { "slug": "orders-table-swiped", "path": "/orders",
    "steps": [{ "scrollRight": ".table-wrap" }] }
]
```

These are format examples, not routes to guess. Use URLs and locators observed in the browser. Never store activation/reset tokens in an inventory.

- `slug`: lower-case, hyphenated screen and state; pictures are `<slug>--<width>.png`.
- `ready`: an observed element that indicates the intended state has loaded.
- `steps`: this helper supports `click`, `scrollRight`, `press`, `wait`. It has no fill step. Clicks and key presses can still mutate data: this is not a read-only enforcement tool.
- Record role, environment, state prerequisites, viewport height and capture provenance in `screens.md`. Keep inventories for different authenticated roles separate when using the batch tool, which takes one session per run.

## Interactive journeys first

Use browser automation directly for filling forms, submitting, inviting, validating input and following emails. Capture before/after and relevant intermediate states as they happen. Save transient captures with their timing, then capture the settled result separately; a transition is not proof of persistent failure. Keep changes in place and record them; do not add a teardown step. Fresh test names let later agents recognise existing work instead of erasing it.

Reach empty, full, error or other-role states through supported interface actions and actual accounts. When a state cannot be reached within the agreed scope, document the gap and what access or conditions would enable it. Do not intercept responses, inject role/data state, inspect source, or alter the rendered page to fabricate evidence. Ordinary fictional test values entered through the app are permitted and should be identified as test data.

## Repeatable batch capture

```sh
NODE_PATH=<project>/node_modules node scripts/capture.cjs --screens screens.json --out shots/<run> --base https://test.example --state session.json
```

Use this for stable states after exploration. **It repeats every entry at every width in new pages and contexts.** Do not put sends, submissions, deletions or other write steps into a multi-width capture list; capture those live once, then revisit their resulting state. Authentication-state files contain secrets: keep them protected outside evidence inputs and prefer in-memory sessions when supported.

Record viewport width and height separately from screenshot pixels: full-page capture height and horizontal overflow are not viewport dimensions. For crops or reductions, record the original path, crop rectangle and final pixel size (see [evidence.md](evidence.md)).

Suggested widths are 320, 390, 820 and 1280; pass `--widths 320,390,820,1280`, since the script's default omits 320. At 320 CSS pixels, Web Content Accessibility Guidelines (WCAG) 2.2 criterion 1.4.10 Reflow requires content to reflow without loss of information or functionality and without scrolling in two directions, except parts that need a two-dimensional layout. `--heights 390:664` tests a short phone viewport. Viewport resizing alone is not touch-device testing: use an appropriate touch context for claims about touch/hover interaction.

`report.json` records page height, screenfuls, overflow and elements crossing the right edge. Direct captures should record equivalent measurements when a finding needs them. Measurements from rendered elements are allowed; hidden app state is not.

Use a fresh run folder each time. Inspect captures before passing them on: verify role, loaded state and intended content. An unexpected error or loading screen may itself be evidence, but is not proof the intended screen was reviewed. For a large app, divide by related areas and give consistency review access across them.

Keep full-page originals. Evidence crops and highlight previews are derived separately; [evidence.md](evidence.md) defines the coordinates and manifest. Never capture visible credentials or raw action links. If a sensitive value was captured, keep the original restricted and create an explicitly labelled redacted derivative that preserves the fault; never silently alter the evidence.

## Resolve uncertainty while the session is available

Prioritise uncertain claims that would change the finding's treatment: a disabled action, missing success feedback, an apparent navigation failure or a suspected contrast problem. Ask for a specific observation, not a complete second exploration. Confirm the loaded state, triggering action, elapsed observation and working recovery. Avoid repeating a send or submission merely to obtain a cleaner picture.

For contrast, inspect the visible element's computed text colour, font size/weight and opacity, plus the background actually behind it, including ancestor opacity, images and gradients. Use settled normal/focus/hover states where relevant. If the effective background or state is unknown, retain a visual concern with that limitation instead of publishing a precise failure ratio from antialiased screenshot pixels. Keyboard checks should identify the focused control; do not dump broad page text that may include hidden application data.
