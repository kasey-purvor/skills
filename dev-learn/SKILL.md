---
name: dev-learn
description: Use at the end of a conversation to extract and summarize key learning points before closing - reviews the conversation for questions answered, concepts explained, and technical knowledge shared
---

# Extract Learning Points

## Overview

Capture specific, concrete knowledge gained during a conversation before it disappears. The goal is a quick-reference summary that refreshes your memory months later.

**Announce at start:** "Reviewing conversation for learning points..."

## The Process

### 1. Review the Conversation

Scan the entire conversation for:
- **Questions asked and answers given** — especially "why" questions
- **Concepts explained** — foundational knowledge, non-obvious mechanisms, how things actually work
- **Patterns and conventions** — best practices, industry norms, naming conventions, directory structures
- **"Aha moment" connections** — where two concepts clicked together or a misconception was corrected
- **Tool/command knowledge** — flags, options, workflows that were new or clarified

**Skip:** Task logistics (what was built, files changed, commands run for the task itself). Focus on what was LEARNED, not what was DONE.

### 2. Produce the Summary

Format as a single concise document:

```markdown
# Learning Summary: <Main Topic(s)>

**Date:** YYYY-MM-DD

## Key Learning Points

- **<Specific fact or concept>** — <1-2 sentence explanation that is self-contained and concrete>
- **<Another point>** — <explanation>
...
```

**Quality bar for each bullet:**
- SPECIFIC and CONCRETE — contains a fact, name, mechanism, or reason
- SELF-CONTAINED — makes sense when read in isolation months later
- Answers "what did I learn?" not "what topic was discussed?"

**Examples of good bullets:**
- **The `bin` directory name is historical** — it stands for "binary" but actually contains any executable, including shell scripts and symlinks to scripts. The name stuck from early Unix.
- **`set -euo pipefail` combines three bash safety features** — `-e` exits on error, `-u` treats unset variables as errors, `-o pipefail` makes pipes fail if any command in the chain fails (by default only the last command's exit code matters).
- **Retry logic should use exponential backoff with jitter** — without jitter, all clients retry at the same intervals, causing "thundering herd" spikes. Jitter randomizes the delay so retries spread out.

**Examples of bad bullets (do NOT write these):**
- Learned about Linux directories
- Discussed bash scripting
- Explored retry patterns

### 3. Skill Opportunities

After the summary, add a brief section:

```markdown
## Skill Opportunities

- <1-3 bullets identifying potential new skills or updates to existing skills suggested by the learning, OR "None identified">
```

This is observational only — just note the opportunity, don't take action.

### 4. Ask About Saving

After presenting the full summary, ask:

> Would you like me to save this to `~/dev_wsl/learning/`?

**If yes:**
- Create directory `~/dev_wsl/learning/` if it doesn't exist
- Save as `~/dev_wsl/learning/YYYY-MM-DD-<topic-slug>.md`
- Topic slug: lowercase, hyphens, 3-5 words max (e.g., `bash-safety-and-signals`, `python-packaging-fundamentals`)

**If no:** That's fine. The user just wanted to review before closing.

## Key Principles

- **Specificity over coverage** — 5 concrete bullets beat 15 vague ones
- **Learning over doing** — capture what was UNDERSTOOD, not what was BUILT
- **Self-contained bullets** — each point should refresh memory independently
- **Ask before saving** — presenting the summary is the primary value; saving is secondary
- **No categories or tags** — keep it simple, one flat list of bullets
