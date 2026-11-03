# Pitfalls

Anti-patterns observed in real codebases during production readiness assessments. Each pitfall is named, brief, and references the relevant handbook chapter for the correct approach.

**How to use:** Scan the relevant section before starting work. If you recognise a pattern you're about to create, stop and check the referenced topic file for the correct approach.

**These are guardrails, not rules.** Some situations genuinely call for what looks like a pitfall (e.g., a module-level singleton for a truly global resource). The point is to make it a conscious choice rather than an accidental default.

---

## When Writing a Function or Module

### The Singleton Trap
Creating a service client (database, API, cache) at module level and importing it directly everywhere. Every consumer is now married to that specific client — you can't swap it for testing, point it at a different environment, or create isolated instances.
**Instead:** Accept clients as parameters or use a provider pattern. See [Configuration](./configuration.md#service-clients-are-built-in-the-composition-root).

### Trapped Logic
Embedding business calculations inside data-fetching functions or I/O code. The calculation is correct but unreachable without also setting up the entire I/O chain. Commission formulas inside database hooks. Scoring algorithms inside API handlers.
**Instead:** Extract substantial pure logic into standalone functions that take explicit inputs and return explicit outputs. See [Module Design](./module-design.md#structuring-around-dependencies) and [Testing](./testing.md#unit-tests--does-this-logic-work-in-isolation).

### The Read-That-Writes
A function that appears to read data but secretly creates records, triggers API calls, or mutates state as a side effect. Breaks assumptions about safety, makes caching dangerous, and can cost real money (AI API calls) on every refetch.
**Instead:** Separate read and write operations. If a read needs to trigger a write (e.g., lazy initialisation), make it explicit in the function name and documentation.

### The Unreachable Calculation
Writing a substantial pure calculation inside a closure or hook body, where no test can reach it. The logic is clean but unverifiable. Often happens when a utility function is written "just for this hook" and never given a home.
**Instead:** Give a substantial calculation a home inside its module and test it through the module's interface or an internal seam. Export it only when a real second caller needs it; an export added just for tests becomes interface that other code couples to. See [Module Design](./module-design.md#judging-a-proposed-module).

### Copy-Paste Utilities
Redefining a helper function locally instead of importing the shared version. Each copy drifts slightly — different null handling, different formatting, different edge cases. The shared version exists but nobody uses it.
**Instead:** Search for an existing utility before writing one. Share a helper when it encodes a rule that must change together everywhere it is used (rounding, a currency or date format); code that merely looks alike can stay local until it proves to be the same rule. See [Module Design](./module-design.md#judging-a-proposed-module).

---

## When Designing a Schema or Data Model

### Missing Database Constraints
Relying entirely on application-layer validation (Pydantic, Zod, TypeScript types) without database-level enforcement. Application bugs, direct database access, and ETL pipelines will all bypass your application validation. Orphaned records, impossible states, and corrupted aggregations follow.
**Instead:** Enforce integrity at both layers. FKs for relationships, CHECKs for valid values, UNIQUE for natural keys. Application validation for user experience; database constraints for data safety. See [Data Integrity](./data-integrity.md#database-level-integrity).

### The Case Sensitivity Bug
Storing user-facing string values (statuses, categories, types) without normalisation or constraints. The ETL writes "Active", the UI writes "active", the seed script writes "ACTIVE". Queries that filter on one case silently exclude the others.
**Instead:** Normalise at ingest (lowercase), add a CHECK constraint for valid values, and treat any new casing as a bug. See [Data Integrity](./data-integrity.md#database-level-integrity).

### The Loose Foreign Key
Joining tables on string columns (customer_code, product_code) without FK constraints. Works fine until the ETL loads a batch of orders referencing customers that haven't been imported yet, or a customer gets deleted while their orders remain. Aggregations silently exclude orphaned rows.
**Instead:** Add FK constraints. Use `NOT VALID` initially if you're adding to an existing table with potentially dirty data, then validate after cleanup. Where a load inserts children before parents, declare the FK `DEFERRABLE INITIALLY DEFERRED` and load in one transaction, so it is checked at commit. See [Schema Evolution](./schema-evolution.md#adding-constraints-to-existing-tables).

### The Invalid Index Left Behind
A `CREATE INDEX CONCURRENTLY` that fails (duplicate, lock timeout, cancelled deploy) leaves an INVALID index: queries ignore it, writes still maintain it, a rerun fails with "already exists", and `IF NOT EXISTS` reports success while leaving it invalid.
**Instead:** `DROP INDEX CONCURRENTLY IF EXISTS` before every retry, and check `pg_index.indisvalid` after the build. See [Schema Evolution](./schema-evolution.md#lock-queueing--the-outage-expand-and-contract-does-not-prevent).

### The Migration Skipped by Its Timestamp
A Drizzle migration (drizzle-orm 0.x; v1 selects by name) generated on a branch before another that has since deployed carries the older journal timestamp. `migrate` runs only entries newer than the newest applied one, so it skips the branch's migration for ever and the deploy exits 0.
**Instead:** Regenerate a branch's migration on current `main` before merging, and make the migrate step fail when a journal entry is older than the newest applied one and has no row. See [Schema Evolution](./schema-evolution.md#drizzle-typescript).

---

## When Connecting to External Services

### Production Defaults
Setting the production URL or credentials as the default value when an environment variable is missing. A test run with missing config silently hits production. A developer running the ETL locally corrupts live data.
**Instead:** Required credentials should have no default — fail at startup if missing. Only provide defaults for genuinely safe values (localhost URLs, development ports). See [Configuration](./configuration.md#environment-variable-validation).

### The Hardwired Client
Creating API clients, database connections, or SDK instances inline inside business logic. The function works, but you can't test it without the real service, can't point it at a staging environment, and can't control its behaviour in development.
**Instead:** Create clients at the application boundary (startup, request handler entry) and pass them to the functions that need them. See [Configuration](./configuration.md#service-clients-are-built-in-the-composition-root).

### Error Leaking
Catching an error and returning it directly to the client: `return { error: String(err) }`. The error object may contain connection strings, file paths, stack traces, API keys from headers, or internal service names.
**Instead:** Log a safe serialisation of the error server-side with the correlation ID (a driver's error text carries the query's values). Return a generic message and the correlation ID to the client. See [Error Handling](./error-handling.md#http-error-response-schema) and [Logging](./logging.md#scrubbing-sensitive-data).

### CORS Wildcard
Opening CORS to any origin *with credentials* because it's the fastest way to stop CORS errors during development: reflecting the request's origin (`origin: true` with `credentials: true` in Express `cors`), matching origins with a loose regex or suffix, allowing the `null` origin, or pairing Starlette/FastAPI `allow_origins=["*"]` with `allow_credentials=True`, which echoes the caller's origin. Any website can then read responses to your users' cookie-authenticated requests. A literal `Access-Control-Allow-Origin: *` is not the hole: browsers refuse it on credentialed requests, and it is harmless on a bearer-token API.
**Instead:** Restrict credentialed CORS to an explicit list of your frontend origins, compared exactly. Use environment-specific CORS configuration. CORS decides who may *read* responses, not who may send requests, so it is no substitute for CSRF protection. See [Security](./security.md#cors-cross-origin-resource-sharing).

### The Audience Check Switched Off
Verifying Cognito access tokens with a generic JWT verifier that requires `aud`. Cognito access tokens carry `client_id` and, unless the app requests a resource binding, no `aud`, so verification fails, and the quick fix of disabling the audience check makes the API accept tokens issued to any app client in the pool, ID tokens included.
**Instead:** Require `token_use` to be `access` and `client_id` to be one of yours, keeping the issuer check; AWS's `aws-jwt-verify` does both. See [Authentication & Authorization](./authentication-authorization.md#tokens).

---

## When Designing an API or Error Contract

### The Class-Name Error Contract
Setting the RFC 9457 `type` field (or any identifier clients branch on) to your internal error *class name*, welding the public wire contract to your code's class hierarchy. Rename `InvalidLicenseError` in a refactor and every client switching on it breaks — a purely internal change becomes a breaking API change. RFC 9457 does intend clients to branch on `type`, but on a stable URI chosen independently of class names; a non-resolvable `tag:` URI needs no docs site.
**Instead:** Expose a stable identifier chosen independently of class names: a `code` extension member with `type` left as `about:blank`, or a stable `type` URI per problem type such as a `tag:` URI. See [Error Handling](./error-handling.md#http-error-response-schema).

### The 500 Without CORS Headers
FastAPI's `Exception` handler runs in Starlette's `ServerErrorMiddleware`, outside `CORSMiddleware`, so every 500 reaches the browser without `Access-Control-Allow-Origin`. The browser reports a CORS error, the front end never sees the problem body or its request id, and the bug is debugged as a CORS misconfiguration.
**Instead:** Wrap the finished app in `CORSMiddleware` at the ASGI level so it sits outside the error middleware, and test a forced 500 sent with an `Origin` header. See [Error Handling](./error-handling.md#fastapi-python).

### The Millisecond Cursor
A keyset cursor on `created_at` read as a JS `Date` keeps milliseconds, while `timestamptz` keeps microseconds, so the next page's `(created_at, id) < ($1, $2)` silently skips unseen rows in the last row's millisecond. Drizzle's default `mode: 'date'` does this.
**Instead:** Read the sort column with Drizzle's `mode: 'string'`, or sort on a time-ordered id alone. See [API Design](./api-design.md#cursor-based-more-robust).

---

## When Building UI Components

The engineering guidance lives in [Front-end Development](./frontend-development.md) and
the observable-fault catalogue in [Front-end Patterns](./frontend-patterns.md).
Read the chapter's component-boundary and state sections for structural work and the
catalogue for observable interface faults. These reminders identify friction; they
are not file-size thresholds or a mandatory hook/utility/component split.

### The Monolith Component
A component combines responsibilities that change independently, so a small interaction change risks unrelated behaviour.
**Instead:** extract a coherent responsibility when that simplifies its callers; keep closely related behaviour together. See [Component Boundaries and Composition](./frontend-development.md#component-boundaries-and-composition).

### The God Hook
A hook hides unrelated requests, domain calculations, and lifecycle coordination behind an unclear contract.
**Instead:** make ownership explicit and isolate substantial calculations where useful. A coherent hook can legitimately coordinate several requests; request count alone is not the defect. See [Effects and External Systems](./frontend-development.md#effects-and-external-systems).

### The Tangled Provider Tree
Rendering one feature requires unrelated providers and network work, making dependencies hard to understand and verification expensive.
**Instead:** scope providers to the consumers that need them; prefer explicit inputs where sharing is unnecessary. Nesting depth alone does not establish a problem. See [State Ownership](./frontend-development.md#state-ownership).

### Inline Data Transformation
Substantial transport mapping or domain calculations are entangled with rendering and duplicated across screens.
**Instead:** give meaningful transformations an appropriate feature or data-layer home. Keep trivial display expressions local instead of extracting every property mapping. See [Component Boundaries and Composition](./frontend-development.md#component-boundaries-and-composition).

---

## When Building Multi-Tenant Systems

### Trust the Caller
Accepting a `tenant_id` parameter from the client and using it to scope database queries, without verifying server-side that the authenticated user actually belongs to that tenant. Any authenticated user can pass a different tenant's ID and access their data.
**Instead:** Derive tenant_id from the authenticated session server-side. Never trust client-supplied tenant identifiers for authorisation decisions. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#enforcing-the-boundary).

### The Security Bypass
Using elevated database privileges (SECURITY DEFINER in PostgreSQL, service role keys in Supabase) that skip row-level security, then trusting caller-supplied parameters to scope the query correctly. The RLS policies exist but are being bypassed by the functions the frontend actually calls.
**Instead:** Prefer SECURITY INVOKER (let RLS handle access). If SECURITY DEFINER is necessary, verify the caller's tenant membership inside the function. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### RLS Silently Off
Writing row-level security policies on a table that never had `ALTER TABLE … ENABLE ROW LEVEL SECURITY` (and `FORCE ROW LEVEL SECURITY` for the owner), or connecting the application's pool as a superuser or the table's owner. A table without RLS enabled ignores its policies entirely and bypass roles ignore them by default, so every policy you wrote is silently inert — the system looks protected and isn't, and no error ever fires to tell you.
**Instead:** Enable and force RLS on every table with a tenant column and assert in a test that each has `pg_class.relrowsecurity` and `relforcerowsecurity` set (FORCE binds the owner too, so a cross-tenant backfill run as the owner must use a bypass role or it silently updates zero rows); connect as an unprivileged role that is subject to policies; reserve any bypass-capable role for deliberate, audited admin paths. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Owner-Rights View
Querying an RLS-protected table through a view. A Postgres view applies row-level policies as its *owner*, usually the migration role, which bypasses them unless the table forces RLS, so a harmless-looking view returns every tenant's rows to the app role.
**Instead:** Create the view `WITH (security_invoker = true)` (Postgres 15+) so the policies apply to the querying role, and put a view in the isolation tests. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Read-Only Policy
Isolating reads by tenant while a separate, looser rule governs writes. In PostgreSQL a `FOR ALL` or `FOR UPDATE` policy with only `USING` still checks writes, because it reuses `USING` as `WITH CHECK`. The smuggle comes from permissive policies combining with OR: a tenant-scoped `FOR SELECT` policy plus a `FOR INSERT ... WITH CHECK (true)` (or any looser write check) lets a session scoped to tenant A insert a row stamped for tenant B — a cross-tenant write that later reads then hide.
**Instead:** Write the tenant predicate explicitly in both `USING` and `WITH CHECK`, make sure no permissive write policy is looser than the read rule, and test the write side. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Fail-Open Predicate
Writing a tenant predicate that returns every row when the session's tenant context is unset or empty. A request that reaches the database without tenant context then sees all tenants' data — one missing-context bug becomes a full leak. A predicate that *errors* instead leaks nothing, but errors inconsistently: in PostgreSQL a never-set value reads as NULL, while a pooled connection that ran an earlier transaction-local `set_config` reads it as `''`, and `''::uuid` raises — so missing context fails on reused connections only.
**Instead:** Make the predicate fail closed: missing or empty context must match zero rows. Read the setting missing-ok and normalise empty to NULL: `USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)`. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Interpolated Tenant Setting
Building the statement that sets the per-session tenant value by string-concatenating a user-derived tenant ID, because `SET`/`SET LOCAL` cannot take bind parameters. This re-introduces SQL injection on the exact value your whole isolation model depends on.
**Instead:** Set it parameter-safely — on PostgreSQL, `set_config('app.tenant_id', $1, true)` is bind-parameterisable and transaction-local. Never interpolate the value into a `SET LOCAL` string. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Leaky Pooled Connection
Setting the tenant context on a connection but not confining it to the transaction. Connection pools hand the same physical connection to the next request, which inherits the previous request's tenant scope — an intermittent cross-tenant leak that is brutal to reproduce.
**Instead:** Bind the tenant value to the transaction (transaction-local), so it is established at the start of each transaction and cannot outlive it. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

### The Index the App Role Can't Use
Leading an index with an enum column on an RLS-protected table. Postgres applies the row policy before any query condition whose function is not leakproof, and `enum_eq` is not, so `status = 'pending'` never becomes an index condition. The index is dead for the app role yet works perfectly when tested as a superuser, who bypasses RLS.
**Instead:** Lead the index with a uuid or timestamp and move the enum into the partial predicate; `EXPLAIN` as the app role inside a transaction that set the tenant, and read the Index Cond. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop).

---

## When Building Backend or Pipeline Code

### Non-Atomic Operations
Deleting all existing records for a scope, then inserting the new batch — without a transaction. If the process crashes between delete and insert, the data is gone with no recovery path.
**Instead:** Wrap delete+insert in a transaction, or use upsert (INSERT ... ON CONFLICT UPDATE). See [Database Transactions](./data-integrity.md#database-transactions).

### No Concurrency Guard
Running a scheduled job (cron, timer) with no protection against overlapping executions. If one run is slow and the next run starts, both write to the same tables — duplicates, partial overwrites, or corrupted state.
**Instead:** Make each run single-flight: a lease row taken with one conditional `UPDATE`, or `pg_try_advisory_lock` on a dedicated direct connection (a session advisory lock does not survive a transaction-mode pooler). A file lock guards one host only. See [Resilience](./resilience.md#background-jobs).

### The Monolith Handler
An entire serverless function or API handler in one file: auth, validation, business logic, external API calls, response formatting. Often 500-1000+ lines. Nothing is importable or testable independently. Shared patterns (auth, CORS, error handling) are copy-pasted across every function.
**Instead:** Extract auth, validation, and shared utilities into importable modules. Keep the handler thin — it orchestrates, it doesn't compute. See [Module Design](./module-design.md#structuring-around-dependencies).

### Duplicated Boilerplate
Every serverless function or API route re-implements auth verification, CORS headers, error formatting, and client creation from scratch. They drift apart over time — one gets a bug fix, the others don't.
**Instead:** Create shared middleware or utility modules. Auth, CORS, error formatting, and client creation should be defined once and imported. See [Error Handling](./error-handling.md#global-error-handlers).

### The 72-Byte Password
Hashing passwords with bcrypt, which cannot use more than 72 bytes of input. Python's `bcrypt` 5 raises `ValueError` beyond that in both `hashpw` and `checkpw`; Node's `bcrypt` and older Python versions silently ignore the rest. A passphrase in a multi-byte script passes 72 bytes well before 64 characters.
**Instead:** Use Argon2id for new systems. On a legacy bcrypt system, refuse new or changed passwords over 72 UTF-8 bytes. Verify existing hashes with the input cut to its first 72 bytes, because older hashes were made from truncated input and bcrypt 5 now raises instead, then rehash to Argon2id on that successful sign-in. See [Authentication & Authorization](./authentication-authorization.md#passwords--mfa).

### The Limiter Behind the Proxy
Rate limiting per IP behind a load balancer without telling the framework which proxies to trust. Every request appears to come from the load balancer, so one client's burst throttles everyone, or the limiter trusts an `X-Forwarded-For` the client wrote and an attacker rotates it. An in-memory limiter also counts per process, so N replicas allow N times the limit and a restart resets it.
**Instead:** Set the trusted proxy hops (Express `app.set('trust proxy', <hops>)`, Uvicorn `--forwarded-allow-ips` set to the load balancer's addresses or subnet in CIDR form, never `'*'`, which trusts the client-written leftmost entry) and keep counters in a shared store such as Redis. See [Security](./security.md#rate-limiting).

---

## When Writing Tests

### The Replay That Lost Its Grant
A migration-replay test that drops and recreates the `public` schema loses its default grants on every Postgres version: `CREATE SCHEMA` grants nothing to other roles, and the `USAGE` that `public` normally gives everyone came with the database. The replayed database silently lacks the `USAGE`/`CREATE` grants the application role needs: objects exist, the role can't use them, and the failure looks nothing like a missing grant.
**Instead:** have the replay harness re-issue the schema grant explicitly after recreating `public`, instead of relying on the grants the original database came with. See [Schema Evolution](./schema-evolution.md#testing-migrations).

### High-Value Tests Gated Out of CI
The integration tests that need Docker or a real database get put behind a separate opt-in command, and CI runs only the fast unit suite. The tests that prove your hardest guarantees — tenant isolation, migration parity, concurrency — then never run in CI and decay into checks nobody executes. Related: a runner told to pass when it matches no files (`--passWithNoTests`, or a glob that quietly matches nothing) turns a green pipeline into one that ran zero tests.
**Instead:** wire the real-database/integration command into CI as a required step, and fail the build if zero tests were collected. See [Testing](./testing.md#deciding-for-your-project).

### The Test Pool That Hid the Deadlock
Running tests with a connection-pool shape unlike production's — a roomy test pool (`max: 10`) when production runs lean (`max: 1` per instance). Self-deadlocks and pool-saturation bugs that only bite at the production shape never surface, because the test pool always has a spare connection to hand out. Green in CI, hung in prod.
**Instead:** when testing concurrency, deadlock, or connection-exhaustion behaviour, size the test harness's pool the way production is sized. See [Testing](./testing.md#harness-parity-and-proving-a-test-can-fail).

### The Announcer That Broke the Locator
An end-to-end assertion on visible text (`getByText('All done!')`) intermittently fails with a strict-mode violation: the framework's accessibility live region (e.g. Next.js's route announcer, which re-reads the page's `h1` to screen readers after client-side navigation) duplicates the same text in a second element. The collision is timing-dependent — the announcer only carries the text after a client navigation — so the test flakes rather than fails.
**Instead:** scope text assertions to a role or landmark (`getByRole('heading', { name: … })`) instead of bare page-wide text matches, and treat framework live regions as legitimate duplicators of any visible text. See [Front-end Development](./frontend-development.md#testing-front-end-behaviour).

### The Teardown That Failed the Green Run
A throwaway database container (Testcontainers) is stopped while the app's connection pool still holds open connections. The server terminates them (`FATAL 57P01 admin_shutdown`), the driver surfaces it as an unhandled error *after* every test has already passed, and the runner marks a fully-green suite red. Looks like a mystery database failure; is actually teardown ordering.
**Instead:** order the teardown — close pools/clients before stopping the container — and treat connection-termination errors arriving during shutdown as expected, not fatal. See [Testing](./testing.md#test-database--use-a-real-one).

### The Tamper Test That Flipped a Dead Bit
An AEAD tamper test mutates the LAST character of a base64url ciphertext and asserts decryption fails — but the final character of a base64 string can carry padding bits the decoder discards, so some mutations decode to the *identical* bytes and the "tampered" input decrypts fine. The test flakes with the randomness of the ciphertext (fired in two separate modules before the pattern was named).
**Instead:** mutate a position that provably changes the decoded bytes — the FIRST character is always significant — and treat "encodings have dead bits" as a class: never assume a textual mutation changes the underlying bytes. Run new crypto/probability-adjacent tests several times in a row before trusting them. See [Testing](./testing.md#harness-parity-and-proving-a-test-can-fail).

### The Env File the Test Runner Also Read
An operator applies a runbook's environment (e.g. `AUTH_MODE=cognito` in `.env.local`, pointing the app at a real identity pool) and later runs the e2e suite — whose harness spawns its own app server, which auto-loads the same env file. The suite's app silently boots in the wrong mode (every page gated to a login screen) and the tests time out with no visible connection to the env change made an hour earlier.
**Instead:** treat mode-selecting env files as mutually exclusive with the test loop: park or remove them before running the suite, and document the exclusivity in the runbook that applies them — the failure is invisible from the test output alone. See [Configuration](./configuration.md#testing-configuration).

---

## When Merging a Pull Request

### The Check Nobody Required
The team treats "CI green" as the merge gate, but the check is not enforced by branch protection (or the plan doesn't offer it) — so a merge on a red check succeeds silently, by a hurried human or an automation that never re-read the final status. Green-as-convention is not green-as-enforcement; the gap is invisible until the day it isn't.
**Instead:** mark load-bearing checks as required in branch protection where the platform allows it; where it doesn't, make "read the final checks status immediately before merging" an explicit step of the merge procedure, not an assumption. See [Deployment](./deployment.md#cicd-pipeline-basics).

### The Watch That Reported the Wrong Run
A checks watcher (`gh pr checks --watch` or similar) started before a late push binds to the SUPERSEDED workflow run and happily reports green — for a commit that is no longer the branch head. The merge then rides a verdict that belongs to different code. It has happened in practice; the watcher gives no hint it is stale.
**Instead:** after ANY post-review push, resolve the workflow run by the exact head SHA (`gh run list --json headSha`, match it yourself) and gate the merge on that run — never on a watcher started earlier. See [Deployment](./deployment.md#cicd-pipeline-basics).

---

## When Building a Deployable Image

### The Mode Frozen Into the Bundle
A bundling framework (Next.js edge middleware is the canonical case) inlines `process.env.X` reads at BUILD time. If the variable is present in the build environment, its value is baked into the artifact — and the runtime task definition's value is silently ignored. A mode switch (`AUTH_MODE`) frozen this way means the deployed artifact can never change posture, no matter what the deploy config says.
**Instead:** keep behavior-selecting variables OUT of the image build entirely (no ARG/ENV, clean build stage — one promotable image), and prove it: boot the built image with a different runtime value and observe the runtime value win. See [Configuration](./configuration.md#build-time-vs-runtime-configuration).

### The Two Builds of One Library
A package ships parallel CJS and ESM builds (`main` → `lib/`, `module` → `es/`) with no `exports` map. The package-root import resolves to a DIFFERENT build under a bundler than under node — while a deep import (`pkg/lib/Thing`) always pins one build. Two copies of the same class now coexist in the bundled artifact, `instanceof` fails across them ("Not a BigInteger"), and the breakage exists ONLY in the bundled runtime: every test runner (vitest, tsx) resolves both imports to the same build and stays green. This shipped a login page that could not log anyone in.
**Instead:** import every helper of such a package from the SAME explicit build path, and exercise the code inside the actual bundled artifact (a booted image, `next dev`/`next start`) at least once — a green unit suite proves nothing about the bundler's module graph. See [Testing](./testing.md#smoke-tests--does-the-deployed-system-serve-real-requests).

---

## When Writing Infrastructure as Code

### The Description That Deadlocked
A security group's `description` is create-only in EC2 — editing it forces a REPLACEMENT. With a static `name`, the replacement deadlocks three ways at once: the new SG can't be created while the old one holds the name, the old one can't be deleted while other SGs' rules reference it, and those rules only re-point after the new SG exists. The provider retries the delete until the operation times out; if other groups' rules were already updated by the same apply, the interrupted run leaves manual cleanup.
**Instead:** give security groups `name_prefix` + `lifecycle { create_before_destroy = true }` from day one (the provider-documented pattern), and until that lands, treat every create-only attribute (description included) as immutable. Killing a stuck apply also strands the state lock — resolve the run by checking `Lock Info` before force-unlocking anything. See [Deployment](./deployment.md#infrastructure-as-code).
