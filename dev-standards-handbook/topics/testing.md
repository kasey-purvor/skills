# Testing

## The Systems View of Testing

Most developers think of testing as "write a function, write a test for that function." That's the micro view. The systems view asks a completely different question: **how do you prove your entire system works correctly?**

A system has many layers and boundaries. Data enters, gets validated, transformed, stored, retrieved, transformed again, and sent out. Errors get thrown, caught, classified, and turned into responses. External services get called, fail, retry, and recover. Each of these is a place where bugs hide.

Testing at the systems level means covering all of these concerns systematically — not just "does this function return the right value?" but "does this system behave correctly under real conditions?"

---

## Test Types — What Each One Proves

### Unit Tests — "Does this logic work in isolation?"

A unit test exercises a single function or class with controlled inputs and verifies the output. Dependencies are replaced with test doubles (mocks, stubs).

**TypeScript (Vitest):**
```typescript
test('applies percentage discount correctly', () => {
  const result = calculateDiscount({
    price: 100,
    discount: { type: 'percentage', value: 20 },
  });
  expect(result).toBe(80);
});

test('rejects discount over 100%', () => {
  expect(() =>
    calculateDiscount({
      price: 100,
      discount: { type: 'percentage', value: 150 },
    })
  ).toThrow(ValidationError);
});
```

**Python (pytest):**
```python
def test_applies_percentage_discount():
    result = calculate_discount(price=100, discount=Discount(type="percentage", value=20))
    assert result == 80

def test_rejects_discount_over_100():
    with pytest.raises(ValidationError):
        calculate_discount(price=100, discount=Discount(type="percentage", value=150))
```

**What unit tests prove:** Your logic is correct when given known inputs.
**What they don't prove:** That the inputs actually look like that in the real system. That the function is wired into the right place. That the database or external service behaves the way your mock said it would.

### Integration Tests — "Do components work together?"

An integration test exercises multiple components working together — your API handler + your database, your service + an external API, your middleware + your routes.

**TypeScript:**
```typescript
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

**Python:**
```python
async def test_create_user(client, db):
    response = await client.post(
        "/api/users",
        json={"name": "Kasey", "email": "kasey@example.com"},
    )

    assert response.status_code == 201
    assert response.json()["id"]

    user = await db.find_user(response.json()["id"])
    assert user.name == "Kasey"
```

**What integration tests prove:** Components actually work together — the handler validates, writes to the DB, returns the right response.
**What they don't prove:** That the system handles load, that the UI renders correctly, that the deploy works.

**When the deploy unit isn't a server.** The `request(app)` pattern above assumes a long-running HTTP server. If your deploy unit is a function the platform invokes (a serverless handler), the equivalent integration test invokes the *real exported handler* with a synthetic provider event (e.g. an API-Gateway request object built by a typed factory), running the whole middleware chain — routing, auth, validation, handler — against a real database, mocking only the composition root. Test the unit you actually deploy: if that's `handler(event)`, drive `handler(event)`, not a server you only construct in tests.

### Contract Tests — "Does my code match what external data actually looks like?"

A contract test runs your schemas against real or snapshot data to prove they match reality:

```typescript
test('UserSchema matches actual database rows', async () => {
  const rows = await db.query('SELECT * FROM users LIMIT 10');
  for (const row of rows) {
    expect(() => UserSchema.parse(row)).not.toThrow();
  }
});
```

```python
def test_user_schema_matches_api(client):
    response = client.get("/api/users/1")
    # If the schema is wrong, this throws ValidationError
    user = User(**response.json())
