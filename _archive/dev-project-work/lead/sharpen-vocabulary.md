# Sharpen Vocabulary — Playbook

Loaded only when the **Sharpen Vocabulary** action fires (see `lead.md` Actions). The goal: drag terminology in a chosen scope from "fuzzy and inconsistent" to "precise, opinionated, and shared." Output is updates to `.context/project/vocabulary.md` and, where a question can't be resolved, entries in `design.md` Open Questions.

---

## When to invoke

Trigger Sharpen Vocabulary when:

- A new conceptual area is being designed and you want its language nailed down before behaviour decisions ride on it
- The user is oscillating between two or more words for what seems like one concept ("task" / "ticket" / "chunk") — sharpen the area before the inconsistency propagates
- You're about to write a chunk scope or implementation plan and several terms feel slippery
- A code review or sub-agent finding flags terminology drift in code vs docs
- The user explicitly asks to "sharpen vocabulary", "lock down terms", "do a vocabulary pass", or similar

This is *not* a wholesale audit. Always scope it to a specific area: one feature, one workflow, one entity cluster. If the project needs a global sweep, run multiple focused passes — don't try to do everything in one session.

---

## Posture

Interview the user **relentlessly** until you reach a shared, opinionated answer for every in-scope term. Walk down each branch of the decision tree, resolving dependencies one-by-one. For each question:

- Provide your **recommended answer** with reasoning — don't ask open questions and wait
- Ask **one question at a time**, wait for feedback before moving on
- If a question can be answered by **exploring the codebase**, explore instead of asking
- If a question can be answered by **reading existing context files**, read instead of asking

The user's job is to confirm, correct, or push back. Your job is to never let a fuzzy term slide.

---

## Pre-session

1. **Re-read `.context/project/vocabulary.md`** (already loaded by startup reads, but re-confirm its current shape — terms covered, ambiguities flagged, relationships recorded)
2. **Identify and announce scope.** What area is being sharpened? Tell the user explicitly: *"I'm scoping this pass to [X]. I'll grill you on terms in this area only — anything outside scope I'll surface but defer."*
3. **Surface candidate terms.** Scan the recent conversation, the relevant context files, and the area in code. Make a short list of terms that look:
   - Ambiguous (one word used for multiple concepts)
   - Synonymous (multiple words used for one concept)
   - Missing (a concept clearly exists but has no canonical name)
   - Inconsistent with existing `vocabulary.md` entries
4. **Present the agenda** before grilling begins. Give the user a chance to add, remove, or re-prioritise terms before the deep work starts.

---

## Five techniques

Use each as the conversation calls for them. They overlap and chain — a single term might trigger all five before it's resolved.

### 1. Challenge against existing terminology

If the user uses a term that conflicts with `vocabulary.md`, call it out *the moment it happens*, not at the end of the discussion:

> *"Your vocabulary defines **Cancellation** as 'a buyer-initiated rollback before fulfillment'. You just used it for what sounds like a refund after delivery. Are these the same thing or do we need a second term?"*

Resolving the conflict while the example is fresh is much easier than reconstructing it later.

### 2. Sharpen fuzzy language

When the user uses a vague or overloaded term, propose a precise canonical term and ask which they mean:

> *"You're saying 'account' — do you mean the **Customer** (the person/org that places orders) or the **User** (an auth identity that logs in)? Those are different things in our model."*

Recommend the term that already exists in `vocabulary.md` if one fits. If neither fits, propose new canonical names with brief rationale.

### 3. Scenario probing

When relationships between terms are being discussed, **invent concrete scenarios** that probe edge cases and force the user to be precise about boundaries:

> *"Suppose a **Customer** has three **Orders**: one cancelled, one partially fulfilled, and one fully shipped. When you say 'their orders', do you mean all three or only the active two? And does an **Invoice** for the partial one exist yet?"*

The goal is to surface boundary cases *before* code is written that gets them wrong. Edge cases are where ambiguous terms cause the most damage.

### 4. Cross-reference with code

When the user states how something works, **check whether the code agrees**. If you find a contradiction, surface it:

> *"You said partial cancellation is supported. The code in `src/orders/cancel.ts` only cancels whole **Orders** — there's no per-line logic. Which is right — does the code need updating, or does the term need narrowing to 'whole-order cancellation'?"*

This isn't a full audit (use the **Vocabulary Audit** sub-agent for that — `sub-agents/vocabulary-audit-prompt.md`). It's spot-checks while a term is being discussed — verifying the user's mental model matches the code's behaviour.

### 5. Propose canonical names when missing

When a concept clearly exists but has no canonical name, **propose one** rather than letting it stay nameless:

> *"There's no name yet for the period between **Order Placed** and **Fulfillment Confirmed**. I'd call it the **Pending Window** because that's the phase where cancellation is still no-cost. Reasonable?"*

Don't wait for the user to coin terms — they often won't, and the concept stays implicit. Being implicit is exactly the failure mode this action exists to prevent. Be opinionated.

---

## Writing back to vocabulary.md

**Update inline, never batch.** When a term is resolved, write to `vocabulary.md` immediately, then continue grilling. Three reasons:

