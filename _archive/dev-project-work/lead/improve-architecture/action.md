# Find Deepening Opportunities — Playbook

Loaded only when the **Find Deepening Opportunities** action fires (see `lead.md` Actions). The goal: surface architectural friction in the codebase as **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

This action is _informed by_ the project's durable truth — it reads `.context/project/vocabulary.md`, `.context/project/domain.md` (if it exists), and ADRs in `.context/decisions/`. The vocabulary gives names to good seams; ADRs record decisions the action should not re-litigate.

---

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point — don't drift into "component," "service," "API," or "boundary." Full definitions in [language.md](./language.md).

- **Module** — anything with an interface and an implementation (function, class, package, slice).
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** — the code inside.
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary.")
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers get from depth.
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles (see [language.md](./language.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

---

## When to invoke

Trigger Find Deepening Opportunities when:

- The user asks to improve architecture, find refactoring opportunities, consolidate tightly-coupled modules, or make a codebase more testable
- The user complains about test friction — "I can't test this without mocking five things", "the tests are brittle and break on every change"
- The user describes navigation friction — "I have to bounce between six files to understand what happens when X"
- A code review or sub-agent finding flags shallow modules masquerading as architecture
- The user explicitly asks for an "architecture audit", "deepening pass", or "refactor opportunities"

This is *not* a one-shot global refactor. It surfaces candidates and grills one at a time. If the project needs a wider sweep, run multiple focused passes.

---

## Posture

The action runs in three sequential stages — **Explore**, **Present candidates**, **Grilling loop**. Don't propose interfaces in stages 1 or 2; that work belongs to the grilling loop and (optionally) the parallel sub-agent pattern in [interface-design.md](./interface-design.md).

---

## Process

### 1. Explore

Read existing durable truth first:

- `.context/project/vocabulary.md` (canonical names — drives how candidates are described)
- `.context/project/domain.md` (if it exists — structural domain knowledge, useful for spotting natural seams)
- Relevant ADRs in `.context/decisions/` (decisions the action must not re-litigate)

If any of these files don't exist, proceed silently — don't flag their absence or suggest creating them upfront. The action degrades gracefully: without `vocabulary.md`, candidates are described in plainer language; the architecture vocabulary in [language.md](./language.md) still applies.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present candidates

Present a numbered list of deepening opportunities. For each candidate:

- **Files** — which files/modules are involved
- **Problem** — why the current architecture is causing friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality and leverage, and also in how tests would improve

**Use `vocabulary.md` for the domain, and [language.md](./language.md) for the architecture.** If `vocabulary.md` defines "Order," talk about "the Order intake module" — not "the FooBarHandler," and not "the Order service."

**ADR conflicts**: if a candidate contradicts an existing ADR in `.context/decisions/`, only surface it when the friction is real enough to warrant revisiting the ADR. Mark it clearly (e.g. _"contradicts ADR-0007 — but worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

Do NOT propose interfaces yet. Ask the user: *"Which of these would you like to explore?"*

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive. See [deepening.md](./deepening.md) for how to classify dependencies and choose a testing strategy.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in `vocabulary.md`?** Add the term to `vocabulary.md` (canonical name + one-line definition + `_Avoid_` aliases) — same discipline as the **Sharpen Vocabulary** action. See `dev-project-work/SKILL.md` "vocabulary.md" section for format. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `vocabulary.md` right there.
- **Surfacing structural domain knowledge** (e.g., entity lifecycle, real-world process) that informs the seam? Update `.context/project/domain.md` if it exists; if not, ask the user whether to create it. (Don't create `domain.md` unilaterally — it's an optional file in this skill's system.)
- **User rejects the candidate with a load-bearing reason?** Hand off to the **Record Decision** action (see `lead/record-decision.md`). Frame as: *"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"* Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones. The Record Decision playbook applies the three-question filter; don't write ADRs from inside this action directly.
- **Want to explore alternative interfaces for the deepened module?** See [interface-design.md](./interface-design.md) for the parallel sub-agent pattern (Ousterhout's "Design It Twice").

---

## Wrap-up

When the user has settled on a deepening (or chosen to defer one):

1. **Summarise to the user** what was decided: the candidate chosen, the seam shape, the testing strategy, any vocabulary additions made inline, any ADRs offered.
2. **If the deepening will be implemented now**, switch out of this action and into Sprint mode (or Direct mode for small refactors). The action surfaces opportunities; Sprint/Direct mode executes them.
3. **If the deepening is deferred**, add it to `backlog.md` under the appropriate cluster — don't lose it.
4. **Note in HANDOFF** if any in-scope candidates were left unresolved.

---

## What this action is NOT

- **Not a one-shot full-codebase refactor.** It surfaces a numbered list, then grills one candidate at a time. If the project needs broad change, run multiple sessions.
- **Not a substitute for ADRs.** When a candidate is rejected with a load-bearing reason, hand to **Record Decision**. When a candidate is accepted with a non-obvious shape (port placement, transport choice), hand to **Record Decision** after the grilling loop resolves.
- **Not a substitute for vocabulary work.** Inline vocabulary additions are fine, but if the grilling reveals systemic naming drift across an area, switch to **Sharpen Vocabulary** for a focused pass before continuing.
- **Not a place to design interfaces from cold.** First propose a candidate (the *what*), grill the user on constraints (the *why*), and only then sketch interfaces. For genuinely hard interface choices, use [interface-design.md](./interface-design.md)'s parallel sub-agent pattern rather than guessing.
- **Not a code-modification action.** The output is a discussed deepening with shape and testing strategy. Implementation happens in Sprint or Direct mode, with the deepening either becoming a chunk scope (Sprint) or a small refactor (Direct).
