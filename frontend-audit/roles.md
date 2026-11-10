# Assignments and delegation

These assignments belong to an explicitly user-initiated `frontend-audit` workflow. The coordinator's brief identifies the user's invocation and the worker's portion. A routine request to test a front-end change or capture screenshots does not activate this skill.

The coordinator selects assignments that fit the application and available concurrency. Agents work only their assigned portion; loading this skill does not make every agent a coordinator. They do not dispatch more agents unless explicitly assigned to do so.

## Brief every worker

Include the review folder, assignment, role/account access, environment, allowed actions, protected fixtures, output paths and finding-id range. State explicitly:

> Review through the visible interface; do not read application source or internal product documents. Complete the assigned portion only. Choose plausible tasks within your role and scope; exercise the write actions authorised in this brief without asking for each click. Leave test changes in place; do not clean up unless instructed. Record all actions that change data and what remains. Do not alter the app or other workers' sessions or records. Keep evidence local and exclude credentials and action-link tokens.

Each browser worker uses an isolated session and distinguishable test-record names. Isolation is a capability to verify, not an assumption: separate pages may still share a profile. Where workers use shared records or a shared browser profile, the coordinator assigns one owner at a time. Other reviewers work on saved evidence meanwhile. Do not forward the coordinator's full transcript or old tickets to independent explorers. Operational setup can be supplied without explanations of the intended interface.

## Ownership and handoffs

| Assignment | Owns | Returns |
|---|---|---|
| Coordinator | Scope, access, browser schedule, combined report, tracker bookkeeping and delivery | One review with coverage, action log and owner feedback |
| Explorer / capture worker | Assigned session, journey notes, originals and evidence files | The evidence package in [evidence.md](evidence.md), including gaps and retained changes |
| Lens reviewer | Assigned assessment of shared evidence | Supported findings, uncertain leads and contradictory evidence; no separate HTML |
| Merger / reconciliation worker | Assigned consolidated findings or ticket mapping | Traceable duplicates/splits/rejections or exact/partial/new mappings |
| Verifier | Independent claim, image and rendered-report checks | Corrections with file/finding anchors, limits and pass/fail results |

Choose model and effort from the user's current instructions and platform capabilities; the skill does not override those preferences. Give each assignment explicit file ownership. Workers do not edit another worker's files or manage other sessions' terminals.

For browser handoff, report the owned profile/context, role, current visible state, outstanding operations and whether the session is retained or released. Keep credentials and session files private; provide only protected-path pointers when needed. Do not release a shared browser until its owner has finished. Repeated startup failures or approval requests require diagnosing the affected operation, not repeated retries or a new interactive terminal workaround.

Linked journeys, such as invitation → email → respondent completion → administrator status, share safe record identifiers and a coordinator-owned action record. Assign the next actor explicitly and watermark/read the actual delivered message as the mailbox skill requires. Report uncertain send outcomes before anyone tries again. Handoffs transfer state and evidence, not a suggested verdict on the interface.

## Role explorer

Approach the app as a person in the assigned role. Use visible navigation and wording to decide what to do. Pursue plausible tasks to completion, try related paths, and recover from mistakes. Do not require a user-provided script or report every click for approval. Do not use the agent's ability to guess routes or inspect hidden state to compensate for an unclear interface. A bookmarked entry URL supplied for login is fine; guessing undiscovered routes is not evidence of navigability.

Record:

- The goal chosen, what you expected to happen, how you found it, confusing choices or wrong turns, and the actual outcome.
- Screens and states visited, role and viewport, entry paths and reproducible interaction steps; capture before/after, validation, success and failure states when encountered.
- Candidate findings with user impact, screenshot evidence and highlight coordinates where possible. State when highlights or additional capture still need doing.
- Every record created or changed, submission, message sent or deletion tested: identifying name or safe identifier, outcome, and what remains at the end. Do not record secrets or raw mail links. Report uncertain outcomes rather than repeating sends blindly.
- Unvisited areas and unreachable states, with the reason.

Write assigned journey, coverage and changes notes under `notes/`, discovered screens in the assigned inventory file, and candidate findings/manifests using [evidence.md](evidence.md). Do not build HTML unless that is your assignment. Capture-only workers need no invented findings: record observations and screen provenance for later reviewers.

