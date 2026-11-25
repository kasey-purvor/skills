---
name: session-wrap-up
description: Review a session's transcript for worthwhile, durable decisions, traps and instruction corrections. Propose only those that earn a place in the relevant docs; a review may yield no proposals. Use at a stream's close, before a handoff, after `to-issues` has published a plan's tickets, or when the human asks to review a session for decisions and traps. Also offer it, in one line, when the human signals they are wrapping up (wrapping up, closing, done for today, signing off); start it only on a yes.
---

# Session wrap-up

Preserve only what will materially help future work: durable decisions, non-obvious traps, and instructions proved wrong. There is no quota for proposals or destinations. If nothing qualifies, say "No durable additions warranted" and stop without an approval prompt. The human says yes or no to each qualifying line. Nothing is written without a yes.

## When

- At a stream's close: step 3 of the `stream` skill's close checklist runs it.
- Before any handoff: the `handoff` skill offers it first.
- After `to-issues` has published a plan's tickets: that skill offers it in one line. Not earlier in planning: never after a grill or a requirements document alone.
- When the human signals they are wrapping up ("wrapping up", "closing", "done for today", "signing off"), in any session, stream or not: offer it in one line, once. Start it only on a yes.
- When the human asks.

Otherwise never on your own initiative. A no or a "not now" just drops it: the review can run later on that session's transcript with `--file`.

## Read the session, not your memory

Your memory of a long session is compressed and drifts; the transcript does not. Run the bundled script and work from its output:

```bash
python3 -I ~/.agents/skills/session-wrap-up/scripts/extract-session.py --latest --out <scratchpad>/session.md
```

- **Claude Code** keeps each session at `$CLAUDE_CONFIG_DIR/projects/<cwd>/<session-id>.jsonl`, where `<cwd>` is the directory the session started in, with every character other than a letter or digit turned to `-` (`/home/kasey/dev_wsl/x` → `-home-kasey-dev-wsl-x`). Its subagents are under `<session-id>/subagents/*.jsonl`. `--latest` reads the session `$CLAUDE_CODE_SESSION_ID` names, wherever it started, and every subagent. When that is not set, it falls back to the newest `.jsonl` for this directory, which may be another session.
- **Codex** keeps `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`. `--codex` reads the newest one started in this directory, and its subagents.
- **Codex builders:** a lane built through `codex-dispatch` has its own rollout, `rollout-<time>-<thread id>.jsonl` in that folder; the launcher prints the thread id. When the stream used Codex builders, read each rollout with `--file <rollout>`. There, a `USER` turn is the orchestrator's brief to the builder, not the human's words.
- `--file PATH` reads any one transcript instead.
- **At a stream's close**, also read the stream ticket's comments: every decision the human made is logged there. Earlier sessions of the stream are not re-read unless the human asks; one whose review was declined can still be reviewed with `--file`. A session already reviewed is never reviewed again, so a `seen` count is never bumped twice for one session.

The script first prints a `reading …` line naming the transcript it chose and why. With `--latest` or `--codex`, check that line names your own session before you trust the output. Always run Python as `python3 -I`. Write the output to your scratchpad, never into a repo.

The output keeps everything the human typed in full, messages typed mid-turn included. From the main session it also keeps one line per tool call, every tool error, the agent's text cut short, and the reports other agents sent back, whole. The last message of a transcript read with `--file` is kept whole too. A compaction summary becomes one marker line. Messages from other agents are labelled `AGENT-MSG`, `PEER-MSG` or `PARENT`, so they are never mistaken for the human. Harness chatter is cut to one line: a notice that a background command finished, and an idle notice that only repeats a report the agent had just sent.

Near the top, tool errors seen more than once are counted across every transcript: a repeat is a trap worth a look. At the end, each subagent gets one line, then only what the main session never saw of it: its tool errors, and its final message when that message did not arrive. Its narration and its tool calls are left out. To see one subagent in full, read its transcript with `--file`.

**Will it fit?** The script's last line gives the arithmetic: this session's context, plus the extract, as a share of the window. Read the extract yourself by default. When that total is over 75%, tell the human the figure and offer a reader instead. It takes several minutes, so send one only on a yes. If the total will not fit at all, say so and let the human choose; never compact on your own.

**Sending a reader.** One subagent on Opus at extra-high effort. It finds candidates and changes nothing; you still do the selecting, checking, routing and asking. Give it the extract's full path, the layout of the file as described above, and the six kinds under "Look for candidates" below, copied word for word. Tell it to:

- read the whole file in order, first line to last, and nothing else: no skimming, no searching in place of reading, no repo files and no tickets;
- be inclusive, since you filter: a doubtful candidate goes in marked "unsure", and one the session already recorded goes in marked "already handled";
- read the long reports from builders and reviewers as closely as the human's words, because a trap is often one line inside one;
- return one numbered list in the order of the file, each candidate with its kind, what happened, the timestamp, the line number and the human's exact words;
- end with the number of reads it made and the last line it read, and never quote a secret.

## Look for candidates

