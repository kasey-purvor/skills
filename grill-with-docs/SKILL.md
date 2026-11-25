---
name: grill-with-docs
description: Grilling session that challenges your plan against the existing domain model, sharpens terminology, and updates documentation (CONTEXT.md and ADRs as decisions crystallise). Use when user wants to stress-test a plan against their project's language and documented decisions.
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, also look for existing documentation:

### File structure

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   ├── adr/
│   │   ├── 0001-event-sourced-orders.md
│   │   └── 0002-postgres-for-write-model.md
│   └── decisions.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   ├── adr/                          ← system-wide decisions
│   └── decisions.md                  ← one at the repo root, never per context
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Setup creates these files. If one is missing, tell the human and suggest running the `set-up-sdlc` skill. Do not create it yourself. Who may write each file, and when, is in the repo's `docs/agents/domain.md`; every change needs the human's yes.

## During the session

### Challenge against the standards

One lens among the practices here — the grilling stays a broad design conversation, not a handbook compliance check. Early in the session, invoke the `dev-standards-handbook` skill and note which chapters the plan touches; when a decision lands in a chapter's territory, bring what it says into the discussion at a rigor matching the app's actual context. When the plan proposes a new module or reshapes how code is split, `topics/module-design.md` is worth its own challenge — apply the deletion test to each proposed module and ask what its interface hides. Raise gaps as questions, not verdicts, and keep grilling everything the handbook has nothing to say about.

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

When the plan goes against a line in `docs/decisions.md`, name it and ask whether it is being reversed.

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, propose its `CONTEXT.md` entry to the human right there and write it on their yes. Don't batch these up. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` should be totally devoid of implementation details. Do not treat `CONTEXT.md` as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else.

### Offer ADRs sparingly

Offer an ADR only for a ruling that passes the test in the repo's `docs/agents/domain.md`: hard to reverse, surprising without its reason, and a real choice between options. If any of the three is missing, skip it. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

### Decisions that don't earn an ADR

A decision the user made that fails the ADR test is still a decision. Record it on the ticket. It is not written to `docs/decisions.md` here: the repo's `docs/agents/domain.md` says how a line gets there.

</supporting-info>
