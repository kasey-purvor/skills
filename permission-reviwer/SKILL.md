---
name: util-permission-helper
description: Help add commands to the permission allow list with appropriate wildcard patterns. Use when asked about permissions, allow lists, or after repeated permission prompts.
---

# Permission Helper

Guide the user through adding permissions thoughtfully.

## Step 1: Offer Consolidation Review (Optional)

Ask:
> Before adding new permissions, want me to review your existing allow list for consolidation opportunities? This spawns a quick sub-agent to analyze patterns. [y/n]

**If yes:** Use the Task tool to spawn a sub-agent with this prompt:
```
Read ~/.claude/settings.json and examine the permissions.allow array.
Report back with:
1. Total count of rules
2. Any overly specific entries that could be wildcarded (e.g., multiple git -C /specific/path commands)
3. Redundant entries already covered by existing wildcards
4. Suggested consolidations with before/after

Be terse. Format as a short table or bullet list.
```

Present the sub-agent's findings to the user and ask which consolidations to apply.

**If no:** Skip to Step 2.

## Step 2: Analyze and Present Commands

**MANDATORY - You MUST do all of this before presenting to the user:**

1. **Read `~/.claude/settings.json`** to get existing `permissions.allow` rules
2. **Collect ALL bash commands** from this session that required or would require permission
3. **For each command**, check if any existing rule covers it
4. **Build the table** with wildcard options at three levels

**Present this table:**

| # | Command | Covered? | Specific | Moderate | Broad | Notes |
|---|---------|----------|----------|----------|-------|-------|
| 1 | `git clone https://github.com/user/repo` | ✓ `git clone:*` | — | — | — | Already covered |
| 2 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | ✗ | `curl -LsSf https://astral.sh/* \| sh` | — | `curl:*` | **Rec: Specific.** ⚠️ High risk - pipes to shell |
| 3 | `mkdir -p ~/projects/foo` | ✗ | `mkdir -p ~/projects/foo` | `mkdir:*` | — | **Rec: Moderate.** Low risk |
| 4 | `mv ~/.claude/skills/old new` | ✗ | `mv ~/.claude/skills/old new` | `mv ~/.claude/*` | `mv:*` | **Rec: Moderate.** Scoped to config dir |

**Column definitions:**

- **#** - Row number for easy reference
- **Command** - The actual command that was run
- **Covered?** - Shows existing rule if covered, ✗ if not
- **Specific** - Exact command or narrow pattern (leave blank if covered)
- **Moderate** - Balanced wildcard pattern (leave blank if no sensible middle ground)
- **Broad** - Widest reasonable pattern (leave blank if moderate is already broadest)
- **Notes** - Recommendation (which level), reasoning, and risk assessment

**Wildcard guidance:**

- Leave columns blank when that level doesn't make sense
- High-risk patterns (pipes to shell, rm -rf, etc.) should recommend Specific
- Low-risk patterns (mkdir, ls, cat) can recommend Moderate or Broad
- When moderate and broad would be the same, only fill Moderate

**If no commands in current session**, ask:
> What command or action are you trying to allow?

## Step 3: Get User Selection

Ask:
> Which rules do you want to add?

The user can respond in any format - interpret their intent. Examples:
- "2 specific, 3 and 4 moderate"
- "all recommended"
- "2S 3M 4M"
- "just the mkdir one, broad"
- "skip curl, do the rest as recommended"
- "none"

Parse their response and proceed to Step 4.

## Step 4: Confirm and Add

For each rule the user selected, show:

```
Adding to ~/.claude/settings.json:
  Bash(mkdir:*)
  Bash(mv ~/.claude/*)

Proceed? [y/n]
```

Edit `~/.claude/settings.json` to add the rules to `permissions.allow`.

## Notes

- Always USER-level (`~/.claude/settings.json`)
- Changes apply immediately (no restart needed)
- When a command is already covered, no action needed for that row
