# Multi-Tenant Isolation

> **First, does this apply at all?** If your system serves a single tenant — one
> customer, or internal users only — skip this chapter entirely; don't build tenant
> machinery for tenants that don't exist. If it serves multiple customer orgs on shared
> infrastructure, everything below applies, and the core rules don't scale down with
> app size: a cross-tenant leak is a breach at three users just as at three thousand.
> The core is the tenant from the verified session, a scoped data layer, a deliberate
> and logged cross-tenant path, and negative tests; wherever tenants share a schema,
> the database backstop with its fail-closed and non-bypass rules is expected too (on
> Postgres, RLS is the cheap structural default, not an optional extra). What you
> calibrate is the investment around that core: which isolation strategy, and how
> heavily the admin path is gated.

## The Problem

A multi-tenant system runs one instance — one codebase, often one database — serving many customer organisations (tenants). That changes the authorization question. It is no longer just "may this user do X?" but "may this user do X *for this tenant*?"

Get it wrong and the failure mode is the worst one in B2B software: one customer sees another customer's data. It is silent (nothing throws), it is a breach rather than a bug, and for regulated customers it is contract-ending. A single query missing its tenant filter — one `WHERE` clause out of thousands — is enough to cause it.

So tenant isolation is something you answer *structurally*, not by remembering to check every time. This topic covers how: choosing an isolation strategy, enforcing the boundary in layers, backing it with the database itself, and the few deliberate exceptions where you cross the boundary on purpose.

---

## Isolation Strategies

How completely you separate tenants is the first decision, and it is a trade-off between isolation strength and operational cost:

| Strategy | How it works | Isolation | When teams pick it |
|----------|--------------|-----------|--------------------|
| **Database per tenant** | Each tenant gets its own database | Strongest — nothing shared | Regulated/enterprise single-tenancy; very large tenants; contractual "your data is physically separate" requirements. Highest ops cost — migrations, backups, and connections multiply per tenant |
| **Schema per tenant** | One database, one schema (namespace) per tenant | Strong — shared engine, separate tables | A middle ground; breaks down as tenant count grows, because every migration runs N times |
| **Shared schema, tenant column** | One set of tables; every tenant-scoped row carries a `tenant_id` | Weakest *by default* — one query away from a leak | The common SaaS default: cheapest to operate, scales to many tenants. Isolation has to be *added* on top |

The trend for most SaaS is shared-schema, because the operational cost of the others grows with every customer signed. But shared-schema is the one where isolation is *your* job rather than the infrastructure's — so the rest of this topic is mostly about making shared-schema safe.

---

## Enforcing the Boundary

With a shared schema, *how* the tenant filter gets applied is the whole game. There is a ladder from fragile to robust, and mature systems climb several rungs at once (defence in depth):

| Rung | Mechanism | Failure mode |
|------|-----------|--------------|
| **Convention** | "We always remember to add `WHERE tenant_id = ?`" | One forgotten filter leaks across tenants. This is not a strategy — it is a hope |
| **Scoped data layer** | A wrapper/repository that *cannot* issue a query without injecting the tenant filter | Robust — unless someone reaches past it to the raw client |
| **Database-level enforcement** | The database itself refuses to return or write non-matching rows | The strongest backstop — application bugs and sessions running as the unprivileged role cannot bypass it |

One rule underpins every rung: **the tenant identity always comes from the authenticated session, verified server-side — never from the request body, the URL, or a header the client controls.** A client-supplied tenant ID is simply a request to read someone else's data. (The two sanctioned exceptions are covered under Elevated-Access Exceptions below; a background job carries the tenant stamped from the enqueuing session, under Beyond the Database.)

---

## The Database Backstop

The top rung deserves its own treatment, because it is what turns "we are careful" into "the system is safe." The idea: move the tenant boundary *into the database engine*, so that a forgotten application filter returns **zero rows instead of another tenant's data**.

On Postgres the mechanism is **Row-Level Security (RLS)** — a per-row predicate the engine applies automatically to every query against a table, comparing each row's tenant column against the tenant of the current session. Other databases have their own equivalents; the principle is what matters. Treat it as **defence-in-depth *under* correct application-layer scoping, not a replacement for it** — your queries should still filter by tenant for clarity and performance; the database is the net that catches the one query you forgot.

