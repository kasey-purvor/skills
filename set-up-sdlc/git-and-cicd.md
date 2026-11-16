<!--
The practice the setup agent proposes from. Rewritten 16 Nov 2026 as rules only:
no step-by-step instructions, no lists of options. Agreed with Kasey in outline;
not yet read by him in this form. Drawn from two of his setups (the most recent
is the main target). It names no tool, company or product.
-->

# Git and CI/CD

How a change gets from someone's machine to production. Read this when a repo is being set up, or when its setup is being looked at again. Day to day, an agent works from the repo's own agent instructions, not from this.

It states one suggested setup, as rules. Propose it, and let the repo's owner change what does not fit. What they decide is written into the repo's agent instructions as its "Git and CI/CD" section: the stage and when to raise the next step, the environments, the picture of the route, the gates and the tests.

Leave out whatever a repo has no use for. A library or a command-line tool has no environments beyond local, and a project with no database has no database rules.

## The principle

- **Cheap checks first, costly ones later.** A mistake should be caught at the earliest point that can catch it.
- **A machine checks wherever a machine can.** A rule that rests on someone remembering it will drift.
- **A person decides at the steps that cannot be undone.**
- **Each environment answers one question.** If two answer the same question, one of them is not needed.

## The suggested setup

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

## What to decide when

One stage matters: whether the product is live, meaning any real user's data exists. An environment becomes production the day a real user's data lands in it.

| When | What is decided | Why then |
| --- | --- | --- |
| Day one, not live | The commit hook. CI on every pull request. The rules that protect `main`. What the GitHub account itself enforces. Whether an agent may push, and who merges. The database built from the repo, with made-up data. | All of it is cheap now. Building the database from the repo is very costly to add once months of changes have been made by hand. |
| When someone else needs to see the merged work, or going live is near | Integration. | Before then, one person on a project that is not live skips it: local and CI are enough, and changes are proved locally. |
| Before going live | Pre-production and production. What data each environment holds. Who promotes and who deploys. What an agent may do in each environment. Where test logins are kept. | None of it means anything until there is somewhere to deploy to. It has to be settled before the first real user, not after. |
| Later, when it hurts | Running only the tests a change touches. Something that keeps pull requests up to date. A cap on open pull requests. Regular runs. An alert that reaches a person. | Each has its own trigger (below). Until the trigger shows, it is work for nothing. |

### When to raise the next step

Setup copies the stage, and the triggers that fit it, into the repo's agent instructions. That is the only place a working agent will see them. The agent tells the human when one shows up. It never changes the setup itself.

| Stage | What is happening | What is due |
| --- | --- | --- |
| Not live | A ticket would deploy the app somewhere for the first time, or someone else needs to see the merged work. | Integration |
| Not live | A real user is about to sign up, or real data is about to be loaded. | The going-live decisions |
| Any | CI takes long enough that people stop waiting for it. | Running only the tests a change touches |
| Any | Pull requests wait on each other to be brought up to date. | A step that updates the next one automatically. A paid queue only if that is still too slow. |
| Any | The line of open pull requests keeps growing. | A cap on how many each person may have open |
| Live | A failed run or an outage goes unnoticed. | Regular runs, and an alert that reaches a named person. No tickets filed automatically. |
| Live | Customers meet slowness before anyone else does. | A regular performance run on pre-production |

## The environments

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

## GitHub's own rules

Read what the repo's GitHub account already enforces before proposing the merge rules. These are facts, not choices, and they limit the choices. Look at the rules on the repo and any its organisation applies.

- Is an approving review required? GitHub never lets a pull request's author approve it, so if an agent opens pull requests under a person's account, that person cannot be the approver.
- Who may merge? This decides whether merging automatically is possible at all.
- Do the rules bind administrators too? If not, the gate rests on people.
- Are the rules enforced, not only present? On some plans they can be created for a private repo and are not enforced. Then every merge rule rests on people.

Then ask the owner whether their organisation has rules that the settings do not show.

## The rules at each gate

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

## Where tests run

- Put each group of tests in the cheapest place where it actually passes. Find out by running it, not by reading it.
- The places, cheapest first: tests that need only the code, on every pull request; tests that need an empty database built from the repo, on every pull request; tests that also need the demo customer, on integration, or on a pull request while there is no integration or where they are quick.
- A test that needs more data than the demo customer has gets that data added to the demo customer.
- A test that is out of date is listed for repair. A test nothing uses is proposed for deletion.
- Proving one change by signing in and using the app is not one of these. An agent or a person does it on integration after the merge, or locally while there is no integration, and the evidence goes on the ticket.
- Load and speed tests are not CI.

## Changing the setup

- Design first, then change one thing at a time.
- No check is switched off, loosened or moved without the human's explicit yes, each time.
- The old check stays on until the new one passes.
- Whoever pushes is responsible for what breaks afterwards.

## What never to do

The default list for a repo's agent instructions:
- skip the commit hook;
- force-push, or reset or clean a shared branch;
- commit with no branch checked out;
- change a database or an environment by hand.
