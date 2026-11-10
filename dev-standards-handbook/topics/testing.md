# Testing

> **Calibrate to the context.** The per-concern table below is a menu, not a mandate:
> each row applies only if your app actually has that concern (no tenants, no
> tenant-isolation tests; no auth, no auth tests). An app that has auth or tenants owes
> those negative tests at any size. Beyond that floor, depth scales with stakes and
> lifespan — a long-lived service earns the full treatment; a small internal tool is
> often well-served by a handful of integration tests over its core paths. The test
> *craft* (harness parity, real database, HTTP-level mocking) is worth doing right at
> any size once you write the test at all. Reference material, not a checklist.

## The Problem

A payment endpoint takes an idempotency key so that a retry cannot charge twice. Its test sends the same request twice, asserts one charge, and passes. In production a client retries while its first request is still running, and the customer is charged twice. The test sent its requests one after the other, so the second always found the first one's stored result: it passed against the broken code too, and nobody had run it there to find out.

That is the usual shape of an expensive test failure: not a missing test, but a green one that could not go red. A test proves something only when it runs under the production condition it claims to check and someone has watched it fail. This chapter covers that craft and routes each production concern to the chapter that owns what to assert.

---

## Test Types — What Each One Proves

### Unit Tests — "Does this logic work in isolation?"

A unit test exercises one unit of behaviour — a function, a class, or a deep module through its interface — with controlled inputs, and verifies the output. Default to *sociable* unit tests: let the unit use its real in-process collaborators, and substitute a test double only at a slow or external boundary (the database, the network, the clock). Mocking every collaborator pins the test to today's internal structure, so it breaks on refactors that keep the behaviour; [Module Design](./module-design.md#structuring-around-dependencies) sets which seams get a stand-in. A discount calculator, for example, gets one test per rule and boundary — 20% off 100 returns 80, and a 150% discount throws a validation error — with no database, network or framework involved.

**What unit tests prove:** Your logic is correct when given known inputs.
**What they don't prove:** That the inputs actually look like that in the real system. That the function is wired into the right place. That the database or external service behaves the way your mock said it would.

### Integration Tests — "Do components work together?"

An integration test exercises multiple components working together — your API handler + your database, your service + an external API, your middleware + your routes.

```typescript
// supertest 7
test('POST /api/users creates a user and returns 201', async () => {
  const response = await request(app)
    .post('/api/users')
    .send({ name: 'Kasey', email: 'kasey@example.com' });

  expect(response.status).toBe(201);
  expect(response.body.id).toBeDefined();

  // Verify it's actually in the database
  const user = await db.findUser(response.body.id);
  expect(user.name).toBe('Kasey');
});
```

The Python version has the same shape: drive the endpoint through the app's test client, then read the row back through the repository.

**What integration tests prove:** Components actually work together — the handler validates, writes to the DB, returns the right response.
**What they don't prove:** That the system handles load, that the UI renders correctly, that the deploy works.

**When the deploy unit isn't a server.** The `request(app)` pattern above assumes a long-running HTTP server. If your deploy unit is a function the platform invokes (a serverless handler), the equivalent integration test invokes the *real exported handler* with a synthetic provider event (e.g. an API-Gateway request object built by a typed factory), running the whole middleware chain — routing, auth, validation, handler — against a real database, substituting only at the composition root. Test the unit you actually deploy: if that's `handler(event)`, drive `handler(event)`, not a server you only construct in tests.

### Schema-Conformance Tests — "Does my code match what external data actually looks like?"

A schema-conformance test runs your schemas against real or snapshot data to prove they match reality: select real rows, or take a real or recorded API response, and parse each one through the Zod or Pydantic schema. That parse-only form is the weaker one; prefer the round-trip form below, which also catches values that parse but change on the way through the store.

**What schema-conformance tests prove:** Your schemas match the real world — not just what you think the data looks like.

This is not consumer-driven contract testing (Pact), which checks that two separately deployed services agree on their interface; reach for that when another team owns the other side. Run the same conformance test against recorded or sandbox responses from each external provider too: the hand-written HTTP mocks in **Mocking External HTTP Services** below can drift from what the real provider sends, and nothing else will tell you.

