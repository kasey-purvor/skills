<!--
The whole of the git and CI/CD part of setup, in one file. Put together 16 Nov 2026.
Agreed with Kasey in outline; he will check it the first time it is used.
Part 2 is drawn from two of his setups (the most recent is the main target).
It names no tool, company or product.
-->

# Git and CI/CD

The setup agent follows this file to fill in the "Git and CI/CD" section of a repo's agent instructions, and then to build what that section describes. Part 4 also builds the scheduled runs agreed in the repo's "Scheduled runs" section. It has four parts: how to run the conversation, what to propose, what to write, and what to build.

Day to day, an agent works from the repo's own agent instructions, not from this.

## 1. How to run the conversation

Propose a whole setup and let the owner change what does not fit. Do not ask them to design it.

1. **Look first.** Read the repo's CI workflows, commit hook, deploy scripts and infrastructure folder, and what its GitHub account enforces (below). Tell the owner what you found. If something is already built, do not assume it stays or goes: report it and ask.
2. **Ask whether the product is live:** does any real user's data exist yet? If it does not, ask whether anyone else needs to see the merged work, and whether going live is near. The answers decide how much of the setup is due now (part 2, "What to decide when").
3. **Propose the setup for that stage,** whole, from part 2. Leave out whatever the repo has no use for: a library or a command-line tool has no environments beyond local, and a project with no database has no database rules.
4. **Say what is left for later,** and what will bring it up. Do not discuss the later parts.
5. **Ask the two decisions that part 2 marks "ask the owner",** one at a time, each with your recommendation.
6. **Ask what does not fit,** and change it.
7. **Write the section** (part 3) and show it. The owner corrects the tables, not a list of their earlier answers.
8. **What was decided is built in step 10 of `SKILL.md`** (part 4), once the whole file has the owner's yes.

### A repo that already has a setup

Do not replace it. Write the section to describe what exists, in the forms of part 3. For each environment it has, name the question that environment answers, which shows which of the suggested ones it is. Then go through the suggested setup with the owner, and for each difference agree one of three things: leave it as it is, change it now, or file a ticket for it.

### GitHub's own rules

Read these before proposing the merge rules. They are facts, not choices, and they limit the choices. Look at the rules on the repo and any its organisation applies.

- Is an approving review required? GitHub never lets a pull request's author approve it, so if an agent opens pull requests under a person's account, that person cannot be the approver. Tell the owner this.
- Who may merge? This decides whether merging automatically is possible at all.
- Do the rules bind administrators too? If not, the gate rests on people.
- Are the rules enforced, not only present? On some plans they can be created for a private repo and are not enforced. Then every merge rule rests on people.
- Which branches do the rules cover, and can a branch be pushed to again once it exists? Most accounts protect only `main`, and a branch is updated freely. Some apply their rules to every branch, and GitHub then refuses any push to a branch that already exists. Read every rule on a working branch to find out, and never assume either case. It decides how a pull request is changed and brought up to date (the Merge gate, below).

Then ask the owner whether their organisation has rules that the settings do not show.

## 2. What to propose

One suggested setup, stated as rules.

### The principle

- **Cheap checks first, costly ones later.** A mistake should be caught at the earliest point that can catch it.
- **A machine checks wherever a machine can.** A rule that rests on someone remembering it will drift.
- **A person decides at the steps that cannot be undone.**
- **Each environment answers one question.** If two answer the same question, one of them is not needed.

### The suggested setup

| Part | What it says |
| --- | --- |
| Foundation | Everything the database needs can be recreated from the repo with one command. Made-up data loads cleanly with another. |
| Local | Every person and agent has their own running copy and their own database. |
| Commit | A hook checks the files being committed, in seconds. |
| Pull request | CI runs the tests. Each check builds its own database, so nothing queues. |
| Merge | A pull request for every change, with the checks green and the branch up to date with `main`. |
| Integration | Every merge is deployed there automatically. |
| Pre-production | A person promotes what is on integration. |
| Production | A person deploys, and only what is already in pre-production. |

This gives two separate flows:

- **The work's flow ends at integration.** A change merges, is deployed within minutes, and is proved there. Nobody building waits for a promotion or a deploy, which is what lets several agents merge in a day.
- **The release's flow is the two steps a person starts.** Promoting and deploying move a batch of merged changes, when the person chooses. They gate a release, not a ticket.

