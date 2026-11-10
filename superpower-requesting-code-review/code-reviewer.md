# Reviewer handoff

Compatibility template for workflows that already supply these fields. The shared [change-review](../change-review/SKILL.md) skill owns the procedure, handbook routing, report and worker boundaries.

Give a fresh reviewer this focused assignment:

- Load /home/kasey/.agents/skills/change-review/SKILL.md and follow assigned-reviewer mode.
- Change: {DESCRIPTION}
- Requirements or plan: {PLAN_OR_REQUIREMENTS}
- Base: {BASE_SHA}
- Target: {HEAD_SHA}
- Checkout and any dirty-tree fingerprint: supply explicitly when applicable.
- Existing verification evidence and scoped access: supply the actual results and boundaries.

The coordinator resolves these fields before dispatch. For a working tree or files outside Git, supply the explicit snapshot/target instead of inventing commit ids. Use current user model/effort instructions.

Return the review target, selected handbook chapters, verified ranked findings and coverage gaps to the coordinator. Do not edit code or tracker records, dispatch subagents, or infer permission to push/merge. The stream findings procedure owns disposition.
