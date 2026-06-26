# Deployment & Operations

## The Problem

Getting code from "it works on my machine" to "it's running in production serving real users" is where most outages happen. The deploy itself is the most dangerous moment — you're changing a running system. Deployment and operations patterns exist to make this safe and recoverable.

---

## Release Patterns

### Blue-Green Deployment

Two identical production environments — "blue" (currently serving traffic) and "green" (idle):

```
Before deploy:
  Load Balancer → [Blue - v1.0] (live)
                   [Green - idle]

During deploy:
  Load Balancer → [Blue - v1.0] (live)
                   [Green - v1.1] (deploying + smoke testing)

After switch:
  Load Balancer → [Blue - v1.0] (idle, kept as rollback)
                   [Green - v1.1] (live)

If something's wrong:
  Load Balancer → [Blue - v1.0] (live again — instant rollback)
                   [Green - v1.1] (pulled)
```

**Key benefit:** Instant rollback — just flip the load balancer. No re-deploying old code.

**Tradeoff:** You need two identical environments, which doubles infrastructure cost. For small projects, this might be overkill.

### Canary Releases

Instead of sending 100% of traffic to new code at once, start small:

```
Phase 1: 5% of traffic → v1.1, 95% → v1.0
          Monitor error rates, latency for 10 minutes
Phase 2: 25% → v1.1, 75% → v1.0
          Monitor for 10 minutes
Phase 3: 50% → v1.1, 50% → v1.0
          Monitor for 10 minutes
Phase 4: 100% → v1.1
          v1.0 instances shut down

At any phase, if metrics degrade → roll back to 100% v1.0
```

Named after "canary in a coal mine." A small group detects danger before it affects everyone.

**Tradeoff:** More complex than blue-green. Requires traffic routing capabilities and good monitoring to detect issues at small percentages.

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

**Tools:** LaunchDarkly (SaaS), Unleash (self-hosted), Vercel Feature Flags, environment variables (simplest — just `if (env.ENABLE_NEW_CHECKOUT)`).

### When to Use Which

| Pattern                                | Best for                                                         | Complexity  |
| -------------------------------------- | ---------------------------------------------------------------- | ----------- |
| **Simple deploy** (just push new code) | Solo projects, early stage, can tolerate brief downtime          | Low         |
| **Blue-green**                         | Zero-downtime requirement, need instant rollback                 | Medium      |
| **Canary**                             | High traffic, need to detect issues before they affect all users | Medium-High |
| **Feature flags**                      | Decoupling deploy from release, gradual rollouts, A/B testing    | Medium      |

For most projects starting out: **simple deploy + feature flags** gets you 80% of the benefit with minimal infrastructure.

---

## Rollback Strategy

When something goes wrong, how fast can you get back to the last working state? This needs to be planned, not improvised during an incident.

### The Rollback Checklist

1. **Can you re-deploy the previous version?** You should be able to deploy any recent version in under 5 minutes. If your deploy process takes 30 minutes, your recovery time is at least 30 minutes.
2. **Are your database migrations reversible?** If your deploy includes a migration that drops a column, you can't roll back the code (it depends on the column). See [Schema Evolution](./schema-evolution.md) for the expand-and-contract pattern that keeps migrations reversible.
3. **Do you have a runbook?** When something breaks at 2am, the oncall engineer shouldn't be figuring out rollback steps for the first time. See [Monitoring](./monitoring.md) for runbook practices.
4. **Have you tested the rollback?** An untested rollback is not a rollback — it's a hope. Practice it.

### The Migration-Rollback Problem

The most common source of failed rollbacks:

```
Deploy v1.1:
  1. Run migration: ALTER TABLE users DROP COLUMN name  ← IRREVERSIBLE
  2. Deploy code that reads first_name, last_name

Rollback to v1.0:
  1. Deploy old code that reads "name"  ← CRASH: column doesn't exist
```

**Solution:** Use the expand-and-contract pattern from [Schema Evolution](./schema-evolution.md). Never drop columns in the same deploy that changes the code that reads them. Separate them by at least one deploy cycle.

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

