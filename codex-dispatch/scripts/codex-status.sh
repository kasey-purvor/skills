#!/usr/bin/env bash
# Summarise a Codex events file written by codex-run.sh (or by `codex exec --json`).
# Safe to run while Codex is still writing to it.
#
# Usage: codex-status.sh <name>.events.jsonl [number of recent items, default 8]

set -uo pipefail
events="${1:-}"
recent="${2:-8}"
[[ -f "$events" ]] || { echo "usage: codex-status.sh <events.jsonl> [recent]" >&2; exit 2; }
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# A run still being written can end in a half-written line; drop lines jq cannot parse.
jq -cR 'fromjson? // empty' "$events" | jq -rs --argjson n "$recent" -f "$here/codex-status.jq"
