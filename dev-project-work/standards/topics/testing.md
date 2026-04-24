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

This is the systems view. For each production topic in this skill, here's what needs testing and why.

### Data Integrity Tests

See [Data Integrity](./data-integrity.md) for the concepts these tests verify.

**Schema-to-reality alignment:**
```typescript
// Does our schema match what the database actually returns?
test('UserSchema matches database rows', async () => {
  const rows = await db.query('SELECT * FROM users LIMIT 10');
  for (const row of rows) {
    expect(() => UserSchema.parse(row)).not.toThrow();
  }
});
```

**Validation wiring — is validation actually being called?**
```typescript
// Send invalid data → expect rejection
test('POST /api/users rejects missing email', async () => {
  const response = await request(app)
    .post('/api/users')
    .send({ name: 'Kasey' });  // no email
  expect(response.status).toBe(400);
  expect(response.body.errors).toBeDefined();
});
```

**Data transformation correctness — the data pipeline:**

Data enters valid but gets transformed at multiple stages. Each transformation needs testing:

```
DB row → API serialization → Frontend fetch → Hook/transform → Component props
  ↑            ↑                   ↑               ↑                ↑
 test         test               test            test             test
```

```typescript
// Testing a React hook that transforms API data
test('useUserGroups groups users by role', () => {
  const apiUsers = [
    { id: 1, name: 'Alice', role: 'admin' },
    { id: 2, name: 'Bob', role: 'member' },
    { id: 3, name: 'Carol', role: 'admin' },
  ];

  const { result } = renderHook(() => useUserGroups(apiUsers));

  expect(result.current.admin).toHaveLength(2);
  expect(result.current.member).toHaveLength(1);
});
```

```python
# Testing a service function that derives data
def test_calculate_order_summary():
    orders = [
        Order(id=1, amount=50.00, status="completed"),
        Order(id=2, amount=30.00, status="pending"),
        Order(id=3, amount=20.00, status="completed"),
    ]

    summary = calculate_order_summary(orders)

    assert summary.total_completed == 70.00
    assert summary.count_pending == 1
```

**Complex schema logic:**
```typescript
// Custom refinements have logic that can be wrong — test them
const DiscountSchema = z.object({
  type: z.enum(["percentage", "fixed"]),
  value: z.number(),
}).refine(
  (d) => d.type !== "percentage" || (d.value >= 0 && d.value <= 100),
  "Percentage discount must be 0-100"
);

test('rejects percentage discount over 100', () => {
  const result = DiscountSchema.safeParse({ type: "percentage", value: 150 });
  expect(result.success).toBe(false);
});

test('allows fixed discount over 100', () => {
  const result = DiscountSchema.safeParse({ type: "fixed", value: 150 });
  expect(result.success).toBe(true);
});
```

### Configuration Tests

See [Configuration](./configuration.md) for the concepts these tests verify.

```typescript
// Does the app fail fast with clear message when config is missing?
test('startup fails when DATABASE_URL is missing', () => {
  const original = process.env.DATABASE_URL;
  delete process.env.DATABASE_URL;
  expect(() => envSchema.parse(process.env)).toThrow(/DATABASE_URL/);
  process.env.DATABASE_URL = original;
});

// Does type coercion work?
test('PORT is coerced from string to number', () => {
  const result = envSchema.parse({ ...validEnv, PORT: '8080' });
  expect(result.PORT).toBe(8080);
  expect(typeof result.PORT).toBe('number');
});
```

### Error Handling Tests

See [Error Handling](./error-handling.md) for the concepts these tests verify.

```typescript
// Does the error hierarchy produce correct HTTP status codes?
test('NotFoundError returns 404', async () => {
  const response = await request(app).get('/api/users/nonexistent');
  expect(response.status).toBe(404);
  expect(response.body.type).toBe('NotFoundError');
});

// Does the global handler catch unknown errors safely?
test('unknown errors return 500 without exposing internals', async () => {
  vi.spyOn(db, 'findUser').mockRejectedValue(new Error('segfault'));

  const response = await request(app).get('/api/users/123');

  expect(response.status).toBe(500);
  expect(response.body.type).toBe('InternalError');
  expect(response.body.title).toBe('Internal server error');
  // MUST NOT contain stack trace or internal error details
  expect(response.body).not.toHaveProperty('stack');
  expect(response.body.title).not.toContain('segfault');
});

// Does the error response match RFC 9457 format?
test('validation errors include field-level details', async () => {
  const response = await request(app)
    .post('/api/users')
    .send({ name: '', email: 'not-an-email' });

  expect(response.status).toBe(400);
  expect(response.body).toMatchObject({
    type: 'ValidationError',
    status: 400,
    errors: expect.arrayContaining([
      expect.objectContaining({ field: 'name' }),
      expect.objectContaining({ field: 'email' }),
    ]),
  });
});
```

```python
async def test_not_found_returns_404(client):
    response = await client.get("/api/users/nonexistent")
    assert response.status_code == 404
    assert response.json()["type"] == "NotFoundError"

async def test_unknown_error_returns_safe_500(client, monkeypatch):
    async def broken_query(*args):
        raise RuntimeError("segfault")
    monkeypatch.setattr(db, "find_user", broken_query)

    response = await client.get("/api/users/123")
    assert response.status_code == 500
    assert "segfault" not in response.json()["title"]
```

