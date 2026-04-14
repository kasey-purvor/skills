# API Exploration Pattern

## When

- Need to verify how an API actually behaves (not just what docs claim)
- Need to check current API capabilities, versions, or constraints
- Need to discover undocumented behaviour or limitations

## What to Investigate

- **Documentation**: What version? What endpoints are relevant? What auth model? Regional constraints?
- **Live testing**: Hit real endpoints, observe actual responses, verify rate limits and error responses, check response formats against docs
- **Constraints**: Rate limits (stated vs actual), payload size limits, feature availability by tier/region/plan, auth differences between dev and production

## Source Tier Examples

| Tier | Examples |
|------|---------|
| 1 — Official/Primary | The API itself (live responses), official API documentation, official changelogs |
| 2 — Established Authority | Official SDKs and their source code, official blog posts about the API |

## Findings Go To

- Tested behaviour (with dates) → returned for recording in `integrations.md`
- Discovered constraints → returned for recording in `integrations.md`
- Gotchas (docs say X, API does Y) → returned flagged clearly as gotchas
- Design implications → returned flagged for `design.md` or `architecture.md`
