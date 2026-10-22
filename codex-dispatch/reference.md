# Codex dispatch reference

## `codex exec` flags worth knowing

| Flag | Effect |
|---|---|
| `-m <slug>` | Model for this run |
| `-c model_reasoning_effort=<level>` | `low`, `medium`, `high`, `xhigh`, `max` |
| `-c model_reasoning_summary=<mode>` | `none`, `auto`, `detailed` |
| `-s <mode>` | Sandbox: `read-only`, `workspace-write`, `danger-full-access`. New runs only; on `resume` use `-c sandbox_mode="<mode>"` |
| `-C <dir>` | Working root (the launcher `cd`s instead, which also works for `resume`) |
| `--json` | Event stream as JSON lines on stdout |
| `-o <file>` | Write the final message to a file |
| `--output-schema <file>` | Force the final message to match a JSON Schema |
| `--ephemeral` | Do not save the session; it cannot be resumed |
| `--add-dir <dir>` | Extra writable directory |
| `-` as the prompt | Read the prompt from stdin |
| `exec resume <id> "<prompt>"` | Continue a saved session; the thread id stays the same |
| `exec review` | Codex's built-in review of the current repo |

Schemas must be strict: every object sets `"additionalProperties": false` and lists every
property in `required`. Use an empty string or array for "nothing", not an optional field.

## Event stream

Each line of `<name>.events.jsonl` is one event:

| `type` | Meaning |
|---|---|
| `thread.started` | Carries `thread_id`, the id used by `resume` |
| `turn.started` | The model began working |
| `item.started` / `item.completed` | One step; the step is in `.item` |
| `turn.completed` | Done; `.usage` holds input, cached, output and reasoning tokens |
| `turn.failed` / `error` | The run failed; the message is in `.error.message` or `.message` |

Step types in `.item.type`:

| Step | Useful fields |
|---|---|
| `agent_message` | `.text` |
| `reasoning` | `.text`, a summary heading; present only when summaries are on and the model reasoned |
| `command_execution` | `.command`, `.exit_code`, `.aggregated_output` |
| `file_change` | `.changes[]` with `.path` and `.kind` (`add`, `update`, `delete`) |

Handy queries:

```bash
jq -c 'select(.item.type=="command_execution" and .type=="item.completed") | {cmd: .item.command, exit: .item.exit_code}' f.jsonl
jq -r 'select(.item.type=="file_change" and .type=="item.completed") | .item.changes[].path' f.jsonl | sort -u
jq -r 'select(.item.type=="reasoning") | .item.text' f.jsonl
```

A human-readable live view for the person you work for, in its own tmux window:

```bash
tmux new-window -d -n con-123 "watch -n 15 ~/.claude/skills/codex-dispatch/scripts/codex-status.sh $SCRATCH/con-123-build.events.jsonl 15"
```

## Session files

Saved sessions live at `~/.codex/sessions/YYYY/MM/DD/rollout-<time>-<thread id>.jsonl`.
Lines of type `turn_context` record the model, effort and summary setting actually used.
Lines of type `response_item` hold the full transcript. The model's raw reasoning is stored
encrypted and cannot be read; only summaries are readable. A person can open a saved
session in the Codex app to read the whole run.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Reading additional input from stdin...` and then nothing | Stdin was left open. Redirect from a file or `/dev/null` |
| `Background server has incompatible feature settings` | The command-line tool and the shared background server are on different versions. Do not restart the server; tell the person you work for |
| `Codex could not find bubblewrap on PATH` | Harmless. Codex uses its bundled copy; it only matters in sandboxed runs |
| `Command blocked by PreToolUse hook: Orientation guard ... behind origin/main` | Merge `origin/main` into the branch, then rerun |
| `apply_patch verification failed` | Codex usually retries on its own. If it keeps failing, check that nothing else is editing the same worktree |
| No report file | The run failed before its final message. Read `<name>.stderr.log` and the last events |
| Report claims checks you cannot find in the events | Treat them as unverified and rerun the check yourself |