In CI, always use the frozen install (`pnpm install --frozen-lockfile`; `npm ci` if you're on npm). It guarantees the build uses exactly what the lockfile says — a plain install can silently resolve different versions.

Python equivalents: `uv sync` (reads lockfile exactly), `poetry install --no-update`.

### Version Pinning

```
"lodash": "4.17.21"      → exact pin — most conservative
"lodash": "^4.17.21"     → caret — allows minor/patch updates (default)
"lodash": "~4.17.21"     → tilde — allows only patch updates
```

Most teams use `^` (the default) and rely on the lockfile for reproducibility, then update intentionally with `pnpm update`.

### Update Cadence

Update dependencies regularly — monthly is a common cadence. The longer you wait:

- More breaking changes accumulate
- Security vulnerabilities go unpatched
- The update becomes a scary, risky event instead of routine maintenance

**Process:** Once a month, run `pnpm outdated` (or `uv pip list --outdated`), update packages, run tests, create a PR. Dependabot can automate this.

### Vulnerability Scanning

```bash
# pnpm / npm — built-in
pnpm audit                 # report known vulnerabilities
pnpm update <pkg>          # bump a flagged package to a patched version

# Python
pip-audit            # pip install pip-audit
safety check         # pip install safety
```

**Run in CI.** Don't just run locally — make it a gate in your pipeline. A deploy with known vulnerable dependencies should require explicit approval.

**Dependabot** (GitHub, free) — automatically creates PRs to update vulnerable dependencies. Enable it: repo Settings → Security → Dependabot alerts → Enable.

---

## Concurrency Patterns

Most production code is async — handling multiple requests simultaneously. Concurrency bugs are the hardest to find because they're non-deterministic. Your tests pass 99 times and fail on the 100th.

### Race Conditions

The outcome depends on the order in which concurrent operations complete:

```
User A reads balance: $100
User B reads balance: $100
User A withdraws $80, writes: $20
User B withdraws $80, writes: $20  ← should be rejected!
```

Both reads happened before either write. Both saw $100. $160 was withdrawn from a $100 account.

**Solutions:**

**Optimistic locking** — every record has a version number:

```sql
-- Read: note the version
SELECT balance, version FROM accounts WHERE id = 123;
-- balance = 100, version = 5

-- Write: only succeed if version hasn't changed
UPDATE accounts SET balance = 20, version = 6
WHERE id = 123 AND version = 5;
-- If this affects 0 rows, someone else modified it — retry or reject
```

**Pessimistic locking** — lock the row while you're working:

```sql
-- Lock the row — other transactions wait
SELECT balance FROM accounts WHERE id = 123 FOR UPDATE;
-- Do your work...
UPDATE accounts SET balance = 20 WHERE id = 123;
COMMIT;
-- Lock released, other transactions can proceed
```

**When to use which:**

- **Optimistic:** Conflicts are rare, you don't want to block users (most web apps)
- **Pessimistic:** Conflicts are common, correctness is critical (financial transactions)

### Promise.all vs Promise.allSettled

When running multiple async operations in parallel:

```typescript
// Promise.all — FAILS FAST: if ANY promise rejects, everything rejects
try {
  const [users, orders] = await Promise.all([
    fetchUsers(),   // succeeds
    fetchOrders(),  // fails
  ]);
} catch (err) {
  // You get the error, but you LOSE the successful users result
}

// Promise.allSettled — waits for ALL, reports each result independently
const results = await Promise.allSettled([fetchUsers(), fetchOrders()]);
// results[0] = { status: 'fulfilled', value: [...users] }
// results[1] = { status: 'rejected', reason: Error(...) }
// You get BOTH results — can handle each independently
```

**Python equivalent:**

```python
import asyncio

# Default: if one fails, exception propagates (like Promise.all)
users, orders = await asyncio.gather(fetch_users(), fetch_orders())

# With return_exceptions: failures returned as values (like Promise.allSettled)
results = await asyncio.gather(
    fetch_users(), fetch_orders(),
    return_exceptions=True,
)
# results[0] might be a list of users
# results[1] might be an Exception object
```

**When to use which:**

- `Promise.all` / `asyncio.gather()`: When all results are needed and any failure should abort
- `Promise.allSettled` / `asyncio.gather(return_exceptions=True)`: When results are independent and partial success is useful

### Connection Pooling

Database connections are expensive to create (TCP handshake, TLS, authentication). A connection pool maintains a set of open connections and lends them to requests:

```typescript
// BAD: new connection per request — slow, wasteful, will exhaust DB limits
app.get('/users', async (req, res) => {
  const client = new Client(env.DATABASE_URL);
  await client.connect();
  const result = await client.query('SELECT * FROM users');
  await client.end();
  res.json(result.rows);
});

// GOOD: pool reuses connections across requests
const pool = new Pool({
  connectionString: env.DATABASE_URL,
  max: 20,  // max simultaneous connections
});

app.get('/users', async (req, res) => {
  const result = await pool.query('SELECT * FROM users');
  res.json(result.rows);
});
```

```python
# SQLAlchemy — pool is built into the engine
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    settings.database_url,
    pool_size=10,       # maintained connections
    max_overflow=20,    # extra connections under load
    pool_timeout=30,    # seconds to wait for a connection
)
```

**Pool sizing:** Too small → requests queue up waiting (saturation). Too large → database gets overwhelmed with connections. Start with 10-20, monitor, adjust based on your [Monitoring](./monitoring.md) metrics.

### Deadlock Prevention

Two operations each hold a resource the other needs:

```
Transaction A: locks Row 1, then tries to lock Row 2
Transaction B: locks Row 2, then tries to lock Row 1
→ Both wait forever
```

**Prevention:** Always acquire locks in the same order (e.g., by ascending ID). If every transaction locks rows in ID order, deadlocks can't occur.

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
  6. Build
        ↓
CD Pipeline runs (if CI passes):
  7. Deploy to staging
  8. Run smoke tests against staging
  9. Deploy to production
  10. Run smoke tests against production
```

**Key principles:**

- **Fast feedback:** The pipeline should tell you about failures in minutes, not hours.
- **Fail fast:** Run the cheapest checks first (lint, type check) before expensive ones (tests, build).
- **Reproducible:** Use lockfiles, pin tool versions, run the frozen install (`pnpm install --frozen-lockfile`) not a plain install.
- **Gated:** Production deploy only happens if all previous steps pass.

**Tools:** GitHub Actions (most common for GitHub repos), GitLab CI, CircleCI, Jenkins.

### Environment promotion

Modern teams run **trunk-based**: one long-lived branch (`main`), short-lived feature branches merged via PR — no permanent `staging`/`prod` branches. Every merge to `main` auto-deploys to a non-prod environment (UAT/staging); production is a **gated promotion**, not another branch merge.

- **Build once, promote the same artifact.** Promote the exact build that passed UAT to production — never rebuild for prod (a rebuild can resolve different versions, or surface "works in staging, breaks in prod").
- **Gate the promotion.** Production waits behind an approval — e.g. GitHub Environments' required-reviewer rule — and runs with environment-scoped secrets.
- **Smoke-gate each step.** The smoke tests after each deploy should be an automated pipeline step that fails the deploy on any non-2xx — not a suite someone runs by hand. In a promotion model, a failing staging smoke blocks promotion to prod. Probe the real public entry point with a generous per-endpoint retry window so cold starts don't read as failures, and keep health endpoints unauthenticated so the probe can reach them.

---

## Anti-Patterns

| Don't                                                    | Do Instead                                            | Why                                                             |
| -------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| Deploy directly to production without testing            | Deploy to staging first, run smoke tests              | Untested deploys are the #1 cause of outages                    |
| Drop database columns in the same deploy as code changes | Use expand-and-contract (separate deploys)            | Makes rollback impossible                                       |
| Deploy with `npm install` in CI                          | Use `npm ci` — reproducible builds                    | `npm install` can resolve different versions than your lockfile |
| Wait 6 months to update dependencies                     | Update monthly (or enable Dependabot)                 | Deferred updates become high-risk big-bang migrations           |
| Ignore `npm audit` findings                              | Run audit in CI as a gate                             | Known vulnerabilities are the easiest attack vector             |
| Use `Promise.all` when partial success is acceptable     | Use `Promise.allSettled` for independent operations   | `Promise.all` throws away successful results when one fails     |
| Leave feature flags in code after full rollout           | Remove flags in the sprint after full rollout         | Stale flags become confusing dead code                          |
| Create a new DB connection per request                   | Use a connection pool                                 | Per-request connections are slow and exhaust DB limits          |
| Acquire locks in inconsistent order                      | Always lock resources in the same order (e.g., by ID) | Inconsistent ordering causes deadlocks                          |
| Skip rollback planning                                   | Document rollback steps before deploying              | Improvising rollback during an incident wastes critical time    |

---

## Deciding for Your Project

1. **What's your deploy target?** Vercel/Netlify (handles most of this for you), containers (Docker/K8s — you manage more), bare VMs (you manage everything).
2. **Do you need zero-downtime deploys?** If users notice downtime → blue-green or canary. If brief downtime is OK → simple deploy is fine.
3. **Do you need feature flags?** If you want to decouple deploy from release, or do gradual rollouts → yes. For simple apps → env variable flags are sufficient.
4. **What's your CI/CD platform?** GitHub Actions is the default for GitHub repos. Match your platform.
5. **What's your rollback strategy?** Document it before your first production deploy. Test it.
6. **What database do you use?** Relational DBs need connection pooling. Serverless DBs (Neon, PlanetScale) handle pooling for you.

---

## Related Topics

- **Database migrations and rollback** — see [Schema Evolution](./schema-evolution.md) for expand-and-contract pattern and migration safety
- **Graceful shutdown during deploys** — see [Resilience](./resilience.md) for SIGTERM handling and connection draining
- **Health checks for deploy verification** — see [Resilience](./resilience.md) for liveness/readiness probes
- **Deploy metrics** — see [Monitoring](./monitoring.md) for tracking deploy frequency, failure rate, and rollback frequency
- **Secrets in CI/CD** — see [Configuration](./configuration.md) and [Security](./security.md) for managing secrets in pipelines
- **Dependency vulnerabilities** — see [Security](./security.md) for scanning and supply chain security
- **Deploy smoke tests** — see [Testing](./testing.md) for what a post-deploy smoke test should assert
