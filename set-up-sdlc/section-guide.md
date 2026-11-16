<!--
DRAFT, started 16 Nov 2026. Being agreed with Kasey one section at a time.
Covers every section of the template that is not a plain copy: the blanks in
fixed sections, and the discussed sections. Sections not listed here are
copied from the template word for word.
-->

# Section guide

## The opening line

One sentence saying what the product is: its name, what kind of thing it is, and what it does. For example: "Larder is a mobile app that helps households plan their meals and waste less food."

- If the repo has a README or a package description, draft the sentence from it and ask the user whether it is right.
- If it has neither, ask the user what the product is and who it is for.
- The user's answer does not have to be the sentence. If it does not yet tell you what kind of thing the product is, what it does or who uses it, ask about the missing part, one question at a time. Then offer to write the sentence for them, and show it for a yes.
- Leave out the stack, what is built so far, what is planned, and any history. The stack has its own section, and the rest goes out of date.

## Tickets

The blank is the Linear team that holds this repo's tickets, and that team's ticket prefix. One repo has one team, so do not offer to share a team between repos.

- List the Linear teams. If one matches the repo's name, ask the user to confirm the team and its prefix.
- If none matches, show the list and ask which it is. If the user says the team does not exist yet, offer to create it, and create it only on a yes.
- If you cannot reach Linear, ask the user for the team's name and prefix.

## Worktrees

The folder for worktrees and the pattern for branch names are fixed. The example worktree name uses the ticket prefix found for Tickets. The one blank is what must be run in a new worktree before work can start there. A worktree is a fresh folder: the installed packages, the commit hook and, in Python, the virtual environment do not come with it. It needs the same environment as the main folder.

Setup covers Node and Python projects.

- **Nothing is built yet.** Ask the user which of the two the project will use. Recommend pnpm as the package manager for Node and uv for Python, and write the chosen manager's install command into the line.
- **Something is built.** Do not assume. Tell the user what you found (the lock file, the package manager, any commit hook, any virtual environment) and explain that every worktree needs the same environment as the main folder. Then ask them to confirm what has to be run in a new one.
- If they confirm that nothing needs running, leave the line out.

## Git and CI/CD

Too big for an entry here. Follow [git-and-cicd.md](./git-and-cicd.md) for the whole section, and for building what it describes.

## About this repo

Two parts. Both hold only what every session needs and the repo does not show for itself. No map of the folders.

**The stack table.** A table of plain facts, two columns: the language, the frameworks, the database, the hosting, the package manager, and the command that runs the full local check.

- Read them from the repo and ask the user to confirm.
- If nothing is built, ask what they plan to use.
- Leave out a row the project does not have. A row may carry one short fact a session would otherwise get wrong.

**The rules that hold across the code.** A short list, one line each.

- Ask the user which rules every agent must follow in every part of the code.
- Take a rule only if breaking it would do real harm and nothing in the code already stops it. If a lint rule, a type or a test enforces it, it is not needed here.
- Where an ADR holds the reason, name the ADR and do not repeat it.
- A new repo may have none. Then leave the list out. Do not invent rules to fill it.

## A repo that is already built

The context files can be built backwards from the app. Work through them with the user, one file at a time, and write nothing without their yes. How far to go is theirs to say.

- **The vocabulary.** Draft the terms from the code, the screens and the names in the database. The user corrects what each one means.
- **ADRs.** Do not write up the project's past wholesale. Ask the user which choices were hard to reverse and would still surprise a newcomer, and write an ADR only for those, with the reason in their words.
- **About this repo.** Draft the stack and the rules that hold across the code from what the code actually does. Have the user confirm that each rule is a rule and not an accident.
- **Notes and instruction files already there.** Show the user what exists. Agree what moves where under the context file rules, and what is dropped.
- **Git and CI/CD.** See "A repo that already has a setup" in [git-and-cicd.md](./git-and-cicd.md).
