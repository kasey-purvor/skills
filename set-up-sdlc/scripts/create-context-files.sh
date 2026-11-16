#!/usr/bin/env bash
# Creates a repo's context files and folders, once, at setup.
# Usage: create-context-files.sh [repo-root]   (default: the current folder)
# Creates only what is missing. Never overwrites or changes an existing file.
set -euo pipefail

root="${1:-.}"
skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! git -C "$root" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "error: $root is not inside a git repository" >&2
  exit 1
fi
cd "$(git -C "$root" rev-parse --show-toplevel)"

made=()
kept=()

write_if_missing() { # path, content
  if [ -e "$1" ]; then
    kept+=("$1")
  else
    mkdir -p "$(dirname "$1")"
    printf '%s' "$2" > "$1"
    made+=("$1")
  fi
}

write_if_missing "CONTEXT.md" "# Context

The vocabulary of this product: each term and what it means. Nothing about how things are built. Rules: \`docs/agents/domain.md\`.
"

write_if_missing "docs/decisions.md" "# Decisions

Rulings the human made that no ADR covers, one line each, newest last. Rules and line shape: \`docs/agents/domain.md\`.
"

write_if_missing "docs/pitfalls.md" "# Pitfalls

Traps in this repo that cost an agent time and will recur, one line each. Rules and line shape: \`docs/agents/domain.md\`.
"

if [ -d "docs/adr" ]; then
  kept+=("docs/adr/")
else
  mkdir -p docs/adr
  : > docs/adr/.gitkeep
  made+=("docs/adr/")
fi

if [ -d "docs/PRD" ]; then
  kept+=("docs/PRD/")
else
  mkdir -p docs/PRD
  : > docs/PRD/.gitkeep
  made+=("docs/PRD/")
fi

if [ -e "docs/agents/domain.md" ]; then
  kept+=("docs/agents/domain.md")
else
  mkdir -p docs/agents
  cp "$skill_dir/domain.md" docs/agents/domain.md
  made+=("docs/agents/domain.md")
fi

echo "Created:"
if [ ${#made[@]} -eq 0 ]; then echo "  nothing"; else printf '  %s\n' "${made[@]}"; fi
echo "Already there, left alone:"
if [ ${#kept[@]} -eq 0 ]; then echo "  nothing"; else printf '  %s\n' "${kept[@]}"; fi
