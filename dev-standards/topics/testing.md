# Testing Standards

**Status:** Draft

## Core Principle

TDD is mandatory at all tiers. AI agents must always write tests first — no exceptions.

---

## Tier Requirements

### Exploratory

**TDD only.** The red-green-refactor cycle produces baseline tests. No additional requirements.

- Write failing test
- Write minimal code to pass
- Refactor
- Repeat

This naturally produces tests for implemented functionality, sufficient for throwaway/exploratory code.

### Internal

**TDD + Explicit edge cases in plan.**

The Implementer must specify edge cases when writing the plan. AI executes against the list.

Example in plan:
```markdown
### Test: validate_email()
- Valid: standard format, subdomains, plus addressing
- Invalid: missing @, missing domain, spaces, empty string
- Boundary: max length (254 chars), min length (3 chars)
```

### Production

**TDD + Edge cases + Templates + Specification-grounded testing + Mutation testing.**

All Internal requirements, plus:

1. **Test case templates** — Use predefined checklists for common patterns (see Templates section)
2. **Specification-grounded testing** — When formal data models exist (see [Data Integrity Standards](./data-integrity.md)), tests use those schemas as both input constructors and output validators (see Testing Against Specifications section)
3. **Mutation testing** — Run `mutmut` (or equivalent) on changed files; surviving mutants must be addressed

---

## Design for Testability

Writing tests is only possible if the code is structured to accept them. These patterns make code testable by design — apply them as you write, not after the fact.

### Separate Pure Logic from I/O

Business calculations (scoring, formatting, validation, transformation) should be standalone functions that take explicit inputs and return explicit outputs. They should not import database clients, make API calls, or access browser APIs.

**The test:** Can you call this function from a test file by passing in plain values and checking the return value? If yes, it's testable. If you need to set up a database, mock an HTTP client, or render a React component first — the logic needs extracting.

```
# Good: pure function, testable with plain values
def calculate_commission(gp_amount: float, tiers: list[Tier]) -> float:

# Bad: logic trapped inside I/O
def get_commission():
    gp = db.query("SELECT sum(gp) FROM orders WHERE ...")
    tiers = db.query("SELECT * FROM commission_tiers WHERE ...")
    # ... 30 lines of calculation ...
    return result
```

### Accept Dependencies as Parameters

Functions that need external services (database, API client, cache) should receive them as parameters rather than importing module-level singletons. This lets tests pass in fakes or mocks without patching imports.

```python
# Good: client is passed in
def fetch_customers(db_client, tenant_id: str) -> list[Customer]:

# Bad: client is grabbed from a global
from integrations.database import db  # module-level singleton
def fetch_customers(tenant_id: str) -> list[Customer]:
```

This applies to React hooks too — a hook that imports a Supabase/Firebase/Prisma client directly can only be tested by mocking that module. A hook that receives a data-fetching function can be tested by passing a fake.

### Export Pure Functions

If a function is pure (no side effects, explicit inputs/outputs), export it — even if only one consumer uses it today. Private pure functions are untestable from outside their module. This is one of the most common testability mistakes: the logic is clean, but unreachable.

### Make Date-Dependent Functions Accept a Date

Functions that use `new Date()` or `datetime.now()` internally produce different output depending on when they run. This makes tests non-deterministic — they might pass today and fail tomorrow.

**Fix:** Accept an optional `now` parameter that defaults to the current time in production but can be fixed to a known value in tests.

```typescript
// Good: testable with a fixed date
function getDueLabel(dueDate: Date, now: Date = new Date()): string

// Bad: non-deterministic
function getDueLabel(dueDate: Date): string {
  const now = new Date();  // can't control this in tests
```

### What to Mock, What Not to Mock

- **Mock external services** (databases, APIs, file systems) — these are slow, stateful, and not what you're testing
- **Don't mock your own abstractions** — if you wrote the function, call the real one. Mocking your own code means you're testing that the mock works, not that the code works
- **Don't mock what you can extract** — if you need to mock a calculation to test a component, that calculation should be a separate function that you test directly instead

---

## Testing Against Specifications

When formal data models and contracts exist (see [Data Integrity Standards](./data-integrity.md)), tests should use those schemas as both input constructors and output validators. This grounds tests in a verified specification rather than developer assumptions about what the data looks like.

### Why This Matters

Without schemas, test data is invented by the developer writing the test. If their mental model of the data is wrong, the test passes but the code breaks on real data. Schema-validated test data eliminates this failure mode: `Schema.parse(data)` in a test guarantees the test data matches the spec.

