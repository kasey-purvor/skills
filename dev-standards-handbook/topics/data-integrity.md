# Data Integrity

## The Problem

Every application has boundaries — places where data enters your system from somewhere you don't control. A user submits a form. Another service calls your API. You read a row from a database. You load an environment variable.

At each boundary, you have a choice: trust the data or verify it.

If you trust it:

```typescript
app.post('/users', (req, res) => {
  const user = req.body;  // Could be ANYTHING
  db.insert('users', {
    name: user.name,       // What if this is undefined?
    email: user.email,     // What if this is the number 42?
    age: user.age,         // What if this is "DROP TABLE users"?
  });
});
```

This code works perfectly when the data is what you expect. It explodes in unpredictable ways when it isn't — maybe it inserts `undefined` into your database, maybe it crashes 3 function calls deep with a cryptic error, maybe it stores garbage data that breaks something else next week.

**The professional engineering principle: data from outside your system is guilty until proven innocent.** Verify it the moment it crosses the boundary. After that, every function inside your system can trust it completely.

---

## Manual Validation vs Schema Validation

The naive approach is manual validation:

```typescript
app.post('/users', (req, res) => {
  if (!req.body.name || typeof req.body.name !== 'string') {
    return res.status(400).json({ error: 'name must be a string' });
  }
  if (!req.body.email || typeof req.body.email !== 'string') {
    return res.status(400).json({ error: 'email must be a string' });
  }
  if (!req.body.email.includes('@')) {
    return res.status(400).json({ error: 'email must be valid' });
  }
  if (req.body.age !== undefined && typeof req.body.age !== 'number') {
    return res.status(400).json({ error: 'age must be a number' });
  }
  // ... finally, the actual logic
});
```

This works but has serious problems:

- **Tedious and error-prone.** Same kind of checks for every endpoint. Miss one and you have a bug.
- **Validation and business logic are tangled.** The handler is 80% validation, 20% actual work.
- **No single source of truth.** "What does a valid user look like?" is scattered across every endpoint that accepts user data.
- **TypeScript still doesn't know the type.** After all those checks, `req.body` is still `any`. No autocomplete, no compile-time safety.

Schema validation libraries solve all of these.

---

## Zod (TypeScript)

Zod lets you define a schema — a description of what valid data looks like — and then validate data against it at runtime.

```typescript
import { z } from 'zod';

// Define the schema ONCE
const UserSchema = z.object({
  name: z.string().min(1),                        // non-empty string
  email: z.string().email(),                       // string that looks like an email
  age: z.number().int().positive().optional(),     // optional positive integer
});

// Use it in your handler
app.post('/users', (req, res) => {
  const result = UserSchema.safeParse(req.body);

  if (!result.success) {
    // Zod gives you detailed, structured error messages automatically
    return res.status(400).json({ errors: result.error.issues });
  }

  // result.data is fully typed: { name: string, email: string, age?: number }
  // TypeScript KNOWS this. You get autocomplete. You get compile-time checks.
  const user = result.data;
  db.insert('users', user);
});
```

What Zod gives you:

