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
- Decided library choice + rationale → returned for recording in `architecture.md`
- Service-specific constraints discovered → returned for recording in `integrations.md`