For each one, say what happened in plain words and which moment in the session it came from (the timestamp, or the human's own words).

1. **Decisions the human made that are settled.** The human's words, not an agent's suggestion that nobody answered.
2. **Traps that cost time in this repo:** a hook that bit, a flaky test, a command that must run from a certain place.
3. **Traps in a tool or a machine:** Claude Code, Codex, Linear, a scraping or search service, git and GitHub, the machines.
4. **Instruction gaps or errors:** instructions in the repo or an existing workflow skill that this session demonstrated were missing, ambiguous or wrong.
5. **Decisions, changes of scope and blockers that never reached their ticket.** They should have been recorded when they happened. This is the second chance.
6. **Lines in the repo's agent instructions that this session made untrue or out of date:** a command, an environment, a rule or a part of the stack changed, or the setup has stopped fitting the project (it is about to go live, for example).

Builders report their traps at the end of their final reports (what bit, the fix, roughly how long it cost). Those reports are kept whole where the main session received them, as `AGENT-MSG`. A final report that never arrived is kept in that subagent's part at the end.

## Select before proposing

An observation earns a proposal only if it adds specific, durable information that changes a future decision or prevents a concrete failure, and fits the destination's purpose. Being applicable across repos is not enough.

- Skip ordinary competence advice, routine agent inattention, session narratives, and reminders to follow existing instructions. Do not turn every mistake into a new rule.
- Keep ticket status, completion evidence and ticket-specific decisions in the tracker. Promote a decision only when it establishes an enduring repo policy or domain rule that is missing from the repo docs.
- Repo pitfalls must describe a specific repo constraint or trap and a verified way to avoid it. When a useful lesson instead exposes a gap in an existing workflow skill, prefer a targeted correction to that skill. Name the missing, ambiguous or wrong instruction; merely failing to follow adequate instructions does not qualify.
- For a trap line in the handbook's `topics/pitfalls.md` (traps in shared tools and machines), require a specific, observed tool or machine behaviour, its trigger and consequence, and an actionable workaround useful across repos. General workflow advice such as "check linked evidence" does not qualify. A demonstrated hidden tool constraint can qualify on its first occurrence.
- Check existing guidance before proposing an addition. Do not rephrase what is already covered or move a rejected proposal elsewhere just to retain it. Uncertain value is a reason to omit it, not to ask the human to filter it.

## Check what is already there

Read `docs/decisions.md`, `docs/pitfalls.md`, the ADRs in `docs/adr/` and the tool and machine sections of the handbook's `topics/pitfalls.md` (in the `dev-standards-handbook` skill). For a workflow candidate, also read the existing skill and the relevant procedure it references before deciding there is a gap.

- A decision an ADR already holds: skip it.
- The same qualifying trap again: propose bumping its `seen` count, not a new line.
- A decision that reverses an earlier line: propose filling in `superseded by:` on the old line, as well as the new line.
- An existing trap line whose trap this session shows is now fixed at the source (a hook, a script, a preflight step): propose deleting it. The human says yes or no to each deletion, as to any line. List any others that look ready for the same ending, so the files shrink. Only a line that carries `seen:` may be deleted. A decision is never deleted, only superseded.

## Route

| Found                                                                     | Goes to                                                                                              |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| A decision                                                                | `docs/decisions.md`. If it passes the ADR test (hard to reverse, surprising without context, the result of a real trade-off), offer an architecture decision record (ADR) instead |
| A qualifying repo-specific constraint or trap                             | `docs/pitfalls.md`                                                                                   |
| A demonstrated gap or error in an existing workflow skill                 | A targeted correction to the owning `SKILL.md` or referenced procedure                               |
| A qualifying trap in a shared tool or machine                             | the handbook's `topics/pitfalls.md`, under its tool's heading                                            |
| A wrong instruction                                                       | a proposed edit to that file                                                                         |
| A decision, change of scope or blocker its ticket does not record         | a comment on that ticket, or an edit to its description for a change of scope                        |
| A line in the repo's agent instructions that is now untrue or out of date | a proposed edit to that line. Where the setup itself no longer fits the project, propose running the `set-up-sdlc` skill again |

Prefer correcting the owning procedure over copying the same lesson into several destinations. Routing does not rescue a candidate that failed selection.

## Ask, line by line

Only if proposals survive selection, send one short message, grouped by destination. Each item is a proposed line in the shape `docs/agents/domain.md` gives, a targeted instruction edit, or a proposed deletion, numbered so the human can answer "1 yes, 2 no…". Give each proposed line its tags: use tags already in that file before making a new one. The part of the line before its first named field must make sense by itself, because that part is all a new session is shown. Put any detail beneath the line, indented, not on it. State what useful new information each adds and why it belongs there. Write it in plain English and gloss every ticket id and file name the first time. Nothing is written without a yes, and anything the human declines is dropped.

## Write

- **Repo changes** (decisions, pitfalls, instruction fixes including repo-local skills, and deletions) land in one pull request: the stream's last pull request if there is one and it has not merged, otherwise a small docs pull request. Its body lists each approved change under "Approved in a session wrap-up on <date>", so a reviewer can see the human said yes.
- **Shared-skill edits and handbook lines** land as one change in the skills repo (`~/.agents/skills`). Leave it uncommitted: the human commits and pushes it from their own profile.

## Never copy a secret

Transcripts contain keys, tokens and passwords. Never quote one, in the message to the human or in a line. A pitfall about a credential names where it lives (the secret's name, the file), never its value.