```

**What contract tests prove:** Your schemas match the real world — not just what you think the data looks like.

**Round-trip contract tests.** A parse-only contract test (does the schema accept the data?) misses *lossy* serialization — a value that survives parsing but changes on the way through the store (JSON/`jsonb` coercion, date/timezone normalisation, composite keys). To catch it, write a value in through the application's own query/serialization path, read it back through the read path, and assert it both parses against the schema *and* deep-equals the original input. This matters most for schemas **shared** between services (e.g. backend and frontend) — see [API Design](./api-design.md) for defining that shared contract.

### End-to-End Tests — "Does the whole system work from the user's perspective?"

An E2E test drives the actual UI (or the API from outside) and verifies the full flow:

```typescript
test('user can sign up and see their dashboard', async ({ page }) => {
  await page.goto('/signup');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'SecurePass123!');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1')).toContainText('Welcome');
});
```

**What E2E tests prove:** The system works as a user experiences it.
**What they cost:** Slow, flaky (UI changes break them), expensive to maintain. Use sparingly for critical paths only.

### Concurrency and Race-Condition Tests — "Does the guard hold when two callers race?"

A race condition — two requests reading the same row before either writes (a time-of-check-to-time-of-use, or TOCTOU, gap) — is invisible to ordinary tests, because the dangerous interleaving only fires under precise timing. Make it deterministic instead of hoping to catch it: inject a synchronization barrier at the check step that parks every caller until all of them have read, then releases them together, so the worst-case ordering happens on *every* run.

```typescript
test('two concurrent creates cannot both pass the uniqueness check', async () => {
  const barrier = makeBarrier(2);                 // releases once both callers arrive
  onRead(repo, () => barrier.arriveAndWait());    // park each caller after it reads

  const results = await Promise.allSettled([createDraft(input), createDraft(input)]);

  expect(results.filter(r => r.status === 'fulfilled')).toHaveLength(1);  // exactly one wins
});
```

The guarded implementation makes the barrier unsatisfiable for more than one caller (only one ever reaches the read), so the test turns green — put a timeout on the barrier so a green run can't hang. This is the opposite of waiting out a flaky test: you're *forcing* the bad interleaving, not polling for an expected state.

### The Testing Pyramid

```
         /  E2E  \          Few — slow, expensive, critical user journeys only
        /----------\
       / Integration \      Moderate — component interactions, API contracts
      /----------------\
     /    Unit Tests     \  Many — fast, cheap, logic and edge cases
    /______________________\