### What to decide when

One stage matters: whether the product is live, meaning any real user's data exists. An environment becomes production the day a real user's data lands in it.

| When | What is decided | Why then |
| --- | --- | --- |
| Day one, not live | The commit hook. CI on every pull request. The rules that protect `main`. What the GitHub account itself enforces. Whether an agent may push, and who merges. The check on the layout's boundaries. The pull request sweep. The database built from the repo, with made-up data. | All of it is cheap now. Building the database from the repo is very costly to add once months of changes have been made by hand. |
| When someone else needs to see the merged work, or going live is near | Integration. | Before then, one person on a project that is not live skips it: local and CI are enough, and changes are proved locally. |
| Before going live | Pre-production and production. What data each environment holds. Who promotes and who deploys. What an agent may do in each environment. Where test logins are kept. | None of it means anything until there is somewhere to deploy to. It has to be settled before the first real user, not after. |
| Later, when it hurts | Running only the tests a change touches. Something that keeps pull requests up to date. A cap on open pull requests. Scheduled full test runs. An alert that reaches a person. | Each has its own trigger (below). Until the trigger shows, it is work for nothing. |

#### When to raise the next step

The first two rows are stages in the product's life. Each one the owner agrees is coming is written into the repo's own list, "What this setup still lacks" (part 3), so a working agent tells the human when its work reaches it. The rest are signs that the pipeline is straining, and are not copied into the repo's agent instructions as they stand. (A gap the owner agrees to write down, such as monitoring, still goes in that list.) They are for setup, when it is run again on a repo: they say which part is due. A working agent has one general rule there instead (the house rule "This file"): tell the human when the setup stops fitting the project, and never change it yourself.

| Stage | What is happening | What is due |
| --- | --- | --- |
| Not live | A ticket would deploy the app somewhere for the first time, or someone else needs to see the merged work. | Integration |
| Not live | A real user is about to sign up, or real data is about to be loaded. | The going-live decisions |
| Any | CI takes long enough that people stop waiting for it. | Running only the tests a change touches |
| Any | Pull requests wait on each other to be brought up to date. | A step that updates the next one automatically. A paid queue only if that is still too slow. |
| Any | The line of open pull requests keeps growing. | A cap on how many each person may have open |
| Live | A failed run or an outage goes unnoticed. | Scheduled full test runs, and an alert that reaches a named person. No tickets filed automatically. |
| Live | Customers meet slowness before anyone else does. | A scheduled performance run on pre-production |

A scheduled run, once it is agreed, is listed in the repo's "Scheduled runs" section. The section guide says how.

### The environments

| Environment | The question it answers | What data it holds | How code gets there |
| --- | --- | --- | --- |
| Local | Does my branch work? | Its own database, built from the repo, with made-up data. | You run it. |
| Pull-request checks | Is this change safe to merge? | Each check builds its own empty database. | Opening a pull request. |
| Integration | Does everything merged work once it is deployed? | No real data: the structure plus a made-up demo customer. | Every merge, automatically. Merges only, never a branch. |
| Pre-production | Is this exact release ready for customers? | Standing test data. No customer data. | A person promotes it. |
| Production | | Customers' data. | A person deploys it. |

- **Build the database from the repo,** never by copying another environment and never by hand. For a database with no fixed structure, that means its indexes and validation rules.
- **Keep a demo customer that loads cleanly.** Most tests and every environment except production depend on it.
- **No real customer data outside production.** An environment that holds a copy of it is production in all but name, and is locked down like production. Do not start one.
- **Integration is a real deployment or it is nothing.** A local container by that name only repeats what CI did. It adds proof that the app works as deployed, a place someone else can open, and a rehearsal of the deploy before there is anything to lose. When it breaks it is rebuilt from the repo, never repaired by hand.
- **What an agent may do.** Anything locally. In integration and pre-production, use the app and never delete standing test data. In production, nothing unless the human asks.
- **Pre-production holds a release still.** Integration changes with every merge. Pre-production is the one batch a person chose, unchanged while it is checked, and production takes exactly that.

### The rules at each gate

