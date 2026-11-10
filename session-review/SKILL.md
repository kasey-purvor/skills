---
name: session-review
description: Review a session's transcript for worthwhile, durable decisions, traps and instruction corrections. Propose only those that earn a place in the relevant docs; a review may yield no proposals. Use at a stream's close, at the end of a `grill-with-docs` session, before a handoff, or when the human asks to review a session for decisions and traps. Also offer it, in one line, when the human signals they are wrapping up (wrapping up, closing, done for today, signing off); start it only on a yes.
---

# Session review

Preserve only what will materially help future work: durable decisions, non-obvious traps, and instructions proved wrong. There is no quota for proposals or destinations. If nothing qualifies, say "No durable additions warranted" and stop without an approval prompt. The human says yes or no to each qualifying line. Nothing is written without a yes.

## When

- At a stream's close: step 3 of the `stream` skill's close checklist runs it.
- At the end of a `grill-with-docs` session: its last step runs it.
- Before any handoff: the `handoff` skill offers it first.
- When the human signals they are wrapping up ("wrapping up", "closing", "done for today", "signing off"), in any session, stream or not: offer it in one line, once. Start it only on a yes.
- When the human asks.

Otherwise never on your own initiative. A no or a "not now" just drops it: the review can run later on that session's transcript with `--file`.

## Read the session, not your memory

Your memory of a long session is compressed and drifts; the transcript does not. Run the bundled script and work from its output:

```bash
python3 -I ~/.agents/skills/session-review/scripts/extract-session.py --latest --out <scratchpad>/session.md
```

- **Claude Code** keeps each session at `$CLAUDE_CONFIG_DIR/projects/<cwd>/<session-id>.jsonl`, where `<cwd>` is the directory the session started in, with every character other than a letter or digit turned to `-` (`/home/kasey/dev_wsl/x` → `-home-kasey-dev-wsl-x`). Its subagents are under `<session-id>/subagents/*.jsonl`. `--latest` reads the session `$CLAUDE_CODE_SESSION_ID` names, wherever it started, and every subagent. When that is not set, it falls back to the newest `.jsonl` for this directory, which may be another session.
- **Codex** keeps `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`. `--codex` reads the newest one started in this directory, and its subagents.
- **Codex builders:** a lane built through `codex-dispatch` has its own rollout, `rollout-<time>-<thread id>.jsonl` in that folder; the launcher prints the thread id. When the stream used Codex builders, read each rollout with `--file <rollout>`. There, a `USER` turn is the orchestrator's brief to the builder, not the human's words.
- `--file PATH` reads any one transcript instead.
- **At a stream's close**, also read the stream ticket's comments: every decision the human made is logged there. Earlier sessions of the stream are not re-read unless the human asks; one whose review was declined can still be reviewed with `--file`. A session already reviewed is never reviewed again, so a `seen` count is never bumped twice for one session.

The script first prints a `reading …` line naming the transcript it chose and why. With `--latest` or `--codex`, check that line names your own session before you trust the output. Always run Python as `python3 -I`. Write the output to your scratchpad, never into a repo.

The output keeps everything the human typed in full, messages typed mid-turn included, plus one line per tool call, every tool error, and the agent's text cut short. Two things are kept whole: the last message of every transcript (each subagent's and a builder rollout read with `--file`), and the reports other agents send back. A compaction summary becomes one marker line. Messages from other agents are labelled `AGENT-MSG`, `PEER-MSG` or `PARENT`, so they are never mistaken for the human.

## Look for candidates

