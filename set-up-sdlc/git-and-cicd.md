<!--
FIRST DRAFT, 16 Nov 2026. Revised the same day, after the setup skill's design was
agreed with Kasey: one suggested setup, live or not live, integration, GitHub's own
rules. Not reviewed by Kasey yet.
Moved here from the handbook's topics on 16 Nov: its one reader is the setup agent.
Drawn from two of his setups (the most recent one is the main target), the
worked example in set-up-sdlc/AGENTS-example.md, and the old setup-pre-commit skill
(now in the skills repo's _archive folder).
-->

# Git and CI/CD

How a change gets from someone's machine to production, and how to choose a setup for a repo. Read this when a repo is being set up, or when its setup is being reviewed. Day to day, an agent works from the repo's own agent instructions, not from this.

This is the one part of the lifecycle that can be done many ways. So it gives one suggested setup, the options at each step and the usual choice, and the person setting up the repo decides. What they decide is written into the repo's agent instructions as its "Git and CI/CD" section: the environments, the picture of the route, the gates and the tests.

## The principle

- **Cheap checks first, costly ones later.** A mistake should be caught at the earliest point that can catch it.
- **A machine checks wherever a machine can.** A rule that rests on someone remembering it will drift.
- **A person decides at the steps that cannot be undone.**
- **Each environment answers one question.** If two answer the same question, one of them is not needed.

## The suggested setup

Propose this unless the repo's owner has a reason to differ. It is one setup, and a project builds as much of it as it needs today (next section).

| Part | What it says |
| --- | --- |
| Foundation | Everything the database needs can be recreated from the repo with one command. Made-up data loads cleanly with another. |
| Local | Every person and agent has their own running copy and their own database. |
| Commit | A hook checks format, lint and types on the files being committed, and scans for secrets. |
| Pull request | CI runs the tests. Each check builds its own database, so nothing queues. |
| Merge | A pull request for every change, with the checks green and the branch up to date with `main`. |
| Integration | Every merge is deployed there automatically. |
| Pre-production | A person promotes what is on integration. Code whose checks were not green is refused. |
| Production | A person deploys, and only what is already in pre-production. |

This gives two separate flows:

- **The work's flow ends at integration.** A change merges, is deployed within minutes, and is proved there. Nobody building waits for a person to press anything, which is what lets several agents merge in a day.
- **The release's flow is the two steps a person starts.** Promoting and deploying move a batch of merged changes, when the person chooses. They gate a release, not a ticket.

## What to decide when

One stage matters: whether the product is live, meaning any real user's data exists. An environment becomes production the day a real user's data lands in it.

| When | What is decided | Why then |
| --- | --- | --- |
| Day one, not live | The commit hook. CI on every pull request. The rules that protect `main`. What the GitHub account itself enforces. Whether an agent may push, and who merges. The database built from the repo, with made-up data. | All of it is cheap now. Building the database from the repo is very costly to add once months of changes have been made by hand. |
| Before going live | Pre-production and production. What data each environment holds. Who promotes and who deploys. That a deploy takes only proved code. A check after each deploy. What an agent may do in each environment. Where test logins are kept. | None of it means anything until there is somewhere to deploy to. It has to be settled before the first real user, not after. |
| Later, when it hurts | Running only the tests a change touches. Something that keeps pull requests up to date. Regular runs. An alert that reaches a person. A cap on open pull requests. | Each has its own trigger (below). Until the trigger shows, it is work for nothing. |

**Integration is added at the first of two moments:** someone else needs to see the merged work (a second contributor, a client), or going live is near. Before either, one person on a project that is not live can skip it: local and CI are enough, and changes are proved locally. Once the project is live it is always there.

### When to raise the next step

An agent working in a repo does not change the setup. It tells the human when one of these shows up.

Not live:
- a ticket would deploy the app somewhere for the first time;
- someone else needs to see the merged work;
- a real user is about to sign up, or real data is about to be loaded.

Live:

| What is happening | What to consider |
| --- | --- |
| CI takes long enough that people stop waiting for it | Running only the tests a change touches |
| Pull requests wait on each other to be brought up to date | An automatic step that updates the next one. A paid queue only if that is still too slow. |
| A failed run or an outage goes unnoticed | Regular runs, and an alert that reaches a named person |
| Customers meet slowness before anyone else does | A regular performance run on pre-production |

## The environments

| Environment | The question it answers | What data it holds | How code gets there | Needed |
| --- | --- | --- | --- | --- |
| Local | Does my branch work? | Its own database, built from the repo, with made-up data. | You run it. | From day one |
| Pull-request checks | Is this change safe to merge? | Each check builds its own empty database. Nothing is shared, so nothing queues. | Opening a pull request. | From day one |
| Integration | Does everything merged work once it is deployed? | No real data: the structure plus a made-up demo customer. Rebuilt from the repo when it breaks, never repaired by hand. | Every merge, automatically. Merges only, never a branch. | See above. Always, once live. |
| Pre-production | Is this release ready for customers? | Standing test data. No customer data. | A person promotes it. | Before going live |
| Production | | Customers' data. | A person deploys it. | Before going live |

Rules that sit under all of them:
- **Build the database from the repo,** never by copying another environment and never by hand. For a database with no fixed structure, that means its indexes and validation rules.
- **Keep a demo customer that loads cleanly.** Most tests and every non-production environment depend on it.
- **A check never queues for a shared environment.** If it does, give it its own database.
- **No real customer data outside production.** A setup that already keeps a copy of production in pre-production locks it down: a short access list, and all of its preparation in the repo. Do not start one.
- **Integration is a real deployment or it is nothing.** A local container by that name only repeats what CI did. What integration adds is proof that the app works as deployed, a place someone else can open, and a rehearsal of the deploy before there is anything to lose.

## GitHub's own rules

Before choosing the merge rules, read what the repo's GitHub account already enforces. These are facts, not choices, and they limit the choices.

| What to find out | Why it matters |
| --- | --- |
| Is an approving review required? | It is a demand of the merge gate that a machine enforces. |
| Who may merge? | It decides who merges, and whether merging automatically is possible at all. |
| Do the rules bind administrators too? | If not, the gate rests on people. |
| Does the account's plan allow such rules on this repo? | Some plans do not allow them on private repos. Then every merge rule rests on people. |

Then ask the repo's owner whether their organisation has rules that the repo's settings do not show.

GitHub never lets the author of a pull request approve it. If an agent opens pull requests under a person's account and a review is required, that person cannot be the approver.

## The gates

A change passes a gate at each step: commit, pull request, merge, then one for each environment it is deployed to. For each gate, choose what it demands.

### Commit

Protects against careless mistakes, in seconds, before anyone else sees them.

| Option | Trade-off |
| --- | --- |
| No hook | Nothing slows a commit. Every mistake waits for CI. |
| Format, lint and type checks on the files being committed | Fast enough that nobody skips it. **The usual choice.** |
| The same, plus the tests | Catches more, but a slow hook gets bypassed. |

A scan for secrets belongs here too. The steps to install the hook are at the end of this file.

### Pull request

Protects `main`: nothing reaches it until the checks have passed on that change.

| Decision | Options | The usual choice |
| --- | --- | --- |
| What runs | Everything, every time. Or only what the change touches. | Everything, until the suite is big enough to hurt. |
| Which tests belong here | See "Sorting tests" below. | Every test that needs only the code, or an empty database. |
| A change to the database's structure | A subset of the permission tests, or all of them. | All of them. Never a subset. |
| When an agent may push | Only when asked. Or whenever the branch is ready. | Decided per repo. |

### Merge

Protects `main` again: it should only ever hold changes that were reviewed and tested together.

| Decision | Options | The usual choice |
| --- | --- | --- |
| How a change reaches `main` | Direct pushes allowed. Or a pull request for every change. | A pull request for every change, with the rule binding administrators too. |
| Keeping `main` tested | Merge freely and test `main` afterwards. Or require each branch to be up to date with `main` first. | Up to date first. |
| Who does the updating | Each person, by hand. An automatic step that updates the next pull request. A merge queue service. | By hand while pull requests are few. Automatic when the waiting starts to cost. A paid queue only if that is still too slow. |
| Who merges | The human. Or automatically once the checks are green and a review is attached. | Decided per repo. This is the choice that differs most between setups. |
| Review | Who reviews, and whether the review must come from a different account than the author. | A review attached to the pull request. |
| Open pull requests | No limit. Or a cap per person. | No limit at first. A small cap once the line gets long. |
| A second full run on `main` after the merge | Run it. Or skip it. | Skip it, but only if branches must be up to date, because then the pull request's last run already tested the same code. |

### Each environment after the merge

| Decision | Options | The usual choice |
| --- | --- | --- |
| What starts a deploy | Every merge. A person. A schedule. | Every merge for integration. A person for pre-production and production. |
| What a deploy refuses | Nothing. Or any commit whose checks were not green. | Refuse it. |
| What production accepts | Any proved commit. Or only the exact commit already in pre-production. | Only the exact commit. |
| How the database changes | By hand. Or only through the repo, as migrations. | Only through the repo, with one emergency route that is logged. |
| After a deploy | Nothing. Or a quick check that it is alive. | A quick check, every time. |
| What a pull-request job can reach | Any login it is given. Or nothing that reaches production. | Nothing that reaches production. |

How a deploy itself is built (rollback, migrations, health checks) is in the deployment chapter, `deployment.md`.

## Sorting tests

Put each group of tests in the cheapest place where it actually passes. Do not decide in advance.

| Slot | What the tests need | Where it runs |
| --- | --- | --- |
| 1 | Only the code | Every pull request |
| 2 | An empty database built from the repo | Every pull request that could affect it |
| 3 | That, plus the demo customer | Integration, or a pull request if it is quick |
| 4 | Real data | Pre-production, after a promotion. Only in a setup that already keeps a locked-down copy of production there. |

To place a group: run it in the lowest slot that might work. If it passes, it lives there. If it fails for missing data, try the next slot up. If the test itself is out of date, list it for repair. If nothing uses it, propose deleting it.

Proving one change in a deployed environment, by signing in and using it, is not one of these slots. An agent or a person does it on integration after the merge, and the evidence goes on the ticket.

Load and speed tests are not CI. Run them regularly against pre-production.

## What runs regularly

Not everything belongs on a pull request. Decide what runs nightly or weekly, such as the full permission set, checks specific to one customer, and a performance run.

A regular run is not a gate, so nobody is waiting on it. When one fails, or does not run, that has to reach a named person. Do not file tickets automatically.

## Changing the setup

- Design first, then change one thing at a time.
- No check is switched off, loosened or moved without the human's explicit yes, each time.
- The old check stays on until the new one passes.
- Whoever pushes is responsible for what breaks afterwards.

## What never to do

The default list for a repo's agent instructions:
- skip the commit hook with `--no-verify`;
- force-push, or run `git reset --hard` or `git clean` on a shared branch;
- commit with no branch checked out;
- change a database or an environment by hand.

## Installing the commit hook

### A JavaScript or TypeScript repo

Using Husky (which runs the hook) and lint-staged (which runs commands on only the files being committed).

1. Find the package manager from the lock file: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock` or `bun.lockb`.
2. Install `husky` and `lint-staged` as development dependencies, with the repo's formatter and linter if it has none.
3. Run `npx husky init`. It creates `.husky/` and adds a `prepare` script, so the hook is installed whenever dependencies are.
4. Write `.husky/pre-commit` with one line that runs lint-staged.
5. Configure lint-staged to format and lint the staged files, and to run the type check for a package when one of its TypeScript files is staged.
6. Check that it works: stage a file with a formatting mistake and commit it.
7. Commit the hook itself, which runs it for the first time.

A new clone or worktree has no working hook until its dependencies are installed there.

### A Python repo

Using the `pre-commit` tool (which runs the hook on only the files being committed) and Ruff (which formats and lints).

1. Add `pre-commit` and `ruff` as development dependencies with the repo's package manager, and a type checker if the repo has none.
2. Write `.pre-commit-config.yaml` with Ruff's two hooks, one that lints and one that formats, and a hook that runs the type checker.
3. Run the type checker as a local hook, through the package manager, so that it sees the project's own dependencies. A type checker run in the tool's separate environment cannot see them and reports imports it cannot find.
4. Run `pre-commit install` once in the clone. It writes the hook into the repo's `.git` folder, which the repo's worktrees share.
5. Check that it works: stage a file with a formatting mistake and commit it.
6. Commit the configuration file.

`pre-commit install` has to be run in every new clone: unlike the JavaScript set-up, installing dependencies does not do it. A worktree shares the clone's hook, but the type check needs the dependencies installed in that worktree.

## Previous setups, and why they differ

A record of setups already made with this approach, so the next one starts from experience and not from a blank list. Reasons only, no history. Setup B is the nearer of the two to the suggested setup.

| | Setup A | Setup B |
| --- | --- | --- |
| What it is | A product with two contributors, live with customers | A larger product with several contributors, live with customers |
| Environments | Local, one test environment, production | Local, integration, pre-production, production |
| Test environment data | Standing test data. No customer data. | A locked-down copy of production in pre-production, which it had before this approach. A demo customer everywhere else. |
| Pull-request checks | The whole suite, every time | Sorted into slots, and only what the change touches |
| Up to date with `main` | Required, updated by hand | Required, with an automatic step being added |
| Who merges | The human | Automatically, once the checks are green and a review is attached |
| Deploys | Both started by hand | Integration on every merge. Pre-production and production by a person. |
