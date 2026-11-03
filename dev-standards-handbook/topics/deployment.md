# Deployment & Release

> **Calibrate to the context.** Release machinery scales with whether users would
> notice a bad deploy. Most platforms already roll out without downtime; blue-green and
> canary earn their keep on high-traffic systems, and for most projects starting out the
> platform's rolling deploy plus feature flags gets 80% of the benefit with minimal
> infrastructure. The hygiene rules — commit the lockfile, frozen installs in CI, keep each
> release compatible with the one before it (never drop a column in the same deploy as the
> code that reads it) — are cheap insurance and hold at any size. Reference material, not
> a checklist.

## The Problem

Getting code from "it works on my machine" to "it's running in production serving real users" is where most outages happen. The deploy itself is the most dangerous moment — you're changing a running system. Deployment and operations patterns exist to make this safe and recoverable.

---

## Release Patterns

### Rolling Deploys and the Mixed-Version Window

Most platforms deploy without downtime by default. ECS, Kubernetes and Cloud Run start new instances, wait for their health checks, then drain the old ones ([Resilience](./resilience.md#graceful-shutdown) covers the drain). Fly's default rolling strategy takes each Machine down before replacing it, so a one-Machine Fly app needs `bluegreen` or a second Machine. Vercel and Netlify switch each deployment atomically. So zero downtime is usually something you configure, not a reason to build blue-green.

What every zero-downtime pattern shares is the **mixed-version window**: during a rollout, old and new code serve traffic side by side, and around any switch, old workers are still draining queued jobs. Each release must therefore stay compatible with the one before it on:

- **the database schema** — expand before the code deploy, contract in a later release ([Migrations in the Pipeline](#migrations-in-the-pipeline))
- **service-to-service APIs** — add fields; remove or rename only after every caller has moved
- **queued job payloads** — new code reads messages the old code queued, and old workers either tolerate new messages or never receive them
- **cache entries** — version the key, or read both shapes

### Blue-Green Deployment

Run two identical environments: deploy to the idle one, smoke-test it, then switch the load balancer to it; rollback is switching back. Both colours usually share one database, so that instant rollback holds only while the schema still serves the old code, the same compatibility rule as a rolling deploy. The cost is a second full environment.

### Canary Releases

Send a small share of traffic (say 5%) to the new version, compare its error rate and latency with the old version's, and widen in steps (25%, 50%, 100%), rolling back at any step whose metrics degrade. It needs traffic splitting, and monitoring good enough to see a regression in 5% of traffic; without that, a canary is just a slow rolling deploy.

### Feature Flags

Deploy code but keep it hidden behind a flag:

```typescript
// The code is deployed but inactive
if (featureFlags.isEnabled('new-checkout', { userId: user.id })) {
  return <NewCheckout />;
} else {
  return <OldCheckout />;
}
```

The workflow:

1. Deploy with flag off (code is in production but nobody can reach it)
2. Enable for internal users (your team tests in production)
3. Enable for 10% of users (canary-like, but at the feature level)
4. Enable for everyone
5. If it breaks at any stage — turn off the flag, no deployment needed

**The deploy and the release are separate events.** You can deploy on Monday and release on Wednesday. You can release to staff before customers. You can instantly disable a feature without a deploy.

**Tradeoff:** Feature flags add complexity to your codebase. Old flags that are never cleaned up become tech debt. Establish a practice: when a flag is fully rolled out, remove it in the next sprint.

**Tools:** LaunchDarkly (SaaS), Unleash (self-hosted), Vercel Feature Flags, environment variables (simplest — just `if (env.ENABLE_NEW_CHECKOUT)`). Env-var flags are deploy-time switches: flipping one needs a redeploy or restart, so they let you ship code switched off but are not the no-deploy kill switch in step 5 above.

### When to Use Which

| Pattern                                    | Best for                                                                    | Complexity  |
| ------------------------------------------ | --------------------------------------------------------------------------- | ----------- |
| **Simple deploy** (stop old, start new)    | Solo projects, early stage, can tolerate brief downtime                     | Low         |
| **Rolling** (the platform default)         | Most services on a container platform; zero downtime with compatible releases | Low         |
| **Blue-green**                             | Instant rollback by switching back                                          | Medium      |
| **Canary**                                 | High traffic, need to detect issues before they affect all users            | Medium-High |
| **Feature flags**                          | Decoupling deploy from release, gradual rollouts, A/B testing               | Medium      |

For most projects starting out: **the platform's rolling deploy + feature flags** gets you 80% of the benefit with minimal infrastructure.

---

## Rollback Strategy

When something goes wrong, how fast can you get back to the last working state? This needs to be planned, not improvised during an incident.

### The Rollback Checklist

1. **Can you re-deploy the previous version?** You should be able to deploy any recent version in under 5 minutes. If your deploy process takes 30 minutes, your recovery time is at least 30 minutes.
2. **Does the new schema still serve the previous code version?** A rollback redeploys old code against the schema you have *now* — roll back code, not schema. If your deploy includes a migration that drops a column the previous version reads, the rollback crashes. Down-migrations that drop data are not incident tools. See [Schema Evolution](./schema-evolution.md) for the expand-and-contract pattern that keeps each schema compatible with the release before it.
3. **Do you have a runbook?** When something breaks at 2am, the oncall engineer shouldn't be figuring out rollback steps for the first time. See [Monitoring](./monitoring.md) for runbook practices.
4. **Have you tested the rollback?** An untested rollback is not a rollback — it's a hope. Practice it.
5. **Roll back or roll forward?** Decide the policy before the incident. Roll back by default: redeploy the previous artifact, which is fast if item 1 holds and safe if item 2 does. Roll forward, shipping a fix through the normal pipeline, when the release wrote data or queued work the previous version can't read. Either way the fix goes through CI, not around it.

### The Migration-Rollback Problem

The most common failed rollback: release v1.1 drops the `name` column and ships code that reads `first_name`, so rolling back to v1.0 redeploys code that reads `name` against a schema that no longer has it. Drop the column in a later release than the code change, as [Schema Evolution](./schema-evolution.md#the-expand-and-contract-pattern) walks through.

---

## Dependency Management

Every project depends on code written by other people. Managing those dependencies is a security and stability concern.

### Lockfiles

`pnpm-lock.yaml`, `package-lock.json`, `poetry.lock`, `uv.lock` — record the exact version of every dependency and sub-dependency. They ensure:

- Everyone on the team gets identical versions
- CI builds are reproducible
- A library releasing a buggy patch doesn't silently break your build

**Always commit your lockfile.**

### Reproducible installs

For TypeScript, **pnpm is the default**. It differs from npm in three ways that matter: a content-addressable global store hard-linked into each project (faster installs, far less disk), a strict non-flat `node_modules` that blocks *phantom dependencies* (you can only import what `package.json` declares), and first-class workspaces for monorepos. npm and yarn remain common alternatives — the install discipline is identical for all three.

| Command                          | When to use                            | What it does                                                              |
| -------------------------------- | -------------------------------------- | ------------------------------------------------------------------------ |
| `pnpm install`                   | Development — adding/updating packages | Reads `package.json`, may update `pnpm-lock.yaml`                         |
| `pnpm install --frozen-lockfile` | CI/CD pipelines                        | Installs the lockfile exactly, fails if out of sync (`npm ci` equivalent) |

In CI, always use the frozen install (`pnpm install --frozen-lockfile`; `npm ci` if you're on npm). It guarantees the build uses exactly what the lockfile says — a plain install can silently resolve different versions. pnpm already freezes when it detects CI and a lockfile, but a `docker build` sets no `CI` variable and not every runner is detected, so pass the flag explicitly.

Python equivalents: `uv sync --locked` (fails if `uv.lock` is out of date — plain `uv sync` silently re-locks, and `--frozen` skips the check entirely), or `poetry check --lock` then `poetry install` (`poetry sync` on Poetry 2.x).

### Version Pinning

```
"lodash": "4.17.21"      → exact pin — most conservative
"lodash": "^4.17.21"     → caret — allows minor/patch updates (default)
"lodash": "~4.17.21"     → tilde — allows only patch updates
```

Most teams use `^` (the default) and rely on the lockfile for reproducibility, then update intentionally with `pnpm update`. That holds for applications, whose lockfile is what ships. A library you publish states ranges, because its lockfile never reaches consumers and exact pins only force duplicate copies on them; the same split holds in Python, where an app is pinned by `uv.lock` and a library's `pyproject.toml` states ranges.

### Update Cadence

Update dependencies regularly — monthly is a common cadence. The longer you wait:

- More breaking changes accumulate
- Security vulnerabilities go unpatched
- The update becomes a scary, risky event instead of routine maintenance

**Process:** Once a month, run `pnpm outdated` (or `uv tree --outdated` in a uv project), update packages, run tests, create a PR. Dependabot version updates (configured in `.github/dependabot.yml`) can automate this.

### Vulnerability Scanning

```bash
# pnpm 11+ · pip-audit 2 · uv
pnpm audit --prod --audit-level high   # CI gate: production deps, high/critical only
pnpm update <pkg>                      # bump a flagged package to a patched version
# npm: npm audit --omit=dev --audit-level=high

# Python (`safety check` is deprecated)
pip-audit                              # pip install pip-audit
uv lock --upgrade-package <pkg>        # bump a flagged package in a uv project
```

**Run in CI, as a gate with a threshold.** Don't just run locally. A gate that fails on every advisory is noisy (dev-only tools, code paths you never reach), and noisy gates get switched off. Gate on production dependencies at high/critical, keep a documented ignore list with a reason per entry (on pnpm 11.16+, a list of GHSA ids under `audit.ignore` in `pnpm-workspace.yaml`, which `pnpm audit --ignore <GHSA>` appends to once the list exists; pnpm 11 stopped reading pnpm 10's `auditConfig.ignoreCves`, so convert CVE entries to GHSA ids when upgrading; `pip-audit --ignore-vuln`), and require explicit approval to deploy past a finding.

**Dependabot** (GitHub, free) has three separate parts. *Alerts* flag vulnerable dependencies but open no PRs. *Security updates* open PRs that bump a vulnerable dependency to a patched version (repo Settings → Security → Dependabot security updates). *Version updates* open routine upgrade PRs and need a `.github/dependabot.yml`.

### Install-Time Supply-Chain Controls

Installing a package runs code, and a compromised release can read CI secrets before any scan runs. Four controls close that gap:

- **Dependency build scripts need approval.** pnpm 10 and later run a dependency's install scripts only once they are allowed. pnpm 11 records approvals in `allowBuilds` in `pnpm-workspace.yaml`, replacing pnpm 10's `onlyBuiltDependencies` (`pnpm approve-builds` writes it), and its default `strictDepBuilds` fails the install when a dependency's build script has no ruling. npm 12 also blocks dependency install scripts by default and records approvals in `allowScripts` in package.json (`npm install-scripts approve <pkg>`), but it skips an unapproved script without failing the install, only listing it at the end. npm 11 and earlier, which Node 22, 24 and 26 LTS still bundle, run every script unless you pass `--ignore-scripts`.
- **A release cooldown, with a fast lane for fixes.** Waiting before adopting a new version gives the registry and scanners time to catch a compromised one. pnpm 11 won't resolve a version younger than `minimumReleaseAge` (1440 minutes, one day, by default), and Dependabot version updates wait three days by default (its `cooldown` option). Security fixes must not wait: Dependabot security updates skip the cooldown, and `pnpm audit --fix` adds each patched version to `minimumReleaseAgeExclude`.
- **Pin third-party GitHub Actions to a full commit SHA**, with the version in a comment (`uses: owner/action@<40-character SHA> # v4.2.0`). A tag can be moved to different code after you reviewed it, as happened to `tj-actions/changed-files` in March 2025. Dependabot keeps SHA pins current.
- **CI reaches the cloud through OIDC federation**, not stored keys. The job requests `permissions: id-token: write` and exchanges its short-lived token for a role whose trust policy names the repository and the branch or environment, so there is no long-lived credential to leak or rotate. Keep the workflow's default `permissions` read-only and grant more per job.

---

## CI/CD Pipeline Basics

CI/CD (Continuous Integration / Continuous Deployment) automates your build, test, and deploy process:

```
Developer pushes code
        ↓
CI Pipeline runs:
  1. Install dependencies (pnpm install --frozen-lockfile)
  2. Lint code
  3. Type check (tsc --noEmit)
  4. Run tests
  5. Security scan (pnpm audit)
  6. Build the artifact, once
        ↓
CD Pipeline runs (if CI passes), for staging and then production:
  7. Run expand migrations as a one-off job
  8. Roll out the artifact
  9. Run smoke tests against it
```

**Key principles:**

- **Fast feedback:** The pipeline should tell you about failures in minutes, not hours.
- **Fail fast:** Run the cheapest checks first (lint, type check) before expensive ones (tests, build).
- **Reproducible:** Use lockfiles, pin tool versions, run the frozen install (`pnpm install --frozen-lockfile`) not a plain install.
- **Gated:** Production deploy only happens if all previous steps pass. A check gates a merge only if branch protection or a ruleset marks it required, and its verdict counts only for the exact head SHA being merged, not an earlier push.

**Tools:** GitHub Actions (most common for GitHub repos), GitLab CI, CircleCI, Jenkins.

### Migrations in the Pipeline

Run migrations as their own pipeline step before the rollout, not from app startup. When every replica migrates on boot, the replicas race each other (neither Drizzle's migrator nor Alembic takes an advisory lock), and a migration that fails becomes a crash-looping deploy instead of one failed step. Use a one-off job that must succeed before the rollout starts: an ECS run-task, a Kubernetes Job or Helm pre-upgrade hook, or the platform's release or pre-deploy command. That step runs only the *expand* half, which leaves the schema usable by the release still serving. Because it runs before the release's code is live, a backfill rides with the release after the dual-write code. The *contract* half ships in a later release, once nothing running reads what it removes. [Schema Evolution](./schema-evolution.md#the-expand-and-contract-pattern) has the phases.

### Environment promotion

Modern teams run **trunk-based**: one long-lived branch (`main`), short-lived feature branches merged via PR — no permanent `staging`/`prod` branches. Every merge to `main` auto-deploys to a non-prod environment (UAT/staging); production is a **gated promotion**, not another branch merge.

- **Build once, promote the same artifact.** Promote the exact build that passed UAT to production — never rebuild for prod (a rebuild can resolve different versions, or surface "works in staging, breaks in prod"). This holds only if the build reads nothing environment-specific: a value inlined at build time (`NEXT_PUBLIC_*`, `VITE_*`, a Docker build arg) is frozen into the artifact, so keep environment-selecting values out of it ([Configuration](./configuration.md#build-time-vs-runtime-configuration)).
- **Gate the promotion.** Production waits behind an approval — e.g. GitHub Environments' required-reviewer rule — and runs with environment-scoped secrets.
- **Smoke-gate each step.** Run the smoke tests after each deploy as an automated pipeline step that fails the deploy, not a suite someone runs by hand. In a promotion model, a failing staging smoke blocks promotion to prod. Probe the real public entry point with a generous per-endpoint retry window so cold starts don't read as failures, and keep health endpoints unauthenticated so the probe can reach them. What the smoke tests assert is listed in [Testing](./testing.md#smoke-tests--does-the-deployed-system-serve-real-requests).

### Infrastructure as Code

Infrastructure changes get the same review as code. Run `terraform plan -out=<file>` in the pull request so reviewers read the exact change, including any replacement (`-/+`) that a small edit to a create-only attribute can force ([The Description That Deadlocked](./pitfalls.md#the-description-that-deadlocked)), and apply that saved plan rather than a fresh one. The saved plan holds variable values, sensitive ones included, in cleartext, so keep it in a short-lived, access-restricted store, not a readable workflow artifact. Keep state remote with locking, and never edit a managed resource in the console: the next apply reverts the edit or trips over it.

---

## Anti-Patterns

| Don't                                                    | Do Instead                                            | Why                                                             |
| -------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| Deploy directly to production without testing            | Deploy to staging first, run smoke tests              | Most outages follow a change, and a staging smoke run catches a broken one before users do |
| Drop database columns in the same deploy as code changes | Use expand-and-contract (separate deploys)            | Makes rollback impossible                                       |
| Ship a release that only works with the new schema, API or job format | Keep each release compatible with the one before it | Old and new code run side by side during every rollout |
| Run migrations from app startup on every replica         | Run them as a pre-deploy job                          | Replicas race, and a failed migration becomes a crash loop      |
| Deploy with a plain `pnpm install` / `npm install` in CI | Use the frozen install (`pnpm install --frozen-lockfile`; `npm ci` on npm) | Outside a detected CI (npm always, pnpm inside `docker build`), a plain install can resolve versions your lockfile doesn't hold |
| Wait 6 months to update dependencies                     | Update monthly (or enable Dependabot)                 | Deferred updates become high-risk big-bang migrations           |
| Ignore audit findings (`pnpm audit`, `pip-audit`)        | Gate CI on production deps at high/critical, with a documented ignore list | Known vulnerabilities are the easiest attack vector; an unthresholded gate gets switched off |
| Reference third-party Actions by tag                     | Pin each to a full commit SHA                         | A tag can be moved to malicious code after you reviewed it      |
| Leave feature flags in code after full rollout           | Remove flags in the sprint after full rollout         | Stale flags become confusing dead code                          |
| Skip rollback planning                                   | Document rollback steps before deploying              | Improvising rollback during an incident wastes critical time    |

---

## Deciding for Your Project

1. **What's your deploy target?** Vercel/Netlify (handles most of this for you), containers (Docker/K8s — you manage more), bare VMs (you manage everything).
2. **What does your platform already do on deploy?** Most roll instances out with no downtime, given health checks, graceful shutdown and releases compatible with their predecessor. Add blue-green for instant rollback, or canary to expose a small share of traffic first, only where that is worth a second environment or traffic splitting.
3. **Do you need feature flags?** If you want to decouple deploy from release, or do gradual rollouts → yes. For simple apps → env variable flags are sufficient (but they are deploy-time switches: changing one needs a redeploy).
4. **What's your CI/CD platform?** GitHub Actions is the default for GitHub repos. Match your platform.
5. **Where do migrations run?** A pre-deploy job before the rollout, running the expand half only; the contract half ships in a later release.
6. **Roll back or roll forward?** Default to redeploying the previous artifact, name the cases that roll forward, and document and test the rollback before your first production deploy.
7. **How do dependencies stay current, and what fails the build?** Decide the update automation (Dependabot version and security updates), the release cooldown, and the audit gate's severity threshold, with an owner for its ignore list.
8. **How many database connections will a rollout open?** Instances × workers × pool size, and during a rolling deploy old and new instances overlap, so the total rises for a while. Keep it under the database's limit ([Resilience](./resilience.md#fan-out-and-connection-pools)).

---

## Related Topics

- **Database migrations and rollback** — see [Schema Evolution](./schema-evolution.md) for expand-and-contract pattern and migration safety
- **Graceful shutdown during deploys** — see [Resilience](./resilience.md#graceful-shutdown) for SIGTERM handling and connection draining
- **Health checks for deploy verification** — see [Resilience](./resilience.md#health-checks) for liveness/readiness probes
- **Races, locking and deadlocks** — see [Data Integrity](./data-integrity.md#concurrency-control) for conditional updates, optimistic and pessimistic locking and deadlock retries, and its [Transactions Behind a Pooler](./data-integrity.md#transactions-behind-a-pooler) for what a transaction-mode pooler breaks
- **Parallel calls and connection pools** — see [Resilience](./resilience.md#fan-out-and-connection-pools) for bounded fan-out, `Promise.all` vs `allSettled`, and pool sizing
- **Secrets in CI/CD** — CI authenticates through OIDC federation ([above](#install-time-supply-chain-controls)); see [Configuration](./configuration.md#secret-delivery-and-rotation) for how secrets reach the running app
- **Build-time configuration** — see [Configuration](./configuration.md#build-time-vs-runtime-configuration) for keeping environment-selecting values out of the artifact
- **Which dependencies to trust** — see [Security](./security.md#supply-chain) for release-age delays, install scripts and typosquats as trust decisions; the settings that enforce them are above
- **Deploy smoke tests** — see [Testing](./testing.md#smoke-tests--does-the-deployed-system-serve-real-requests) for what a post-deploy smoke test should assert
