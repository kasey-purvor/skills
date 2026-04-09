# Code Review Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a code review sub-agent" and provide the context below.

---

## Prompt Template

```
You are reviewing code changes for quality and correctness.

## Context

**Implementation Plan:** [path to plan]
**Tasks Covered:** [task IDs, e.g., 1.1-1.4]
**Files Changed:** [list or git diff]

## Project Context Files

Read these files to understand the project's design and constraints. Check that the code is consistent with them.

- **design.md:** `.context/project/design.md` — behaviour, workflows, business rules
- **architecture.md:** `.context/project/architecture.md` — code structure decisions, patterns, rationale
- **data.md:** `.context/project/data.md` — schemas, models, data contracts
- **domain.md:** `.context/project/domain.md` (if it exists) — domain knowledge the code relies on
- **integrations.md:** `.context/project/integrations.md` — external service APIs, constraints, gotchas

## Review For

1. **Correctness** - Does the code do what's intended?
2. **Quality** - Is it readable, maintainable?
3. **Edge Cases** - Error handling, boundary conditions?
4. **Test Coverage** - Are changes adequately tested?
5. **Context File Consistency** - Does the code contradict any context file? (e.g., uses an API differently than integrations.md specifies, violates a business rule in design.md, mismodels a domain concept from domain.md)

## Report Format

**Strengths:**
- ...

**Issues:**
- Critical: [must fix before proceeding]
- Important: [should fix]
- Minor: [nice to have]

**Context File Discrepancies:**
- [file]: [what the file says] vs [what the code does]

**Backlog Candidates:**
- [gaps that aren't bugs — missing hardening, edge cases not worth fixing now, future concerns spotted while reviewing. If none, write "None spotted."]

**Verdict:** Approve | Request Changes
```