### Resilience Tests

See [Resilience](./resilience.md) for the concepts these tests verify.

```typescript
// Health check returns 503 when database is down
test('readiness returns 503 when DB is down', async () => {
  await db.disconnect();
  const response = await request(app).get('/health/ready');
  expect(response.status).toBe(503);
  expect(response.body.status).toBe('not ready');
  await db.connect();
});

// Liveness always returns 200 regardless of dependencies
test('liveness returns 200 even when DB is down', async () => {
  await db.disconnect();
  const response = await request(app).get('/health/live');
  expect(response.status).toBe(200);
  await db.connect();
});

// Idempotency — same key returns same result
test('duplicate idempotency key returns original result', async () => {
  const key = 'order-123-payment';
  const first = await request(app)
    .post('/api/payments')
    .set('Idempotency-Key', key)
    .send({ amount: 1000 });
  const second = await request(app)
    .post('/api/payments')
    .set('Idempotency-Key', key)
    .send({ amount: 1000 });

  expect(first.status).toBe(201);
  expect(second.status).toBe(200);  // or 201 — but same result
  expect(second.body.id).toBe(first.body.id);  // same payment, not a duplicate
});
```

### Security Tests

See [Security](./security.md) for the concepts these tests verify.

```typescript
// Authorization — user cannot access another user's data
test('user cannot access another user\'s data', async () => {
  const response = await request(app)
    .get('/api/users/456')
    .set('Authorization', `Bearer ${userAToken}`);
  expect(response.status).toBe(403);
});

// Authentication — protected routes reject unauthenticated requests
test('protected route rejects missing auth', async () => {
  const response = await request(app).get('/api/users/123');
  expect(response.status).toBe(401);
});

// SQL injection — malicious input doesn't break the system
test('SQL injection attempt is handled safely', async () => {
  const response = await request(app)
    .get('/api/users')
    .query({ search: "'; DROP TABLE users; --" });

  // Should either reject (400) or return empty results safely
  expect([200, 400]).toContain(response.status);
  // Table must still exist
  const count = await db.query('SELECT COUNT(*) as c FROM users');
  expect(count[0].c).toBeGreaterThan(0);
});

// Sensitive data not leaked in errors
test('error responses do not contain stack traces', async () => {
  const response = await request(app).get('/api/force-error');
  expect(response.body).not.toHaveProperty('stack');
  expect(JSON.stringify(response.body)).not.toContain('.ts:');
  expect(JSON.stringify(response.body)).not.toContain('.py:');
});
```

### API Contract Tests

See [API Design](./api-design.md) for the concepts these tests verify.

```typescript
// Response shape consistency
test('GET /api/users returns paginated response', async () => {
  const response = await request(app).get('/api/users?limit=10');
  expect(response.body).toHaveProperty('data');
  expect(response.body).toHaveProperty('pagination');
  expect(Array.isArray(response.body.data)).toBe(true);
  expect(response.body.pagination).toHaveProperty('hasMore');
});

// Status codes are consistent
test('creating returns 201, not 200', async () => {
  const response = await request(app)
    .post('/api/users')
    .send(validUser);
  expect(response.status).toBe(201);
});

// Pagination edge cases
test('empty results return empty data array, not 404', async () => {
  const response = await request(app).get('/api/users?status=nonexistent');
  expect(response.status).toBe(200);
  expect(response.body.data).toEqual([]);
});
```

### Deployment Smoke Tests

See [Deployment](./deployment.md) for the concepts these tests verify.

```typescript
// Run after every deploy — verify critical paths work
test('health check is reachable', async () => {
  const response = await fetch(`${DEPLOY_URL}/health/ready`);
  expect(response.status).toBe(200);
});

test('homepage loads', async () => {
  const response = await fetch(`${DEPLOY_URL}/`);
  expect(response.status).toBe(200);
});

test('API returns data', async () => {
  const response = await fetch(`${DEPLOY_URL}/api/health`);
  const body = await response.json();
  expect(body.status).toBe('ok');
});
```

---

## Test Infrastructure

### Test Framework

| Language | Framework | Why |
|----------|-----------|-----|
| TypeScript | **Vitest** | Fast, ESM-native, Jest-compatible API, built-in TypeScript support |
| Python | **pytest** | The standard, excellent fixtures, extensible with plugins |

Alternatives: Jest (TypeScript, older, slower than Vitest), unittest (Python, built-in but verbose).

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
5. **When do tests run?** Unit + integration on every PR. E2E on merge to main. Smoke tests on every deploy.

---

## Related Topics

This topic connects to every other topic in the skill. Each section above links to the relevant topic for the concepts being tested:

- [Data Integrity](./data-integrity.md) — schemas, validation boundaries, transformation correctness
- [Configuration](./configuration.md) — startup validation, type coercion
- [Error Handling](./error-handling.md) — error hierarchy, response format, information leakage
- [Resilience](./resilience.md) — health checks, idempotency, timeout handling
- [Security](./security.md) — authentication, authorization, injection, sensitive data exposure
- [API Design](./api-design.md) — response shapes, pagination, status codes
- [Deployment](./deployment.md) — smoke tests, migration verification