## Capture and coverage

Merge discovered inventories after explorers have recorded their initial observations. Fill gaps in widths and reachable states, preserving the role and test-data context. Prioritise missing parts of real journeys over an arbitrary screenshot count. Capture the actual application, verify each image is the intended state, and record remaining gaps. See [capture.md](capture.md).

## Focused lenses

Read only the relevant group in the handbook's [pattern catalogue](../dev-standards-handbook/topics/frontend-patterns.md), plus [evidence.md](evidence.md). Work from shared screenshots and, when behaviour or missing evidence requires it, the live browser within the same access rules. No lens has source-code access. Patterns guide attention; a finding needs an observed consequence.

| Lens | Questions and evidence |
|---|---|
| Navigation and tasks | Can people discover and complete their work? Do labels lead where expected, do back/forward and return paths make sense, and can they recover without guessing? Record the journey, not just the destination. |
| Fit and responsiveness | Is content or an action clipped, overlapping, unreadable or awkward to reach at the tested widths? Measure overflow and distinguish intentional scrolling from an obstacle. |
| First-screen hierarchy | Can people understand where they are and what matters? How much scrolling separates them from the relevant content or action? |
| Controls | Are actions discoverable, reachable and operable by the tested input method? Check target size/spacing, hover dependence, nested interactive controls and menu/sheet reach. Treat 44px as a touch-comfort heuristic, not a universal compliance threshold. |
| Consistency | Does the same concept or interaction behave differently across screens without a useful reason? Show both examples at comparable widths. |
| Wording | Do labels, instructions, dates, counts and messages help the person understand and act? Avoid declaring a date format or the word “click” a defect without context. |
| States and recovery | What happens with empty/full lists, loading, invalid input, failure, success, long content and different roles? Exercise reachable states through the app; document unavailable ones. |
| Accessibility | Check keyboard operation, focus order and visibility, control names, contrast and the semantics exposed to assistive technology. Distinguish measured failures from usability heuristics; say what was and was not tested. |

Send observations outside your lens as leads for the merger. Do not omit a significant issue merely because no separate lens was assigned. A screenshot-only assignment must report behavioural questions as unverified leads.

## Merger

Read worker findings, evidence, journey/coverage notes, changes logs and settled decisions. Consolidate duplicate observations without losing affected roles, states or devices. Separate cases when the owner needs to rule on them independently; one shared problem may retain several screenshots. Rank by task impact, observed frequency and reach; avoid unsupported claims about how often users visit a screen. Write `findings.json`, preserving evidence status and grouping potential fixes. Classify each retained finding as a reproduced defect, usability improvement or product-policy question, with confidence, impact and recovery. Follow up material evidence gaps or clearly mark the limitation; do not treat every open question as a reason to extend the review.

The coordinator or a separately assigned reconciliation worker then reads existing ticket descriptions and comments and maps them to these findings. Keep existing-ticket expectations out of initial discovery. Do not close a ticket solely because the review did not reproduce it. Distinguish evidence already covered by a ticket from a proposed extension, and a successful tested sub-item from resolution of the whole ticket.

## Fresh verifier

The coordinator assigns an independent verifier for a full delegated review. For a limited or solo assignment where delegation is unavailable or out of scope, perform the relevant checks yourself and disclose that independent verification was not performed. Do not dispatch another agent just to satisfy this section unless delegation is assigned.

Inspect each finding and all its screenshot highlights, using `ring.py` previews. Check that images show the stated fault and that coordinates use the final image pixels. Reproduce important behavioural claims where feasible; any additional test changes go in your own changes log and remain in place. Challenge severity, assumptions and supposed duplicates. Correct or downgrade unsupported claims and retain the reason.

The coordinator builds draft HTML as evidence arrives. The verifier checks the consolidated report's claims, screenshots, highlights and feedback controls in a browser; the coordinator inspects a representative sample. Once the retained evidence and limitations are settled, freeze that set and finish reconciliation and delivery. After corrections, check only the changed findings, pictures or report behaviour and any directly affected controls. Reopen broad review only for a material contradiction or invalidated evidence, not to invent another final sweep. The completion gate is in [findings.md](findings.md).
