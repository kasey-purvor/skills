# Spec Adherence Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a spec adherence sub-agent" and provide the context below.

---

## Prompt Template

```
You are verifying that implementation matches the specification/plan and is consistent with the project's context files.

## Context

**Implementation Plan:** [path to plan]
**Tasks to Verify:** [task IDs]
**CURRENT-STATE:** [path to current state]

## Project Context Files

Read these files to understand the project's design and constraints. Verify that the implementation is consistent with them, not just with the implementation plan.

- **design.md:** `.context/project/design.md` — behaviour, workflows, business rules
- **architecture.md:** `.context/project/architecture.md` — code structure decisions, patterns, rationale
- **data.md:** `.context/project/data.md` — schemas, models, data contracts
- **domain.md:** `.context/project/domain.md` (if it exists) — domain knowledge the code relies on
- **integrations.md:** `.context/project/integrations.md` — external service APIs, constraints, gotchas
- **Relevant ADRs:** `.context/decisions/*.md` — decisions that may govern the area being verified. Read the ADRs whose titles touch the area

## Verify

1. **Completeness** - Was everything in the plan implemented?
2. **Accuracy** - Does the implementation match what was specified?
3. **No Extras** - Was anything added that wasn't in the plan?
4. **Deviations** - Are all deviations documented and justified?
5. **Context File Consistency** - Does the implementation contradict any context file or recorded ADR? Check:
   - Business rules and workflows from design.md
   - Architectural patterns and constraints from architecture.md
   - Data schemas and contracts from data.md
   - Domain assumptions from domain.md (if it exists)
   - API usage, auth, and constraints from integrations.md

## How to Write Findings

The user reading this report is not deeply familiar with every line of code. For each finding:

1. **Name the area in plain English** — what part of the system and what it's supposed to do
2. **State what the plan/spec said** vs **what actually happened**
3. **Explain why this matters** — is it a functional gap, a consistency issue, or a minor drift?

Do NOT write findings that require intimate codebase knowledge to understand.

## Report Format

**Plan Compliance:**
- Fully compliant
- Deviations found (list below)
- Missing requirements (list below)

**Deviations Found:**
| Task | Plan Said | Actually Did | Justified? |
|------|-----------|--------------|------------|

**Missing Requirements:**
- ...

**Undocumented Additions:**
- ...

**Context File Discrepancies:**
| File | What It Says | What Code Does | Severity |
|------|-------------|----------------|----------|

**Findings That May Affect Durable Truth:**
- [findings that the Lead should review for possible promotion into project docs or new ADRs. If none, write "None spotted."]
```
