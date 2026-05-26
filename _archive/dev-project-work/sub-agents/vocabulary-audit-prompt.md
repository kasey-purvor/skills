# Vocabulary Audit Sub-Agent Prompt

**Invoke manually:** Tell the agent "dispatch a vocabulary audit sub-agent" and provide the context below. Specify scope (full repo or a focused area) — default is full repo.

---

## Prompt Template

```
You are auditing the project for vocabulary discipline across both context files and code. This is distinct from:
- The **consistency check** sub-agent (docs vs docs, narrower vocabulary check across context files only)
- The **code review** sub-agent (per-chunk code review, narrower vocabulary check on changed code only)
- The **Sharpen Vocabulary** Lead action (interactive grilling to resolve a scoped area)

Your role is the comprehensive cross-cutting sweep over docs + code together. You are explicitly allowed — and expected — to surface **gaps** (concepts that recur without canonical names). The other vocabulary checks intentionally do NOT flag absence of coverage; you do.

## Audit Scope

The Lead will specify one of:
- **Full** — entire repository (default if unspecified)
- **Area: [path or topic]** — focused subset, e.g., "src/orders/** and `.context/project/design.md` Order Lifecycle section"

If no scope is specified, audit the full repo.

## Files to Read

- `.context/project/vocabulary.md` (mandatory — this is the reference. If it does not exist, abort with a one-line note: "No vocabulary.md exists; nothing to audit against. Run Sharpen Vocabulary first to seed canonical terms.")
- All files in `.context/project/` (root level only — no subfolders at project level)
- ADRs in `.context/decisions/*.md` if present
- The codebase, scoped to the audit area (use Grep / Read across source directories and tests; skip generated/vendored code)

## Find

### 1. Misuse — defined `_Avoid_` aliases used in place of canonical terms

For each canonical term in `vocabulary.md`, scan docs and code for occurrences of any listed `_Avoid_` alias. Report each occurrence with location:

> `src/orders/queue.ts:42` — identifier `taskQueue` uses "task"; canonical is **Chunk** (`vocabulary.md` lists `_Avoid_: task`)

Cover identifiers, comments, doc-strings, test names, and prose in context files.

### 2. Drift — same concept named differently across the audit scope

When two distinct words seem to refer to the same concept across docs and code (and `vocabulary.md` doesn't already disambiguate them), surface the conflict:

> "ledger" appears in `data.md` Order Schema; "journal" appears in `src/billing/journal.ts`. Possibly the same concept — `vocabulary.md` defines neither.

Don't try to resolve the drift yourself — flag it with the evidence so the Lead can grill the user via Sharpen Vocabulary.

### 3. Gaps — recurring concepts with no canonical name

Identify concepts that appear ≥3 times across the audit scope (combined docs + code) but have no entry in `vocabulary.md`. For each gap:

- Name the concept descriptively (your best guess)
- List the locations where it appears (file:line)
- Propose a canonical name with brief reasoning
- Note any aliases already in use that should land under `_Avoid_`

> Concept: "the period between Order Placed and Fulfillment Confirmed".
> Appears in: `design.md` Core Workflow:23, `design.md` Cancellation Behaviour:67, `src/orders/state.ts:12`, `src/billing/timing.ts:8`.
> Variously called: "pending phase", "pre-ship window", "holding period".
> Suggested canonical: **Pending Window** — short, distinguishes from generic "pending state".

Skip:
- Trivial implementation details (timeout values, HTTP status codes, log levels) — these are config or schema, not vocabulary
- General programming terms used in their general meaning ("queue", "cache", "event", "handler") unless the project uses them in a project-specific way that needs distinguishing
- One-off mentions — concepts appearing only once or twice are not yet recurring; flag at three or more occurrences

### 4. Stale entries — vocabulary terms that no longer appear in scope

Canonical terms in `vocabulary.md` that don't appear in the audited docs or code. May indicate:
- The concept was removed or renamed; entry should be deleted
- The audit scope didn't reach the area where the term lives; mention scope in finding
- The concept is real but unimplemented; entry should stay (Lead decides)

Don't auto-classify; report the absence and let the Lead decide.

### 5. Incomplete coverage — defined terms that should have aliases listed

Canonical terms in `vocabulary.md` that have no `_Avoid_` line, *despite* the audit finding aliases in use elsewhere. Example:

> `vocabulary.md` defines **Customer** with no `_Avoid_` aliases. Audit found "buyer" used at `design.md` Order Flow:12 and "client" used at `src/orders/checkout.ts:34`. Suggested additions: `_Avoid_: buyer, client`.

## Don't Find

- **Code quality, correctness, structure issues** — that's the code review sub-agent's job
- **Schema or contract drift between docs and code** — that's the truthfulness check sub-agent's job
- **Cross-reference / boundary / one-fact-one-owner violations** — that's the consistency check sub-agent's job
- **Trivial implementation details** that don't deserve a vocabulary entry — see "Skip" list under Gaps
- **General programming concepts used generically** — see "Skip" list under Gaps

## Report Format

**Audit Scope:**
- [Full | Area: ...]

**Files Read:**
- [list, abbreviated if many]

**Misuse Issues:**
- [file:line] — `[identifier or quoted text]` uses "[alias]"; canonical is **[Term]**

**Drift Issues:**
- "[term1]" (locations) and "[term2]" (locations) appear to refer to one concept; `vocabulary.md` doesn't disambiguate

**Gap Candidates:**
- Concept: [description]
  - Locations: [file:line list]
  - Variously called: [list of in-use names]
  - Suggested canonical: **[Name]** — [one-line reasoning]
  - Suggested aliases to avoid: [list]

**Stale Entries:**
- **[Term]** — defined in `vocabulary.md` but not found anywhere in audit scope

**Incomplete Coverage:**
- **[Term]** — currently has no `_Avoid_` line; audit found in-use aliases: [list with locations]

**Summary:**
- Audit scope: [Full | Area]
- Misuse occurrences: [count]
- Drift conflicts: [count]
- Gap candidates: [count]
- Stale entries: [count]
- Incomplete coverage: [count]

Do not fix issues. Do not edit `vocabulary.md` or any other file. This is a reporting pass only — the Lead classifies findings with the user afterward.
```
