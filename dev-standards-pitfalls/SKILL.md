---
name: dev-standards-pitfalls
description: Named anti-patterns from real production codebases. Load alongside dev-standards when building new code to catch common structural mistakes before they become embedded.
---

# Common Pitfalls

Anti-patterns observed in real codebases during production readiness assessments. Each pitfall is named, brief, and references the relevant `dev-standards` topic for the correct approach.

**How to use:** Scan the relevant section before starting work. If you recognise a pattern you're about to create, stop and check the referenced topic file for the correct approach.

**These are guardrails, not rules.** Some situations genuinely call for what looks like a pitfall (e.g., a module-level singleton for a truly global resource). The point is to make it a conscious choice rather than an accidental default.

---

## When Writing a Function or Module

### The Singleton Trap
Creating a service client (database, API, cache) at module level and importing it directly everywhere. Every consumer is now married to that specific client — you can't swap it for testing, point it at a different environment, or create isolated instances.
**Instead:** Accept clients as parameters or use a provider pattern. See `dev-standards` > configuration.md.

### Trapped Logic
Embedding business calculations inside data-fetching functions or I/O code. The calculation is correct but unreachable without also setting up the entire I/O chain. Commission formulas inside database hooks. Scoring algorithms inside API handlers.
**Instead:** Extract pure logic into standalone functions that take explicit inputs and return explicit outputs. See `dev-standards` > testing.md.

### The Read-That-Writes
A function that appears to read data but secretly creates records, triggers API calls, or mutates state as a side effect. Breaks assumptions about safety, makes caching dangerous, and can cost real money (AI API calls) on every refetch.
**Instead:** Separate read and write operations. If a read needs to trigger a write (e.g., lazy initialisation), make it explicit in the function name and documentation.

### The Private Pure Function
Writing a pure, testable function but leaving it unexported or defined inside a closure. The logic is clean but unreachable from test code. Often happens when a utility function is written "just for this hook" and never extracted.
**Instead:** If a function is pure (no side effects, explicit inputs and outputs), export it. Even if only one consumer uses it today.

### Copy-Paste Utilities
Redefining a helper function locally instead of importing the shared version. Each copy drifts slightly — different null handling, different formatting, different edge cases. The shared version exists but nobody uses it.
**Instead:** Search for existing utilities before writing a new one. If a utility doesn't exist, create it in the shared location first. See `dev-standards` > data-integrity.md.

---

## When Designing a Schema or Data Model

### Missing Database Constraints
Relying entirely on application-layer validation (Pydantic, Zod, TypeScript types) without database-level enforcement. Application bugs, direct database access, and ETL pipelines will all bypass your application validation. Orphaned records, impossible states, and corrupted aggregations follow.
**Instead:** Enforce integrity at both layers. FKs for relationships, CHECKs for valid values, UNIQUE for natural keys. Application validation for user experience; database constraints for data safety. See `dev-standards` > data-integrity.md.

### The Case Sensitivity Bug
Storing user-facing string values (statuses, categories, types) without normalisation or constraints. The ETL writes "Active", the UI writes "active", the seed script writes "ACTIVE". Queries that filter on one case silently exclude the others.
**Instead:** Normalise at ingest (lowercase), add a CHECK constraint for valid values, and treat any new casing as a bug. See `dev-standards` > data-integrity.md.

### The Loose Foreign Key
Joining tables on string columns (customer_code, product_code) without FK constraints. Works fine until the ETL loads a batch of orders referencing customers that haven't been imported yet, or a customer gets deleted while their orders remain. Aggregations silently exclude orphaned rows.
**Instead:** Add FK constraints. Use `NOT VALID` initially if you're adding to an existing table with potentially dirty data, then validate after cleanup. See `dev-standards` > data-integrity.md.

---

## When Connecting to External Services

### Production Defaults
Setting the production URL or credentials as the default value when an environment variable is missing. A test run with missing config silently hits production. A developer running the ETL locally corrupts live data.
**Instead:** Required credentials should have no default — fail at startup if missing. Only provide defaults for genuinely safe values (localhost URLs, development ports). See `dev-standards` > configuration.md.

### The Hardwired Client
Creating API clients, database connections, or SDK instances inline inside business logic. The function works, but you can't test it without the real service, can't point it at a staging environment, and can't control its behaviour in development.
**Instead:** Create clients at the application boundary (startup, request handler entry) and pass them to the functions that need them. See `dev-standards` > configuration.md.