- The decision is freshest at the moment it's made
- If the session ends abruptly, the resolved decisions are captured
- The user sees the decision land — closes the loop, builds confidence the discussion is being recorded faithfully

### Format reminders

- **Be opinionated.** Pick one canonical term. List the rejected aliases under `_Avoid_:`. When the user prefers a term you wouldn't have chosen, defer to them — but make sure exactly one term is canonical
- **One sentence per definition.** What it IS, not what it does. Behaviour belongs in `design.md`, not in vocabulary entries
- **Show relationships** explicitly — bold the term names, express cardinality where obvious
- **Group under subheadings** when natural clusters emerge (e.g., `### Order Lifecycle`, `### Customer Identity`). A flat list is fine if no clusters exist yet
- **Don't include trivial implementation details that don't need a name.** A timeout value, retry count, or HTTP status code isn't a vocabulary term — it's a configuration value or schema detail. Vocabulary holds *names for concepts*, not all the concepts that exist
- **Don't define general programming concepts.** "Cache", "queue", "event" only belong if the project uses one of them in a *project-specific* way that needs distinguishing from the generic meaning

Write each entry like:

```markdown
**Pending Window**: the time between **Order Placed** and **Fulfillment Confirmed** during which the Order can be cancelled without penalty.
_Avoid_: grace period, holding period, pre-fulfillment window
```

### When ambiguity is resolved

If the session resolved an ambiguity (e.g., "we were using 'account' for both Customer and User — they're now distinct"), add a one-liner to **Recently Resolved Ambiguities** in `vocabulary.md` so future readers see the resolution path. Example:

```markdown
- "account" was used for both **Customer** and **User** — resolved 2026-04-27: these are distinct. Customer = ordering party, User = auth identity.
```

This isn't required for every change, but it's valuable when the previous usage is likely to come back.

---

## Wrap-up

When the in-scope terms are resolved:

1. **Summarise to the user** what was added/changed in `vocabulary.md`. List terms newly defined, terms whose definitions changed, and aliases newly explicitly avoided
2. **Capture unresolved questions in `design.md` Open Questions.** If a term couldn't be resolved without more information (domain expert, stakeholder decision, codebase clarification), record it as an Open Question — never leave a decision implicit. Cross-reference back: *"Open Question for `vocabulary.md`: is **Cancellation** one concept or two?"*
3. **Confirm scope close.** Ask the user: *"Anything else in this area that feels fuzzy?"* Don't expand the pass beyond the announced scope — but make sure nothing inside the chosen scope was skipped
4. **Note in HANDOFF** if any in-scope decisions were deferred to a future session, so the next Lead picks them up

---

## Worked example

Brief illustration of how a session might flow. *Not a script — the actual interview adapts to what the user says.*

> **Lead:** I'm scoping this pass to the **Order Lifecycle** area. From the recent conversation and `design.md`, I see ambiguity around 'cancellation' (used for two different things), 'order' vs 'cart' (might be the same concept), and there's no name yet for the gap between placing an order and shipment. Agenda look right?
>
> **User:** Yeah, plus I keep saying 'pending' for things in different states.
>
> **Lead:** Good catch — added. Let's start with cancellation. You used it twice today: once for "buyer changes their mind before we ship", once for "buyer wants a refund after delivery". I'd argue these are two different concepts — the first is **Cancellation** (no goods moved), the second is a **Return** (goods moved, need to come back). Recommend keeping **Cancellation** for the pre-shipment case only and using **Return** for post-delivery. Sound right?
>
> **User:** Agreed.
>
> *[Lead immediately writes to `vocabulary.md`:]*
> ```markdown
> **Cancellation**: a buyer-initiated rollback of an Order before any goods have shipped. Free of charge.
> _Avoid_: refund, abort, void
>
> **Return**: a buyer-initiated request to send delivered goods back for a refund.
> _Avoid_: refund, post-delivery cancellation
> ```
>
> **Lead:** Recently Resolved entry too — "cancellation" was overloaded; now distinct from Return. Next: 'order' vs 'cart'. The code has both — `Order` and `Cart` types in `src/`. Quick scenario: a buyer adds three items, removes one, places the request. Is the thing they 'placed' an **Order**? Is what existed before an **Order** or a **Cart**?
>
> *[and so on, walking each term...]*

---

## What this action is NOT

- **Not a global audit.** For systematic terminology-drift scanning across all context files and code, dispatch the **Vocabulary Audit** sub-agent (`sub-agents/vocabulary-audit-prompt.md`). It surfaces misuse, drift, gaps, stale entries, and incomplete coverage as evidence; Sharpen Vocabulary then resolves with the user. Audits find; grilling resolves
- **Not the place for design or architecture decisions.** If a vocabulary discussion exposes a design gap (e.g., "wait, do we even support partial cancellation?"), pause this action and switch to Design mode for that discussion. Resume the vocabulary pass once the design question is resolved
- **Not a one-shot for all terms.** Sharpening is iterative. Run multiple focused passes over time as new areas come into focus, rather than trying to lock down the entire vocabulary up front
- **Not for ADR-style decisions.** Hard-to-reverse, surprising, real-trade-off decisions go in their own ADR (`.context/decisions/`) via the Lead's Record Decision action. Vocabulary is naming, not decision-recording
