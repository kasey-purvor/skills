# Multi-Tenant Isolation

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
| **Database-level enforcement** | The database itself refuses to return or write non-matching rows | The strongest backstop — bugs, ad-hoc database sessions, and even a malicious insider cannot bypass it |

One rule underpins every rung: **the tenant identity always comes from the authenticated session, verified server-side — never from the request body, the URL, or a header the client controls.** A client-supplied tenant ID is simply a request to read someone else's data. (The one sanctioned exception is covered under Elevated-Access Exceptions below.)

---

## The Database Backstop

The top rung deserves its own treatment, because it is what turns "we are careful" into "the system is safe." The idea: move the tenant boundary *into the database engine*, so that a forgotten application filter returns **zero rows instead of another tenant's data**.

On Postgres the mechanism is **Row-Level Security (RLS)** — a per-row predicate the engine applies automatically to every query against a table, comparing each row's tenant column against the tenant of the current session. Other databases have their own equivalents; the principle is what matters. Treat it as **defence-in-depth *under* correct application-layer scoping, not a replacement for it** — your queries should still filter by tenant for clarity and performance; the database is the net that catches the one query you forgot.

Adopting database-level enforcement well comes down to a handful of guidelines:

- **Filter reads *and* writes.** A read predicate stops a tenant from *seeing* foreign rows; a separate write predicate stops them from *creating* a row stamped for another tenant. You need both — a read-only rule still permits a cross-tenant write. (On Postgres these are the `USING` clause for reads and `WITH CHECK` for writes.)
- **Fail closed when tenant context is missing.** If the session's tenant context is unset, the predicate must match *no* rows — never all rows, and never raise an error that takes the feature down. Missing context is a bug; the safe response is "you see nothing," not "you see everything."
- **Connect as a role that cannot bypass the rules.** Most engines let privileged roles (a superuser, or the table's owner) skip row-level policies entirely. Enforcement only exists if your application connects as an unprivileged role that is actually subject to it.
- **Don't let elevated/definer functions silently bypass the rules.** A database function that runs with its *definer's* privileges rather than the *caller's* is exempt from row-level policies — a common way to accidentally hand a caller cross-tenant reach. Prefer caller's-privileges execution so the policies still apply; if a definer function is genuinely necessary, re-verify the caller's tenant scope inside it (the Confused Deputy rule). (On Postgres: `SECURITY INVOKER` versus `SECURITY DEFINER`.)
- **Scope the tenant context per transaction.** Connection pools reuse physical connections across requests. If you set the tenant on the connection and do not confine it to the transaction, the next request inherits the previous tenant's scope — a leak. Bind it to the transaction, not the connection.
- **Choose a runtime-role model deliberately, and know its failure direction.** Two common shapes exist: (a) connect as the *unprivileged* role and *escalate* for the rare cross-tenant job — a forgotten escalation **fails closed** (the feature breaks, loudly, with no leak); (b) connect as a *privileged* role and *drop* to the tenant scope per transaction — a forgotten drop **fails open** (it leaks, though usually loudly under testing). Model (a) is the safer default; model (b) is sometimes forced by connection-budget constraints. Pick with eyes open.

The specific implementation idioms behind these — the fail-closed predicate, setting the tenant value parameter-safely — are easy to get subtly wrong, so they are recorded as named traps in `dev-standards-pitfalls` rather than spelled out here.

---

## Elevated-Access Exceptions

Two situations legitimately cross the tenant boundary. Both are *deliberate* and *narrow*; the danger is when either happens by accident.

- **Cross-tenant admin and support tooling.** Platform operators sometimes must read or act across tenants — support, billing, data migrations. This needs a *separate, deliberate, logged* path, not the normal request flow with a check quietly skipped. Because the power is extraordinary, gate it strongly: ideally require two independent facts to agree (for example, an admin role *and* a dedicated admin context), so a single leaked or corrupted claim cannot unlock it on its own. And an elevated path that accepts a tenant from its caller must independently verify the caller's authorisation for that tenant — the **Confused Deputy** rule (see [Authentication & Authorization](./authentication-authorization.md)).
- **Capability URLs (token-keyed public routes).** Invite links, password-reset links, and share links are opened by users with no session — so there is no session tenant to scope by. Here the **high-entropy token in the URL is itself the credential**, and resolving it yields the tenant. This is the one sanctioned exception to "tenant from the verified session." Its own rules apply: the token must be cryptographically random (not a guessable ID), single-purpose, short-lived, and ideally single-use. Treat the token lookup as the *entire* authorisation decision for that route, and keep the route's surface minimal.

---

## Testing Tenant Isolation

Isolation is a *negative* property — "tenant A can never see tenant B" — and negatives need explicit tests, because no ordinary feature test exercises them. What to verify is below; the *how* of standing up a real database for these tests lives in [Testing](./testing.md).

- **Prove the negative directly.** Issue a query with *no* tenant filter while scoped to tenant A, and assert you get only A's rows back. This tests the backstop rather than your application filter — so deliberately write the query the way a *bug* would.
- **Cover the fail-safe paths.** Unset tenant context and empty tenant context must both yield zero rows — not all rows, and not an error.
- **Test the write side.** Attempt to write a row stamped for another tenant and assert it is rejected. A read-only isolation test misses write smuggling entirely.
- **Reproduce the production privilege drop.** Isolation can only be proven against the real engine — mocks cannot enforce policies — and the test must connect *as the same unprivileged role the application uses*. A test run as a privileged or bypass role silently skips the very policy it claims to test, producing a false green.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Read the tenant ID from the request body, URL, or a client header | Derive it from the authenticated session | A client-supplied tenant ID is a request to read another tenant's data |
| Rely on "we always remember to filter by tenant" | Enforce in a scoped data layer, backed by the database | One forgotten filter is a silent cross-tenant breach |
| Treat the database backstop as your only defence | Scope in the application *and* back it in the database | Each layer covers the other's gaps; the database net catches the filter you missed |
| Let cross-tenant admin access reuse the normal path with a check skipped | Use a separate, deliberate, logged, strongly-gated path | Accidental cross-tenant access is indistinguishable from a breach |
| Write a row-level policy that returns all rows (or errors) when tenant context is missing | Fail closed — missing context returns zero rows | Failing open turns one bug into a full data leak |

---

## Deciding for Your Project

1. **Which strategy?** Shared-schema with a tenant column is the common default. Move to schema- or database-per-tenant only when compliance, contractual physical separation, or noisy-neighbour pressure demands it.
2. **Where does the tenant ID come from?** The verified session, always. Audit that no code path reads it from the request.
3. **Do you have a database backstop?** Add one (RLS on Postgres, or the equivalent for your store) as defence-in-depth under application-layer scoping. Decide your runtime-role model — and its failure direction — consciously.
4. **What is your deliberate cross-tenant path?** Define it explicitly, gate it strongly, and log it. Do not let cross-tenant access be an accident of a skipped check.
5. **Do your isolation tests prove the negative, against a real engine, as the unprivileged role?** If not, you are testing your hopes.

---

## Related Topics

- **Authentication & Authorization** — see [Authentication & Authorization](./authentication-authorization.md) for who-can-do-what, the enforcement-layer model, and the Confused Deputy pattern that governs elevated cross-tenant access.
- **Security** — see [Security](./security.md) for the broader posture (injection, input validation) that the tenant boundary sits within.
- **Testing** — see [Testing](./testing.md) for the real-database test infrastructure that isolation tests require.
- **Schema Evolution** — see [Schema Evolution](./schema-evolution.md) for safely adding tenant columns and isolation policies through migrations.
- **Implementation traps** — see `dev-standards-pitfalls` for the named RLS gotchas: read-vs-write predicates, the fail-closed idiom, setting the tenant value safely, bypass roles, and per-transaction scoping.
