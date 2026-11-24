<!--
DRAFT, started 16 Nov 2026. Being agreed with Kasey one section at a time.
Covers every section of the template that is not a plain copy: the blanks in
fixed sections, and the discussed sections. Sections not listed here are
copied from the template word for word.
-->

# Section guide

## The opening line

One sentence saying what the product is: its name, what kind of thing it is, and what it does. For example: "Larder is a mobile app that helps households plan their meals and waste less food."

- If the repo has a README or a package description, draft the sentence from it and ask the owner whether it is right.
- If it has neither, ask the owner what the product is and who it is for.
- The owner's answer does not have to be the sentence. If it does not yet tell you what kind of thing the product is, what it does or who uses it, ask about the missing part, one question at a time. Then offer to write the sentence for them, and show it for a yes.
- Leave out what the product is built with, what is built so far, what is planned, and any history. What it is built with has its own section, and the rest goes out of date.

## Tickets

The blank is the Linear team that holds this repo's tickets, and that team's ticket prefix. One repo has one team, so do not offer to share a team between repos.

- List the Linear teams. If one matches the repo's name, ask the owner to confirm the team and its prefix.
- If none matches, show the list and ask which it is. If the owner says the team does not exist yet, agree its name and prefix. Creating a team needs a Linear API key, because the Linear tools cannot do it. If the owner has a key, offer to create the team with it, and create it only on a yes. If not, the owner creates it in Linear. Either way a new team needs the statuses the `linear` skill lists. Copying them from another team is the quick way, and it is drawing on another repo's setup, so ask first.
- If you cannot reach Linear, ask the owner for the team's name and prefix.

## Worktrees

The folder for worktrees and the pattern for branch names are fixed. The example worktree name uses the ticket prefix found for Tickets. The one blank is what must be run in a new worktree before work can start there. A worktree is a fresh folder: the installed packages, the commit hook and, in Python, the virtual environment do not come with it. It needs the same environment as the main folder.

Setup covers Node and Python projects.

- **Nothing is built yet.** This blank waits for the table of what the product needs ("About this repo"), which settles the language and the package manager. Recommend pnpm as the package manager for Node and uv for Python there, and write the chosen manager's install command into the line.
- **Something is built.** Do not assume. Tell the owner what you found (the lock file, the package manager, any commit hook, any virtual environment) and explain that every worktree needs the same environment as the main folder. Then ask them to confirm what has to be run in a new one.
- If they confirm that nothing needs running, leave the line out.

## Git and CI/CD

Too big for an entry here. Follow [git-and-cicd.md](./git-and-cicd.md) for the whole section, and for building what it describes.

## Scheduled runs

A table of the work that runs on a schedule in this repo, and of the runs agreed for later. Five columns, headed Run, What it does, How it runs, Who it tells and State.

