<!--
FIRST DRAFT, 16 Nov 2026. Not reviewed by Kasey yet.
Drawn from two of his setups (the most recent one is the main target), the
worked example in set-up-sdlc/AGENTS-example.md, and the old setup-pre-commit skill
(now in the skills repo's _archive folder).
-->

# Git and CI/CD

How a change gets from someone's machine to production, and how to choose a setup for a repo. Read this when a repo is being set up, or when its setup is being reviewed. Day to day, an agent works from the repo's own agent instructions, not from this.

This is the one part of the lifecycle that can be done many ways. So it gives options and the usual choice, and the person setting up the repo decides. What they decide is written into the repo's agent instructions as its "Git and CI/CD" section: the environments, the picture of the route, the gates and the tests.

## The principle

- **Cheap checks first, costly ones later.** A mistake should be caught at the earliest point that can catch it.
- **A machine checks wherever a machine can.** A rule that rests on someone remembering it will drift.
- **A person decides at the steps that cannot be undone.**
- **Each environment answers one question.** If two answer the same question, one of them is not needed.

## Start small

A project does not need four environments on its first day. Add a gate or an environment when there is something for it to protect.

| Stage | Environments | What is checked |
| --- | --- | --- |
| Nobody depends on it yet | Local only | A commit hook, and CI on every pull request. |
| First real users | Local, one test environment, production | Add a deploy that only takes proved code, and proof in the test environment before production. |
| Outages are costly, or several people contribute | Local, an environment that takes every merge, a pre-production environment, production | Add tests grouped by what they need, regular runs, and an alert that reaches a person. |

An environment becomes production the day a real user's data lands in it.

## The environments

| Environment | The question it answers | What data it holds | How code gets there |
| --- | --- | --- | --- |
| Local | Does my branch work? | Its own database, built from the repo, with made-up data. | You run it. |
| Pull-request checks | Is this change safe to merge? | Each check builds its own empty database. Nothing is shared, so nothing queues. | Opening a pull request. |
| Integration | Does everything merged work together? | No real data: the structure plus a seeded demo customer. Rebuilt from the repo when it breaks, never repaired by hand. | Every merge, automatically. Merges only, never a branch. |
| Pre-production | Does the release work on real data? | Either a locked-down copy of production, or standing test data where real data is not allowed. | A person promotes it. |
| Production | | Customers' data. | A person deploys it. |

Three rules sit under all of them:
- **Build the database from the repo,** never by copying another environment.
- **Keep a demo customer that loads cleanly.** Most tests and every non-production environment depend on it.
- **A check never queues for a shared environment.** If it does, give it its own database.

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
| What runs | Everything, every time. Or only what the change touches. | Only what the change touches, once the suite is big enough to hurt. |
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
| Open pull requests | No limit. Or a cap per person. | A small cap. It keeps the line short. |
| A second full run on `main` after the merge | Run it. Or skip it. | Skip it, but only if branches must be up to date, because then the pull request's last run already tested the same code. |

### Each environment after the merge

| Decision | Options | The usual choice |
| --- | --- | --- |
| What starts a deploy | Every merge. A person. A schedule. | Every merge for an integration environment. A person for pre-production and production. |
| What a deploy refuses | Nothing. Or any commit whose checks were not green. | Refuse it. |
| What production accepts | Any proved commit. Or only the exact commit already in pre-production. | Only the exact commit. |
| How the database changes | By hand. Or only through the repo, as migrations. | Only through the repo, with one emergency route that is logged. |
| After a deploy | Nothing. Or a quick check that it is alive. | A quick check, every time. |

How a deploy itself is built (rollback, migrations, health checks) is in the deployment chapter, `deployment.md`.

## Sorting tests

Put each group of tests in the cheapest place where it actually passes. Do not decide in advance.

| Slot | What the tests need | Where it runs |
| --- | --- | --- |
| 1 | Only the code | Every pull request |
| 2 | An empty database built from the repo | Every pull request that could affect it |
| 3 | That, plus the demo customer | The integration environment, or a pull request if it is quick |
| 4 | Real data | Pre-production, after a promotion |

To place a group: run it in the lowest slot that might work. If it passes, it lives there. If it fails for missing data, try the next slot up. If the test itself is out of date, list it for repair. If nothing uses it, propose deleting it.

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

For a JavaScript or TypeScript repo, using Husky (which runs the hook) and lint-staged (which runs commands on only the files being committed).

1. Find the package manager from the lock file: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock` or `bun.lockb`.
2. Install `husky` and `lint-staged` as development dependencies, with the repo's formatter and linter if it has none.
3. Run `npx husky init`. It creates `.husky/` and adds a `prepare` script, so the hook is installed whenever dependencies are.
4. Write `.husky/pre-commit` with one line that runs lint-staged.
5. Configure lint-staged to format and lint the staged files, and to run the type check for a package when one of its TypeScript files is staged.
6. Check that it works: stage a file with a formatting mistake and commit it.
7. Commit the hook itself, which runs it for the first time.

A new clone or worktree has no hook until its dependencies are installed there.

## Previous setups, and why they differ

A record of setups already made with this approach, so the next one starts from experience and not from a blank list. Reasons only, no history.

| | Setup A | Setup B |
| --- | --- | --- |
| What it is | A product with two contributors, live with customers | A larger product with several contributors, live with customers |
| Environments | Local, one test environment, production | Local, integration, pre-production, production |
| Test environment data | Standing test data. No customer data. | A locked-down copy of production in pre-production. A demo customer everywhere else. |
| Pull-request checks | The whole suite, every time | Sorted into slots, and only what the change touches |
| Up to date with `main` | Required, updated by hand | Required, with an automatic step being added |
| Who merges | The human | Automatically, once the checks are green and a review is attached |
| Deploys | Both started by hand | Integration on every merge. Pre-production and production by a person. |
| Why it differs | Few pull requests a day, so waiting is cheaper than a queue. Customer data may not leave production. | The suite is too large to run whole. Checks were queuing for a shared environment. Releases have to be proved on real data. |
