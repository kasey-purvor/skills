# Front-end Patterns

Interface faults observed in real front-end reviews, grouped by review lens. Each entry
names what goes wrong, a proportionate alternative, and a **Check** a reviewer can perform
through the running interface. The engineering guidance behind them (state, data loading,
forms, accessibility) is in [Front-end Development](./frontend-development.md).

**How to use:** a browser-only reviewer, such as a lens in an `audit-frontend` review or a
`verify-frontend-change` run, reads only the groups relevant to its assignment and checks them through
visible behaviour. A builder scans the group for the screen being changed. What a reviewer
may inspect, change or publish comes from the workflow and brief that assigned the work,
not from this file.

**These are leads, not verdicts.** A pattern guides attention; a finding needs an observed
consequence. Established product decisions and the user's assignment take precedence over
an entry's **Instead**. Numerical targets are review heuristics unless the entry names the
standard behind them.

**Probe sizes:** widths of 320, 390, 820 and 1280 Cascading Style Sheets (CSS) pixels,
and a short viewport about 660 pixels tall. 320 is the width in Web Content Accessibility
Guidelines (WCAG) 2.2 criterion 1.4.10 Reflow (level AA): content there must reflow
without loss of information or functionality and without scrolling in two directions,
except parts that need a two-dimensional layout, such as a data table or a map. Adapt
the other sizes to the supported devices, and also test between breakpoints.