### The Schema is the Arbiter

When schemas and code disagree, the schema wins — because it was verified against real data (see "Schema verification against real data" in data-integrity.md). If a function expects a field that the schema says doesn't exist, that's a bug in the function, not a missing test case.

### Pattern: Schema as Input Constructor

Use the schema to build test inputs. If the data doesn't parse, the test data is wrong — not the schema.

**Python (Pydantic):**
```python
from models.customer import CustomerSummary

def test_commission_calculation():
    # Schema validates the test data matches the real shape
    customer = CustomerSummary(
        customer_code="CUST001",
        name="Acme Ltd",
        gp_amount=1500.00,
        account_status="active",
    )
    result = calculate_commission(customer)
    assert result > 0
```

**TypeScript (Zod):**
```typescript
import { CustomerSummarySchema } from "@/models/customer";

test("commission calculation", () => {
  // Schema.parse() guarantees test data matches the spec
  const customer = CustomerSummarySchema.parse({
    customerCode: "CUST001",
    name: "Acme Ltd",
    gpAmount: 1500.0,
    accountStatus: "active",
  });
  const result = calculateCommission(customer);
  expect(result).toBeGreaterThan(0);
});
```

### Pattern: Schema as Output Validator

Use the schema to validate function output. If the output doesn't parse, the function is producing data that doesn't match the contract.

**Python (Pydantic):**
```python
def test_build_customer_summary():
    raw_row = {"customer_code": "CUST001", "name": "Acme Ltd", ...}
    result = build_customer_summary(raw_row)

    # If this raises ValidationError, the function output
    # doesn't match the contract
    CustomerSummary.model_validate(result)
```

**TypeScript (Zod):**
```typescript
test("build customer summary", () => {
  const rawRow = { customerCode: "CUST001", name: "Acme Ltd", ... };
  const result = buildCustomerSummary(rawRow);

  // If this throws, the function output doesn't match the contract
  CustomerSummarySchema.parse(result);
});
```

---

## Test Types

Tests serve different purposes. Understanding what each type proves — and what it doesn't — determines which types you need.

### Unit Tests — "Does this function do the right thing?"

Test one function in isolation. Give it known inputs, check the outputs.

**What gets mocked:** External services (databases, APIs, file systems). You're testing your logic, not whether AWS is up.

**What they prove:** Your code is correct when given correct inputs.

**What they don't prove:** That the inputs your code receives in production are actually correct. That the pieces work when wired together.

### Boundary / Contract Tests — "Does data at the edge match expectations?"

Test that data crossing a system boundary matches the schema. These use the Zod/Pydantic schemas from [Data Integrity Standards](./data-integrity.md) as both input validators and output validators.

**What gets mocked:** Usually nothing — these test the schema itself, or test that real data from a database/API matches the schema.

**What they prove:** The contract between systems is honoured. The schemas match reality.

**What they don't prove:** That your business logic is correct (that's unit tests).

**Examples:**
- Schema rejects a save-progress request with missing courseId
- Schema accepts a valid DynamoDB course record
- API response from a third-party service matches the expected schema