Adopting database-level enforcement well comes down to a handful of guidelines:

- **Turn it on for every tenant table, and prove it.** Postgres applies a table's policies only once `ALTER TABLE … ENABLE ROW LEVEL SECURITY` has run, and `FORCE ROW LEVEL SECURITY` binds the owner too; a table shipped without `ENABLE` is open to every tenant while its policies sit inert. Assert in a test that every table with a tenant column has `pg_class.relrowsecurity` and `relforcerowsecurity` set.
- **Filter reads *and* writes.** A read predicate stops a tenant from *seeing* foreign rows; a write predicate stops them from *creating* a row stamped for another tenant. Write both explicitly, and test the write side. The cross-tenant write smuggle comes from a *second*, looser write rule: rules that grant access combine with OR, so one extra write rule with a weak check accepts rows for any tenant even when the tenant rule is correct. (On Postgres these are the `USING` clause for reads and `WITH CHECK` for writes. A `FOR ALL` or `FOR UPDATE` policy with only `USING` reuses it as the check, so it does block cross-tenant writes; the hole is a separate permissive policy such as `FOR INSERT WITH CHECK (true)`, which is ORed with the tenant policy.) The structural fix on Postgres is to declare the tenant policy `AS RESTRICTIVE`: restrictive policies are ANDed with every other policy, so no permissive policy added later can widen the boundary. A restrictive policy only narrows, so at least one permissive policy must still grant access, or the table returns nothing.
- **Fail closed when tenant context is missing.** If the session's tenant context is unset, the predicate must match *no* rows — never all rows. Missing context is a bug; the safe response is "you see nothing," not "you see everything." Prefer zero rows to an error too — not because an error leaks (it doesn't), but for consistency: on pooled connections the same missing context can read as *unset* on one connection and *empty* on another that ran an earlier transaction, so the predicate must treat both alike.
- **Connect as a role that cannot bypass the rules.** Most engines let privileged roles (a superuser, or the table's owner) skip row-level policies entirely. Enforcement only exists if your application connects as an unprivileged role that is actually subject to it. (On Postgres: superusers and `BYPASSRLS` roles always skip policies, and the table owner does too unless the table has `FORCE ROW LEVEL SECURITY`.) A view applies its owner's rights by default, so querying through one can skip the policies too ([The Owner-Rights View](./pitfalls.md#the-owner-rights-view)).
- **Don't let elevated/definer functions silently bypass the rules.** A database function that runs with its *definer's* privileges rather than the *caller's* is exempt from row-level policies — a common way to accidentally hand a caller cross-tenant reach. Prefer caller's-privileges execution so the policies still apply; if a definer function is genuinely necessary, re-verify the caller's tenant scope inside it (the Confused Deputy rule). (On Postgres: `SECURITY INVOKER` versus `SECURITY DEFINER`; a definer function also needs a pinned `SET search_path`, or a caller can shadow the tables and functions it references with their own.)
- **Scope the tenant context per transaction.** Connection pools reuse physical connections across requests. If you set the tenant on the connection and do not confine it to the transaction, the next request inherits the previous tenant's scope — a leak. Bind it to the transaction, not the connection. Behind a transaction-mode pooler a session-level `SET` is worse still, because the next client's transaction can land on that connection ([Data Integrity](./data-integrity.md#transactions-behind-a-pooler)).
- **Choose a runtime-role model deliberately, and know its failure direction.** Two common shapes exist: (a) connect as the *unprivileged* role and *escalate* for the rare cross-tenant job — a forgotten escalation **fails closed** (the feature breaks, loudly, with no leak); (b) connect as a *privileged* role and *drop* to the tenant scope per transaction — a forgotten drop **fails open** (it leaks silently, unless a negative test catches it). Model (a) is the safer default; model (b) is sometimes forced by connection-budget constraints. Pick with eyes open.
- **Carry the tenant in unique indexes and foreign keys.** Unique, primary-key and foreign-key checks always bypass row-level security (Postgres docs, Row Security Policies), so a constraint sees every tenant's rows. A global unique index on `email` tells tenant A, through a conflict error, that tenant B holds that address; make it `(tenant_id, email)`. A plain foreign key lets a child row reference another tenant's parent, which breaks integrity and lets a cascade cross tenants; make it composite, `(tenant_id, parent_id)` referencing the parent's `(tenant_id, id)`, which needs its own unique constraint.
- **Index for the role the app runs as.** Under RLS, Postgres applies the policy before any condition from your query whose function is not *leakproof*, so such a condition can never become an index condition, and an index that works for a superuser can be dead for the app role. Check plans with `EXPLAIN` as the app role, inside a transaction that has set the tenant, and read the Index Cond line ([The Index the App Role Can't Use](./pitfalls.md#the-index-the-app-role-cant-use)).

The specific implementation idioms behind these — the fail-closed predicate, setting the tenant value parameter-safely — are easy to get subtly wrong, so they are recorded as named traps in [Pitfalls](./pitfalls.md#when-building-multi-tenant-systems) rather than spelled out here.

---

## Beyond the Database

RLS protects tables. The tenant boundary runs wherever tenant data lives, and nothing enforces it there but your code:

- **Caches:** the tenant id is part of every cache key, server-side and in the client's query cache, or one tenant is served another's cached result.
- **Background jobs:** a worker has no session. Stamp the tenant on the job at enqueue, from the enqueuing request's verified session, and re-establish it in the worker for each job; a job missing its tenant fails rather than running unscoped. [Resilience](./resilience.md#background-jobs) covers the rest of running jobs safely.
- **Object storage:** keep each tenant's objects under its own prefix, authorise every read against the session's tenant, and hand out a short-lived signed URL only after that check.
- **Search indexes:** filter every query by tenant, or keep one index per tenant; no row-level policy stands behind a search engine.
- **Exports and reports:** they read in bulk, often from a job, so they need the same scoping as the request path.
- **Idempotency keys:** unique per tenant, not globally, or one tenant's reused key replays another tenant's stored result (see [Resilience](./resilience.md#the-idempotency-key-pattern)).

---

## Elevated-Access Exceptions

Two situations legitimately cross the tenant boundary. Both are *deliberate* and *narrow*; the danger is when either happens by accident.

- **Cross-tenant admin and support tooling.** Platform operators sometimes must read or act across tenants — support, billing, data migrations. This needs a *separate, deliberate, logged* path, not the normal request flow with a check quietly skipped. Because the power is extraordinary, gate it strongly: ideally require two independent facts to agree (for example, an admin role *and* a dedicated admin context), so a single leaked or corrupted claim cannot unlock it on its own. And an elevated path that accepts a tenant from its caller must independently verify the caller's authorisation for that tenant — the **Confused Deputy** rule (see [Authentication & Authorization](./authentication-authorization.md)).
- **Capability URLs (token-keyed public routes).** Invite links, password-reset links, and share links are opened by users with no session — so there is no session tenant to scope by. Here the **high-entropy token in the URL is itself the credential**, and resolving it yields the tenant. This is the second sanctioned exception to "tenant from the verified session," alongside the admin path above. Its own rules apply: the token must be cryptographically random (not a guessable ID), single-purpose, short-lived, and ideally single-use. Store only its hash, so a database read hands out no live links. Send `Referrer-Policy: no-referrer` so the URL does not leak to resources the page loads. Email link scanners fetch links before the user does, so the `GET` only renders a page; its button `POST`s the token, and that request consumes it, opens the session and redirects to a token-free URL. Treat the token lookup as the *entire* authorisation decision for that route, and keep the route's surface minimal.

---

## Testing Tenant Isolation

Isolation is a *negative* property — "tenant A can never see tenant B" — and negatives need explicit tests, because no ordinary feature test exercises them. What to verify is below; the *how* of standing up a real database for these tests lives in [Testing](./testing.md).

- **Prove the negative directly.** Issue a query with *no* tenant filter while scoped to tenant A, and assert you get only A's rows back. This tests the backstop rather than your application filter — so deliberately write the query the way a *bug* would.
- **Cover the fail-safe paths.** Unset tenant context and empty tenant context must both yield zero rows — not all rows, and not an error.
- **Test the write side.** Attempt to write a row stamped for another tenant and assert it is rejected. A read-only isolation test misses write smuggling entirely.
- **Reproduce the production privilege drop.** Isolation can only be proven against the real engine — mocks cannot enforce policies — and the test must connect *as the same unprivileged role the application uses*, not as the migration owner or a container's default superuser. A test run as a privileged or bypass role silently skips the very policy it claims to test, producing a false green.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Read the tenant ID from the request body, URL, or a client header | Derive it from the authenticated session | A client-supplied tenant ID is a request to read another tenant's data |
| Rely on "we always remember to filter by tenant" | Enforce in a scoped data layer, backed by the database | One forgotten filter is a silent cross-tenant breach |
| Treat the database backstop as your only defence | Scope in the application *and* back it in the database | Each layer covers the other's gaps; the database net catches the filter you missed |
| Let cross-tenant admin access reuse the normal path with a check skipped | Use a separate, deliberate, logged, strongly-gated path | Accidental cross-tenant access is indistinguishable from a breach |
| Write a row-level policy that returns all rows (or errors) when tenant context is missing | Fail closed — missing context returns zero rows | Failing open turns one bug into a full data leak; an error leaks nothing but fails inconsistently across pooled connections |
| Keep unique indexes and foreign keys tenant-blind | Lead them with `tenant_id`; make foreign keys composite | Constraint checks bypass RLS: they reveal other tenants' values and let rows reference another tenant |
| Key a cache, search query, storage path or idempotency key without the tenant | Carry the tenant id in every key, filter and prefix | Outside the database, no policy catches the omission |
| Check an index plan as a superuser | `EXPLAIN` as the app role and read the Index Cond | A non-leakproof condition never uses the index under RLS |

---

## Deciding for Your Project

1. **Which strategy?** Shared-schema with a tenant column is the common default. Move to schema- or database-per-tenant only when compliance, contractual physical separation, or noisy-neighbour pressure demands it.
2. **Where does the tenant ID come from?** The verified session, always. Audit that no code path reads it from the request.
3. **Do you have a database backstop?** On a shared schema, expect one (RLS on Postgres, or the equivalent for your store) under application-layer scoping, with the tenant policy declared restrictive. Decide your runtime-role model — and its failure direction — consciously.
4. **What is your deliberate cross-tenant path?** Define it explicitly, gate it strongly, and log it. Do not let cross-tenant access be an accident of a skipped check.
5. **Do your isolation tests prove the negative, against a real engine, as the unprivileged role?** If not, you are testing your hopes.
6. **Where else does tenant data live?** Name each cache, job queue, bucket, search index, export and idempotency store, and the tenant key it carries.

---

## Related Topics

- **Authentication & Authorization** — see [Authentication & Authorization](./authentication-authorization.md) for who-can-do-what, the enforcement-layer model, and the Confused Deputy pattern that governs elevated cross-tenant access.
- **Security** — see [Security](./security.md) for the broader posture (injection, input validation) that the tenant boundary sits within.
- **Testing** — see [Testing](./testing.md) for the real-database test infrastructure that isolation tests require.
- **Data Integrity** — see [Data Integrity](./data-integrity.md#enforce-at-both-layers) for tenant-led unique constraints and mapping a violation to 409, and [Transactions Behind a Pooler](./data-integrity.md#transactions-behind-a-pooler) for keeping tenant context transaction-local.
- **Resilience** — see [Resilience](./resilience.md#the-idempotency-key-pattern) for idempotency keys scoped per tenant, and [Background Jobs](./resilience.md#background-jobs) for running the jobs that carry a tenant.
- **Logging** — see [Logging](./logging.md#deciding-for-your-project) for the tenant id on every log line; audit logging of cross-tenant admin actions is in [Authentication & Authorization](./authentication-authorization.md#audit-logging).
- **Schema Evolution** — see [Schema Evolution](./schema-evolution.md) for safely adding tenant columns and isolation policies through migrations.
- **Implementation traps** — see [Pitfalls](./pitfalls.md#when-building-multi-tenant-systems) for the named RLS gotchas: read-vs-write predicates, the fail-closed idiom, setting the tenant value safely, RLS left off or bypassed, per-transaction scoping, [owner-rights views](./pitfalls.md#the-owner-rights-view), and [the index the app role can't use](./pitfalls.md#the-index-the-app-role-cant-use).
