---
name: frontend-audit
disable-model-invocation: true
description: Use only when the user explicitly invokes frontend-audit or asks to run this named skill. Guides a usability and visual-design review for the user, with highlighted screenshots, a local HTML report and Keep / Drop / Discuss feedback. Do not select automatically for front-end work, agent reviews, implementation verification or screenshot capture.
---

# UX and UI review

## Invocation and purpose

**Only the human user initiates this skill.** Use it when they invoke `$frontend-audit` in Codex, `/frontend-audit` in Claude Code, or explicitly name the skill and ask to run it. Do not load or start it on your own initiative because a task involves the front end, navigation, responsiveness, accessibility, browser testing or screenshots. A general request to review or verify a front-end change is not an invocation of this skill.

This skill guides the review presented to the user: how to explore, gather evidence, explain findings, deliver a visual report and work through their feedback. It is not a prerequisite for an agent to assess the interface, test a change or take screenshots; do those tasks within their own scope without activating this workflow.

Within an explicitly user-initiated review, the coordinator may delegate portions and instruct the assigned agents to load the relevant guidance. That delegation carries the user's invocation; it does not authorise workers to initiate another review. State that the user invoked this skill and identify the assigned portion in each brief.

Authorisation to implement findings does not automatically request another review or an updated HTML report. Keep the existing review available for the user; ordinary implementation verification and screenshot evidence continue under the build's requirements. Create or extend review pages for that follow-up only when the user requests them.

## Review outcome

Review the experience a person actually encounters: what they understand, where they go, whether they can complete their work, and what gets in their way. Discover journeys from the interface instead of asking the owner to script each task. Screenshots support the observations; a screenshot collection alone is not a complete review.

**The overall deliverable is a local HTML review**, with screenshot highlights, plain-language findings, coverage and limitations, a record of changes made while exploring, and Keep / Drop / Discuss feedback. A delegated reviewer may own only exploration, capture, a lens, or verification. Complete that assignment and return its evidence; do not restart the whole workflow, build a separate report, or dispatch more agents unless assigned to do so. The coordinator owns the combined report and discussion with the owner.

## Scope and access

- Use the agreed environment, roles, test accounts and protected-fixture boundaries. Obtain missing access through the project's documented setup; do not ask the owner to choose every click. Reuse decisions already made in the conversation.
- **Explore through the browser, without application source code.** Do not inspect routers, components, internal design documents, bundles, hidden application state or request payloads to learn where to go or why something happens. Rendered elements, accessible names, focus and layout measurements are available for operating and assessing the visible interface. Browser automation code and these evidence tools are allowed.
- The coordinator may read operational instructions to arrange access. Give independent explorers only the access instructions, their role, scope and data boundaries; withhold existing tickets, other reviewers' findings and explanations of intended navigation until their initial observations are recorded.
- **Exercise complete journeys.** In an authorised test environment, create, edit, save, submit, invite and send as the journey requires. Deletion is available when testing the deletion journey on an allowed test record. Do not stop at the form before the behaviour can be assessed. Existing authorisation covers routine actions within these boundaries; ask only when a necessary action is outside them or a material boundary is unknown.
- **Leave test changes in place by default.** Test data does not imply disposable-after-use. Do not delete, revert, reset or undo work as routine cleanup, and do not make cleanup a completion gate. Record what was created, changed, submitted, sent or deleted, and what remains. Clean up only when explicitly instructed. Continue to respect protected fixtures and other sessions' data.
- Honour an explicitly read-only review. Do not infer write permission for production or real people's records from this skill. If the environment or write scope is unknown, establish that boundary once, then proceed autonomously within it.
- When a journey sends email, use the project's approved test inbox and load `mailbox-agents` when available. Follow the delivered links; never substitute invented tokens. The coordinator handles any operational delivery checks separately from the code-blind experience review.
- Reach states with real accounts, data and supported interface actions. An inaccessible state is a coverage gap: no intercepted responses, injected roles, fabricated browser state or source inspection to manufacture coverage.
- Keep screenshots and reports local. Keep credentials, session data and action-link tokens out of screenshots, notes and reports. Do not modify the application during a review.

## How to organise the work

Adapt the size and sequence to the assignment. A small review can use one explorer; a larger review benefits from independent role explorers followed by focused lenses. There is no mandatory agent count. Respect available concurrency and isolate sessions and test records so workers do not overwrite one another. Assign one browser owner per shared profile; evidence-only work can run in parallel. The coordinator schedules linked journeys and maintains their shared action record. Use the platform's agent coordination, not messages to other terminals. See [roles.md](roles.md) for ownership and handoffs.