This is a distinct test type, not a unit test. Unit tests verify your code does the right thing with correct data. Boundary tests verify the data itself is correct. See [Data Integrity Standards — Validation Boundaries](./data-integrity.md#validation-boundaries) for where boundaries exist.

### Integration Tests — "Do the pieces work together?"

Test multiple components connected together, with minimal or no mocking.

**What gets mocked:** As little as possible. Ideally hits a real (test) database, real file system, etc.

**What they prove:** The wiring is correct. Components that work individually also work when connected.

**What they don't prove:** That the full user flow works end-to-end through the UI.

### End-to-End Tests — "Does the full flow work as a user would experience it?"

Test complete user journeys from the UI or API surface through to the database and back.

**What gets mocked:** Nothing. Real browser, real API, real database (test environment).

**What they prove:** The system works as a whole. The user experience is correct.

**What they don't prove:** Individual function correctness (too coarse-grained for that).

### Edge Case Tests — "What happens when things go wrong?"

Not a separate test type — these are unit, boundary, or integration tests that specifically target error paths and boundary conditions:
- What if the input is empty / null / malformed?
- What if the database returns no results?
- What if the file is too large?
- What if the external service times out?

The Test Case Templates section below provides checklists for common edge case patterns.

### Summary

| Type | What it proves | What gets mocked | When required |
|------|---------------|-----------------|---------------|
| **Unit** | Function logic is correct | External services | All tiers |
| **Boundary / Contract** | Data at edges matches schemas | Usually nothing | Production (wherever schemas exist) |
| **Integration** | Components work together | Minimal | Internal, Production |
| **End-to-end** | Full user flows work | Nothing | Production (critical paths) |

---

## Build Order — When to Write What

The order you build things affects what you can test. This sequence ensures each layer is testable before the next depends on it.

1. **Define data models as runtime schemas** (Zod, Pydantic) — not plain interfaces. The schema is the single source of truth: it gives you the compile-time type (`z.infer<typeof CourseSchema>`) AND runtime validation (`.parse()`) from one definition. Starting with plain interfaces creates a retrofit tax later. Everything else depends on knowing what the data looks like.
2. **Write pure logic + unit tests** — functions with no side effects (parsers, validators, transformers, calculators). Use schemas to construct test inputs (`Schema.parse(testData)` guarantees your test data matches the spec). Easiest to test, most valuable to get right.
3. **Write the I/O layer + unit tests with mocks** — repositories, API clients, file handlers. Schemas validate what comes back from the database/API. Mock external services to test your code sends the right commands.
4. **Wire it together + integration tests** — orchestrators, handlers, routes. Test the full flow with minimal mocking.
5. **Verify boundary coverage** — not "add" boundary validation (it's been there since step 1), but verify every entry/exit point actually calls `.parse()`. This is a review checkpoint, not a retrofit. Check: does every API endpoint validate its input? Does every database read validate the response shape? Are there boundaries where data crosses unchecked?

**For prototypes being upgraded to production:** If the codebase started with plain interfaces instead of schemas (a common shortcut), step 5 becomes a retrofit — migrating interfaces to schemas and adding `.parse()` calls at boundaries. This is more expensive than starting with schemas, but it's a known path. See [Data Integrity Standards — Reverse-Engineering Data Specifications](./data-integrity.md#reverse-engineering-data-specifications) for the upgrade process.

This sequence is a guide, not a rigid rule. The key insight is: **schemas from the start, not bolted on later.** See [Data Integrity Standards — The Three Layers of Data Safety](./data-integrity.md#the-three-layers-of-data-safety) for why runtime validation matters alongside compile-time types.

---

## Test Case Templates

Reference these when writing plans for common patterns.

### Validation Function

```
- Valid input → returns true/success
- Empty input → appropriate response
- Null/undefined → appropriate response
- Type mismatch → appropriate response
- Boundary: minimum valid value
- Boundary: maximum valid value
- Just outside boundaries (off-by-one)
```

### CRUD Operation

```
- Create: valid data → success
- Create: duplicate → appropriate error
- Create: missing required fields → validation error
- Read: exists → returns data
- Read: not found → appropriate error
- Update: exists → success
- Update: not found → appropriate error
- Update: partial data → handles correctly
- Delete: exists → success
- Delete: not found → appropriate error
- Delete: cascading effects (if applicable)
```

### State Machine

```
- Each valid state transition
- Invalid state transitions → rejected
- Initial state correct
- Terminal states handled
- Idempotent transitions (if applicable)
```

### API Endpoint

```
- Success case → correct status code and body
- Authentication required → 401 without token
- Authorization required → 403 without permission
- Validation error → 400 with helpful message
- Not found → 404
- Server error → 500 (and logged)
- Rate limiting (if applicable)
```

---

## Mutation Testing

**Tool:** `mutmut` (Python), `Stryker` (JavaScript/TypeScript)

**When to run:** Production tier, on changed files before merge.

**Process:**
1. Run mutation testing on modified code
2. Review surviving mutants
3. Add tests to kill surviving mutants, or document why they're acceptable

**Acceptable survivors:**
- Equivalent mutants (change doesn't affect behavior)
- Logging/cosmetic changes
- Documented exceptions

---

## Anti-Patterns

| Don't | Why |
|-------|-----|
| Test implementation details | Tests break on refactor |
| Mock your own code | Tests pass but integration fails |
| Skip edge cases "for speed" | Bugs ship to production |
| Write tests after the fact | Loses TDD benefits, tests often miss cases |
| Rely on coverage % alone | 100% coverage with useless assertions is worthless |

---

## Open Questions

- Specific coverage thresholds per tier? (Currently relying on TDD + mutation testing rather than % targets)
- E2E test framework preferences?
