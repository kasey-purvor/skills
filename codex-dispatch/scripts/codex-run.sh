#!/usr/bin/env bash
# Launch one non-interactive Codex run and leave files an orchestrating agent can read.
#
# Writes, under --out:
#   <name>.events.jsonl   live event stream (one JSON object per line)
#   <name>.report.json    final message, when --schema is given
#   <name>.report.md      final message, otherwise
#   <name>.stderr.log     Codex's own diagnostics
# and prints a short summary when the run ends. Run it in the background from your
# harness so you are notified on exit; check progress with codex-status.sh.

set -uo pipefail

usage() {
  cat <<'EOF'
Usage: codex-run.sh --name <label> --dir <abs path> --out <abs dir>
                    (--prompt <text> | --prompt-file <file>)
                    [--model <slug>] [--effort <low|medium|high|xhigh|max>]
                    [--sandbox <read-only|workspace-write|danger-full-access>]
                    [--schema <file>] [--resume <thread id>] [--ephemeral]

  --name         Log prefix. Start it with the ticket id (con-123-build), because
                 scratch directories are often shared by several runs.
  --dir          Directory Codex works in. For any run that writes, a dedicated worktree.
  --out          Directory for the events, report and stderr files.
  --resume       Continue an earlier Codex session instead of starting a new one.
  --ephemeral    Do not save the session to ~/.codex/sessions (it cannot be resumed).
Anything not given falls back to ~/.codex/config.toml.
EOF
  exit "${1:-0}"
}

name="" dir="" out="" prompt="" prompt_file="" model="" effort="" sandbox="" schema="" resume="" ephemeral=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) name="$2"; shift 2 ;;
    --dir) dir="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --prompt) prompt="$2"; shift 2 ;;
    --prompt-file) prompt_file="$2"; shift 2 ;;
    --model) model="$2"; shift 2 ;;
    --effort) effort="$2"; shift 2 ;;
    --sandbox) sandbox="$2"; shift 2 ;;
    --schema) schema="$2"; shift 2 ;;
    --resume) resume="$2"; shift 2 ;;
    --ephemeral) ephemeral=1; shift ;;
    -h|--help) usage 0 ;;
    *) echo "codex-run: unknown argument: $1" >&2; usage 2 ;;
  esac
done

die() { echo "codex-run: $*" >&2; exit 2; }
[[ -n "$name" && -n "$dir" && -n "$out" ]] || die "--name, --dir and --out are required"
[[ -n "$prompt" || -n "$prompt_file" ]] || die "give --prompt or --prompt-file"
[[ -z "$prompt" || -z "$prompt_file" ]] || die "give only one of --prompt and --prompt-file"
[[ -d "$dir" ]] || die "--dir does not exist: $dir"
[[ -z "$prompt_file" || -f "$prompt_file" ]] || die "--prompt-file not found: $prompt_file"
[[ -z "$schema" || -f "$schema" ]] || die "--schema not found: $schema"
[[ "$resume" == "" || "$ephemeral" == 0 ]] || die "--resume and --ephemeral do not mix"
command -v codex >/dev/null || die "codex is not on PATH"
command -v jq >/dev/null || die "jq is not on PATH"
mkdir -p "$out"

events="$out/$name.events.jsonl"
stderr_log="$out/$name.stderr.log"
if [[ -n "$schema" ]]; then report="$out/$name.report.json"; else report="$out/$name.report.md"; fi

args=(exec)
[[ -n "$resume" ]] && args+=(resume)
args+=(--json -o "$report")
[[ -n "$model" ]] && args+=(-m "$model")
[[ -n "$effort" ]] && args+=(-c "model_reasoning_effort=$effort")
# -c works for both new and resumed sessions, unlike -s.
[[ -n "$sandbox" ]] && args+=(-c "sandbox_mode=\"$sandbox\"")
[[ -n "$schema" ]] && args+=(--output-schema "$schema")
[[ "$ephemeral" == 1 ]] && args+=(--ephemeral)
[[ -n "$resume" ]] && args+=("$resume")

# The prompt goes in last. Stdin is always a file or /dev/null: an open terminal on
# stdin makes Codex wait for more input.
if [[ -n "$prompt_file" ]]; then
  args+=(-)
  stdin_src="$prompt_file"
else
  args+=("$prompt")
  stdin_src=/dev/null
fi

echo "codex-run: $name started $(date '+%F %T') in $dir"
echo "codex-run: events $events"
( cd "$dir" && codex "${args[@]}" <"$stdin_src" >"$events" 2>"$stderr_log" )
code=$?

thread=$(jq -r 'select(.type=="thread.started") | .thread_id' "$events" 2>/dev/null | head -1)
usage_line=$(jq -r 'select(.type=="turn.completed") | .usage | "tokens in=\(.input_tokens) cached=\(.cached_input_tokens) out=\(.output_tokens) reasoning=\(.reasoning_output_tokens)"' "$events" 2>/dev/null | tail -1)
failed=$(jq -r 'select(.type=="turn.failed" or .type=="error") | (.error.message // .message // "error")' "$events" 2>/dev/null | tail -1)

echo "codex-run: $name finished $(date '+%F %T') exit=$code"
echo "codex-run: thread ${thread:-unknown}"
[[ -n "$usage_line" ]] && echo "codex-run: $usage_line"
[[ -n "$failed" ]] && echo "codex-run: FAILED: $failed"
if [[ -s "$report" ]]; then echo "codex-run: report $report"; else echo "codex-run: no report written; see $stderr_log"; fi
if git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then
  echo "codex-run: working tree now:"
  git -C "$dir" status --short | head -20
fi
exit "$code"
