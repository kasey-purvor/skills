# Record Decision (ADR) — Playbook

Loaded only when the **Record Decision** action fires (see `lead.md` Actions). When a decision arises that meets the three-question filter, capture it as an ADR in `.context/decisions/`.

ADRs are an industry-standard pattern (Architecture Decision Records, originated by Michael Nygard, 2011). The format and discipline below are deliberately strict: every rule prevents a known failure mode.

---

## The three-question filter

Write an ADR only when **all three** are true:

1. **Hard to reverse** — cost of changing your mind later is meaningful (quarter+ to swap, not a few-line code change)
2. **Surprising without context** — a future reader looking at the code would wonder "why on earth did we do it this way?"
3. **Result of a real trade-off** — genuine alternatives existed and were rejected for specific reasons

If any of the three is missing, **stop**. Note the choice inline in the relevant context file (architecture.md component description, design.md behaviour, vocabulary.md if it's a naming choice) without ceremony. Skipping the filter recreates the dumping-ground problem in a new shape.

### What qualifies

- **Architectural shape** — "write model is event-sourced", "monorepo over polyrepo"
- **Integration patterns between subsystems** — "communicate via domain events, not synchronous HTTP"
- **Technology choices that carry lock-in** — database, message bus, auth provider, deployment target. Not every library — only those that would take a quarter+ to swap
- **Boundary and scope decisions** — "Customer data owned by Customer subsystem; others reference by ID only". Explicit no-s are as valuable as yes-s
- **Deliberate deviations from the obvious path** — "manual SQL instead of an ORM because X". Stops the next engineer from "fixing" something that was deliberate
- **Constraints not visible in the code** — compliance ("can't use AWS"), partner SLAs, performance contracts ("under 200ms because partner API")
- **Rejected alternatives when the rejection is non-obvious** — "considered GraphQL, picked REST because Y". Stops the alternative from being suggested again in six months

### What doesn't qualify

- Library choices that are easily swapped ("Pydantic v2 instead of v1") — note in `architecture.md` if relevant, no ADR
- Coding patterns within a module — these live in code, not in ADRs
- Configuration values (timeouts, retries, log levels) — schema in `data.md`
- Naming or formatting conventions enforced by linter — let the linter be the record
- "We did some thinking" — the thinking is the design conversation; ADRs capture only the *decision*

---

## File location and numbering

ADRs live in `.context/decisions/` named `NNNN-<slug>.md`:

```
.context/decisions/
├── 0001-event-sourced-orders.md
├── 0002-postgres-for-write-model.md
├── 0003-result-pattern-no-throw.md
└── ...
```

**Numbering:** Sequential. Scan `.context/decisions/` for the highest existing number, increment by one. Never reuse numbers — even for superseded ADRs. The number is permanent.

**Slug:** Short kebab-case description of the decision. Aim for 3-6 words that distinguish this ADR from neighbours. Avoid generic slugs like `architecture` or `database-choice`.

If `.context/decisions/` doesn't exist yet, create it on first ADR.

---

## Format

### Minimum template (most ADRs need only this)

```markdown
# NNNN: [Short title of the decision]

**Date:** YYYY-MM-DD
**Status:** Accepted

## Context
[1-2 sentences: what was the situation that forced a choice?]

## Decision
[1-2 sentences: what we decided.]

## Consequences
[1-3 bullets: what follows from this — what we accept, what we lose.]
```

3-5 sentences in the core sections is acceptable and often ideal. **Long ADRs feel ceremonious; short ones don't.** If you're writing more than half a page, ask whether you're trying to record one decision or several — split if it's several.

### Optional sections

Add only when they genuinely add value. Most ADRs won't need them.

- **Considered Options** — when rejected alternatives are worth remembering ("we considered MongoDB; rejected because..."). Useful for the rejection-stops-future-suggestions case
- **Constraints** — when external factors (compliance, partner SLAs, team skills) drove the decision, and a future reader wouldn't otherwise know
- **Revisit Trigger** — if the decision is contingent on something that may change ("revisit if request volume exceeds 10k/min"). Helps future-you know when to re-open

### Worked example

```markdown
# 0007: Token bucket rate limiter for outbound LLM calls

**Date:** 2026-04-27
**Status:** Accepted

## Context
The 2026-01 outage was caused by constant-rate retry storms after the auth provider degraded — every retry hit at the same instant, amplifying the overload. We need rate limiting that smooths bursts and respects LLM provider quotas.

## Decision
Token bucket strategy with per-provider buckets. Buckets refill at the provider's published RPM divided by 60 (per-second refill). Burst capacity = 2x sustained rate.

## Consequences
- Smooths bursts without dropping requests
- Per-provider isolation: one provider's degradation doesn't starve others
- Operational complexity: new metric to monitor (bucket utilisation)
- Slight added latency under saturation (queueing rather than rejection)

## Considered Options
Constant-rate limiter (rejected: caused 2026-01 incident). External rate-limit service like Envoy (rejected: overkill for current call volume; revisit if we reach 10x current load).
```

---

## Status values

- **Accepted** — active state when written. Use this for almost all ADRs
- **Superseded by ADR-NNNN** — replaced by a newer decision; the old ADR stays in place for history
- **Deprecated** — no longer relevant but no replacement exists (rare)

### Superseding an ADR

When a previously-accepted decision is reversed:

1. **Write a new ADR** with its own number. In the new ADR's Context, reference the old: "Supersedes [ADR-0007](0007-token-bucket-rate-limiter.md) because..."
2. **Edit the old ADR's status line only**: change `**Status:** Accepted` to `**Status:** Superseded by ADR-NNNN`
3. **Don't edit anything else** in the old ADR. Its content is the historical record of what was reasonable to believe at the time

This is the **only** edit allowed to an ADR after it's accepted. Everything else is immutable. Treat ADRs like git commits — append, never rewrite.

---

## Cross-references from other context files

Other files reference the ADR by short link rather than restating context, alternatives, or rationale:

In `architecture.md` Component Map:
> "Rate Limiter sits between the Orchestrator and the LLM Client. Token bucket strategy — see [ADR-0007](../decisions/0007-token-bucket-rate-limiter.md)."

In `design.md` describing behaviour:
> "Rate limited to a configurable RPM per provider. Requests exceeding the limit are queued, not dropped. See [ADR-0007](../decisions/0007-token-bucket-rate-limiter.md) for the rationale."

In `vocabulary.md` if a term emerges from the decision:
> "**Token Bucket Window**: the per-second window in which the rate limiter accumulates capacity. See [ADR-0007](../decisions/0007-token-bucket-rate-limiter.md)."

Don't restate the ADR's reasoning in those files. The cross-reference is enough.

---

## Process when the action fires

1. **Apply the three-question filter.** If it doesn't pass, stop and note the choice inline in the relevant context file. Don't write an ADR
2. **Pick the next number.** Run `ls .context/decisions/` (or check the folder if the user is reviewing) for the highest existing
3. **Draft the ADR.** Aim for 3-5 sentences in core sections. Don't pad
4. **Confirm with the user before writing.** ADRs are durable truth; user approval before commit
5. **Write the file** at `.context/decisions/NNNN-<slug>.md`
6. **Update cross-references.** Edit any context files that should now point at the ADR instead of restating reasoning. Don't leave duplicate rationale in the snapshot files
7. **Commit with a descriptive message** at end of session per the existing git conventions

---

## What this action is NOT

- **Not a place to capture every choice.** The filter is the discipline. Skipping it recreates the dumping-ground problem
- **Not a synonym for "we did some thinking".** The thinking is the design conversation; the ADR captures only the *decision* that came out of it
- **Not for naming or vocabulary.** Canonical names live in `vocabulary.md`. An ADR may inform naming but shouldn't restate the canonical-name list
- **Not for feature behaviour or business rules.** Those go in `design.md`. An ADR captures *why a non-obvious technical/architectural choice was made*
- **Not editable.** Once accepted, only the status line can change (for supersession). Treat ADRs like a git log of decisions
