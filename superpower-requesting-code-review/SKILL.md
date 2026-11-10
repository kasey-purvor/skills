---
name: superpower-requesting-code-review
description: Use when completing a change, a major feature or pre-merge work to request an independent review through the shared change-review workflow.
---

# Requesting code review

Use the current shared global review policy for timing and authorisation, and load [change-review](../change-review/SKILL.md) for the review procedure. Routine delivery reviews are already authorised; extra specialists follow the shared approval policy.

The coordinator supplies the exact target, requirements, relevant instructions and observed test evidence to one fresh reviewer by default. Use the platform's available delegation tools and the user's model/effort policy, not hard-coded tool or model names. Do not pass the builder's full conversation or a suggested verdict.

An assigned reviewer follows change-review's assigned-reviewer mode and does not dispatch another reviewer. Do not create nested review chains just because a worker loads this skill.

For older workflows using a prompt template, [code-reviewer.md](code-reviewer.md) provides the same handoff fields. Findings, fresh fixers and verification of fixes follow the shared policy and [stream/review-findings.md](../stream/review-findings.md); this adapter defines no competing severity or disposition rules.