**Groups:** [Fit](#fit) · [First Screen](#first-screen) · [Controls](#controls) ·
[Tasks](#tasks) · [Consistency](#consistency) · [Wording](#wording) · [States](#states) ·
[Accessibility](#accessibility)

---

## Fit

### Wide Tables On A Narrow Screen

A table with more columns than the screen has room for. A sideways swipe separates each row's name from its figures and its action.
**Instead:** pick one of four treatments by what the rows are for, and use the same one for the same kind of table everywhere:

- **Cards** where each row is a thing you open or act on. One card per row, every field in view, every row control on the card.
- **A collapsing name column** where you read down columns to compare figures. The name shows in full at rest; swiped, it shrinks to a short form that stays pinned.
- **Fold to fit** where the table is only a little too wide: a second figure moves under the first, or a row takes two lines.
- **A switch between two views** where neither wins; remember the choice.

**Check:** at 390 and 820, at rest and swiped to the far end: can you always see which row a figure or a button belongs to?

### The Fixed Minimum

A table or panel given a minimum width larger than the smallest box it will ever sit in (a 1,100px table in a card that is 740px on a tablet). The designer's screen was wide enough; nobody else's is.
**Instead:** let it fit by folding or wrapping, or scope the minimum to the widths where it holds.
**Check:** compare content with its container at supported widths; during implementation, also inspect fixed and minimum width rules.

### The Tab Row That Cannot Wrap

Tabs in one row with no wrapping. It fits the three tabs it was built with; a role or a feature adds five more and the row runs off the screen, sometimes cut exactly between two tabs so nothing hints that more exist.
**Instead:** choose a discoverable narrow layout, such as a scrollable tab strip or another navigation control, preserving the selected state and appropriate keyboard behaviour. Check wrapping carefully rather than assuming it preserves tab navigation.
**Check:** view the supported role/feature combination with the most tabs.

### The Bar That Cannot Shrink

A top bar whose items all refuse to shrink or truncate. One longer value (a name, an email address, a tenant) pushes the bar wider than the screen, the whole page scrolls sideways, and the items at the far end are gone.
**Instead:** give variable text a maximum width and let it truncate; let the group holding it shrink.
**Check:** put the longest real value in every variable slot at once.

### The Silent Clip

A box that hides whatever overflows it, so a whole column is simply absent and nothing shows that it exists.
**Instead:** make the content fit; if it cannot, let it scroll and show that it scrolls.
**Check:** measure the content's width against the box's, not just whether the page scrolls.

### The Oversized Popover

A dropdown list, picker or popover with a fixed width wider than a phone.
**Instead:** cap it to the screen (or to its trigger) and let long entries wrap.
**Check:** open every dropdown at 390.

### The Value That Cannot Break

A long unbroken value (an email address, a code, a URL, a monospace payload) in a narrow box, pushing everything beside it off the edge.
**Instead:** allow it to break, or put the label above the value.
**Check:** use a real long value, not "test@x.com".

### The Split Figure

A signed or prefixed figure ("+£27.4k", "-12%") that wraps after the sign, making rows taller and the figure harder to read.
**Instead:** keep a figure and its sign or unit on one line.
**Check:** look at the widest figures in the narrowest column.

### The Side List That Eats The Page

A permanent side list of sections that takes a third of a tablet's width, so every table beside it needs a swipe it would not need with the full width.
**Instead:** below desktop width, fold the list into a button that opens it.
**Check:** at 820, measure what is left for the page.

---

## First Screen

### Controls Before Content

The first phone screen is title, subtitle, chips, search, and four rows of filters; the first real row starts on the second screen.
**Instead:** search on one row, filters two or three per row or behind one button showing how many are in use, secondary actions (export, show archived) out of the way. Ask the owner which: some prefer every filter in view.
**Check:** at 390, how many pixels down is the first row of content?

### One Tile Per Row

Summary figures that sit four across on desktop and stack one per full-width row on a phone, so eleven figures take two screens.
**Instead:** two or three small tiles per row at phone width, label above a slightly smaller figure.
**Check:** count the screens of tiles before anything else.

### The Endless List

A list shown in full that buries everything below it: 200 rows above the section the user came for.
**Instead:** the first few, then "Show all n" that opens in place; or paging; or search.
**Check:** with real volumes, how far down is the next section?

### The Tall Card

A card per item that is so tall under three fit on a screen: labels on their own lines, repeated notes, nested padding.
**Instead:** name and the one or two figures that matter on the first line, the rest small beneath; repeat nothing that is the same on every card.
**Check:** how many items fit on one phone screen?

### Admin Above The Work

Rarely used controls (archive, classify, layout settings) placed above the content people came for, so they are scrolled past on every visit.
**Instead:** put them in a "more" menu or at the foot of the page.
**Check:** list what sits above the main content and which of it the screen's main task needs; how often each is used is the owner's to confirm, not the reviewer's to assume.

### The Dead Desktop Control

A control that only works on desktop (drag-to-rearrange lock, column chooser) still shown on a phone, taking a place on the first screen and doing nothing.
**Instead:** hide it where it has no effect, keyed to the capability it needs (a `(hover: none)` or `(pointer: coarse)` media query) or to whether it works in the current layout, not to screen width alone.
**Check:** tap every control on the first screen at 390 on a touch device.

### Boxes In Boxes

A card inside a card inside a padded page, each with its own heading repeating the last. On a phone the content is left 250px.
**Instead:** one level of card on a phone; drop the repeated heading.
**Check:** measure the content's width against the screen's.

### The Empty State That Takes A Full Slot

Every empty group drawn at full height saying "nothing here", pushing the groups that have content off the screen.
**Instead:** collapse an empty group to its heading line.
**Check:** view with mostly empty data.

---

## Controls

### The Hover-Only Control

A button or icon that appears only when the pointer is over its row. For a touch-only user there is no hover, so the control does not exist.
**Instead:** make it discoverable for touch and keyboard users at every width, for example through a visible "more" menu or a persistent action. Screen width alone does not determine input method.
**Check:** operate the screen by touch and keyboard; for implementation work, also inspect hover-only styles.

### The Action At The Far End

A row's action (Save, Edit, End, Request change) in the last column of a table that needs a swipe. Swiping to the action slides the row's name away, so you act on a row you can no longer identify.
**Instead:** keep the name pinned, or move the action beside the name, or make the row a card.
**Check:** swipe to the action: is the row's name still on screen?

### The Unmarked Unsaved Change

A save button that appears only after a change, somewhere out of view, with nothing else marking the row as changed. Leaving the page drops the change silently.
**Instead:** mark the changed row where the user is looking, with a labelled Save there; warn before leaving.
**Check:** change a value and look only at the part of the screen you were already on.

### A Button On A Button

A small button (a status dot, a flag) sitting on a card or row that is itself one big button. A near miss triggers the big one, which may navigate away.
**Instead:** make the primary link and secondary controls separate interactive elements in a non-interactive container. Provide distinct, comfortably sized targets; do not nest a button inside a button or link.
**Check:** tap just beside the small control.

### The Tiny Target

A 16px close icon, 24px text links, 20px arrows stacked 2px apart.
**Instead:** aim for a 44px touch area where practical; padding can enlarge the target without enlarging the icon. 44px is WCAG 2.2 criterion 2.5.5 Target Size (Enhanced), level AAA, so missing it is not by itself a conformance failure. The level AA criterion, 2.5.8 Target Size (Minimum), asks for 24 by 24 CSS pixels, with exceptions that include enough spacing around a smaller target; check the [target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) before reporting a failure.
**Check:** measure the tappable box, not the icon.

### The Menu That Cannot Reach Its End

A menu, sheet or dialog with no height limit and no scrolling of its own, drawn under a fixed bar. It fits a full-height phone screen; with the browser's address and tool bars showing, its last entries are covered and cannot be reached. Sizing it with `100vh` is the usual cause: on a phone that unit is the height with the browser's bars hidden.
**Instead:** limit it to the visible height between the fixed bars, sized with `svh` (or `dvh` when it must track the bars, at the cost of resizing while the user scrolls) rather than `100vh`, and let it scroll inside.
**Check:** with the browser's bars showing, open it on a screen about 660px tall with the longest list of entries any role gets.

### The Save Below The Fold

A form or reorder list whose Save is a screen and a half below where the work happens.
**Instead:** once something has changed, pin the Save in view.
**Check:** make a change at the top of the form: can you see how to save it?

### Drag That Fights Scroll

A drag handle on touch that starts a drag when the user meant to scroll.
**Instead:** start the drag only after press and hold, and offer move up and move down buttons; WCAG 2.2 criterion 2.5.7 Dragging Movements (level AA) requires a single-pointer alternative that does not drag.
**Check:** swipe quickly across the handle.

### The Button That Only Renames Itself

A "Show all" that changes its own label and nothing else; a "More options" with no handler.
**Instead:** make it do what it says or remove it.
**Check:** tap every button and compare before and after.

---

## Tasks

### The Card That Opens Something Else

A card labelled or announced as opening one thing (an order) that lands on another (the customer's overview), leaving the user to scroll and tap again to find what they came for.
**Instead:** land on the thing itself; if it has no page, land on the tab and position that shows it, and name the card for what it really opens.
**Check:** tap it: how many more taps and screens of scrolling until the thing is in view?

### The Panel That Opens Off Screen

Tapping a row opens its detail panel somewhere else on the page, far below, and nothing scrolls or moves focus there. The tap looks dead.
**Instead:** make the opened content apparent near the trigger, or use appropriate scroll and focus handling for the interaction. Do not steal focus from a simple disclosure unnecessarily.
**Check:** after the tap, has anything on screen changed?

### The Link That Ignores Its Parameter

A button that opens another screen "for this item", passing the item in the address, where the destination never reads it and shows everything.
**Instead:** make the destination filter on it, or remove the link.
**Check:** follow the link and compare with the destination opened plainly.

### Arriving At The Top

A deep link to a tab or section that selects the tab but leaves the user at the top of a long page, screens above it.
**Instead:** scroll the target into view on arrival.
**Check:** open the link on a phone.

### The Way Out That Scrolls Away

The only way to change section or go back sits at the top of a page that is thirty screens long.
**Instead:** keep it pinned, or repeat it at the end.
**Check:** scroll to the bottom of the longest page: how do you leave?

### Two Controls For One Thing

Two elements side by side that show the same state and do the same job (a status pill and a button both naming the current mode). Twice the width, and the user must work out which to use.
**Instead:** one control that shows the state and changes it.
**Check:** list what each element in a bar tells the user; remove duplicates.

### The One Way To Do It Is The Smallest

The only route to a common action below desktop width is a control built as an afterthought (a native select 26px tall replacing drag and drop).
**Instead:** design the touch route as the main route for that width.
**Check:** do the screen's main job by touch only.

---

## Consistency

### Sibling Patterns Built Apart

Several lists turned into cards in the same week, each built on its own: one shows an arrow on cards that open, one does not; a code is inline here, on its own line there, in a typewriter font somewhere else; buttons sit in different places.
**Instead:** decide the pattern once (what marks a card as openable, where the code goes, where buttons go) and build every instance from it, ideally from one shared component.
**Check:** put one card from each list side by side at the same width.

### Margins That Jump

Pages or tabs with different side margins, so the content's edge moves as you navigate, and some pages lose 30px of an already narrow screen.
**Instead:** one gutter per width for the whole product, applied by the page shell, not by each page.
**Check:** measure the left edge of the content on every page at 390.

### The Fix Applied To One Sibling

A fix made on the tab that was reported, while the tab beside it, built the same way, keeps the fault.
**Instead:** when fixing a pattern, find every instance first.
**Check:** compare equivalent visible screens; during implementation, also find the shared component and its other callers.

### Repeated On Every Row

The same note or line printed on every card or row ("refreshed at 09:00", "applies to activity only"), costing a line each time and saying nothing new.
**Instead:** say it once above the list.
**Check:** read three rows in a row: what repeats word for word?

### One Size Left Behind

Phone and desktop each have a designed layout; the tablet gets the desktop table squeezed, and ends up showing less than the phone does.
**Instead:** decide deliberately which layout each width gets; a tablet can take the phone's.
**Check:** compare how much of the content is visible at 390, 820 and 1280.

---

## Wording

### Raw Values On Screen

A date shown as `2026-10-11`, an internal code where a name should be, a customer shown only by its account code, "(-25d ago)" for a date in the future.
**Instead:** format values for the audience and task; an unambiguous year-month-day date may be appropriate. Handle future, missing, and zero values intentionally; do not expose unexplained internal codes.
**Check:** look for anything that reads like a database column.

### The Count That Disagrees

"Showing top 20 of 30" above a list of 30. A total that does not match the rows. A badge count that never changes.
**Instead:** derive the words from the same data that draws the list.
**Check:** count the rows and compare with every number on the screen.

### Desktop Words On Touch

"Drag and drop a file, or click to browse" on a phone. "Hover for details." "Click any name."
**Instead:** prefer input-neutral wording such as "Choose a file"; provide a usable alternative when instructions mention dragging or hovering.
**Check:** search the screen's text for click, hover, drag.

### Two Names For One Thing

The menu says one name, the page heading another. A status appears as "Pending" in one row and "pending" in the next.
**Instead:** one name per thing, defined once and reused.
**Check:** read the menu entry, the page title and the heading together.

### The Heading Said Twice

The section's name on the menu button, again as the page heading 80px below, again as the card title.
**Instead:** remove unhelpful visible repetition while preserving the page heading and labels that provide meaningful navigation or accessibility context.
**Check:** read the first screen aloud.

### The Cut-Off Identifier

A code or a name truncated so that several rows read the same ("Office…", "Office…").
**Instead:** wrap it, or shorten it in a way that keeps rows distinct; never truncate the one thing that identifies the row.
**Check:** can you tell every row apart at 390?

### Label Running Into Its Neighbour

A key, a total and a legend on one line with no room, so "Missing" touches "Total opportunity".
**Instead:** give each its own line at narrow widths.
**Check:** look at every legend and footer line at 390.

---

## States

Most faults that reach users sit in a state the builder never saw: another tenant's feature, another role, real volumes, a short screen (see [The Menu That Cannot Reach Its End](#the-menu-that-cannot-reach-its-end)). A state you cannot reach is a coverage gap to record.

### Built With The Feature Off

A card laid out and checked where a feature is off. Switched on, the feature adds a badge to a line that was already full, and the text beside it wraps to twice the height.
**Instead:** check supported feature combinations, including combinations that add controls or change layout; do not assume that all features can be enabled together.
**Check:** view the supported combinations available to the task; record combinations you could not reach.

### The Extra Control For A Role

A filter row that fits for an ordinary user. A manager gets one more dropdown, and the search box is left 94px wide.
**Instead:** design the row for the role with the most controls; let it wrap.
**Check:** view as the role that sees the most.

### The Real Long Value

A layout that fits "Jane Smith" and breaks when the system shows an email address as the name.
**Instead:** find the longest real value the field holds and design for it.
**Check:** use realistic long examples from permitted test data; do not access unrelated customer records to find them.

### Real Volumes

A settings list that is comfortable with 5 people and is 37 screens with 229.
**Instead:** search, paging, or grouping once a list can pass a screen or two.
**Check:** view it in the largest test tenant you are permitted to use, and record the row count you tested; a larger volume you could not reach is a coverage gap.

### The Silent Row Limit

A count or total computed in the browser from a query that returns at most a default number of rows (often 1,000). The number is wrong, or blank, for any real data set, and nothing reports it.
**Instead:** use server aggregates for totals over the whole dataset; label intentionally page-local totals and ensure they use the displayed rows.
**Check:** compare each total and count with the rows you can page or scroll through; a total stuck at a round number (100, 500, 1,000) is a lead.

### The Failed Request

A panel whose data request times out for real users every time, showing a spinner or an empty box. Reviews skip it because it "has no data".
**Instead:** a failure state that says what happened; and report the slow request as a fault of its own.
**Check:** exercise an authorised failure fixture in implementation testing; in browser-only reviews record observed failures and any untested recovery state.

### Empty, One, Many

A screen checked only with a comfortable amount of data.
**Instead:** look at it empty, with one row, and full.
**Check:** all three, at 390.

---

## Accessibility

This accessibility catalogue group is a thin start. Only what reviews have actually found is here; extend it as accessibility reviews are run.

### The Spoken Name That Lies

A control announced as "Open order 1234" that opens the customer's page. A screen-reader user is told one thing and taken to another.
**Instead:** the spoken name describes what the control does; change it when the behaviour changes.
**Check:** read each control's accessible name beside where it leads.

### The Nameless Icon Button

A button that is only an icon, with no spoken name, or whose visible label is folded away at narrow widths leaving nothing.
**Instead:** every control has a name at every width.
**Check:** list buttons with no text and no label, at each width.

### Focus Left Behind

Opening a panel, sheet or menu without moving focus to it; closing it without returning focus to what opened it.
**Instead:** apply the focus behaviour of the actual widget. Manage entry and return for dialogs; keep ordinary disclosure triggers focused and expose their expanded state. Return to a logical next control if the original trigger no longer exists.
**Check:** open and close everything with the keyboard only.

### The Dialog Without A Meaningful Name

A dialog has no accessible name, or its name and description do not explain the task. A library warning alone is not proof of an accessibility defect.
**Instead:** provide a meaningful accessible name. A description is not mandatory: add one when a short message explains the task, and omit it for complex structured content, which is worse announced as one flattened description. Follow the [dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
**Check:** verify the dialog name, reading order, focus, and keyboard exit; report the user-facing problem rather than only a console warning.