1. **Single source of truth** — the schema defines "what is a valid user" in one place, used everywhere
2. **Runtime validation** — it actually checks the data when code runs (TypeScript types alone don't)
3. **Type inference** — after validation, TypeScript knows the exact type
4. **Composability** — schemas extend, combine, and transform
5. **Detailed errors** — structured list of exactly what's wrong

### The Critical Insight: TypeScript Types vs Runtime Validation

TypeScript types only exist at compile time. They're erased when your code runs:

```typescript
interface User {
  name: string;
  email: string;
}

// This compiles fine, but at runtime, req.body could be ANYTHING
const user: User = req.body;  // TypeScript trusts you. It shouldn't.
```

TypeScript is saying "I'll treat this as a User" — it's not checking that it actually IS a User. The type is a promise you're making to the compiler. If the data comes from outside your system (HTTP request, database query, JSON file), that promise might be a lie.

Zod bridges this gap. It validates at runtime AND gives you the TypeScript type. The validation is the proof that the type is correct.

### .parse() vs .safeParse()

```typescript
// .parse() — throws ZodError if validation fails
const user = UserSchema.parse(data);  // throws on failure

// .safeParse() — returns a result object, never throws
const result = UserSchema.safeParse(data);
if (result.success) {
  result.data;  // the validated value
} else {
  result.error; // the ZodError with details
}
```

Use `.safeParse()` at API boundaries where invalid data is expected (user input). Use `.parse()` in internal code where invalid data means a programming error.

### Alternatives to Zod

- **Joi** — older, established, but doesn't infer TypeScript types (you define the type separately from the schema, so they can drift apart)
- **Yup** — similar to Joi, popular in React form validation
- **ArkType** — newer, claims better performance
- **Valibot** — smaller bundle size, similar API

Zod won the ecosystem because it solved the type inference problem cleanly. Most new TypeScript projects use it. **Our default choice is Zod** — only deviate if there's a specific reason (e.g., joining a project that already uses Joi).

---

## Pydantic (Python)

Pydantic uses Python's type hints as its schema language. You write normal Python classes with type annotations, and Pydantic makes them validated at runtime.

```python
from pydantic import BaseModel, EmailStr, ValidationError

class User(BaseModel):
    name: str
    email: EmailStr          # validates email format
    age: int | None = None   # optional, must be int if present

# Validate incoming data — validates on construction
try:
    user = User(**request_body)
except ValidationError as e:
    return {"errors": e.errors()}, 400

# user.name, user.email, user.age are all validated and typed
db.insert("users", user.model_dump())
```

### Key Differences from Zod

| Aspect | Zod (TypeScript) | Pydantic (Python) |
|--------|------------------|-------------------|
| Schema definition | Values: `z.string()`, `z.object({...})` | Classes: `class User(BaseModel)` |
| Validation trigger | Explicit: call `.parse()` or `.safeParse()` | On construction: `User(**data)` |
| Type inference | Inferred from schema: `z.infer<typeof Schema>` | The class IS the type |
| Forgetting to validate | Possible (if you skip `.parse()`) | Impossible (construction IS validation) |

Pydantic's "validate on construction" means you can't create an invalid instance. If you have a `User` object, it was validated. This is a strong safety property.

### Pydantic Strict Mode

By default, Pydantic coerces types — `"42"` becomes `42` for an `int` field. Strict mode rejects this:

```python
class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)
    age: int  # "42" is rejected — must be actual int

class CoercingUser(BaseModel):
    age: int  # "42" becomes 42 automatically
```

**When to use which:**
- **Strict:** API boundaries where you control the client (your own frontend). The client should send correct types.
- **Coercing:** Environment variables (always strings), form data (always strings), third-party APIs with inconsistent types.

**Our default: Pydantic** for all Python schema validation. Only deviate if there's a specific reason.

---

## The Three-Layer Model

Data correctness is enforced by three layers, each catching failures the others miss. All three are needed in production systems.

### Layer 1: Type System (compile-time)

TypeScript interfaces, Python type annotations, strict compiler settings. Checked when you write code and when the compiler/type-checker runs. Catches wrong argument types, missing fields, type mismatches.

**What it can't catch:** Anything that arrives at runtime from outside your code. API requests, database responses, user uploads, webhook payloads — the type system is erased before the code runs, so it doesn't exist when real data flows through.

### Layer 2: Runtime Validation (schemas)

Zod schemas (TypeScript), Pydantic models (Python). Code that runs and inspects actual data at runtime. Applied at **boundaries** — the moment data enters or leaves your system.

**What a boundary is:** The line between code you control and data you don't:
- An API request arrives from a client → validate the JSON body
- A database returns a record → validate it matches your schema
- A third-party webhook sends data → validate the payload
- A file is uploaded → validate its structure
- An environment variable is read → validate its format and type

### Layer 3: Storage Constraints (database-level)

Rules enforced by the database itself, regardless of what code sent the data. In relational databases: `NOT NULL`, `FOREIGN KEY`, `CHECK`, `UNIQUE` constraints. These catch everything that bypasses your application — migration scripts, manual console edits, bugs that somehow get past validation.

**NoSQL databases (DynamoDB, MongoDB, etc.):** Enforce very little — typically just key schema. No CHECK constraints, no foreign keys, no UNIQUE on non-key attributes. This means Layers 1 and 2 carry significantly more weight.

### Why All Three Layers

| Scenario | Layer 1 (Types) | Layer 2 (Schemas) | Layer 3 (DB) |
|----------|:---:|:---:|:---:|
| Developer writes wrong type in code | Catches | - | - |
| Client sends malformed JSON | - | Catches | - |
| Migration script writes bad data directly | - | - | Catches |
| Field renamed in code but not in DB | - | Catches | - |
| Two services write conflicting data | - | - | Catches |
| Code deploys with a bug that skips validation | - | - | Catches |

No single layer covers all scenarios. The gaps in one are filled by the others.

### Where ORMs Fit in the Three Layers

When using a relational database with an ORM (Drizzle, SQLAlchemy, Prisma), you end up with **two schema definitions** for the same entity — the ORM schema and the validation schema (Zod/Pydantic). This isn't redundancy. They serve different layers and catch different problems. On TypeScript, **Drizzle is the go-to ORM** in this handbook — schema-in-TypeScript, compile-time-typed queries, and native in-schema Postgres RLS (see [Schema Evolution](./schema-evolution.md) and [Authentication & Authorization](./authentication-authorization.md)).

**The ORM schema** (e.g., Drizzle's `pgTable`) defines what the database table looks like — columns, types, constraints. It serves two purposes: generating SQL migrations (Layer 3), and making queries type-safe at compile time (Layer 1).

**The validation schema** (Zod/Pydantic) defines what the application expects data to look like at runtime. It validates data crossing boundaries (Layer 2) — API requests, database results, external payloads.

```typescript
// Drizzle schema — defines the DATABASE table (Layers 1 + 3)
const courses = pgTable('courses', {
  courseId: uuid('course_id').primaryKey(),
  title: varchar('title').notNull(),
  items: jsonb('items').notNull(),           // opaque JSON column to the DB
  createdAt: timestamp('created_at', { withTimezone: true }).notNull(),
});

// Zod schema — defines the APPLICATION contract (Layer 2)
const CourseSchema = z.object({
  courseId: z.string().uuid(),
  title: z.string().min(1),
  items: z.array(CourseItemSchema),           // validated nested structure
  createdAt: z.string().datetime(),           // ISO string, not a Date
});
```

Notice the differences: Drizzle says `items` is `jsonb` — the database stores it but doesn't inspect its contents. Zod says `items` is an array of `CourseItem` objects with specific fields — the application validates the structure inside the JSON. Drizzle says `createdAt` is a Postgres `timestamp`. Zod says it's an ISO 8601 string — the repository layer handles the conversion.

**The repository layer is the bridge** — it sits between the ORM queries and the validation schemas. It queries via the ORM (type-safe SQL), then parses results through the Zod schema before returning to the rest of the application. Both checks happen, each catching what the other can't.

**Why not just one schema?** Some ORMs (Prisma) try to be the single source of truth for both database structure and application types. This works until your database representation and application representation genuinely differ — a `jsonb` column containing a validated nested structure, a timestamp stored as a Date but serialised as a string, a composite key split into separate application fields. Two schemas let each side describe what it actually cares about without forcing the other to compromise.

**JSON databases (MongoDB, DynamoDB) don't have this problem.** There's no second language to bridge — queries are JavaScript objects, results are JavaScript objects. The ORM layer exists specifically because SQL databases speak a different language than your application code. Zod alone handles validation for JSON databases; the ORM handles the SQL translation that JSON databases don't need.

---

## Validation Boundaries

Validate data when it crosses a trust boundary:

| Boundary | Example | Validation |
|----------|---------|------------|
| **External API → App** | Third-party response | Parse through typed schema |
| **User input → App** | Form submission, API request body | Validate with schema |
| **File → App** | CSV/JSON import | Validate each record |
| **App → Database** | Insert/update | Schema ensures correct shape before write |
| **Database → App** | Query result | Parse through schema (proves DB returns what you expect) |
| **Service → Service** | RPC response, webhook | Parse through boundary contract |
| **Environment → App** | Config / env vars | Parse through config schema (see [Configuration](./configuration.md)) |

**The principle:** Full validation at boundaries. Trust internally. The boundary is where untrusted becomes trusted.

---

## Established Patterns

### Nested Composition

Build complex structures from simple building blocks:

**TypeScript (Zod):**
```typescript
const AddressSchema = z.object({
  street: z.string(),
  city: z.string(),
  country: z.string(),
});

const UserSchema = z.object({
  name: z.string(),
  address: AddressSchema,  // Nested schema
});
type User = z.infer<typeof UserSchema>;
```

**Python (Pydantic):**
```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class User(BaseModel):
    name: str
    address: Address  # Nested model
```

### Literal Types for Constrained Values

Don't use loose strings when only specific values are valid:

**TypeScript:**
```typescript
const OrderSchema = z.object({
  status: z.enum(["pending", "confirmed", "shipped", "delivered"]),
  priority: z.enum(["low", "medium", "high"]),
});
```

**Python:**
```python
from typing import Literal

class Order(BaseModel):
    status: Literal["pending", "confirmed", "shipped", "delivered"]
    priority: Literal["low", "medium", "high"]
```

### Discriminated Unions

Handle data that can be one of several types, distinguished by a field:

**TypeScript:**
```typescript
const EventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("click"), x: z.number(), y: z.number() }),
  z.object({ type: z.literal("keypress"), key: z.string() }),
  z.object({ type: z.literal("scroll"), delta: z.number() }),
]);
// TypeScript knows: if event.type === "click", then event.x and event.y exist
```

**Python:**
```python
from pydantic import BaseModel
from typing import Literal, Union

class ClickEvent(BaseModel):
    type: Literal["click"]
    x: int
    y: int

class KeypressEvent(BaseModel):
    type: Literal["keypress"]
    key: str

class ScrollEvent(BaseModel):
    type: Literal["scroll"]
    delta: int

Event = Union[ClickEvent, KeypressEvent, ScrollEvent]
# Pydantic uses the "type" field to decide which model to validate against
```

### Factory Methods and Defaults

Generate IDs and timestamps automatically:

**TypeScript:**
```typescript
const RecordSchema = z.object({
  id: z.string().default(() => crypto.randomUUID()),
  createdAt: z.string().datetime().default(() => new Date().toISOString()),
  data: z.unknown(),
});
```

**Python:**
```python
from datetime import datetime, timezone
from secrets import token_hex

class Record(BaseModel):
    id: str = Field(default_factory=lambda: f"rec_{token_hex(8)}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Any
```

---

## Database-Level Integrity

Application-layer validation (Zod, Pydantic) protects the happy path. Database constraints protect everything else — direct queries, migration scripts, ETL pipelines, and bugs in application code all bypass your validation schemas.

### Enforce at Both Layers

| Constraint | Application Layer | Database Layer |
|------------|-------------------|----------------|
| **Required fields** | Schema validation | `NOT NULL` |
| **Valid values** | Enum/literal types | `CHECK` constraints |
| **Relationships** | Type references | `FOREIGN KEY` constraints |
| **Uniqueness** | Pre-check before insert | `UNIQUE` constraints |
| **Data format** | String parsing, regex | `CHECK` with regex or domain types |

Application validation gives good error messages. Database constraints prevent bad data. Both are needed.

### Adding Constraints to Existing Tables

When adding constraints to tables with existing data, use `NOT VALID` to avoid scanning all rows:

```sql
ALTER TABLE orders ADD CONSTRAINT fk_customer
  FOREIGN KEY (customer_code) REFERENCES customers(customer_code)
  NOT VALID;

-- Validate later after confirming data quality:
ALTER TABLE orders VALIDATE CONSTRAINT fk_customer;
```

### Normalise at Ingest

String values that serve as categories or statuses must be normalised on entry — lowercase at insert, then add a CHECK constraint:

```sql
ALTER TABLE users ADD CONSTRAINT chk_role_lowercase
  CHECK (role = LOWER(role));
```

---

## Database Transactions

A transaction groups multiple database operations so they either ALL succeed or ALL fail. Without transactions, a multi-step operation can leave your database in a half-finished state.

### The Classic Example

Transferring money between accounts requires two steps:

```sql
-- Without a transaction: if step 2 fails, the money vanishes
UPDATE accounts SET balance = balance - 100 WHERE id = 1;  -- debit
-- 💥 crash here
UPDATE accounts SET balance = balance + 100 WHERE id = 2;  -- credit never happens
```

```sql
-- With a transaction: both succeed or both are rolled back
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
-- If anything fails between BEGIN and COMMIT, all changes are undone
```

### How It Works

- `BEGIN` — starts a transaction. All subsequent operations are provisional.
- `COMMIT` — makes all provisional operations permanent.
- `ROLLBACK` — undoes all provisional operations (as if they never happened).

If your code throws an error between `BEGIN` and `COMMIT`, the database rolls back automatically (when the connection closes without committing).

### In Application Code

**TypeScript (using a pool/client):**
```typescript
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
  await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId]);
  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK');
  throw err;  // re-throw so the error is handled by your error hierarchy
} finally {
  client.release();  // return connection to pool
}
```

**Python (SQLAlchemy async session):**
```python
async with async_session() as session:
    async with session.begin():  # auto-commits on success, auto-rolls-back on exception
        await session.execute(
            update(accounts).where(accounts.c.id == from_id).values(balance=accounts.c.balance - amount)
        )
        await session.execute(
            update(accounts).where(accounts.c.id == to_id).values(balance=accounts.c.balance + amount)
        )
    # If an exception is raised inside the `begin()` block, the transaction is rolled back
```

### When to Use Transactions

Any time you have multiple database operations that must succeed or fail together:
- Transferring between accounts (debit + credit)
- Creating an order (insert order + insert order items + decrement inventory)
- User signup (create user + create profile + send welcome email record)

Single operations (one INSERT, one UPDATE) are already atomic — they don't need explicit transactions.

### Connection to Error Handling

Transactions connect directly to your error hierarchy (see [Error Handling](./error-handling.md)): if step 3 of 5 fails, the transaction rolls back steps 1-2 automatically. Your error handler then classifies the failure (was it a validation error? a constraint violation? a timeout?) and responds appropriately.

---

## Strict Type Checking as Data Integrity

Strict compiler settings are a data integrity tool:

- **TypeScript:** `strict: true` in tsconfig (especially `strictNullChecks`). Without it, `null` and `undefined` flow silently through the entire codebase — the single biggest category of runtime crashes.
- **Python:** mypy with strict settings + type annotations on all function signatures.

Prefer enabling strict mode from day one. Retrofitting it onto an existing codebase is possible but painful — the volume of newly-surfaced errors scales with the amount of loose code already written, and fixes often cascade through call chains. The earlier you turn it on, the smaller the backlog.

---

## Testing Data Correctness

Zod and Pydantic validate data at runtime — but they only help if your schemas are correct and actually wired in. There are four distinct testing concerns for data:

1. **Schema-to-reality alignment** — Does your schema match what the database/API actually sends? (contract tests)
2. **Validation wiring** — Is the validation actually being called in your route handlers? (integration tests)
3. **Transformation correctness** — Data enters valid but gets transformed at multiple stages (DB → API → hook → component). Each transformation can mangle data. (unit/integration tests)
4. **Complex schema logic** — Custom refinements, discriminated unions, conditional validation have logic that can be wrong. (unit tests)

**Don't test that Zod or Pydantic work** — `z.string().parse("hello")` is the library's job. **Do test** that your schemas match reality, that validation is wired in, that transformations produce correct output, and that custom schema logic behaves as expected.

See [Testing](./testing.md) for full examples, code patterns, and the testing checklist for data integrity concerns.

---

## Anti-Patterns

| Don't | Do Instead | Why |
|-------|-----------|-----|
| Pass raw dicts/objects between functions | Define schemas for data structures | Raw objects have no contract — any function can put anything in them |
| Use `any` or `unknown` without parsing | Parse through a schema, then use the typed result | `any` turns off all type safety — it's an escape hatch, not a strategy |
| Use loose strings for constrained values | Use `z.enum()` / `Literal` types | Loose strings accept typos: `"actve"` instead of `"active"` |
| Scatter validation throughout code | Validate once at the boundary, trust internally | Redundant validation clutters code and creates maintenance burden |
| Skip validation for "trusted" internal data | Trust the model, validate at entry | Internal data was external data once — the boundary is where trust is established |
| Store unvalidated external data | Always parse through a schema first | Garbage in, garbage out — but worse, garbage stored permanently |
| Use TypeScript `as` type assertions | Use `.parse()` — assertions skip validation | `as User` tells the compiler to trust you; `.parse()` actually checks |
| Validate at the database layer only | Validate at the application boundary too | DB errors are cryptic ("constraint violation on column X") vs schema errors ("email must be valid") |

---

## Deciding for Your Project

When starting a new project, determine:

1. What external data sources exist? (APIs, files, user input, webhooks)
2. Where are the trust boundaries? (What's "inside" vs "outside" your system?)
3. What database are you using? (Relational with constraints, or NoSQL where app validation carries more weight?)
4. What entities does the system work with? (Users, orders, events — each needs a schema)
5. Strict or coercing mode? (Depends on data sources — see the strict mode section above)

---

## Related Topics

- **When validation fails** — see [Error Handling](./error-handling.md) for how to structure error responses and classify validation errors
- **Validating configuration** — see [Configuration](./configuration.md) for treating env vars and settings as validated data
- **When schemas change over time** — see [Schema Evolution](./schema-evolution.md) for database migrations and the expand-and-contract pattern
- **Validation as security** — see [Security](./security.md) for the OWASP perspective on input validation as a defence against injection attacks
- **Testing data at every stage** — see [Testing](./testing.md) for contract tests, integration tests, and transformation tests that verify data correctness beyond what schemas catch
