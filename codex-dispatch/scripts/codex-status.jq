# Summarise a slurped array of Codex `exec --json` events. Used by codex-status.sh.
def trunc(k): if (.|length) > k then .[0:k] + "..." else . end;
# Drop the shell wrapper and leading cd that Codex puts around every command.
def short: sub("^\\S+ -lc \""; "") | sub("\"$"; "") | sub("^cd '[^']*' && "; "") | gsub("\n"; " ");

(map(select(.type=="thread.started"))[0].thread_id // "unknown") as $thread
| (map(select(.type=="turn.failed" or .type=="error"))) as $fails
| (map(select(.type=="turn.completed"))) as $done
| (map(select(.type=="item.completed")) | map(.item)) as $items
| ($items | map(select(.type=="command_execution"))) as $cmds
| ($cmds | map(select((.exit_code // 0) != 0))) as $badcmds
| ($items | map(select(.type=="file_change")) | map(.changes[]?.path) | unique) as $files
| "state:    " + (if ($fails|length) > 0 then "FAILED" elif ($done|length) > 0 then "finished" else "running" end),
  "thread:   " + $thread,
  "commands: \($cmds|length) run, \($badcmds|length) non-zero exit",
  "files:    \($files|length) changed",
  ($files[] | "  " + .),
  (if ($badcmds|length) > 0 then "non-zero commands (latest 5):" else empty end),
  ($badcmds[-5:][] | "  exit \(.exit_code): " + (.command | short | trunc(160))),
  (if ($fails|length) > 0 then "error: " + ($fails[-1] | (.error.message // .message // tostring)) else empty end),
  (if ($done|length) > 0 then "usage:    " + ($done[-1].usage | "in=\(.input_tokens) out=\(.output_tokens) reasoning=\(.reasoning_output_tokens)") else empty end),
  "recent:",
  ($items[-$n:][] |
    if .type=="agent_message" then "  say:    " + (.text | gsub("\n";" ") | trunc(200))
    elif .type=="reasoning" then "  think:  " + (.text | gsub("\n";" ") | trunc(200))
    elif .type=="command_execution" then "  run:    [\(.exit_code // "?")] " + (.command | short | trunc(160))
    elif .type=="file_change" then "  edit:   " + ([.changes[]? | "\(.kind) \(.path)"] | join(", ") | trunc(200))
    else "  " + .type
    end)