```

Most tests should be **unit tests** (fast, cheap, reliable). Some should be **integration tests** (verify components work together). Few should be **E2E tests** (verify critical user journeys).

The pyramid doesn't mean E2E tests are less important — it means they're more expensive per test, so you target them at flows that matter most (signup, checkout, core workflows).

---

## What to Test for Each Production Concern

This is the systems view. For each production concern below, here's what needs testing — the detail of *what to verify and why* lives in that concern's own topic (linked from each entry); the test *craft* (how to write them) stays here.

### Data Integrity Tests

See [Data Integrity](./data-integrity.md) for what to verify: that your schema matches reality (parse real rows from the tables this concern owns against the schema — the contract-test pattern shown above), that validation is actually wired in (an invalid payload is rejected at the boundary with a 400, not silently inserted), that each stage of the transformation pipeline (DB row → API → hook → component) produces correct output, and that hand-written schema logic — custom refinements, discriminated unions, conditional validation — behaves on both its accept and reject branches. The contract and wiring tests run against a real database — see the **Test Database — Use a Real One** setup below.

### Migration Tests

See [Schema Evolution](./schema-evolution.md) for what to verify: that each migration's intended effect actually holds (a new constraint rejects the rows it should — on both INSERT and UPDATE; a backfill leaves no nulls; a dropped column is gone), proven red-before/green-after; and that a clean replay from an empty schema reproduces the same reference data the app treats as source-of-truth. These run against a real database — see the **Test Database — Use a Real One** setup below.

### Configuration Tests

See [Configuration](./configuration.md) for what to verify: that the config schema fails fast when a required variable is missing — and that the error names the offending variable, so a broken deploy surfaces a clear message at startup rather than a cryptic crash on first use (in serverless, this stands in for the cold-start failure that would otherwise hide deep in a handler); and that the coercion the config relies on is real — a `PORT` string parses to a typed number, and the boolean allowlist doesn't let `"false"`/`"0"` silently flip a flag on. These are small, fast tests against the schema itself — no real database needed, since config validation is pure parsing.

### Error Handling Tests

See [Error Handling](./error-handling.md) for what to verify: that the error hierarchy maps to the right response (a thrown `NotFoundError` returns 404 with code `NOT_FOUND`, a validation failure returns 400 with code `VALIDATION_ERROR` and a field-level `errors` array), proving the RFC 9457 shape is populated; and — the check that matters most — that an unexpected (non-`AppError`) failure deep in a dependency returns a generic 500 with code `INTERNAL_ERROR` whose body leaks nothing: no stack trace, and none of the underlying error message. Assert that negative explicitly. These drive a request through the whole middleware chain against a real backend — see the **Test Database — Use a Real One** setup below.

### Resilience Tests

See [Resilience](./resilience.md) for what to verify: the liveness/readiness split holds against a dependency you can actually stop (readiness returns 503 with a not-ready body when the database is down; liveness still returns 200, so traffic routes away instead of triggering a restart loop), and idempotency de-duplicates (two requests with the same idempotency key produce one effect, the second returning the stored result, not a duplicate). The idempotency test must drive the two requests *concurrently* to reproduce the check-then-act race — a sequential version false-greens against the broken implementation. These need a real database engine to exercise the readiness probe and enforce the storage-layer uniqueness guard, so use the **Test Database — Use a Real One** setup below.

### Security Tests

See [Security](./security.md) for what to verify: that an unauthenticated request to a protected route is rejected (401) and that an authenticated caller cannot reach a resource they don't own (403) — the authentication gate and the resource-ownership check are distinct failures and need separate assertions; that an injection payload driven through a real endpoint is handled safely *and* the target table still exists afterward, proving parameterized queries held; and that an error response leaks no source-file paths or internal implementation detail to a probing attacker (the generic no-stack-trace-in-500 guarantee is Error Handling's). Because these prove negatives against a live request path — and the injection check only means something against a real database engine, not a mock — run them with the **Test Database — Use a Real One** setup below.

### Multi-Tenant Isolation Tests

See [Multi-Tenant Isolation](./multi-tenant-isolation.md) for what to verify: prove the negative (a query with no tenant filter returns only the caller's rows), cover the fail-safe paths (missing or empty tenant context returns zero rows), test the write side (a row stamped for another tenant is rejected), and reproduce the production privilege drop so the test can't false-green. These can only be proven against a real database engine — mocks can't enforce isolation — so use the **Test Database — Use a Real One** setup below.

### API Contract Tests

See [API Design](./api-design.md) for what to verify: that every collection endpoint returns the project's chosen response shape consistently (a bare array, or the `{ data, pagination }` envelope with `hasMore`) and no endpoint drifts to a third shape; that mutations return the status code their HTTP method promises (a create returns 201, not a generic 200); and that the empty-collection edge case is handled as a contract, not an error (a query matching nothing returns 200 with an empty collection, not a 404). These drive the real endpoints end to end against a real database — see the **Test Database — Use a Real One** setup below.

### Deployment Smoke Tests

See [Deployment](./deployment.md) for what to verify and for running these as an automated deploy/promotion gate (its "Smoke-gate each step" bullet) rather than a hand-run suite. A smoke test probes the *live deployed URL* from outside (not an in-process app) right after the deploy: the health/readiness endpoint is reachable, the primary public entry point serves, and a representative API path returns its expected payload — not merely any 2xx, so a process that accepts connections but can't serve real responses still fails the gate. These hit a running deployment over HTTP, so they need no test database.

---

## Test Infrastructure

### Test Framework

| Language | Framework | Why |
|----------|-----------|-----|
| TypeScript | **Vitest** | Fast, ESM-native, Jest-compatible API, built-in TypeScript support |
| Python | **pytest** | The standard, excellent fixtures, extensible with plugins |

Alternatives: Jest (TypeScript, older, slower than Vitest), unittest (Python, built-in but verbose).

### Test Environment Setup

Two setup concerns bite early. First, **match the environment to the test**: DOM-dependent tests need a browser-like environment (jsdom/happy-dom) while pure logic tests run faster on a plain node environment — most runners let you select per file, so don't pay the DOM cost for logic tests. Second, **modules that read environment variables at import time crash test *collection***, not just execution, on a clean checkout where those vars are unset — the import runs before any test does. Fix it centrally by injecting inert dummy values in the test config rather than scattering env setup across files.

### Test Database — Use a Real One

**Don't mock the database.** Mocking means you're testing your mocks, not your queries. A query that passes against a mock might fail against a real database (wrong JOIN, missing index, constraint violation).

Spin up a real test database:

```typescript
// Vitest global setup — test DB lifecycle
beforeAll(async () => {
  testDb = await createTestDatabase();  // Docker, testcontainers, or in-memory
  await runMigrations(testDb);
});

afterAll(async () => {
  await testDb.destroy();
});

beforeEach(async () => {
  await testDb.truncateAll();  // clean state per test
});
```

```python
@pytest.fixture
async def db():
    test_db = await create_test_database()
    await run_migrations(test_db)
    yield test_db
    await test_db.drop()

@pytest.fixture(autouse=True)
async def clean_db(db):
    yield
    await db.truncate_all()
