# After the rulings

The coordinator owns follow-up; a capture or lens assignment ends with its evidence unless more work is assigned. Keep the local HTML review as the shared record of findings, decisions and any later prototypes. Reuse authorisation already given; do not ask again for agreed work.

Moving from the review into implementation does not automatically extend this reporting workflow. Verify the app and collect screenshot evidence under the build's requirements. Create or update owner-facing review pages only when the user requests them; the feedback and presentation rules below apply to those requested pages.

## Record

Save the owner's export as `rulings.txt` in the review folder, unchanged. For each line marked `discuss`, settle it with the owner one at a time, with the picture in front of them, and append the outcome. Add every `drop` to `settled.md` as "decided against", with the reason if one was given, so the next review does not raise it again.

## Settle the fixes, cluster by cluster

Do not walk the owner through kept findings one by one. Group them by the fix they share (twenty squeezed tables are one fix applied twenty times), then take one cluster at a time: what it is, links to two or three of its pictures, the one decision it needs, and a recommendation.

- **Where a cluster's fix is obvious**, the owner rules from the pictures.
- **Where a fix could be done more than one way**, offer a toggleable prototype: one local HTML file showing the screen with a switch between the variations, so the owner picks by looking, not by reading a description. Use the actual component or running app for an existing interface, in an isolated local prototype environment. Do not hand-build a replica. Prototype implementation is a separate assignment from the code-blind review and may need source access; keep its proposals distinct from evidence of the deployed app. Build it only when the owner has requested or authorised the prototype. Offer a prototype when seeing meaningful alternatives would help the owner decide; do not make one a routine gate for every cluster.
- **Every page takes the owner's answers.** A page the owner only reads and then has to answer in chat is tedious to use. Every page handed over after the rulings (cluster pages, before and after pages, prototypes, the index) carries inputs: on each item three tick buttons (Approve / Change / Drop), an "Option I pick" box wherever there is a prototype to choose from, and a note box for their thoughts; and a bar that copies everything answered, on this page or on every page at once, as one block of text to paste back. Copy `scripts/review-input.js` beside the pages and add `<script src="review-input.js"></script>` before each page's closing body tag. Use the supported markup below. It keeps answers in the browser per page and shares an item's answer with its single linked prototype, so the owner need not answer the same thing in two places. Keep it flexible: the note box is where most of the useful answers arrive. Record the pasted block unchanged, as with the first rulings.
- **Ring what changes.** On every cluster page and every before and after pair, outline the part being changed and dim the rest, exactly as on the findings page (see `evidence.md`). Ring the same region in the before and in the after.
- **Show the fix when the owner requests an updated review.** Use representative before/after screenshots on the requested local page. Authorisation to implement a fix does not itself request that page, and a review alone is not permission to edit the app. Use the verified loopback link from [findings.md](findings.md), keeping the same origin where feedback is already stored. Keep the file path as a fallback; do not rely on it as the only way to open the result.
- Every proposed fix states whether it touches the back end.

Clusters, not findings, become the pieces of work below.

### Feedback helper markup

On pages other than `index.html`, `review-input.js` detects targets in this order:

1. `section.group-head[id]` with an `h2`, and `section.item[id]` with an `h3` or `h2`.
2. If neither exists, sections containing `h2 > .id`, for example `<section><h2><span class="id">F012</span> Save action</h2>…</section>`. The `.id` element's text becomes the finding id; heading text alone is not enough.
3. If no sections match, `a.item[href]` links containing a `b` label receive answer controls beside the link.
4. If nothing matches, the page receives one floating prototype answer box.

Use same-folder prototype filenames such as `prototype-save.html` and link with `href="prototype-save.html"` (without `./`). A `section.item` gets the option field when it contains an `a[href^="prototype-"]`; exactly one distinct prototype filename binds its answer to that page's `pick` answer (fragments are stripped). Fallback `a.item` links also bind when their `href` starts with `prototype-`; omit fragments for those links. Keep prototype pages free of the earlier target markup to obtain the floating `pick` box. `index.html` is special: use `a.item[href]` links with `b` labels for page answer counts and the combined export, rather than per-item answer controls.

## Tickets

Use the agreed ticketing scope. If no ticket creation or update has been authorised, agree that scope before writing to the tracker. Reuse exact matches and extend partial matches as appropriate instead of duplicating existing tickets; one ticket per coherent piece of work is usually useful. Each ticket carries:

- the findings it closes, by id, each with its plain description and proposed fix;
- local evidence references for those findings. Keep screenshots local under this workflow; do not upload them to a tracker or other external service unless the owner explicitly changes that boundary;
- what "fixed" will look like: the same screen and width photographed again, compared with the picture in the ticket.

When a fix is implemented, re-take its evidence from the same screen list and equivalent test state. A before and after pair, same framing, is the proof the fault is gone.

**Check everything in the requested review handover.** Code inspection alone does not verify the rendered result. For a full delegated review or an explicitly requested follow-up review, the coordinator assigns a fresh verifier who did not build the result. Before handover, the verifier opens the real app at phone size and judges every changed screen within that assignment: does it read well, is anything cramped, cut, overlapping or inconsistent with its neighbours, does it match the prototype the owner picked. Include a narrower phone (such as 360px) and dark mode if the product supports it. Check requested review pages and prototypes too: every picture against its claim, every "after" against its described fix, and every prototype option against its description. For a limited or solo assignment where delegation is unavailable or out of scope, the builder or author performs the relevant checks and explicitly reports that independent verification was not performed. That self-check does not count as independent verification, and this instruction does not require recursive delegation or add a review/report gate to ordinary implementation. Follow the completion gate in [findings.md](findings.md): after a correction, check the changed surface and its directly affected behaviour, rather than restarting the entire review.

## Feed the patterns

Go through the kept findings and ask of each: is this one instance of something that will happen again on another screen or another project? If so, propose it for the relevant lens group in the handbook's [front-end pattern catalogue](../dev-standards-handbook/topics/frontend-patterns.md). Edit that handbook file, not the compatibility stubs in the legacy `frontend-patterns` skill:

- a new pattern, written without any client name, screen name or picture;
- or one more "also seen as" line on an existing pattern;
- or a correction, where a pattern's advice turned out wrong or the owner ruled against it.

Show the owner the proposed additions as a short list and add only what they approve. Findings the owner dropped are evidence too: if a pattern keeps producing findings that get dropped, propose softening or removing it.
