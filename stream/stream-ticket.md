# The stream ticket

A stream's permanent record is one Linear ticket.

- **Where:** in the team, with no project, because a stream may cross epics.
- **Label:** `stream`.
- **Title:** `Stream: <the outcome in a few words>`.
- **Sub-issues:** the stream's tickets. Each keeps its own project, labels and status.
- **Created** when the human agrees the plan, not when a session starts.
- **Status:** Backlog while planned, In Progress while a session is running it, Done when closed.

A stream planned well ahead holds only its Goal and Tickets. Write Touches when it starts, because code described weeks ahead will have changed.

## Description

The description is the plan. The running log goes in comments.

```markdown
**Session:** vantage-a4 (pane %6)

## Goal
One or two sentences: what this stream finishes.

## Tickets and order
1. Lane A (one branch, one pull request): VAN-160, then VAN-161
2. Lane B: VAN-163

## Touches
🟢 apps
   🟢 apps/web/src/search
   🔴 apps (rest)
🟢 packages
   🟢 packages/search-index
   🔴 packages (rest)
🔴 docs
🔴 infrastructure
🔴 scripts

## Findings
Filled in at close.
```

- **Session:** the session running the stream, or `none` when no session is.
- **Tickets and order:** the lanes and the build order inside each.
- **Touches:** the repo's directory tree as text. Every top-level folder gets a line, 🟢 if the stream changes anything in it and 🔴 if not. Go deeper where the stream is working. A reader should see what is safe as well as what is taken.
- **Findings:** written at close, distilled from the comments: review findings that came up more than once, and what was dropped and why. A later agent reads this instead of every review.

## Close checklist

Run this when the stream's work is finished or the human ends it.

1. **Settle leftovers with the human.** List the tickets and review findings that aren't finished, with a suggestion for each. They decide.
2. **Write the Findings section** on the stream ticket.
3. **Run the session wrap-up.** Run the `session-wrap-up` skill for the stream. It proposes the decision and trap lines, the human says yes or no per line, and the lines land where `session-wrap-up` says.
4. **Post a status update on each project the stream touched:** what it shipped there, anything a later agent should know beyond the lines step 3 added, and the stream ticket's id.
5. **Mark the stream ticket Done.** Leave it, and its tickets, on the pane: pins come off only when the human asks.
