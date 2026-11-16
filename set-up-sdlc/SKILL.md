---
name: set-up-sdlc
description: Sets up a repo for this agent workflow with its owner, in one sitting. Writes the repo's agent instructions file, creates its context files, and builds the commit hook, CI and merge rules that file describes. Use when setting up a new repo, bringing a repo that is already built into the workflow, or when a repo's stage changes and its git and CI/CD setup is due another look.
disable-model-invocation: true
---

# Set up a repo

You are setting up a repo with its owner. By the end the repo has its agent instructions file (`AGENTS.md`), its context files, and the checks that file describes, built and proved.

## Rules

- **A person must be there.** If nobody can answer you, stop. Never run this across several repos at once.
- **Look before you ask.** If the repo can answer a question, read the repo.
- **Propose, do not interview.** Draft the thing and ask whether it is right. One question at a time, each with your recommendation.
- **Fixed text is copied word for word.** Never reword it, trim it or improve it.
- **A worked-out section holds only what the owner decided in this sitting.** If little was decided, it stays short. Never pad it.
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

1. **Read** the template, the section guide and the example.
2. **Look at the repo:** its remote, package files, CI workflows, commit hooks, and any instruction or context files already there. Tell the owner what you found. If the repo is already built, also follow "A repo that is already built" in the section guide.
3. **Create the context files.** On the owner's yes, run `scripts/create-context-files.sh <repo root>`. It creates only what is missing and reports what it did.
4. **Draft the agent instructions** from the template. Copy the fixed text and fill each blank as the section guide says.
5. **Git and CI/CD.** Follow `git-and-cicd.md`, parts 1 to 3.
6. **About this repo.** Follow its entry in the section guide.
7. **Word the three building steps** that depend on the git answers: when a pull request is pushed, who merges, and where a change is proved.
8. **Show the whole file** and write it on the owner's yes. Check that no bracket and no comment from the template is left in it.
9. **Build what the file describes.** Follow `git-and-cicd.md`, part 4.
10. **Finish.** Tell the owner what was written, what was built and proved, and what became tickets. Commit when they ask.

## Running it again

A repo's stage block says when the next set of decisions is due. When the owner runs this again for that reason, do only the part that is due: steps 5 and 7 to 10, changing the sections it touches and nothing else.
