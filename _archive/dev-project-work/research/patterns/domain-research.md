# Domain Research Pattern

## When

- Project operates in a complex, regulated, or specialised domain
- Domain knowledge is prerequisite to software design
- Getting domain facts wrong has real consequences

## What to Investigate

For each major concept, address whichever of these are applicable:

- **Entities**: What are the concrete things in this domain? How do they relate to each other?
- **Lifecycles**: What states or stages does each entity go through? What triggers transitions? What are the time constraints? Who are the participants at each stage?
- **Terminology**: What do domain-specific terms precisely mean? Where do common terms have domain-specific meanings?

Don't just describe what the domain requires — describe how things actually work as concrete sequences of events with states and participants.

## Source Tier Examples

| Tier | Examples |
|------|---------|
| 1 — Official/Primary | Government sites (.gov), primary legislation text, official regulatory bodies, the actual data sources |
| 2 — Established Authority | Cornell LII, university references, established professional bodies, official industry standards |

## Findings Go To

- Verified domain facts → returned for recording in `domain.md`
- Technical access details discovered during research → returned for recording in `integrations.md`
- Unverified claims → returned flagged as "needs verification"
