# Standards & Specification Research Pattern

## When

- The project needs to implement or comply with a formal standard (W3C, ISO, IEEE, industry consortium specs)
- Getting the spec requirements wrong means building the wrong thing
- The standard has its own ecosystem (implementation guides, certification requirements, conformance tests)

## What to Investigate

For each standard, work through these layers:

- **Spec basics**: Who maintains it? What version is current? What's the document structure (spec, implementation guide, certification guide)?
- **Data model**: What does the standard define structurally? Schemas, required fields, formats, concrete examples
- **Implementation requirements**: What must an implementer actually do? Hosting obligations, cryptographic requirements, API surface, runtime behaviour
- **Verification/conformance**: How is compliance checked? Self-assessment, third-party certification, test suites?
- **Infrastructure implications**: Does implementing this standard require persistent endpoints, key management, specific protocols, or hosting commitments?

## Source Tier Examples

| Tier | Examples |
|------|---------|
| 1 — Official/Primary | The specification document itself, official implementation guides, certification/conformance guides, the standards body's website |
| 2 — Established Authority | Official SDKs/reference implementations, the standards body's blog/announcements, recognised adopter documentation |

## Findings Go To

- What the standard IS and how it works → returned for recording in `domain.md`
- Infrastructure/hosting/API requirements for implementation → returned for recording in `integrations.md`
- Design implications (what the software must do to comply) → returned flagged for `design.md`
