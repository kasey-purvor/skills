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
**Instead:** Derive tenant_id from the authenticated session server-side. Never trust client-supplied tenant identifiers for authorisation decisions. See `dev-standards` > security.md.

### The Security Bypass
Using elevated database privileges (SECURITY DEFINER in PostgreSQL, service role keys in Supabase) that skip row-level security, then trusting caller-supplied parameters to scope the query correctly. The RLS policies exist but are being bypassed by the functions the frontend actually calls.
**Instead:** Prefer SECURITY INVOKER (let RLS handle access). If SECURITY DEFINER is necessary, verify the caller's tenant membership inside the function. See `dev-standards` > security.md.

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
