# Truthfulness Check Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a truthfulness check sub-agent" and provide the context below.

---

## Prompt Template

```
You are verifying that the project's context files still accurately reflect the actual codebase. This is distinct from the consistency check (which compares docs against other docs) — this check compares docs against code.

## Files to Read

Read all files in `.context/project/` (root level only — no subfolders at project level), plus all ADRs in `.context/decisions/*.md` if present. These are the durable-truth documents whose claims need verification.

## Rules Reference

Read the entry point skill at `~/.claude/skills/dev-project-work/SKILL.md`, specifically the "Context File Definitions" section, to understand what each file is supposed to contain.

## Verify

Walk through every concrete claim in the context files and check each against the actual codebase. Concrete claims include:

1. **File paths** — does the named file exist at that path?
2. **Function / class / component names** — does the named symbol exist in the codebase?
3. **Schema fields** — do the described fields match the actual schema (DB, Zod, type definitions, etc.)?
4. **Route patterns** — do the described API routes match what's actually defined in the router/gateway config?
5. **Library / tool choices** — is the named library actually in `package.json` / `requirements.txt` / equivalent?
6. **Component responsibilities** — does the file described as "doing X" actually do X?
7. **Configuration keys** — do described config keys match the actual config schema?
8. **External service integrations** — do described integration details (regions, endpoints, auth modes) match what's in the infra code?

Verify each claim using Read / Grep / Bash. Do not assume — check.

## Report Format

**Files Checked:**
- [list of context files read]

**Accurate Claims:**
- [brief summary — count only, or list highlights if few]

**Stale Claims (docs wrong, code correct):**
- [file]: claims [X], but actual code shows [Y] — evidence: [path:line or command]

**Missing Documentation (code exists, docs don't mention):**
- [area of code]: [symbol / component / integration] exists at [path] but is not documented in any context file

**Unverifiable Claims (can't determine true/false):**
- [file]: claims [X] but [reason verification failed — e.g., tests not run, external service not accessible from here]

**Summary:**
- Total concrete claims examined: [count]
- Accurate: [count]
- Stale: [count]
- Missing: [count]
- Unverifiable: [count]

Do not fix issues. This is a reporting pass only — the Lead classifies findings with the user afterward.
```