- **What it does** is one line: what the run looks for.
- **How it runs** holds the technical facts, in one line: what starts it (cron, a scheduled workflow on GitHub, a scheduled cloud run), where it runs (each person's workstation, or once in the cloud), how often, and the model if an agent does the work. How the run behaves beyond that is written in its own script.
- **Who it tells** says who is told and how: a live session, a notification to a named person, or the run's own output page. A run writes nothing into the repo and no ticket, so a longer report stays in the run's own output and the person is sent to it.
- **State** says "Running" for a run that exists, or that is being built in this setup. For a run agreed for later it says what will bring it up. Give a trigger, never a date.

How to fill it:

- **Propose the runs in the table below.** The owner strikes what they do not want and adds their own. Everything you suggest is a suggestion until the owner confirms it, one run at a time.
- **Recommend the pull request sweep every time.** It is what stops a pull request being forgotten once the session that opened it has gone.
- **Decide where each run happens.** A run that belongs to a person runs on that person's workstation. A run that belongs to the repo runs once, in one place, or every collaborator's machine repeats it.
- **Say what each run costs.** A script costs nothing. A run by an agent spends tokens every time, so agree how often it runs.
- **Call every one a scheduled run,** and a review that runs on a schedule a scheduled review. "Routine reviews" already means the reviews on every change.
- A run agreed for now is written as "Running", then built and proved in step 10 of `SKILL.md`. If it cannot be proved, it becomes a run agreed for later: give its row the trigger that would get it working, and tell the owner.
- A run agreed for later is a row with its trigger. It is not made a ticket: the row is what keeps it in view.
- If something is built, look for what already runs on a schedule (scheduled workflows, cron entries) and ask the owner to confirm each one.
- If no run is agreed, write "None yet." in place of the table.

| Run | What it does | Belongs to | Suggest it |
| --- | --- | --- | --- |
| Pull request sweep | Finds pull requests that are red or have sat open too long, and tells the session that owns each one | Each person | Always |
| Scheduled code review | Reads the code for drift and duplication that the reviews on each change miss | The repo | When several people or agents merge daily |
| Scheduled CI review | Looks for slow jobs, tests that fail at random and tests that are skipped | The repo | When CI is slow enough that people stop waiting for it, or starts failing at random |
| Scheduled test suite review | Looks for tests that are out of date and tests nothing uses | The repo | Once the suite is large enough to hide them |
| Agent instructions check | Looks for lines in the repo's agent instructions that have stopped being true | The repo | When more than one person changes the repo |
| Scheduled full test runs, and a scheduled performance run | See "When to raise the next step" in [git-and-cicd.md](./git-and-cicd.md) | The repo | When the trigger named there shows |

The pull request sweep is not in this skill yet (18 Nov 2026). Until this skill's `scripts/` folder holds it, agree it with the owner and give it the State "When the human says the sweep is ready to install".

## About this repo

Three parts. All hold only what every session needs and the repo does not show for itself. No map of the folders.

**The table of what the product needs.** One table for the stack and for everything else the product will need. Three columns, headed Need, Choice and Decided. The Decided column says "Yes" for a need that is decided, with its ADR if it has one, and otherwise what will bring the decision up. The table holds what has been decided and what has not, together.

- **Start from the product, not from tools.** List what the product needs. Read it from the repo's documents if it has them, from the code if something is built, and ask the owner otherwise. Go past the usual rows (language, frameworks, database, hosting, package manager, the full local check) to what this product does: who signs in, what it stores, what it brings in and sends out, what runs in the background.
- **Sort the needs by when each must be decided:** now, in this sitting, because it is hard to change later (how one customer's data is kept from another's, for example) or because the commit hook and CI depend on it; when the first piece of work touches it; when a product decision is made; at a later stage.
- **Everything you suggest is a suggestion until the owner confirms it.** Show the owner the sorted list. They strike what will never be needed and add what is missing. Then take the needs one at a time, with one question at a time: is the need real, is it in the right group, and, for a need that waits, what will bring its decision up. Nothing goes in the table that the owner has not said yes to. Silence is not a yes, and neither is a yes to something else.
- **Decide only the first group in this sitting,** one need at a time. Where there is a real choice, show the options and what each costs, and recommend one. Where there is not, say so and propose it. Each choice is the owner's to confirm.
- **Reason from this product.** The rule in `SKILL.md` against drawing on another repo matters most here: never take a choice from one unless the owner says to. You may offer to look, and you look only on a yes.
- A choice earns an ADR only if it passes the test in `domain.md`: hard to reverse, surprising without its reason, and a real choice between options. Write the ADR on the owner's yes, and name it beside "Yes" in the third column, for example "Yes (ADR-0004)". The table holds the choice, not the reason.
- For a need not yet decided, write "Not chosen" as the choice and, in the third column, what will bring the decision up. Give a trigger, never a date.
- If something is built, read the choices from the repo and ask the owner to confirm them.
- When the package manager is agreed, go back to the Worktrees blank and fill in its install command.
- A row may carry one short fact a session would otherwise get wrong.

Suggest a trigger for each need that waits. These are starting points, and the owner sets each one:

| Kind of need | A trigger to suggest |
| --- | --- |
| Sign-in, and who may see what | Before the first screen that shows real or private data |
| Work that runs in the background | When the first task is too slow to finish inside one request |
| Storing files | When the first upload or export is built |
| A connection to another system | When the first piece of work reads from it or writes to it |
| Sending email or messages | When the first feature has to tell someone something |
| Anything that waits on a product decision | When that decision is made. Name the decision. |
| Defining the hosting in code | With the first deployment |

The template has one fixed line for this part: "A need marked Not chosen is not yours to choose. When your work reaches one, stop and ask the human." The table goes straight above it. Keep the line only if a row is marked Not chosen.

**Where code goes.** The layout of the repo, written as rules and never as a map. The template gives the heading.

- The layout is a need to decide now. It is hard to change once the commit hook, CI and import paths are built on it. It is settled here, and gets no row in the table of needs.
- Before proposing one, read the module design chapter of `dev-standards-handbook`. The house rule "Layout" already fixes that code is grouped by feature, so never offer a layered layout.
- **Propose the convention before any names,** in two questions. First the top level: the parts of the repo, and the test for what goes in each. Then the rules inside a part.
- Agree a closed list of role suffixes for this stack, and write it as a table of each suffix and what it holds. The house rule "Naming" says the role comes second. This table says which roles exist.
- Write the top-level parts and the test for what goes where in one or two lines. Feature folders take their names from the terms in `CONTEXT.md`. Do not list the features: that would be a map.
- If something is built, read the layout from the repo and show the owner where it departs from the house rule "Layout". Agree for each departure whether it is left or made a ticket, and write each one that is left here as an exception.
- A check should enforce the boundaries, as part of the lint or the tests. Agree it with the Git and CI/CD checks, and say in this part which check does it. It is built and proved in step 10 of `SKILL.md`. If it cannot be, leave that line out.
- The template has one fixed line for this part: "Ask before adding a suffix that is not in this table." The table of suffixes goes straight above it.

**The rules that hold across the code.** A short list, one line each, under its own heading, "Rules across the code". The template gives the heading, so the rules do not read as part of the layout.

- Ask the owner which rules every agent must follow in every part of the code.
- Take a rule only if breaking it would do real harm and nothing in the code already stops it. If a lint rule, a type or a test enforces it, it is not needed here.
- Where an ADR holds the reason, name the ADR and do not repeat it.
- A new repo may have none. Then leave the heading and the list out. Do not invent rules to fill it.

## Notes and files already there

A repo may already hold notes, reference documents or instruction files, whether or not anything is built.

- Show the owner what exists.
- Read it to learn what the product is. Reference material that describes the product stays where it is unless the owner says otherwise.
- For notes and instruction files that overlap the context files, agree what moves where under the context file rules, and what is dropped.

## A repo that is already built

The context files can be built backwards from the app. Work through them with the owner, one file at a time, and write nothing without their yes. How far to go is theirs to say.

- **The vocabulary.** Draft the terms from the code, the screens and the names in the database. The owner corrects what each one means.
- **ADRs.** Do not write up the project's past wholesale. Ask the owner which choices were hard to reverse and would still surprise a newcomer, and write an ADR only for those, with the reason in their words.
- **About this repo.** Draft the table of what the product needs, "Where code goes" and the rules that hold across the code from what the code actually does. Have the owner confirm that each rule is a rule and not an accident.
- **Notes and instruction files already there.** See "Notes and files already there", above.
- **Git and CI/CD.** See "A repo that already has a setup" in [git-and-cicd.md](./git-and-cicd.md).
- **Scheduled runs.** List what already runs on a schedule and have the owner confirm each one.