**Round-trip conformance tests.** A parse-only conformance test (does the schema accept the data?) misses *lossy* serialization — a value that survives parsing but changes on the way through the store (JSON/`jsonb` coercion, date/timezone normalisation, composite keys). To catch it, write a value in through the application's own query/serialization path, read it back through the read path, and assert it both parses against the schema *and* deep-equals the original input. This matters most for schemas **shared** between services (e.g. backend and frontend) — see [API Design](./api-design.md) for defining that shared contract. Round-trip invariants are the natural fit for property-based testing (fast-check, Hypothesis): generate many valid inputs and assert every one survives the trip unchanged.

### End-to-End Tests — "Does the whole system work from the user's perspective?"

An E2E test drives the actual UI (or the API from outside) and verifies the full flow:

```typescript
// Playwright 1.27+ — locate by label, role and accessible name, not CSS selectors
test('user can sign up and see their dashboard', async ({ page }) => {
  await page.goto('/signup');
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('SecurePass123!');
  await page.getByRole('button', { name: 'Sign up' }).click();

  await expect(page).toHaveURL('/dashboard');
  await expect(page.getByRole('heading', { name: /Welcome/ })).toBeVisible();
});
```

**What E2E tests prove:** The system works as a user experiences it.
**What they cost:** Slow, brittle (UI changes break them), the most exposed to flakiness from timing and network, expensive to maintain. Use sparingly for critical paths only.