**Commit.** Catches careless mistakes in seconds, before anyone else sees them.
- The hook checks format and lint on the files being committed, checks types for the packages they belong to, and scans for secrets. It runs no tests, because a slow hook gets skipped.
- The type check uses the project's own settings.
- One hook tool per repo.
- A fresh clone or worktree gets a working hook without anyone remembering to install it. Where that cannot be automatic, the repo's agent instructions say what to run.
- The hook is proved once, by committing a mistake it must refuse.

**Pull request.** Nothing reaches `main` until the checks have passed on that change.
- CI runs, on every pull request, every test that can run there ("Where tests run", below).
- A change to the database's structure runs every test that depends on the database, never a chosen few.
- CI also runs the check on the layout's boundaries, as part of the lint or the tests. The repo's "Where code goes" says which.
- A pull-request job holds no login that reaches production.
- Ask the owner: may an agent push its branch once the review is clean, without asking, or only when asked? Recommend without asking: a push to a branch can harm nothing, and the merge gate is what protects `main`.
- When CI fails, the agent reads the failure and finds the cause. The fix then goes through the Fix step like any other round of fixes, before anything is pushed again. Word the building step's blank that way, and add whatever the repo's own rules demand, such as a new pull request where a pushed branch cannot be updated.

**Merge.** `main` only ever holds changes that were reviewed and tested together.
- Every change arrives as a pull request, and the rule binds administrators too.
- The checks are green and the branch is up to date with `main`. GitHub's setting that requires this is switched on. It is what keeps a line of pull requests safe: each one is tested against what the others merged before it.
- How a pull request that has fallen behind is brought up to date depends on what the account allows:
  - **A pushed branch can be updated.** This is the usual case. `main` is merged into the branch and CI runs again. Rebasing the branch does the same job but needs a force-push, so offer it only where the owner allows one on a person's own branch. It is done by hand while pull requests are few.
  - **A pushed branch cannot be updated.** The pull request is closed and replaced by a new branch cut from `main`. So the review and its fixes are finished before anything is pushed, the full local check passes with the latest `main` merged in, and a pull request stays open for as short a time as possible.
- Either way the setting stays on. If keeping up to date is costly in this repo, say what it costs and let the owner decide. Never propose switching it off yourself.
- The change has been reviewed by the repo's review subagents, with every finding settled. This is not GitHub's approving review, which is a separate rule where the account requires one.
- Ask the owner who merges. Recommend that the agent merges its own pull request once the checks are green and that review is done with nothing blocking, and that the human saying "merge it" is enough by itself. The other choice is that only a person merges.

**Each deploy.** Only proved code moves on, and a person decides where a mistake would reach customers.
- Integration takes every merge automatically. A person promotes to pre-production, and a person deploys to production.
- A deploy takes only code that passed the pull-request checks. It checks that this code passed, not this commit: a merge makes a new commit, but with branches kept up to date its code is exactly what the pull request's last run tested. For the same reason there is no second full run on `main` after a merge.
- Production takes only what is already in pre-production.
- After every deploy, a quick check that the app starts and, outside production, that a test user can sign in.
- A database changes only through the repo. If an emergency route is wanted, it is a workflow in the repo that a person starts and that leaves a record.

### Where tests run

- Put each group of tests in the cheapest place where it actually passes. Find out by running it, not by reading it.
- The places, cheapest first: tests that need only the code, on every pull request; tests that need an empty database built from the repo, on every pull request; tests that also need the demo customer, on integration, or on a pull request while there is no integration or where they are quick.
- A test that needs more data than the demo customer has gets that data added to the demo customer.
- A test that is out of date is listed for repair. A test nothing uses is proposed for deletion.
- Proving one change by signing in and using the app is not one of these. An agent or a person does it on integration after the merge, or locally while there is no integration, and the evidence goes on the ticket.
- Whoever builds a change runs the full local check before handing it on. CI is the proof, not the first time the tests are run.
- Load and speed tests are not CI.

### Changing the setup

- Design first, then change one thing at a time.
- No check is switched off, loosened or moved without the human's explicit yes, each time.
- The old check stays on until the new one passes.
- Whoever pushes is responsible for what breaks afterwards.

### What never to do

