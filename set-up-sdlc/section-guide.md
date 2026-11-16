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

- **Nothing is built yet.** Ask the user which of the two the project will use, and with which package manager. Write that manager's install command into the line.
- **Something is built.** Do not assume. Tell the user what you found (the lock file, the package manager, any commit hook, any virtual environment) and explain that every worktree needs the same environment as the main folder. Then ask them to confirm what has to be run in a new one.
- If they confirm that nothing needs running, leave the line out.