**Component tests** sit between unit and E2E for a rendered interface. [Front-end Development](./frontend-development.md#testing-front-end-behaviour) owns them, along with browser journeys and visual evidence.

### Smoke Tests — "Does the deployed system serve real requests?"

A smoke test probes the *live deployed URL* from outside, not an in-process app, right after each deploy. It asserts three things: the health or readiness endpoint is reachable, the primary public entry point serves, and a representative API path returns its expected payload — not merely any 2xx, so a process that accepts connections but cannot serve real responses still fails. It needs no test database. Run it as an automated step that fails the deploy or blocks promotion; [Deployment](./deployment.md#environment-promotion) covers wiring it in as that gate.

### Concurrency and Race-Condition Tests — "Does the guard hold when two callers race?"

A race condition — two requests reading the same row before either writes (a time-of-check-to-time-of-use, or TOCTOU, gap) — is invisible to ordinary tests, because the dangerous interleaving only fires under precise timing. Make it deterministic instead of hoping to catch it: inject a synchronization barrier at the check step that parks every caller until all of them have read, then releases them together, so the worst-case ordering happens on *every* run.

```typescript
// Vitest 3+ — makeBarrier and onRead are your own test helpers
test('two concurrent creates cannot both pass the uniqueness check', async () => {
  const barrier = makeBarrier(2, { releaseAfterMs: 2_000 });  // releases when both arrive, or on timeout
  onRead(repo, () => barrier.arriveAndWait());    // park each caller after it reads

  const results = await Promise.allSettled([createDraft(input), createDraft(input)]);

  expect(results.filter(r => r.status === 'fulfilled')).toHaveLength(1);  // exactly one wins
});
```

How the guarded implementation turns the test green depends on the guard. A lock-before-read guard (an advisory lock on the key, or `SELECT … FOR UPDATE` on a row that already exists, such as the parent; on the row being created it locks nothing, because there is no row yet) makes the barrier unsatisfiable for more than one caller, because only one ever reaches the read — so the barrier's timeout must *release* the parked caller, not throw. A throwing barrier makes every green run wait out the timeout and pass on the timeout error, not on the guard. A releasing barrier still waits out its timeout on every green run, so keep the timeout short. A unique-constraint guard behaves differently: both callers pass the barrier and the database rejects the second write. For a create, that constraint is the guard; see [Data Integrity](./data-integrity.md#enforce-at-both-layers). Either way the callers need at least two real database connections; a single connection serialises them, and the broken implementation passes too. This is the opposite of waiting out a flaky test: you're *forcing* the bad interleaving, not polling for an expected state.

### The Testing Pyramid

```
         /  E2E  \          Few — slow, expensive, critical user journeys only
        /----------\
       / Integration \      Moderate — component interactions, API contracts
      /----------------\
     /    Unit Tests     \  Many — fast, cheap, logic and edge cases
    /______________________\
```

The classic default: most tests are **unit tests** (fast, cheap, reliable), some are **integration tests** (verify components work together), few are **E2E tests** (verify critical user journeys). The ratio legitimately shifts with where your risk lives — a database-heavy CRUD app often gets more value weighting integration tests over units (the integration-heavy shape some teams call the *testing trophy*), because its bugs are in queries and wiring, not pure logic.

The pyramid doesn't mean E2E tests are less important — it means they're more expensive per test, so you target them at flows that matter most (signup, checkout, core workflows).

---

## What to Test for Each Production Concern

Each row names the negative a passing suite must prove, the harness that can prove it, and the chapter that owns what to assert. In the harness column, *pure* needs no database, *real DB as runtime role* drives the real app against a real database with the code under test connected as the application's own role (see **Harness Parity** below), and *live URL* probes a deployed environment from outside.

| Concern | The negative to prove | Harness | What to assert |
|---------|-----------------------|---------|----------------|
| Data validation and transformations | An invalid payload gets a 400, never a silent insert | real DB as runtime role | [Testing Data Correctness](./data-integrity.md#testing-data-correctness) |
| Migrations | A new constraint rejects bad rows on INSERT and UPDATE | real DB; replay as owner, assert as runtime role | [Testing Migrations](./schema-evolution.md#testing-migrations) |
| Configuration | A missing variable fails startup by name; `"false"` stays false | pure | [Testing Configuration](./configuration.md#testing-configuration) |
| Error handling | An unexpected error returns a generic 500 that leaks nothing | real DB as runtime role | [Testing Error Handling](./error-handling.md#testing-error-handling) |
| Health checks | Readiness returns 503 when the database is down; liveness stays 200 | a real DB you can stop | [Testing Resilience](./resilience.md#testing-resilience) |
| Idempotency | Two *concurrent* same-key requests produce one effect | real DB as runtime role, two connections | [Testing Resilience](./resilience.md#testing-resilience) |
| Timeouts, retries and shutdown | A silent stub times out; an unkeyed POST is not retried; SIGTERM lets an in-flight request finish | pure or local stub server; a spawned app process for SIGTERM | [Testing Resilience](./resilience.md#testing-resilience) |
| Authentication and authorization | No session gets 401; another user's resource is refused server-side | real DB as runtime role | [Testing Security](./security.md#testing-security) |
| Injection | A hostile payload returns no extra rows and round-trips literally | real DB as runtime role | [Testing Security](./security.md#testing-security) |
| Tenant isolation | Unfiltered or context-less queries and cross-tenant writes reach no other tenant's rows | real DB as runtime role | [Testing Tenant Isolation](./multi-tenant-isolation.md#testing-tenant-isolation) |
| API shape and status | No shape drift; creates return 201; empty collections return 200, not 404 | real DB as runtime role | [Testing the API Contract](./api-design.md#testing-the-api-contract) |
| Log scrubbing | A sensitive field never reaches the log output | in-process app, captured log sink | [Scrubbing Sensitive Data](./logging.md#scrubbing-sensitive-data) |
| Deploy smoke | A representative path returns its real payload, not merely any 2xx | live URL | [Smoke Tests](#smoke-tests--does-the-deployed-system-serve-real-requests) above |

---

## Test Infrastructure

### Harness Parity and Proving a Test Can Fail

**Harness parity.** A test proves a production property only when it runs under the production constraint that property depends on. Connect the code under test as the runtime role, never as the owner or a superuser: Postgres skips row-level security for superusers and `BYPASSRLS` roles, and for a table's owner unless the table is set to `FORCE ROW LEVEL SECURITY`, so a test connected that way never evaluates the policy it claims to test. The same rule covers the engine and major version you deploy (no SQLite standing in for Postgres, see **Options** below), at least two real connections for anything concurrent (the race barrier above), the production pool size when testing deadlock or pool exhaustion, the environment mode the app boots in, and the artifact you actually deploy (the deployed-unit rule above). The database setup below is the *how* that [Multi-Tenant Isolation](./multi-tenant-isolation.md#testing-tenant-isolation) leaves to this chapter.

**Prove the test can fail.** A test you have never seen fail proves nothing. Write it before the fix and watch it go red against the missing behaviour. For a test that pins behaviour already correct, break the code on purpose (drop the guard, disable the policy, remove the filter), watch the test go red, then restore the code exactly. Run a new test of nondeterministic behaviour (a race, randomness, an encoding) several times in a row before trusting it. Mutation testing (Stryker for TypeScript, mutmut for Python) automates the break-it step across a suite, if you want it.

### Test Framework

| Language | Framework | Why |
|----------|-----------|-----|
| TypeScript | **Vitest** | Fast, ESM-native, Jest-compatible API, built-in TypeScript support |
| Python | **pytest** | The standard, excellent fixtures, extensible with plugins |

Alternatives: Jest (TypeScript, older, slower than Vitest), unittest (Python, built-in but verbose).

### Test Environment Setup

Two setup concerns bite early. First, **match the environment to the test**: DOM-dependent tests need a browser-like environment (jsdom/happy-dom) while pure logic tests run faster on a plain node environment — most runners let you select per file, so don't pay the DOM cost for logic tests. Second, **modules that read environment variables at import time crash test *collection***, not just execution, on a clean checkout where those vars are unset — the import runs before any test does. Fix it centrally by injecting inert dummy values in the test config rather than scattering env setup across files.

### Test Database — Use a Real One

**In tests that exercise queries, don't mock the database.** Mocking means you're testing your mocks, not your queries. A query that passes against a mock might fail against a real database (wrong JOIN, missing index, constraint violation). (Pure-logic unit tests don't touch the database at all — this rule is about the tests that do.)

Spin up a real test database:

```typescript
// Vitest 3+ — test/global-setup.ts (config: test.globalSetup, test.fileParallelism: false). Runs once per run, not per file.
import type { TestProject } from 'vitest/node';

let stopDatabase: () => Promise<void>;

export async function setup(project: TestProject) {
  const { url: ownerUrl, stop } = await startTestDatabase();  // e.g. Testcontainers Postgres; its default user is a superuser
  await runMigrations(ownerUrl);                              // schema and seed run as the owner, once for the whole run
  const appUrl = await provisionAppRole(ownerUrl);            // production's grants: LOGIN, NOSUPERUSER, NOBYPASSRLS, owns nothing
  project.provide('ownerUrl', ownerUrl);                      // tests can't see this module's variables, only provided values
  project.provide('appUrl', appUrl);
  stopDatabase = stop;
}

export async function teardown() {
  await stopDatabase();
}

declare module 'vitest' {
  export interface ProvidedContext { ownerUrl: string; appUrl: string }
}
```

```typescript
// Vitest 3+ — test/db-setup.ts (config: test.setupFiles). Runs in every test file.
import { afterAll, beforeAll, beforeEach, inject } from 'vitest';

export let testDb: TestDb;                // the code under test and its tests use this: the runtime role
let ownerDb: TestDb;                      // reset and reseed only

beforeAll(() => {
  testDb = connectTestDatabase(inject('appUrl'));
  ownerDb = connectTestDatabase(inject('ownerUrl'));
});
beforeEach(() => ownerDb.truncateAll());  // clean state per test, as the owner, so the runtime role keeps production's grants
afterAll(async () => {                    // close this file's pools before teardown stops the database
  await testDb.close();
  await ownerDb.close();
});
```

This pair shares one database across all files with a truncate per test, so it sets `fileParallelism: false` to run files one at a time; the per-worker-database alternative is under **Sharing one container, safely** below.

```python
# pytest-asyncio 1.x — migrate once per session as the owner; tests run as the runtime role
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def owner_db():
    test_db = await create_test_database()   # the container's default user, a superuser
    await run_migrations(test_db)
    await provision_app_role(test_db)        # production's grants: NOSUPERUSER, NOBYPASSRLS, owns nothing
    yield test_db
    await test_db.drop()

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db(owner_db):
    app_db = await owner_db.connect_as_app_role()   # what the code under test uses
    yield app_db
    await app_db.close()                            # closes before owner_db drops the database

@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_db(owner_db):
    yield
    await owner_db.truncate_all()
```

In pytest-asyncio's default strict mode, async fixtures need `@pytest_asyncio.fixture` (as here) and async tests need `@pytest.mark.asyncio`: an unmarked `async def test_…` is not run (and fails outright on pytest 8.4+), and a plain `@pytest.fixture` on an `async def` is never awaited. Setting `asyncio_mode = "auto"` covers both, and the async test examples in this chapter assume it. Tests that use a session-loop fixture must run on that loop too, so set `asyncio_default_test_loop_scope = "session"`.

**Options:** Testcontainers is the default: it runs the same Postgres/MySQL version you deploy, in Docker. PGlite (Postgres compiled to WebAssembly, in-process) is fast for single-connection query logic, but it is single-user and single-connection (pglite-socket's multi-connection mode multiplexes that one connection, so it does not change this), so it cannot exercise concurrency, row locks, pool behaviour or the race barrier above. A dedicated test database in your cloud also works. Don't substitute SQLite in-memory for a Postgres stack: it has no row-level security (RLS), no Postgres `jsonb` semantics and no `FOR UPDATE`, so tests pass that production fails.

**Resetting between tests.** Re-running migrations before every test is correct but slow. The fast path is to truncate instead — `TRUNCATE … RESTART IDENTITY CASCADE` across every table, discovered dynamically from the catalog (so new tables are covered automatically), skipping the migration-ledger table. Re-seed any reference data the app treats as a source of truth from the *same* constant the application uses — otherwise truncation silently wipes seeded rows and tests drift from production. Keep the foreign-key-graph invariants in one reset helper rather than scattering them across tests. Three reset strategies, each with the case that breaks it:

| Strategy | Strength | Breaks when |
|----------|----------|-------------|
| Truncate and reseed (the setup above) | Simple; works whatever the code under test does | Parallel files share one database, so their truncates and seeds collide |
| Wrap each test in a transaction and roll it back | Fastest; other connections never see the test's rows | The code commits on a connection the test does not hold (SQLAlchemy 2's `join_transaction_mode="create_savepoint"` turns commits into savepoints, which leads to the last case); a test needs two connections (the race barrier); or the code relies on transaction-scoped settings (`SET LOCAL`, `set_config(…, true)`), which outlive its own transaction once that becomes a savepoint inside the test's |
| Clone a migrated template database per worker (`CREATE DATABASE … TEMPLATE …`) | Parallel-safe, and a clone is faster than re-migrating | Any session is connected to the template while it is cloned; tests within one worker still need one of the resets above |

**Sharing one container, safely.** Starting a fresh database container per test file is wasteful; start one in global setup and share it. But a shared database and parallel test files don't mix — concurrent files stomp on each other's truncate/seed. **Isolation strategy and parallelism are coupled:** either truncate-per-test with test files run serially, or give each parallel worker its own database (name it from `VITEST_POOL_ID` in Vitest, or pytest-xdist's `worker_id` fixture). Allow generous timeouts on first run, since the image cold-pulls once and per-test timeouts don't cover global setup.

### Mocking External HTTP Services

The "use a real database" principle does NOT apply to external HTTP APIs. Don't call the real Stripe API in tests: test-mode keys charge nothing, but real calls are slow, nondeterministic and rate-limited, and you can't make the provider time out or return a 500 on demand. You can't hit the real SendGrid API (it would send real emails). External services need to be mocked at the HTTP layer.

**The key principle:** Mock the HTTP boundary, not the function boundary. This way your business logic, error handling, retry logic, and serialization all get exercised — only the actual network call is faked.

**TypeScript — MSW (Mock Service Worker):**

MSW intercepts HTTP requests at the network level. Your application code doesn't know it's being mocked — it makes real `fetch` calls that MSW intercepts.

```typescript
// MSW 3 (ESM-only, Node 22.12+; on MSW 2 the option below is named onUnhandledRequest)
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  // Mock the Stripe API
  http.post('https://api.stripe.com/v1/charges', () => {
    return HttpResponse.json({ id: 'ch_test_123', status: 'succeeded' });
  }),

  // Mock a failure scenario
  http.post('https://api.stripe.com/v1/refunds', () => {
    return HttpResponse.json({ error: { message: 'Insufficient funds' } }, { status: 402 });
  }),
);

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }));  // default 'warn' lets unmocked calls reach the network; v3 ignores the old name
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('processes payment through Stripe', async () => {
  const result = await paymentService.charge(1000);
  expect(result.status).toBe('succeeded');
});

test('handles Stripe failure gracefully', async () => {
  // Override for this specific test
  server.use(
    http.post('https://api.stripe.com/v1/charges', () => {
      return HttpResponse.json({ error: { message: 'Card declined' } }, { status: 402 });
    }),
  );

  await expect(paymentService.charge(1000)).rejects.toThrow(ExternalServiceError);
});
```

**Python — respx (for httpx) or responses (for requests):**

```python
# respx 0.23 (httpx 0.28)
import respx
from httpx import Response

@respx.mock
async def test_processes_payment():
    respx.post("https://api.stripe.com/v1/charges").mock(
        return_value=Response(200, json={"id": "ch_test_123", "status": "succeeded"})
    )

    result = await payment_service.charge(1000)
    assert result.status == "succeeded"

@respx.mock
async def test_handles_stripe_failure():
    respx.post("https://api.stripe.com/v1/charges").mock(
        return_value=Response(402, json={"error": {"message": "Card declined"}})
    )

    with pytest.raises(ExternalServiceError):
        await payment_service.charge(1000)
```

**Why mock at HTTP, not at the function level:**

```typescript
// BAD: mocking the function — skips serialization, error handling, retry logic
vi.spyOn(stripe, 'createCharge').mockResolvedValue({ id: 'ch_123' });

// GOOD: mocking the HTTP call — exercises everything except the network
server.use(http.post('https://api.stripe.com/v1/charges', () => {
  return HttpResponse.json({ id: 'ch_123', status: 'succeeded' });
}));
```

Function-level mocks test your mock. HTTP-level mocks test your code. This does not rule out in-memory fakes of your own ports: test the production adapter once against HTTP-level mocks, and let the modules that depend on the port take a fake, as [Module Design](./module-design.md#structuring-around-dependencies) describes. What it rules out is stubbing the SDK or client call inside the adapter.

**A third option for cloud-service SDKs: a local emulator.** For provider SDKs (AWS, GCP) there's an option beyond mocking the HTTP boundary — run a local emulator of the service (e.g. LocalStack) in a container and point the real SDK client at it. This exercises *more* than an HTTP mock: the client's request signing, serialization, pagination, waiters, and error-shape parsing all run. It's viable because an emulator is local, fast and free of side effects. Since March 2026 LocalStack's image needs an auth token, including in CI, and its free plan is aimed at non-commercial use; budget for that, or use a token-free emulator such as moto in server mode or the provider's own local build (DynamoDB Local). Use the SDK's built-in waiters rather than `sleep`s for eventually-consistent operations. Keep HTTP-boundary mocking (above) for arbitrary third-party APIs that have no emulator.

### Test Organization

There are three common layouts; the choice depends on language conventions and team preference.

| Layout | Where tests live | Fits best, and the cost |
|--------|------------------|-------------------------|
| Dedicated folder | A `tests/` tree mirroring `src/`, with fixtures and factories beside the tests | Python, where pytest's convention expects it, and heavy test infrastructure; a rename touches two trees |
| Colocated | `users.test.ts` next to `users.ts`; integration and E2E tests in their own folder | TypeScript (Vitest, Jest and Next.js support it natively); an untested file shows at a glance; the build must exclude `*.test.ts`, which most do by default |
| Hybrid | Unit tests colocated; `tests/integration/`, `tests/e2e/` and `tests/fixtures/` for the rest | Suites whose unit tests map 1:1 to source files while integration, E2E and smoke tests don't |

Python strongly favours a `tests/` directory, and going against it creates friction with pytest defaults. TypeScript supports both, and colocated is increasingly common in React and Next.js projects. Whichever you pick, use one layout across the project.

### Test Data Factories

Don't hardcode test data everywhere. Create factory functions that generate valid objects with sensible defaults:

**TypeScript:**
```typescript
function createTestUser(overrides: Partial<User> = {}): User {
  return {
    id: crypto.randomUUID(),
    name: 'Test User',
    email: `test-${crypto.randomUUID().slice(0, 8)}@example.com`,
    role: 'member',
    createdAt: new Date().toISOString(),
    ...overrides,
  };
}

// In tests — readable, only specifies what matters
test('admin can delete users', async () => {
  const admin = createTestUser({ role: 'admin' });
  const target = createTestUser({ role: 'member' });
  // ...
});
```

**Python:**
```python
def create_test_user(**overrides) -> User:
    defaults = {
        "id": str(uuid4()),
        "name": "Test User",
        "email": f"test-{uuid4().hex[:8]}@example.com",
        "role": "member",
    }
    return User(**{**defaults, **overrides})
```

**Libraries do this for you:** fishery (TypeScript), factory_boy, or polyfactory, which builds Pydantic models from their type hints (Python). Use Faker for realistic values, seeded with a fixed value so a failing run reproduces.

**Build versus persist.** Give each factory two entry points: *build* returns an in-memory object for unit tests, and *create* inserts it through the app's own repository for real-database integration tests and returns the stored row, with its generated id and defaults. fishery, factory_boy and polyfactory all make this split.

**Schemas validate; they don't generate.** Passing an object through your Zod/Pydantic schema proves it is valid. It fills in only the defaults the schema declares; it doesn't generate anything else, and a missing required field still throws:

```typescript
// Zod 4
const testUser = UserSchema.parse({
  name: 'Test User',
  email: 'test@example.com',
  // fills only fields declared with .default(); a missing required field throws
});
```

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Test only the happy path | Test error cases, edge cases, boundary conditions | Happy path tests miss the bugs that break production |
| Mock the database in integration tests | Use a real test database | Mock tests pass even when real queries fail (wrong JOINs, constraint violations) |
| Trust a test you have never seen fail | Watch it fail against broken code, connected as the runtime role under production's pool and mode | A test that cannot go red passes against the bug too |
| Write tests that test the framework/library | Test YOUR code — your logic, your transformations, your wiring | Testing that `z.string().parse("hello")` works is testing Zod, not your app |
| Hardcode test data inline | Use test data factories with overrides | Inline data is duplicated, hard to maintain, and hides what matters in each test |
| Write only unit tests | Follow the pyramid — unit, integration, E2E | Unit tests can't catch wiring bugs, integration issues, or user-visible failures |
| Write E2E tests for everything | E2E only for critical user journeys | E2E tests are slow, brittle, expensive — use them surgically |
| Test implementation details (private methods, internal state) | Test behaviour (inputs → outputs, side effects) | Implementation changes break detail-tests even when behaviour is correct |
| Skip testing error responses | Test that errors return the right status code, format, and don't leak internals | Untested error paths are the ones that expose stack traces in production |
| Ignore flaky tests, or retry until green | Diagnose first: a flake is either a timing assumption in the test (wait on the condition, not a sleep; see the [`dev-condition-based-waiting`](../../dev-condition-based-waiting/SKILL.md) skill) or a real race in the code. Quarantine it with a named owner, treat CI retries as detection rather than a cure, and delete only a test that proves nothing | Flaky tests train the team to ignore failures, and a flake is sometimes the only sign of a real race |
| Test in production by accident | Use test databases, test API keys, test email addresses | Production side effects from tests (real emails, real charges) are incidents |

---

## Deciding for Your Project

1. **Test framework?** Vitest for TypeScript, pytest for Python — recommended defaults.
2. **Test database strategy?** The same engine, major version and harness locally and in CI (Testcontainers by default), with the code under test connected as the runtime role. Choose the reset strategy together with parallelism (see **Resetting between tests**).
3. **What's your minimum testing bar?** For a production service: schema validation wiring, error response format and critical API contracts, trimmed to the concerns the app actually has and scaled down further for prototypes. Authentication, authorization and tenant-isolation negatives are the exception: wherever the app has those concerns, they stay at any size.
4. **How many E2E tests?** One per critical user journey (signup, core workflow, payment if applicable). Not more than 10-20 for most apps.
5. **When do tests run?** Unit, integration and the critical-journey E2E tests on every PR, so every gate runs before the merge; only a slow, broad E2E sweep moves to nightly. Smoke tests on every deploy. The integration tests that need Docker or a real database are exactly the ones most often gated behind a separate opt-in command — make sure CI actually runs them, or your highest-value guards (tenant isolation, migration parity, concurrency) silently rot into checks nobody runs.
6. **How do you stand in for each external service?** Decide per service: an HTTP-level mock (MSW, respx) by default, a local emulator where the provider's SDK has one, and a periodic conformance run against the provider's sandbox to catch drift in your mocks.

---

## Related Topics

Each production concern's owning chapter is linked from the table in **What to Test for Each Production Concern**; the entries here are for the craft.

- **Seams and test doubles** — [Module Design](./module-design.md#structuring-around-dependencies) decides which dependencies get a real stand-in, an in-memory port fake or an HTTP mock, and why tests are replaced rather than layered when modules merge.
- **The incidents behind these rules** — [Pitfalls](./pitfalls.md#when-writing-tests) covers the test pool that hid a deadlock, the teardown that failed a green run, the tamper test that flipped a dead bit, and high-value tests gated out of CI.
- **What the race tests guard** — [Resilience](./resilience.md#the-idempotency-key-pattern) for the check-then-act race behind idempotency keys, and [Data Integrity](./data-integrity.md#database-transactions) for the transactions and locks that close it.