The default list for a repo's agent instructions:
- skip the commit hook;
- force-push, or reset or clean a shared branch;
- commit with no branch checked out;
- change a database or an environment by hand.

## 3. What to write

The section has these parts, in this order. `AGENTS-example.md` shows a finished one. Take its form, never its facts. Write only what exists or is being built now. The exception here is item 3, the list of what the setup still lacks.

1. **The stage.** One line saying whether the product is live.
2. **The environments.** A table with a row for each environment the repo has: what it is for, what data it holds, how a change gets there, and what an agent may do there. Under it, where the project has or plans a database, the rule in full: the database is built from the repo and never changed by hand, with the commands that build it and load made-up data once they exist. The never list says it a second time, on purpose.
3. **What this setup still lacks.** A short table under the environments, with two columns headed "What the setup lacks" and "Due". This fixed text goes above it: "This list is what the pipeline and the infrastructure still lack. A row is about how the code is checked, shipped, run or watched, and its trigger is a stage in the product's life, never a feature being built. When your work reaches a trigger, tell the human."
   - The second sentence of that text is the test for every row. A feature fails it, and so does a choice of technology that a feature will need, and anything about one test or one command. The first two belong in tickets and the last in the README.
   - The rows come from the stages in "What to decide when", above, but not from its last row, "Later, when it hurts", and from the owner: an integration environment, pre-production and production with their gates, the hosting defined in code, error tracking and monitoring. Nothing goes in that the owner has not agreed.
   - A row is deleted when the thing is built, and the rest of the section then describes it as it is.
   - If the setup lacks nothing, leave the heading out.
4. **The picture.** The route from a change on someone's machine to the last environment. One band for each place (the machine, GitHub, deployed) and one arrow for each gate. Number the gates G1, G2 and so on, in order. Adapt `example_pipeline.d2`, render it, and keep the source beside the picture.
5. **Why each gate exists.** A table with one line for each gate.
6. **What each gate demands.** One grid. The gates run across the top, with a row saying what enforces each. Down the side come the tests, then the rules. A filled dot means a machine checks it; an open dot means it rests on a person. Under the grid, say in a line or two how a pull request is changed and brought up to date in this repo.
7. **The never list.**
8. **The tests.** A table numbering them T1, T2 and so on, with what each proves. The grid uses the same numbers.
9. **Test data and logins.** Where logins are kept, and the standing test data with the command that rebuilds each. Never a credential's value. Nothing more goes here: what a fixture is for and how it behaves is written in its script's header, help text and error messages. Ask the human before making any other file about it.

Then, in "How work is done", word three of the building steps from the answers: when a pull request is pushed and what happens if CI fails, who merges, and where a change is proved.

## 4. What to build

Setup is one flow. It does not end with a file that describes checks nobody has made.

- On the owner's yes, build what was decided for this stage, one piece at a time: the commit hook, the CI workflow, the check on the layout's boundaries, the rules on `main`, the commands that build the database and load made-up data where there is a database, any scheduled run agreed for now, and for a later stage the deploys and their checks.
- A builder builds it, the review subagents review it, and each round of fixes goes to a fresh builder, as for any change in this repo. These checks are small, but every later change rests on them.
- Setup's own commits need no ticket. That covers everything setup commits: the agent instructions and the context files, these checks, and the README written at the end. Name the branch and its worktree for what they hold. The evidence goes on the setup ticket at the end (step 11 of `SKILL.md`).
- The rules on `main` are in place before any product code is written. Setup's own commits may go in before them.
- Prove each piece before the next. The hook refuses a commit with a mistake in it. CI runs on a pull request. The rules on `main` refuse what they should. The boundary check refuses an import that crosses a boundary. A scheduled run is seen to fire and to report.
- The section describes only what exists. Anything decided that cannot be built yet is offered to the owner as a ticket and filed on their yes, in the epics agreed at the end (step 11 of `SKILL.md`). It is not written as though it were there. There are two exceptions, and each names what is missing with its trigger: a run agreed for later is a row in the "Scheduled runs" table, as the section guide says, and a gap in the pipeline or the infrastructure is a row in "What this setup still lacks" (part 3).
- If a proof fails, or something could not be built, correct the section to match before you finish.
