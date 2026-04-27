# Consistency Check Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a consistency check sub-agent" and provide the context below.

---

## Prompt Template

```
You are verifying that the project's context files are internally consistent and follow the rules defined in the project work skill.

## Files to Read

Read all files in `.context/project/` (flat — no subfolders at project level), all ADRs in `.context/decisions/*.md` if present, plus `.context/HANDOFF.md` if it exists. **Read `.context/project/vocabulary.md` first** if it exists — its glossary is the reference point for vocabulary adherence checks below.

## Rules Reference

Read the entry point skill at `~/.claude/skills/dev-project-work/SKILL.md`, specifically the "Context File Definitions", "The Boundary Rule", "Cross-File Overlaps", and "Cross-Reference Format" sections. These define what belongs in each file, the boundary rule, the cross-reference format, and the one-fact-one-owner principle.

## Verify

1. **Cross-references are valid and follow the format** — every reference uses the form `See `filename.md` Section Name for [...]` (with backticks around the filename, real section name, and "for [what]" suffix). Each reference must point to a section that actually exists in the target file
2. **Boundary rules are followed** — each fact lives in its owning file per the boundary rule. Implementation details are not in design.md. Behavioural rules are not in data.md. Domain knowledge is not in integrations.md. Etc.
3. **One fact, one owner** — no specification, schema, or policy is restated across multiple files. Acceptable: the same principle framed differently per file's perspective. Not acceptable: the same detail copy-pasted.
4. **No duplication across files** — if the same information appears in two places, flag it and identify which file should own it
5. **Mandatory sections present** — design.md has Purpose & Scope, Interface & Interactions, Configuration, Core Workflow, Open Questions, Deferred Items. architecture.md has System Overview, Component Map. domain.md (if it exists) has Domain Overview. vocabulary.md (if it exists) has Glossary. Etc.
6. **Context files are pure content** — no guidance blocks, no HTML comments with instructions, no meta-commentary about how to use the file. All guidance lives in skill files, not in context files.
7. **Open Questions are centralized** — all unresolved questions live in design.md Open Questions, not scattered across other files
8. **Vocabulary adherence (only if `vocabulary.md` exists)** — context files use the canonical names from `vocabulary.md`. Specifically flag:
   - Use of an `_Avoid_` alias where a canonical term exists (e.g., document says "task" when `vocabulary.md` defines **Chunk** with `_Avoid_: task`)
   - Two different terms used for what appears to be one concept across documents (terminology drift between context files)
   - Do NOT flag terms that simply aren't in `vocabulary.md` — absence of coverage is not a violation, only misuse of *defined* terms is
9. **ADR structure (only if `.context/decisions/` has any ADRs)** — each ADR has the mandatory header structure: `# NNNN: <Title>`, `**Date:** YYYY-MM-DD`, `**Status:** <Accepted | Superseded by ADR-NNNN | Deprecated>`, plus `## Context`, `## Decision`, and `## Consequences` sections. Flag any ADR missing one of these or with a Status value outside the three valid options. Do not check ADR *content* — only structural presence

## Report Format

**Files Checked:**
- [list of files read]

**Cross-Reference Issues:**
- [broken or missing references]

**Boundary Violations:**
- [file]: [content that belongs elsewhere] -> should be in [correct file]

**Duplication Found:**
- [fact/detail]: stated in [file A] and [file B] -> owner should be [correct file]

**Missing Mandatory Sections:**
- [file]: missing [section name]

**Content Purity Issues:**
- [file]: [guidance or meta-commentary found]

**ADR Structure Issues:**
- [ADR file]: missing [Date | Status | Context | Decision | Consequences] section, or invalid Status value
- (If `.context/decisions/` is empty or absent, write: "Skipped — no ADRs yet.")

**Vocabulary Adherence Issues:**
- [file]: uses "[alias]" — `vocabulary.md` says "[canonical]" (alias listed under `_Avoid_`)
- Drift: [file A] uses "[term1]" while [file B] uses "[term2]" for what looks like the same concept — needs Lead clarification or `vocabulary.md` update
- (If `vocabulary.md` does not exist or has no entries, write: "Skipped — no vocabulary defined yet.")

**Summary:**
- Total issues: [count]
- Critical (breaks one-fact-one-owner or boundary rule): [count]
- Minor (formatting, missing optional sections): [count]
```