1. **Establish scope once.** Record environment, roles, widths (suggested: 320, 390, 820 and 1280, where 320 is the Web Content Accessibility Guidelines 2.2 Reflow probe), authorised actions and protected fixtures in the review folder. The coordinator keeps product decisions in `settled.md`; independent explorers receive operational boundaries only, then the merger applies prior decisions to avoid reopening settled proposals without new evidence.
2. **Explore naturally.** Role explorers follow the interface, choose plausible work, complete journeys and record expectations, hesitation, wrong turns, recovery and outcomes. Build the discovered screen/state inventory as they go. See [roles.md](roles.md).
3. **Capture and verify as you go.** Explorers capture transient and before/after states during their journeys. Check uncertain claims while the relevant session is available; record both supporting and contradictory observations. A capture assignment fills reachable gaps. The coordinator starts a draft report from these packages rather than waiting for every worker to finish. See [capture.md](capture.md) and the handoff contract in [evidence.md](evidence.md).
4. **Review through relevant lenses.** Navigation/tasks, fit, first-screen hierarchy, controls, consistency, wording, states and accessibility are useful divisions, not quotas. Read the relevant groups in the handbook's [pattern catalogue](../dev-standards-handbook/topics/frontend-patterns.md), treating patterns as prompts rather than automatic defects. See [roles.md](roles.md) and [evidence.md](evidence.md).
5. **Merge and challenge.** Consolidate duplicates without losing role/device differences. Separate reproduced defects, usability improvements and product-policy questions; state confidence, impact and recovery. For a full delegated review, use a fresh verifier to inspect highlights and challenge important claims. A limited or solo assignment performs relevant checks and discloses the lack of independent verification; it does not start recursive delegation. Freeze the retained evidence once corrections and limitations are recorded. See [findings.md](findings.md) and [roles.md](roles.md).
6. **Reconcile existing work when requested.** After independent discovery, compare findings with existing ticket descriptions and comments. Record exact matches, partial overlaps, new findings and apparently resolved issues with evidence. Reading and mapping tickets does not itself authorise changing their status or creating new work.
7. **Complete and deliver the local HTML.** Include highlighted evidence, coverage, changes left in place, uncertainties and any ticket mapping. Check the report at desktop and phone sizes, then verify only affected parts after corrections. Deliver a working clickable loopback web link, backed by a running local server, plus the file path; do not rely on a filesystem link the owner cannot open. Keep the server available for review. The completion gate and serving helper are in [findings.md](findings.md).
8. **Continue from the owner's feedback.** Preserve rulings and discussion. Offer prototypes where they help a decision and build them only when requested. Follow existing authorisation for tickets and fixes; see [after-rulings.md](after-rulings.md).

## Evidence rules

- Show the actual interface. Keep originals unchanged; record crop and highlight coordinates so the report can draw rings and dim the surroundings.
- Measure visible geometry from the rendered page or screenshot, never infer it from source or class names.
- A behavioural claim needs a recorded interaction and before/after evidence. A still alone cannot prove a tap did nothing; state exactly what was observed and for how long.
- Write in terms of the user's task and consequence. A technical cause is not required or established by this review.
- Use `shown`, `partly shown`, `not shown` or `contradicted` honestly. Failed reproduction and unvisited areas are useful results, not something to hide. Keep evidence status separate from confidence and whether a finding is a defect, improvement or policy question.
- Stable rendered states support conclusions; loading transitions and screenshot colour impressions need qualification. Measure contrast from rendered colours, size, opacity and effective backgrounds before asserting a measured failure. Keep unresolved interpretation separate from an alleged calculation or implementation error.

## Tools and output

Use the existing scripts where they fit; direct browser captures are appropriate for interactive journeys and transient states. Their schemas are described in the linked references.

| Script | Purpose |
|---|---|
| `scripts/capture.cjs` | Batch captures of repeatable screen states and visible geometry; not a general journey runner |
| `scripts/ring.py` | Preview highlight boxes on evidence crops |
| `scripts/build_review.py` | Build local HTML from findings and screenshot manifests |
| `scripts/check_review.cjs` | Check report images, highlight geometry, links, layout and ruling controls in an isolated browser |
| `scripts/serve_review.py` | Serve the report and explicitly selected assets on loopback; print a clickable local web link |
| `scripts/review-input.js` | Add feedback controls to later discussion or prototype pages |

A review folder normally contains `settled.md`, `screens.json`, `screens.md`, `notes/` (journeys, coverage and changes per agent), `shots/<run>/` (originals), `evidence/` (crops, manifests and statuses), `findings.json`, `review.html` and later `rulings.txt`. Keep it outside the product repository. Worker file names and finding-id ranges must be assigned to avoid collisions. Authentication files, if necessary, stay separately protected and never enter report inputs.
