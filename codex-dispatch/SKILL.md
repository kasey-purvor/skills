---
name: codex-dispatch
description: Runs OpenAI Codex non-interactively from another agent's shell, either as a sub-agent that plans, builds or reviews, or for a one-off question or command, and leaves a live event log and a structured final report the caller can read. Use when delegating work to Codex, launching `codex exec`, checking on, resuming or debugging a Codex run, or when the user mentions Codex, Astra or Sol as a sub-agent or builder.
---

# Codex dispatch

`codex exec` runs Codex headless. It loads `~/.codex/config.toml` exactly as an interactive
session does: model, reasoning effort, approvals, sandbox, MCP servers, hooks and the global
`~/.codex/AGENTS.md`. Flags override a setting for that one run only, so never edit the
config to change one run. See the current defaults with `sed -n '1,8p' ~/.codex/config.toml`.

## Pick the shape

| Need | Shape |
|---|---|
| A quick answer or inspection | One-off: foreground, `-s read-only`, `--ephemeral` |
| A plan or a review | Sub-agent: read-only, `gpt-6.1-sol` at `xhigh`, `plan` or `review` schema |
| Code written and committed | Sub-agent: background, dedicated worktree, `build` schema |

## One-off command

```bash
codex exec -s read-only --ephemeral -c model_reasoning_effort=low \
  -o "$SCRATCH/answer.md" "Read AGENTS.md and say which command runs the full check." \
  </dev/null >"$SCRATCH/oneoff.log" 2>&1
cat "$SCRATCH/answer.md"
```

## Sub-agent run

Use the launcher. It names every file after `--name`, keeps stdin safe, and prints the
thread id, token use and working-tree state when the run ends.

```bash
K=~/.claude/skills/codex-dispatch
$K/scripts/codex-run.sh --name con-123-build --dir /abs/path/.claude/worktrees/con-123 \
  --out "$SCRATCH" --prompt-file "$SCRATCH/con-123-brief.md" \
  --schema $K/templates/build.schema.json --model gpt-6.1-sol --effort xhigh
```

- **Run builds in the background** with your harness's background option, such as Claude
  Code's `run_in_background`. You are notified when it exits; do not poll on a timer.
- **Planner and reviewer runs** add `--sandbox read-only` and use `plan.schema.json` or
  `review.schema.json`.
- **Start every `--name` with the ticket id.** Scratch directories are often shared by
  several lanes, and a generic name mixes their logs.
- **Write the brief from `templates/build.brief.md`.** Codex cannot see your conversation
  or the ticket tracker, so paste the full ticket, its decision comments, the worktree
  path, the check command and the gates. A thin brief is the most common cause of a bad run.

## While it runs

- `scripts/codex-status.sh <name>.events.jsonl` summarises state, failed commands,
  changed files, token use and the latest steps. It is safe mid-run.
- To wake only on events that matter, watch the events file for `turn.failed`, `error`
  or `turn.completed` if your harness has a monitor tool.
- Non-zero commands are normal early in a test-first run: the failing test is meant to fail.

## When it finishes

1. **Trust git, not the report.** Read `git log` and the diff in the worktree, and
   check the report's claims against them.
2. **A fix round gets a fresh run** with the findings, the ticket and "read the code as it
   stands". Do not resume the earlier run for it.
3. **Relay what matters** to the person you work for: what shipped, what is unverified,
   and any `blocked_reason` or `open_questions`.

## Models

List what the account offers with
`jq -r '.models[] | "\(.slug)\t\(.description)"' ~/.codex/models_cache.json`.
Use `gpt-6.1-sol` at `xhigh` effort for planning, building and review. `gpt-6-astra` was
the frontier model when this was written: use it only when the human asks for it.
`gpt-6-luna` suits research and one-offs. Effort runs from `low` to `max`. Low effort on an easy task often skips reasoning,
so expect no reasoning summaries there.

## Rules

- **One writer per directory.** A run that can write gets its own worktree, so two runs
  never edit the same checkout. Everything else runs with `--sandbox read-only`.
- **Never launch bare `codex`.** The interactive app waits for a keyboard and hangs an
  agent. Always use `codex exec`, with stdin from a file or `/dev/null`.
- **Never restart or reconfigure Codex's background server.** Other sessions share it.
  If Codex asks to restart it, stop and tell the person you work for.
- **Codex has no ticket-tracker access.** The orchestrator reads tickets and posts evidence.
- **Repo hooks still apply inside Codex.** A branch behind `origin/main` gets its commands
  blocked, so the brief tells Codex to merge main first.

Flags, the event format, session files and troubleshooting: [reference.md](reference.md).
