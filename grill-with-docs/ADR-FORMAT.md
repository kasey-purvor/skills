# ADR Format

ADRs live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.

Setup creates the `docs/adr/` directory. If it is missing, tell the human; do not create it.

## Template

```md
# {Short title of the decision}

{The ruling: what was decided, in one to three sentences.}

**Why:** {the reason.}

**Turned down:** {the options rejected, and why each was.}
```

That's it: the ruling, the reason, and the options turned down. An ADR can be three short paragraphs.

- **The ruling sits at the top.** When the decision changes, rewrite the top in the same edit. Never add an amendment underneath.
- **Nothing about the code.** No description of how it was built, no measurements, no story of a ticket. A test for any sentence: would it still be true if the code were rewritten another way?
- **A ruling lives in one place.** Do not repeat it in another ADR or in `docs/decisions.md`.

The one optional part is a **Status** line (`superseded by ADR-NNNN`), for an ADR that another has replaced.

## Numbering

Scan `docs/adr/` for the highest existing number and increment by one.

## When to offer an ADR

All three of these must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it — you'll just reverse it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library — just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite. These stop the next engineer from "fixing" something that was deliberate.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If you considered GraphQL and picked REST for subtle reasons, record it — otherwise someone will suggest GraphQL again in six months.
