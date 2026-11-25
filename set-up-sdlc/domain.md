# The context files

A context file is a markdown file that agents and people read to understand this project. It is not code and it is not a ticket. This file holds the rules for all of them: what each is for, what goes in it, and how it is changed.

## The files

| File | Holds | Does not hold |
| --- | --- | --- |
| `AGENTS.md` | What every session needs before any task. | How-tos for one task. How the code is built. |
| `CONTEXT.md` | The vocabulary: each term of the product and what it means. | Anything about how things are built. |
| `docs/adr/` | One file for each ruling that is hard to reverse, surprising without its reason, and came from a real choice between options. | Descriptions of the code, measurements, a ticket's story. |
| `docs/decisions.md` | Rulings the human made that no ADR covers, one line each. | Anything an ADR already says. It may point at an ADR, never add to one. |
| `docs/pitfalls.md` | Traps in this repo that cost an agent time and will recur, one line each. | Traps in shared tools and machines: those go in the handbook's `topics/pitfalls.md`. |
| `docs/PRD/` | Requirements documents, one file for each agreed idea, written with the `to-prd` skill. | Decisions made after the document was written: those go on the tickets. |
| `README.md` | What the project is and how to get it running. | Text moved out of the other files. |

A repo with several separate parts may have a `CONTEXT-MAP.md` at the root, pointing at one `CONTEXT.md` for each part.

## Who may write what

Nothing in these files is added, changed or removed until the human has said yes to that specific change.

| File | Who writes it | When |
| --- | --- | --- |
| `AGENTS.md` | The main agent | In a `session-wrap-up`, when a line is proved wrong; or when the human decides a table row. |
| `CONTEXT.md` | The main agent | Whenever a new term appears or an inconsistency is found: proposed to the human, and written only on their yes. |
| `docs/adr/` | The main agent | In `grill-with-docs` or `improve-codebase-architecture`, for a ruling that passes the ADR test in the table above. `session-wrap-up` may also offer one. |
| `docs/decisions.md` | The main agent | In a `session-wrap-up` only. |
| `docs/pitfalls.md` | The main agent | In a `session-wrap-up` only, deletions included. |
| `docs/PRD/` | The main agent | In `to-prd`. |
| `docs/agents/domain.md` | The main agent | When the setup template changes. |
| `README.md` | The main agent, never a subagent | When what it describes changes. |
| A new context file, notes file, planning document, log or folder for them | Nobody, without asking first | |

There is one exception. When a ticket or plan the human approved carries the exact new wording of an ADR, a builder lands it unchanged, without asking again.

A requirements document is written only when the human asks for one with `to-prd`. That request is the yes for that one file.

Subagents never write to any of these files otherwise. A builder, reviewer or verifier reports what it found, and the main agent proposes it.

Nothing goes into decisions or pitfalls that the human did not decide or an agent did not actually hit. A trap in a shared tool or machine does not go in this repo: `session-wrap-up` proposes it for the handbook's `topics/pitfalls.md`.

## Where a thing goes

- Try the specific files first: the vocabulary, an ADR, decisions, pitfalls, a handbook chapter. Nothing goes in `AGENTS.md` that one of those would take.
- A script's manual lives in the script: its header, its help text and its error messages.
- One-time work stays on its ticket.
- If a thing fits none of these files, it stays as a comment on the ticket. Do not make another file for it.

## Reading them

- Read `docs/decisions.md` and `docs/pitfalls.md` before the first command of a piece of work, and the tool and machine traps in the handbook's `topics/pitfalls.md` with them.
- If a hook put these files in your context when the session started, you have read them: do not read them again. Open a file only for the reason or the detail behind a line.
- Read `CONTEXT.md` and the ADRs that touch the area you are about to work in.
- Use the vocabulary's terms when you name a concept in a ticket, a test or a proposal. If the term you need is not there, either you are inventing language the project does not use, or there is a gap to raise with the human.
- If your work goes against an ADR or a decisions line, say so plainly. Do not quietly go against it.

## The vocabulary (`CONTEXT.md`)

One entry for each term: the term, what it means in this product, the words to avoid for it, and how it relates to other terms where that matters. No example dialogues, no implementation, no plans, no decisions.

## ADRs

- An ADR holds three things: the ruling, the reason, and the options turned down.
- The ruling sits at the top. When it changes, the top is rewritten in the same edit. It is never added to underneath.
- A test for any sentence: would it still be true if the code were rewritten another way? If not, it does not belong.
- A ruling lives in one place.

## The shape of a line

A decision and a pitfall are written the same way: one line, with any detail beneath it.

```
YYYY-MM-DD · [tags] · <headline> · <named fields>
  Detail, if any, goes beneath the line, indented two spaces.
```

- **The date** comes first, on every line.
- **The tags** name the areas the line is about, in square brackets with commas between: `[api, routing]`. Any word may be a tag. Use one that is already in the file before you make a new one.
- **The headline** must make sense by itself. At the start of a session a hook shows agents each line up to its first named field, and nothing after it.
- **The named fields** come last. Each section below says which ones its lines carry. `see:` may be added to any line, to point at a file or an ADR.
- **Detail** never goes on the line. Put it beneath, indented, and keep it short.

## Decisions (`docs/decisions.md`)

A ruling the human made that is settled but does not earn an ADR: what is in scope, what is never built, how a feature should feel. One line each, newest last:

```
YYYY-MM-DD · [tags] · <decision> · why: <reason> · from: <ticket, ADR or "chat"> · superseded by: <date or —>
```

A reversed decision is not deleted. Fill in `superseded by:` on the old line and add the new line at the end.

## Pitfalls (`docs/pitfalls.md`)

A trap in this repo's code, hooks, scripts or tests that cost an agent time and will recur. One line each:

```
YYYY-MM-DD · [tags] · <symptom, plainly> → <fix or rule> · seen: N · source: <measured | read in code | an agent's word | the human said>
```

- The date is when the trap was first seen. Before adding a line, look for the same symptom. If it is there, raise `seen` instead.
- This file is an inbox, not an archive. A line stays until the trap is fixed at its source (a hook, a script or a check now stops it), and then it is deleted.