```

**Options:** Docker + testcontainers (spins up a real Postgres/MySQL), SQLite in-memory (fast but lacks some features), dedicated test database in your cloud.

**Resetting between tests.** Re-running migrations before every test is correct but slow. The fast path is to truncate instead — `TRUNCATE … RESTART IDENTITY CASCADE` across every table, discovered dynamically from the catalog (so new tables are covered automatically), skipping the migration-ledger table. Re-seed any reference data the app treats as a source of truth from the *same* constant the application uses — otherwise truncation silently wipes seeded rows and tests drift from production. Keep the foreign-key-graph invariants in one reset helper rather than scattering them across tests.

**Sharing one container, safely.** Starting a fresh database container per test file is wasteful; start one in global setup and share it. But a shared database and parallel test files don't mix — concurrent files stomp on each other's truncate/seed. **Isolation strategy and parallelism are coupled:** either truncate-per-test with test files run serially, or give each parallel worker its own database. Allow generous timeouts on first run, since the image cold-pulls once and per-test timeouts don't cover global setup.

### Mocking External HTTP Services

The "use a real database" principle does NOT apply to external HTTP APIs. You can't call the real Stripe API in tests (it would charge real money). You can't hit the real SendGrid API (it would send real emails). External services need to be mocked at the HTTP layer.

**The key principle:** Mock the HTTP boundary, not the function boundary. This way your business logic, error handling, retry logic, and serialization all get exercised — only the actual network call is faked.

**TypeScript — MSW (Mock Service Worker):**

MSW intercepts HTTP requests at the network level. Your application code doesn't know it's being mocked — it makes real `fetch` calls that MSW intercepts.

```typescript
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

beforeAll(() => server.listen());
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

Function-level mocks test your mock. HTTP-level mocks test your code.

**A third option for cloud-service SDKs: a local emulator.** For provider SDKs (AWS, GCP) there's an option beyond mocking the HTTP boundary — run a local emulator of the service (e.g. LocalStack) in a container and point the real SDK client at it. This exercises *more* than an HTTP mock: the client's request signing, serialization, pagination, waiters, and error-shape parsing all run. It's viable precisely because an emulator costs nothing to call (unlike the real Stripe/SendGrid APIs). Use the SDK's built-in waiters rather than `sleep`s for eventually-consistent operations. Keep HTTP-boundary mocking (above) for arbitrary third-party APIs that have no emulator.

### Test Organization

There are two common approaches, and the choice depends on your project, language conventions, and team preference.

**Approach 1: Dedicated test folder (separate from source)**

```
src/
  api/users.ts
  services/payment.ts
tests/
  api/users.test.ts
  services/payment.test.ts
  e2e/signup-flow.test.ts
  fixtures/factories.ts
```

Tests mirror the source tree in a parallel `tests/` directory. Test infrastructure (fixtures, factories, helpers) lives alongside the tests.

- **When it works well:** Python projects (pytest convention — strong community expectation), projects with complex test infrastructure, when you want a clear separation of production code from test code.
- **Tradeoff:** You navigate two parallel directory trees. When you rename a source file, you have to remember to rename the test file too.

**Approach 2: Colocated (test files alongside source)**

```
src/
  api/
    users.ts
    users.test.ts
  services/
    payment.ts
    payment.test.ts
  hooks/
    useUserGroups.ts
    useUserGroups.test.ts
```

Test files live next to the files they test. Integration and E2E tests that don't map to a single source file go in a dedicated folder.

- **When it works well:** TypeScript/JavaScript projects (Vitest, Jest, Next.js all support it natively), when you want it to be immediately obvious which files are untested (no `.test.ts` next to them).
- **Tradeoff:** Test files mixed into the source tree. Your build tool needs to be configured to exclude `.test.ts` files from production bundles (most already do).

**Approach 3: Hybrid**

```
src/
  api/
    users.ts
    users.test.ts          ← unit tests colocated
  services/
    payment.ts
    payment.test.ts        ← unit tests colocated
tests/
  integration/
    api-users.test.ts      ← integration tests in dedicated folder
  e2e/
    signup-flow.test.ts    ← E2E tests in dedicated folder
  fixtures/
    factories.ts           ← shared test helpers
```

