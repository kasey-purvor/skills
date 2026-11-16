<!--
The whole of the git and CI/CD part of setup, in one file. Put together 16 Nov 2026.
Agreed with Kasey in outline; he will check it the first time it is used.
Part 2 is drawn from two of his setups (the most recent is the main target).
It names no tool, company or product.
-->

# Git and CI/CD

The setup agent follows this file to fill in the "Git and CI/CD" section of a repo's agent instructions, and then to build what that section describes. It has four parts: how to run the conversation, what to propose, what to write, and what to build.

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
8. **On their yes, build what was decided** (part 4).

### GitHub's own rules

Read these before proposing the merge rules. They are facts, not choices, and they limit the choices. Look at the rules on the repo and any its organisation applies.

- Is an approving review required? GitHub never lets a pull request's author approve it, so if an agent opens pull requests under a person's account, that person cannot be the approver. Tell the owner this.
- Who may merge? This decides whether merging automatically is possible at all.
- Do the rules bind administrators too? If not, the gate rests on people.
- Are the rules enforced, not only present? On some plans they can be created for a private repo and are not enforced. Then every merge rule rests on people.

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
| Day one, not live | The commit hook. CI on every pull request. The rules that protect `main`. What the GitHub account itself enforces. Whether an agent may push, and who merges. The database built from the repo, with made-up data. | All of it is cheap now. Building the database from the repo is very costly to add once months of changes have been made by hand. |
| When someone else needs to see the merged work, or going live is near | Integration. | Before then, one person on a project that is not live skips it: local and CI are enough, and changes are proved locally. |
| Before going live | Pre-production and production. What data each environment holds. Who promotes and who deploys. What an agent may do in each environment. Where test logins are kept. | None of it means anything until there is somewhere to deploy to. It has to be settled before the first real user, not after. |
| Later, when it hurts | Running only the tests a change touches. Something that keeps pull requests up to date. A cap on open pull requests. Regular runs. An alert that reaches a person. | Each has its own trigger (below). Until the trigger shows, it is work for nothing. |

#### When to raise the next step

A working agent tells the human when one of these shows up. It never changes the setup itself.

| Stage | What is happening | What is due |
| --- | --- | --- |
| Not live | A ticket would deploy the app somewhere for the first time, or someone else needs to see the merged work. | Integration |
| Not live | A real user is about to sign up, or real data is about to be loaded. | The going-live decisions |
| Any | CI takes long enough that people stop waiting for it. | Running only the tests a change touches |
| Any | Pull requests wait on each other to be brought up to date. | A step that updates the next one automatically. A paid queue only if that is still too slow. |
| Any | The line of open pull requests keeps growing. | A cap on how many each person may have open |
| Live | A failed run or an outage goes unnoticed. | Regular runs, and an alert that reaches a named person. No tickets filed automatically. |
| Live | Customers meet slowness before anyone else does. | A regular performance run on pre-production |

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
- **Pre-production holds a release still.** Integration changes with every merge. Pre-production is the one batch a person chose, unchanged while it is checked, and production takes exactly that.

### The rules at each gate

**Commit.** Catches careless mistakes in seconds, before anyone else sees them.
- The hook checks format, lint and types on the files being committed, and scans them for secrets. It runs no tests, because a slow hook gets skipped.
- The type check uses the project's own settings.
- One hook tool per repo.
- A fresh clone or worktree gets a working hook without anyone remembering to install it. Where that cannot be automatic, the repo's agent instructions say what to run.
- The hook is proved once, by committing a mistake it must refuse.

**Pull request.** Nothing reaches `main` until the checks have passed on that change.
- CI runs the whole suite on every pull request.
- A change to the database's structure runs every test that depends on the database, never a chosen few.
- A pull-request job holds no login that reaches production.
- Ask the owner: may an agent push whenever its branch is ready, or only when asked?

**Merge.** `main` only ever holds changes that were reviewed and tested together.
- Every change arrives as a pull request, and the rule binds administrators too.
- The checks are green and the branch is up to date with `main`. Branches are updated by hand while pull requests are few.
- A review is attached to the pull request, with every finding settled.
- Ask the owner: does a person merge, or does it merge automatically once the checks are green and the review is attached?

**Each deploy.** Only proved code moves on, and a person decides where a mistake would reach customers.
- Integration takes every merge automatically. A person promotes to pre-production, and a person deploys to production.
- A deploy takes only code that passed the pull-request checks. It checks that this code passed, not this commit: a merge makes a new commit, but with branches kept up to date its code is exactly what the pull request's last run tested. For the same reason there is no second full run on `main` after a merge.
- Production takes only what is already in pre-production.
- After every deploy, a quick check that the app starts and a test user can sign in.
- A database changes only through the repo. If an emergency route is wanted, it is a workflow in the repo that a person starts and that leaves a record.

### Where tests run

- Put each group of tests in the cheapest place where it actually passes. Find out by running it, not by reading it.
- The places, cheapest first: tests that need only the code, on every pull request; tests that need an empty database built from the repo, on every pull request; tests that also need the demo customer, on integration, or on a pull request while there is no integration or where they are quick.
- A test that needs more data than the demo customer has gets that data added to the demo customer.
- A test that is out of date is listed for repair. A test nothing uses is proposed for deletion.
- Proving one change by signing in and using the app is not one of these. An agent or a person does it on integration after the merge, or locally while there is no integration, and the evidence goes on the ticket.
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

The section has these parts, in this order. `AGENTS-example.md` shows a finished one. Take its form, never its facts. Write only what exists or is being built now.

1. **The stage.** One line saying whether the product is live. Under it, the rows of "When to raise the next step" for that stage and for "Any", so a working agent knows when to tell the human.
2. **The environments.** A table with a row for each environment the repo has: what it is for, what data it holds, how a change gets there, and what an agent may do there.
3. **The picture.** The route from a change on someone's machine to the last environment. One band for each place (the machine, GitHub, deployed) and one arrow for each gate. Number the gates G1, G2 and so on, in order. Adapt `example_pipeline.d2`, render it, and keep the source beside the picture.
4. **Why each gate exists.** A table with one line for each gate.
5. **What each gate demands.** One grid. The gates run across the top, with a row saying what enforces each. Down the side come the tests, then the rules. A filled dot means a machine checks it; an open dot means it rests on a person.
6. **The never list.**
7. **The tests.** A table numbering them T1, T2 and so on, with what each proves. The grid uses the same numbers.
8. **Test data and logins.** Where logins are kept, and the standing test data with the command that rebuilds each. Never a credential's value.

Then, in "How work is done", word three of the building steps from the answers: when a pull request is pushed, who merges, and where a change is proved.

## 4. What to build

Setup is one flow. It does not end with a file that describes checks nobody has made.

- On the owner's yes, build what was decided for this stage, one piece at a time: the commit hook, the CI workflow, the rules on `main`, and for a later stage the deploys and their checks.
- Prove each piece before the next. The hook refuses a commit with a mistake in it. CI runs on a pull request. The rules on `main` refuse what they should.
- The section describes only what exists. Anything decided that cannot be built yet is told to the owner, and is not written as though it were there.
