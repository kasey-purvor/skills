# Consistency Check Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a consistency check sub-agent" and provide the context below.

---

## Prompt Template

```
You are verifying that the project's context files are internally consistent and follow the rules defined in the project work skill.

## Files to Read

Read all files in `.context/project/` (root level only — not implementation/), plus `.context/HANDOFF.md` if it exists.

## Rules Reference

Read the entry point skill at `~/.claude/skills/dev-project-work/SKILL.md`, specifically the "Context File Definitions" and "Cross-File Rules" sections. These define what belongs in each file, the boundary rule, the cross-reference format, and the one-fact-one-owner principle.

## Verify

1. **Cross-references are valid** — every `See filename.md Section Name for [...]` reference points to a section that actually exists in that file
2. **Boundary rules are followed** — each fact lives in its owning file per the boundary rule. Implementation details are not in design.md. Behavioural rules are not in data.md. Domain knowledge is not in integrations.md. Etc.
3. **One fact, one owner** — no specification, schema, or policy is restated across multiple files. Acceptable: the same principle framed differently per file's perspective. Not acceptable: the same detail copy-pasted.
4. **No duplication across files** — if the same information appears in two places, flag it and identify which file should own it
5. **Mandatory sections present** — design.md has Purpose & Scope, Interface & Interactions, Configuration, Core Workflow, Open Questions, Deferred Items. architecture.md has System Overview, Component Map. domain.md (if it exists) has Domain Overview, Terminology & Glossary. Etc.
6. **Context files are pure content** — no guidance blocks, no HTML comments with instructions, no meta-commentary about how to use the file. All guidance lives in skill files, not in context files.
7. **Open Questions are centralized** — all unresolved questions live in design.md Open Questions, not scattered across other files

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

**Summary:**
- Total issues: [count]
- Critical (breaks one-fact-one-owner or boundary rule): [count]
- Minor (formatting, missing optional sections): [count]
```