### Error Leaking
Catching an error and returning it directly to the client: `return { error: String(err) }`. The error object may contain connection strings, file paths, stack traces, API keys from headers, or internal service names.
**Instead:** Log the full error server-side with a correlation ID. Return a generic message and the correlation ID to the client. See `dev-standards` > error-handling.md.

### CORS Wildcard
Setting `Access-Control-Allow-Origin: *` on production endpoints because it's the fastest way to stop CORS errors during development. Any website can now make authenticated requests to your API if the user has a valid session.
**Instead:** Restrict to your actual frontend domain(s). Use environment-specific CORS configuration. See `dev-standards` > security.md.

---

## When Designing an API or Error Contract

### The Class-Name Error Contract
Setting the RFC 9457 `type` field (or any identifier clients branch on) to your internal error *class name*, welding the public wire contract to your code's class hierarchy. Rename `InvalidLicenseError` in a refactor and every client switching on it breaks — a purely internal change becomes a breaking API change. Using `type`-as-URI also implies hosting a docs page per error type, which most teams never do.
**Instead:** Expose a stable, machine-readable `code` (e.g. `LICENSE_REVOKED`), chosen independently of class names, for clients to dispatch on; keep `type` as an optional documentation URI (`about:blank` until you actually host docs). See `dev-standards` > error-handling.md.

---

## When Building UI Components

### The Monolith Component
A page component that fetches data, transforms it, computes derived values, manages local state, and renders the UI — all in one function. Often 300-500 lines. Untestable without mocking everything, and any change risks breaking unrelated functionality.
**Instead:** Separate data fetching (hooks), data transformation (utilities), and presentation (components). Each piece is testable on its own. See `dev-standards` > testing.md.

### The God Hook
A React hook that makes 5-10 database queries, chains the results together, applies business logic to the combined data, and exposes the final computed object. The business logic is correct but imprisoned — you can't test the computation without mocking every query.
**Instead:** Have the hook fetch data, then call extracted pure functions for computation. The hook orchestrates; the functions calculate. See `dev-standards` > testing.md.

### The Deep Provider Tree
Requiring 5+ nested context providers to render any component, where each provider makes API calls on mount. Testing a single component requires recreating the entire provider stack, and each provider pulls in its own dependencies.
**Instead:** Design providers to accept initial values for testing. Consider whether all providers need to make API calls on mount, or whether some can accept pre-fetched data.

### Inline Data Transformation
Mapping database column names to UI property names inside a component's render body. `{ name: c.customer_name, status: c.account_status === 'at_risk' ? 'at-risk' : c.account_status }`. Mixes presentation with data layer concerns and can't be tested without rendering the component.
**Instead:** Define the transformation as a standalone function. The component receives already-transformed data.

---

## When Building Multi-Tenant Systems

### Trust the Caller
Accepting a `tenant_id` parameter from the client and using it to scope database queries, without verifying server-side that the authenticated user actually belongs to that tenant. Any authenticated user can pass a different tenant's ID and access their data.
**Instead:** Derive tenant_id from the authenticated session server-side. Never trust client-supplied tenant identifiers for authorisation decisions. See `dev-standards` > multi-tenant-isolation.md.

### The Security Bypass
Using elevated database privileges (SECURITY DEFINER in PostgreSQL, service role keys in Supabase) that skip row-level security, then trusting caller-supplied parameters to scope the query correctly. The RLS policies exist but are being bypassed by the functions the frontend actually calls.
**Instead:** Prefer SECURITY INVOKER (let RLS handle access). If SECURITY DEFINER is necessary, verify the caller's tenant membership inside the function. See `dev-standards` > multi-tenant-isolation.md.

### RLS Silently Off
Enabling row-level security policies but connecting the application's pool as a superuser or the table's owner. Those roles bypass RLS by default, so every policy you wrote is silently inert — the system looks protected and isn't, and no error ever fires to tell you.
**Instead:** Connect as an unprivileged role that is subject to policies; reserve any bypass-capable role for deliberate, audited admin paths. See `dev-standards` > multi-tenant-isolation.md.