Unit tests colocated (they map 1:1 to source files). Integration, E2E, and smoke tests in a dedicated folder (they don't map to a single source file).

**Language conventions:**
- **Python:** Strongly favours `tests/` directory. Going against this creates friction with pytest defaults and community expectations.
- **TypeScript/JavaScript:** Both approaches are well-supported. Colocated is increasingly popular in React/Next.js ecosystems. Dedicated folder is more traditional.

The important thing is consistency within a project — pick one and stick with it.

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

**Using schemas as factories:** Your Zod/Pydantic schemas can generate valid test data — the parse guarantees validity:

```typescript
const testUser = UserSchema.parse({
  name: 'Test User',
  email: 'test@example.com',
  // Schema fills in defaults for id, createdAt, etc.
});
```

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Test only the happy path | Test error cases, edge cases, boundary conditions | Happy path tests miss the bugs that break production |
| Mock the database in integration tests | Use a real test database | Mock tests pass even when real queries fail (wrong JOINs, constraint violations) |
| Write tests that test the framework/library | Test YOUR code — your logic, your transformations, your wiring | Testing that `z.string().parse("hello")` works is testing Zod, not your app |
| Hardcode test data inline | Use test data factories with overrides | Inline data is duplicated, hard to maintain, and hides what matters in each test |
| Write only unit tests | Follow the pyramid — unit, integration, E2E | Unit tests can't catch wiring bugs, integration issues, or user-visible failures |
| Write E2E tests for everything | E2E only for critical user journeys | E2E tests are slow, flaky, expensive — use them surgically |
| Test implementation details (private methods, internal state) | Test behaviour (inputs → outputs, side effects) | Implementation changes break detail-tests even when behaviour is correct |
| Skip testing error responses | Test that errors return the right status code, format, and don't leak internals | Untested error paths are the ones that expose stack traces in production |
| Ignore flaky tests | Fix or delete them | Flaky tests train the team to ignore test failures |
| Test in production by accident | Use test databases, test API keys, test email addresses | Production side effects from tests (real emails, real charges) are incidents |

---

## The Testing Checklist

When reviewing whether your system is adequately tested, walk through each concern:

- [ ] **Data validation** — Do API endpoints reject invalid input? Do schemas match real data?
- [ ] **Data transformations** — Is each stage of the data pipeline tested?
- [ ] **Configuration** — Does the app fail fast with clear messages for missing config?
- [ ] **Error handling** — Does each error type produce the correct response? Are internals hidden?
- [ ] **Health checks** — Do they return correct status when dependencies are up vs down?
- [ ] **Authentication** — Do protected routes reject unauthenticated requests?
- [ ] **Authorization** — Can users only access their own data?
- [ ] **API contracts** — Do responses match the documented shape? Are status codes consistent?
- [ ] **Pagination** — Do edge cases work (empty results, last page, invalid cursor)?
- [ ] **Idempotency** — Do retried requests produce the same result?
- [ ] **Smoke tests** — Do critical paths work after every deployment?

---

## Deciding for Your Project

1. **Test framework?** Vitest for TypeScript, pytest for Python — recommended defaults.
2. **Test database strategy?** Docker + testcontainers for CI, local database for development.
3. **What's your minimum testing bar?** At minimum: schema validation wiring, error response format, authentication/authorization, critical API contracts.
4. **How many E2E tests?** One per critical user journey (signup, core workflow, payment if applicable). Not more than 10-20 for most apps.
5. **When do tests run?** Unit + integration on every PR. E2E on merge to main. Smoke tests on every deploy. The integration tests that need Docker or a real database are exactly the ones most often gated behind a separate opt-in command — make sure CI actually runs them, or your highest-value guards (tenant isolation, migration parity, concurrency) silently rot into checks nobody runs.

---

## Related Topics

This topic connects to every other topic in the skill. Each section above links to the relevant topic for the concepts being tested:

- [Data Integrity](./data-integrity.md) — schemas, validation boundaries, transformation correctness
- [Schema Evolution](./schema-evolution.md) — migration behaviour and replay-parity tests
- [Configuration](./configuration.md) — startup validation, type coercion
- [Error Handling](./error-handling.md) — error hierarchy, response format, information leakage
- [Resilience](./resilience.md) — health checks, idempotency, timeout handling
- [Security](./security.md) — authentication, authorization, injection, sensitive data exposure
- [Multi-Tenant Isolation](./multi-tenant-isolation.md) — tenant scoping, RLS, cross-tenant write protection
- [API Design](./api-design.md) — response shapes, pagination, status codes
- [Deployment](./deployment.md) — smoke tests, migration verification
