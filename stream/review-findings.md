# Review findings

These apply to any code review, in a stream or on a lone ticket.

## What happens to a finding

1. **Fixed.** In the same pull request, or in a sweep before the stream closes. A finding outside the diff but inside the stream's area is still the stream's to fix. A real defect in code the pull request introduces is normally fixed before it merges. Each round of fixes goes to a fresh builder, and the same reviewer checks the fix.
2. **Dropped by you.** A non-security finding that is trivial, or that proves wrong when checked against the code, can be dropped without asking. Record one line saying what it was and why.
3. **Settled by the human.** For anything else left unfixed, suggest a ticket, a tally line or dropping it, with your reason. They decide.

Raise a security finding with the human as soon as it is found, and don't drop one yourself.

- **A ticket** is for work the human would plausibly schedule on its own merit. It gets the `review` label and goes in the epic it fits, or in the team with no project if none fits.
- **A tally line** is for everything else worth remembering. It goes in the team document's Recurring findings section: a new line, or a bumped count. When something has come up three or four times, suggest that it become a ticket.

The full review is posted as a comment on the ticket it reviewed.

## The report

A reviewer subagent gives the orchestrator one ranked list: for each finding, what it is in plain words, why it matters, and the outcome it suggests.

The human gets this format, so they don't have to ask for the explanation or your judgement. Put what needs them first.

```markdown
## Review findings: VAN-160 (pull request #101)

### Needs your call (2)
1. **The search endpoint has no rate limit.**
   - What it is: anyone signed in can call it as fast as they like.
   - Why it matters: one script could slow search for everyone.
   - I suggest: a ticket in the Search epic. It needs a decision on the limit and touches the gateway, which this stream does not.
2. **Three tests repeat the same setup.**
   - What it is: the same fixture is copied into three test files.
   - Why it matters: only tidiness; a change to it has to be made three times.
   - I suggest: a tally line. This is the second time it has come up.

### Fixed (3)
- Missing null check on the officer name: fixed in this pull request.
- ...

### Dropped (1)
- Rename `tmp` to `buffer` in the parser: dropped, a style preference with no effect on behaviour.
```
