---
name: set-up-sdlc
description: Sets up a repo for this agent workflow with its owner, in one sitting. Writes the repo's agent instructions file, creates its context files, and builds the commit hook, CI, merge rules and scheduled runs that file describes. Use when setting up a new repo, bringing a repo that is already built into the workflow, or when a repo's stage changes and its git and CI/CD setup is due another look.
disable-model-invocation: true
---

# Set up a repo

You are setting up a repo with its owner. By the end the repo has its agent instructions file (`AGENTS.md`), its context files, and the checks that file describes, built and proved.

## Rules

- **A person must be there.** If nobody can answer you, stop. Never run this across several repos at once.
- **Look before you ask.** If the repo can answer a question, read the repo.
- **Propose, do not interview.** Draft the thing and ask whether it is right. One question at a time, each with your recommendation.
- **Reason from this repo and this product.** Never take a fact, a setting, a wording or a choice from another repo unless the owner says to. You may offer to look ("shall I look at how another repo does this?"), and you look only on a yes. Put this rule in the brief of any subagent you send.
- **The steps describe the usual case.** Where the repo is not as a step expects, use your judgement and tell the owner what you did. But never drop or loosen a rule this skill states without the owner's yes: a rule that is costly here is still the owner's to give up.
- **Fixed text is copied word for word.** Never reword it, trim it or improve it.
- **A worked-out section holds only what the owner agreed in this sitting.** If little was agreed, it stays short. Never pad it.
- **The example shows form only.** Its facts belong to another project. Never copy them.
- **Write nothing into the repo until the owner has said yes to it.**
- **Never change anyone's global instruction files.**

## The files

| File | What it is |
| --- | --- |
| [AGENTS-template.md](./AGENTS-template.md) | The fixed text, with its blanks and the sections to work out |
| [section-guide.md](./section-guide.md) | How to fill each blank and each small section |
| [git-and-cicd.md](./git-and-cicd.md) | The whole git and CI/CD part: what to ask, propose, write and build |
| [AGENTS-example.md](./AGENTS-example.md) | A finished file, for form only |
| [domain.md](./domain.md) | The rules for the context files, copied into the repo |
| `scripts/create-context-files.sh` | Creates the context files and folders |

## Steps

1. **Read** the template, the section guide and the example. Load the `dev-standards-handbook` skill too, and read the chapters that this sitting's choices touch before you propose them: the house standards are there.
2. **Look at the repo:** its remote, package files, CI workflows, commit hooks, and any notes, instruction files or context files already there. Tell the owner what you found. If it holds notes, reference documents or instruction files, follow "Notes and files already there" in the section guide. If the repo is already built, also follow "A repo that is already built".
3. **Create the context files.** On the owner's yes, run `scripts/create-context-files.sh <repo root>`. It creates only what is missing and reports what it did.
4. **Draft the agent instructions** from the template. Copy the fixed text and fill each blank as the section guide says.
5. **About this repo.** Follow its entry in the section guide.
6. **Git and CI/CD.** Follow `git-and-cicd.md`, parts 1 to 3. Then go back to "Where code goes" and name the check that enforces its boundaries.
7. **Scheduled runs.** Follow its entry in the section guide.
8. **Word the three building steps** that depend on the git answers: when a pull request is pushed and what happens if CI fails, who merges, and where a change is proved.
9. **Show the whole file** and write it on the owner's yes. Check that no bracket and no comment from the template is left in it.
10. **Build what the file describes.** Follow `git-and-cicd.md`, part 4.
11. **Finish.**
    - **The README.** If the repo has no `README.md`, draft one now that there is something to run: what the project is and how to get it running. Write it on the owner's yes.
    - **The setup ticket.** Create one ticket in the repo's team that records the sitting: what was agreed, and what was built and proved. It belongs to no epic. If the owner is still creating the team, this waits for it. Then move it to Done, as the `linear` skill says to close a ticket. Setup's own commits need no ticket of their own.
    - **The first epics.** Ask the owner which epics fit the work that comes first, and suggest a few from this conversation. Each is an outcome with an end, never a category. Create them on the owner's yes. The tickets agreed at any step of setup are held until now, and are filed under these epics.
    - Tell the owner what was written, what was built and proved, and what became tickets. If anything is still uncommitted, commit it when they ask.

## Running it again

The owner runs this again when the setup has stopped fitting the project: it is about to go live, say, or CI has become slow. A second run changes the part that brought the owner back and leaves the rest alone.

- **Find what brought the owner back.** If they have not said, ask that and nothing else. "When to raise the next step" in `git-and-cicd.md` says which part is due.
- **Read the repo's agent instructions before you ask anything.** What they say was agreed the first time, and it stands: it counts as agreed in this sitting. Never ask a question they already answer, and never reopen a section this run does not touch.
- **Work only on the sections that part touches.** Read as step 1 says. Then follow the steps and the guide entries that write those sections, and no others: propose the change, write it on the owner's yes, then build and prove it as step 10 says.
- **In `git-and-cicd.md`, propose only what is due.** Its part 1 is written for a first run. Do not propose the whole setup again, do not ask again what the repo's agent instructions answer, and do not treat what the first run built as "A repo that already has a setup". The owner's yes to the changed sections is the yes that building waits for.
- **There is no setup ticket and there are no first epics this time.** The evidence goes on the ticket the owner names for this run, or in your report to them if there is none. A ticket agreed in this run is filed in the epic the owner names.
- **Skip the README.** Tell the owner what changed and what was built and proved.