### The Read-Only Policy
Writing a row-level policy with only a read predicate (PostgreSQL's `USING`) and no write predicate (`WITH CHECK`). Reads are isolated, but a session scoped to tenant A can still INSERT or UPDATE a row stamped for tenant B — a cross-tenant write smuggle.
**Instead:** Mirror the tenant predicate in both the read rule and the write rule, so writes are constrained as tightly as reads. See `dev-standards` > multi-tenant-isolation.md.

### The Fail-Open Predicate
Writing a tenant predicate that returns every row (or raises an error) when the session's tenant context is unset or empty. A request that reaches the database without tenant context then sees all tenants' data — one missing-context bug becomes a full leak.
**Instead:** Make the predicate fail closed: missing or empty context must match zero rows. Read the session value as missing-ok and normalise empty to NULL so the comparison excludes everything. See `dev-standards` > multi-tenant-isolation.md.

### The Interpolated Tenant Setting
Building the statement that sets the per-session tenant value by string-concatenating a user-derived tenant ID, because `SET`/`SET LOCAL` cannot take bind parameters. This re-introduces SQL injection on the exact value your whole isolation model depends on.
**Instead:** Set it parameter-safely — on PostgreSQL, `set_config('app.tenant_id', $1, true)` is bind-parameterisable and transaction-local. Never interpolate the value into a `SET LOCAL` string. See `dev-standards` > multi-tenant-isolation.md.

### The Leaky Pooled Connection
Setting the tenant context on a connection but not confining it to the transaction. Connection pools hand the same physical connection to the next request, which inherits the previous request's tenant scope — an intermittent cross-tenant leak that is brutal to reproduce.
**Instead:** Bind the tenant value to the transaction (transaction-local), so it is established at the start of each transaction and cannot outlive it. See `dev-standards` > multi-tenant-isolation.md.

---

## When Building Backend or Pipeline Code

### Non-Atomic Operations
Deleting all existing records for a scope, then inserting the new batch — without a transaction. If the process crashes between delete and insert, the data is gone with no recovery path.
**Instead:** Wrap delete+insert in a transaction, or use upsert (INSERT ... ON CONFLICT UPDATE). See `dev-standards` > reliability.md.

### No Concurrency Guard
Running a scheduled job (cron, timer) with no protection against overlapping executions. If one run is slow and the next run starts, both write to the same tables — duplicates, partial overwrites, or corrupted state.
**Instead:** Use file-based locking, database advisory locks, or a claim-slot pattern to prevent concurrent execution. See `dev-standards` > reliability.md.

### The Monolith Handler
An entire serverless function or API handler in one file: auth, validation, business logic, external API calls, response formatting. Often 500-1000+ lines. Nothing is importable or testable independently. Shared patterns (auth, CORS, error handling) are copy-pasted across every function.
**Instead:** Extract auth, validation, and shared utilities into importable modules. Keep the handler thin — it orchestrates, it doesn't compute. See `dev-standards` > testing.md.

### Duplicated Boilerplate
Every serverless function or API route re-implements auth verification, CORS headers, error formatting, and client creation from scratch. They drift apart over time — one gets a bug fix, the others don't.
**Instead:** Create shared middleware or utility modules. Auth, CORS, error formatting, and client creation should be defined once and imported. See `dev-standards` > error-handling.md.

---

## When Writing Tests

### The Replay That Lost Its Grant
A migration-replay test (drop everything, replay from an empty schema) recreates the `public` schema — but on PostgreSQL 15+ a freshly-created `public` schema no longer carries the old implicit `GRANT … TO PUBLIC`. The replayed database silently lacks the `USAGE`/`CREATE` grants the application role needs: objects exist, the role can't use them, and the failure looks nothing like a missing grant.
**Instead:** have the replay harness re-issue the schema grant explicitly after recreating `public`, instead of relying on the pre-15 implicit default. See `dev-standards` > schema-evolution.md.

### High-Value Tests Gated Out of CI
The integration tests that need Docker or a real database get put behind a separate opt-in command, and CI runs only the fast unit suite. The tests that prove your hardest guarantees — tenant isolation, migration parity, concurrency — then never run in CI and decay into checks nobody executes. Related: a runner told to pass when it matches no files (`--passWithNoTests`, or a glob that quietly matches nothing) turns a green pipeline into one that ran zero tests.
**Instead:** wire the real-database/integration command into CI as a required step, and fail the build if zero tests were collected. See `dev-standards` > testing.md.

### The Test Pool That Hid the Deadlock
Running tests with a connection-pool shape unlike production's — a roomy test pool (`max: 10`) when production runs lean (`max: 1` per instance). Self-deadlocks and pool-saturation bugs that only bite at the production shape never surface, because the test pool always has a spare connection to hand out. Green in CI, hung in prod.
**Instead:** when testing concurrency, deadlock, or connection-exhaustion behaviour, size the test harness's pool the way production is sized. See `dev-standards` > testing.md.
