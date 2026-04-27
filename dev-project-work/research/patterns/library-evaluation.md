# Library Evaluation Pattern

## When

- Need to assess whether a library is suitable for the project
- Need to check if a library is actively maintained
- Need to compare alternatives for a specific capability

## What to Investigate

- **Maintenance health**: Last release date and frequency, open issues count and response patterns, number of contributors, language version support
- **Feature fitness**: Does it support the specific capability needed? Known limitations? API surface complexity?
- **Integration**: Dependencies it brings in, compatibility with existing stack, license compatibility

## Source Tier Examples

| Tier | Examples |
|------|---------|
| 1 — Official/Primary | PyPI/npm page, GitHub repository, official documentation |
| 2 — Established Authority | Changelog, GitHub issues/discussions, official migration guides |

## Findings Go To

- Evaluation results → returned to conversation for discussion
- Decided library choice → returned for recording in `architecture.md` (the *what*, in the Component Map)
- Rationale for the choice (if it passes the three-question filter: hard to reverse / surprising / real trade-off) → returned for recording as an ADR in `.context/decisions/` via the Lead's Record Decision action
- Service-specific constraints discovered → returned for recording in `integrations.md`