For each one, say what happened in plain words and which moment in the session it came from (the timestamp, or the human's own words).

1. **Decisions the human made that are settled.** The human's words, not an agent's suggestion that nobody answered.
2. **Traps that cost time in this repo:** a hook that bit, a flaky test, a command that must run from a certain place.
3. **Traps in a tool or a machine:** Claude Code, Codex, Linear, a scraping or search service, git and GitHub, the machines.
4. **Instruction gaps or errors:** instructions in the repo or an existing workflow skill that this session demonstrated were missing, ambiguous or wrong.

Builders report their traps at the end of their final reports (what bit, the fix, roughly how long it cost). Those reports are kept whole: as `AGENT-MSG` in the main session, and as each subagent's last message.

## Select before proposing

An observation earns a proposal only if it adds specific, durable information that changes a future decision or prevents a concrete failure, and fits the destination's purpose. Being applicable across repos is not enough.

- Skip ordinary competence advice, routine agent inattention, session narratives, and reminders to follow existing instructions. Do not turn every mistake into a new rule.
- Keep ticket status, completion evidence and ticket-specific decisions in the tracker. Promote a decision only when it establishes an enduring repo policy or domain rule that is missing from the repo docs.
- Repo pitfalls must describe a specific repo constraint or trap and a verified way to avoid it. When a useful lesson instead exposes a gap in an existing workflow skill, prefer a targeted correction to that skill. Name the missing, ambiguous or wrong instruction; merely failing to follow adequate instructions does not qualify.
- For the handbook's `topics/environment.md`, require a specific, observed tool or machine behaviour, its trigger and consequence, and an actionable workaround useful across repos. General workflow advice such as "check linked evidence" does not qualify. A demonstrated hidden tool constraint can qualify on its first occurrence.
- Check existing guidance before proposing an addition. Do not rephrase what is already covered or move a rejected proposal elsewhere just to retain it. Uncertain value is a reason to omit it, not to ask the human to filter it.

## Check what is already there

Read `docs/decisions.md`, `docs/pitfalls.md`, the ADRs in `docs/adr/` and the handbook's `topics/environment.md` (in the `dev-standards-handbook` skill). For a workflow candidate, also read the existing skill and the relevant procedure it references before deciding there is a gap.

- A decision an ADR already holds: skip it.
- The same qualifying trap again: propose bumping its `seen` count, not a new line.
- A decision that reverses an earlier line: propose filling in `superseded by:` on the old line, as well as the new line.
- An existing trap line whose trap this session shows is now fixed at the source (a hook, a script, a preflight step) or moved into a how-to: propose deleting it. The human says yes or no to each deletion, as to any line. List any others that look ready for one of those endings, so the files shrink.

## Route

| Found | Goes to |
|---|---|
| A decision | `docs/decisions.md`. If it passes the ADR test (hard to reverse, surprising without context, the result of a real trade-off), offer an architecture decision record (ADR) instead |
| A qualifying repo-specific constraint or trap | `docs/pitfalls.md` |
| A demonstrated gap or error in an existing workflow skill | A targeted correction to the owning `SKILL.md` or referenced procedure |
| A qualifying trap in a shared tool or machine | the handbook's `topics/environment.md`, under its heading |
| A wrong instruction | a proposed edit to that file |

Where the repo's `## Agent skills` block names another place for decisions and pitfalls, use that place. Prefer correcting the owning procedure over copying the same lesson into several destinations. Routing does not rescue a candidate that failed selection.

## Ask, line by line

Only if proposals survive selection, send one short message, grouped by destination. Each item is a proposed line in the shape `docs/agents/domain.md` gives, a targeted instruction edit, or a proposed deletion, numbered so the human can answer "1 yes, 2 no…". State what useful new information each adds and why it belongs there. Write it in plain English and gloss every ticket id and file name the first time. Nothing is written without a yes, and anything the human declines is dropped.

## Write

- **Repo changes** (decisions, pitfalls, instruction fixes including repo-local skills, and deletions) land in one pull request: the stream's last pull request if there is one and it has not merged, otherwise a small docs pull request. Its body lists each approved change under "Approved in a session review on <date>", so a reviewer can see the human said yes.
- **A place outside the repo:** where the repo's `## Agent skills` block names one, write the approved lines there, with no pull request.
- **Shared-skill edits and handbook lines** land as one change in the skills repo (`~/.agents/skills`). Leave it uncommitted: the human commits and pushes it from their own profile.

## Never copy a secret

Transcripts contain keys, tokens and passwords. Never quote one, in the message to the human or in a line. A pitfall about a credential names where it lives (the secret's name, the file), never its value.
