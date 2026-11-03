# Data Integrity

> **Calibrate to your context.** Validating data where it crosses a trust boundary is
> worth it almost anywhere data arrives from outside, and declaring `NOT NULL`, foreign
> keys and `UNIQUE` when a table is created costs nothing at any size. What scales with
> how much you'd regret bad data is the rest: a system-of-record earns broad `CHECK`
> coverage and schema-conformance tests; a scratch tool earns a boundary parse, the free
> constraints and little else. Reference material, not a checklist.

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

## Zod (TypeScript)

A schema library replaces hand-written `typeof` checks with one declaration that validates at runtime and gives the compiler the type. **Zod is the default** on TypeScript.

```typescript
// Zod 4
import { z } from 'zod';

// Define the schema ONCE
const UserSchema = z.object({
  name: z.string().min(1),                        // non-empty string
  email: z.email(),                               // string that looks like an email
  age: z.number().int().positive().optional(),     // optional positive integer
});

// Use it in your handler
app.post('/users', (req, res) => {
  const result = UserSchema.safeParse(req.body);

  if (!result.success) {
    // Map Zod's issues to the field-level `errors` array from Error Handling;
    // returning raw `issues` would make Zod's internal format your API contract
    const errors = result.error.issues.map((i) => ({ field: i.path.join('.'), message: i.message }));
    return res.status(400).json({
      type: 'about:blank', code: 'VALIDATION_ERROR', title: 'Invalid request data', status: 400, errors,
    });
  }

  // result.data is fully typed: { name: string, email: string, age?: number }
  // TypeScript KNOWS this. You get autocomplete. You get compile-time checks.
  const user = result.data;
  db.insert('users', user);
});
```

### Parse, Don't Assert

TypeScript types are erased at runtime. `const user = req.body as User` (or an annotation on an `any`) compiles, but it checks nothing: it is a promise to the compiler that outside data cannot keep. Parsing is the proof that the type is true, so data from outside your system reaches typed code only through `.parse()` or `.safeParse()`.

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

---

## Pydantic (Python)

Pydantic uses Python's type hints as its schema language. You write normal Python classes with type annotations, and Pydantic makes them validated at runtime.

```python
# Pydantic 2 — EmailStr needs the extra: pip install "pydantic[email]"
from pydantic import BaseModel, EmailStr, ValidationError

class User(BaseModel):
    name: str
    email: EmailStr          # validates email format
    age: int | None = None   # optional, must be int if present

# Validate incoming data — model_validate() runs the same validation as construction
try:
    user = User.model_validate(request_body)
except ValidationError as e:
    # Map to the field-level `errors` array from Error Handling. Raw e.errors() would make
    # Pydantic's format your contract and echo submitted values (passwords too) back
    errors = [
        {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
        for err in e.errors(include_input=False, include_url=False)
    ]
    return {"type": "about:blank", "code": "VALIDATION_ERROR",
            "title": "Invalid request data", "status": 400, "errors": errors}, 400

# user.name, user.email, user.age are all validated and typed
db.insert("users", user.model_dump())
```

### Key Differences from Zod

| Aspect                 | Zod (TypeScript)                               | Pydantic (Python)                            |
| ---------------------- | ---------------------------------------------- | -------------------------------------------- |
| Schema definition      | Values: `z.string()`, `z.object({...})`        | Classes: `class User(BaseModel)`             |
| Validation trigger     | Explicit: call `.parse()` or `.safeParse()`    | On construction: `User.model_validate(data)` |
| Type inference         | Inferred from schema: `z.infer<typeof Schema>` | The class IS the type                        |
| Forgetting to validate | Possible (if you skip `.parse()`)              | Unlikely (construction validates)            |

Pydantic's "validate on construction" means a `User` built the normal way was validated — a strong safety property, with two gaps. Assignment isn't validated by default (`user.age = "abc"` succeeds silently), and `User.model_construct()` skips validation entirely. Where that matters, set `ConfigDict(validate_assignment=True)` or make the model immutable with `ConfigDict(frozen=True)`.

### Pydantic Strict Mode

By default, Pydantic coerces types — `"42"` becomes `42` for an `int` field. Strict mode rejects that, and model-wide strict is a trap. In Python mode it also rejects the ISO strings a JSON body carries for `datetime`, `UUID` and `Decimal` fields, and FastAPI validates request bodies in Python mode after decoding the JSON. Make strictness field-level instead:

```python
# Pydantic 2.14, FastAPI 0.162 (both verified)
from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Strict

class Order(BaseModel):
    quantity: Annotated[int, Strict()]  # "42" rejected: must be a real int
    placed_at: datetime                 # ISO string still parsed
```

Model-wide `ConfigDict(strict=True)` is safe only where you call `model_validate_json` on the raw JSON yourself, because JSON mode still accepts strings for those types. Keep coercion for environment variables and form data, which are always strings.

**Pydantic is our default** for Python schema validation.

---

## The Three-Layer Model

Data correctness is enforced by three layers, each catching failures the others miss. Keep all three at any size: the basic database constraints cost nothing when a table is created, and what scales down is how much `CHECK` coverage and testing you add.

### Layer 1: Type System (compile-time)

TypeScript interfaces, Python type annotations, strict compiler settings. Checked when you write code and when the compiler/type-checker runs. Catches wrong argument types, missing fields, type mismatches.

**What it can't catch:** Anything that arrives at runtime from outside your code. API requests, database responses, user uploads, webhook payloads — the type system is erased before the code runs, so it doesn't exist when real data flows through.

### Layer 2: Runtime Validation (schemas)

Zod schemas (TypeScript), Pydantic models (Python). Code that runs and inspects actual data at runtime. Applied at **boundaries** — the moment data enters or leaves your system.

**What a boundary is:** The line between code you control and data you don't:

- An API request arrives from a client → validate the JSON body
- A database returns a record whose shape it cannot vouch for (a `jsonb` document, a table other writers share) → validate it
- A third-party webhook sends data → validate the payload
- A file is uploaded → validate its structure
- An environment variable is read → validate its format and type

### Layer 3: Storage Constraints (database-level)

Rules enforced by the database itself, regardless of what code sent the data. In relational databases: `NOT NULL`, `FOREIGN KEY`, `CHECK`, `UNIQUE` constraints. These catch everything that bypasses your application — migration scripts, manual console edits, bugs that somehow get past validation.

**NoSQL databases (DynamoDB, MongoDB, etc.):** Enforce less, and it varies. DynamoDB enforces little beyond the key schema — no CHECK constraints, no foreign keys, no UNIQUE on non-key attributes. MongoDB has unique indexes on any field and `$jsonSchema` collection validators, but no foreign keys. Either way, Layers 1 and 2 carry significantly more weight.

### Why All Three Layers

| Scenario                                      | Layer 1 (Types) | Layer 2 (Schemas) | Layer 3 (DB) |
| --------------------------------------------- | :-------------: | :---------------: | :----------: |
| Developer writes wrong type in code           | Catches         | -                 | -            |
| Client sends malformed JSON                   | -               | Catches           | -            |
| Migration script writes bad data directly     | -               | -                 | Catches      |
| Field renamed in code but not in DB           | -               | Catches           | -            |
| Two services write conflicting data           | -               | -                 | Catches      |
| Code deploys with a bug that skips validation | -               | -                 | Catches      |

No single layer covers all scenarios. The gaps in one are filled by the others.

### Where ORMs Fit in the Three Layers

When using a relational database with an ORM (Drizzle, SQLAlchemy, Prisma), you end up with **two schema definitions** for the same entity — the ORM schema and the validation schema (Zod/Pydantic). This isn't redundancy. They serve different layers and catch different problems.

**The ORM schema** (e.g., Drizzle's `pgTable`) defines what the database table looks like — columns, types, constraints. It serves two purposes: generating SQL migrations (Layer 3), and making queries type-safe at compile time (Layer 1).

**The validation schema** (Zod/Pydantic) defines what the application expects data to look like at runtime. It validates data crossing boundaries (Layer 2) — API requests, database results, external payloads.

```typescript
// Zod 4, drizzle-orm 0.45
// Drizzle schema — defines the DATABASE table (Layers 1 + 3)
const courses = pgTable('courses', {
  courseId: uuid('course_id').primaryKey(),
  title: varchar('title').notNull(),
  items: jsonb('items').notNull(),           // opaque JSON column to the DB
  createdAt: timestamp('created_at', { withTimezone: true }).notNull(),
});

// Zod schema — defines the APPLICATION contract (Layer 2)
const CourseSchema = z.object({
  courseId: z.uuid(),
  title: z.string().min(1),
  items: z.array(CourseItemSchema),           // validated nested structure
  createdAt: z.iso.datetime(),                // ISO string with Z; an input schema needs { offset: true }
});
```

Notice the differences: Drizzle says `items` is `jsonb` — the database stores it but doesn't inspect its contents. Zod says `items` is an array of `CourseItem` objects with specific fields — the application validates the structure inside the JSON. Drizzle says `createdAt` is a Postgres `timestamp`. Zod says it's an ISO 8601 string — the repository layer handles the conversion.

**The repository layer is the bridge** — it sits between the ORM queries and the validation schemas. It queries via the ORM (type-safe SQL), then parses results through the Zod schema before returning to the rest of the application. Both checks happen, each catching what the other can't.

**Parsing every row has a cost, so choose where.** Parse results where the database cannot vouch for the shape: a `jsonb` column it stores opaquely, or a table another service or script also writes. For plain typed columns your own migrations control, a schema-conformance test (see Testing Data Correctness below) proves the same thing once instead of on every read. Where the two schemas mostly agree, derive the validation schema from the table and override only the columns that differ, such as the `jsonb` structure. `createSelectSchema` and `createInsertSchema` do this for Drizzle: they ship in the separate `drizzle-zod` package on drizzle-orm 0.x and move to `drizzle-orm/zod` in Drizzle v1, so check the installed version. On Python, SQLModel declares one class that is both the SQLAlchemy table and the Pydantic model.

**Why not just one schema?** Some ORMs (Prisma) try to be the single source of truth for both database structure and application types. This works until your database representation and application representation genuinely differ — a `jsonb` column containing a validated nested structure, a timestamp stored as a Date but serialised as a string, a composite key split into separate application fields. Two schemas let each side describe what it actually cares about without forcing the other to compromise.

**Document databases (MongoDB, DynamoDB) have a smaller version of this problem.** There's no second query language to bridge — queries and results are plain objects. But the stored types still aren't JSON: MongoDB hands back BSON `ObjectId` and `Date` values where your API schema has strings, so the repository layer still converts. The ORM layer exists specifically because SQL databases speak a different language than your application code; for a document database, a validation schema plus that conversion usually does the job.

---

## Validation Boundaries

Validate data when it crosses a trust boundary:

| Boundary               | Example                           | Validation                                                            |
| ---------------------- | --------------------------------- | --------------------------------------------------------------------- |
| **External API → App** | Third-party response              | Parse through typed schema                                            |
| **User input → App**   | Form submission, API request body | Validate with schema                                                  |
| **File → App**         | CSV/JSON import                   | Validate each record                                                  |
| **App → Database**     | Insert/update                     | Schema ensures correct shape before write                             |
| **Database → App**     | Query result                      | Parse `jsonb` and shared tables; conformance-test the rest            |
| **Service → Service**  | RPC response, webhook             | Parse through boundary contract                                       |
| **Environment → App**  | Config / env vars                 | Parse through config schema (see [Configuration](./configuration.md)) |

**The principle:** Full validation at boundaries. Trust internally. The boundary is where untrusted becomes trusted.

---

## Established Patterns

### Separate Input and Output Schemas

The input schema lists only the fields a client may set. Server-owned fields, such as `id`, `createdAt`, the tenant id, a role or a price, belong to the output schema and are filled by the server. If they sit in the input schema, a client that sends them gets to choose them: that is mass assignment (OWASP API3:2023). Zod's `z.object` and Pydantic's default config both drop unknown keys, so leaving a field out of the input schema is enough, provided the parsed result, never the raw body, reaches the write. A schema derived from the table needs the same care: omit the server-owned columns from it.

### Discriminated Unions

For data that is one of several shapes, distinguished by a field, use Zod's `z.discriminatedUnion("type", [...])`, or in Pydantic a union with an explicit discriminator:

```python
# Pydantic 2
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, TypeAdapter

class ClickEvent(BaseModel):
    type: Literal["click"]
    x: int
    y: int

class KeypressEvent(BaseModel):
    type: Literal["keypress"]
    key: str

Event = Annotated[Union[ClickEvent, KeypressEvent], Field(discriminator="type")]
# The discriminator makes Pydantic pick the model from "type"; a bare Union tries every member

event = TypeAdapter(Event).validate_python(payload)  # or use Event as a field on a model
```

---

## Database-Level Integrity

Application-layer validation (Zod, Pydantic) protects the happy path. Database constraints protect everything else — direct queries, migration scripts, ETL pipelines, and bugs in application code all bypass your validation schemas.

### Enforce at Both Layers

| Constraint          | Application Layer                     | Database Layer                     |
| ------------------- | ------------------------------------- | ---------------------------------- |
| **Required fields** | Schema validation                     | `NOT NULL`                         |
| **Valid values**    | Enum/literal types                    | `CHECK` constraints                |
| **Relationships**   | Type references                       | `FOREIGN KEY` constraints          |
| **Uniqueness**      | Map the constraint violation to a 409 | `UNIQUE` constraints               |
| **Data format**     | String parsing, regex                 | `CHECK` with regex or domain types |

Application validation gives good error messages. Database constraints prevent bad data. Both are needed.

For uniqueness, don't pre-check with a `SELECT` before the `INSERT`: two requests can both pass the check and both insert. The `UNIQUE` constraint is the guard — insert, catch Postgres error `23505` (`unique_violation`), and map it to a 409 Conflict. Match the constraint name as well as the code, because a table's primary key and each unique constraint all raise `23505`. On Drizzle 0.44.4+ read both from the error's `cause` chain, because the driver error is wrapped in a `DrizzleQueryError`. Inside a larger transaction, catching the error is not enough: the failed statement aborts the transaction, and every later statement fails until it rolls back. There, use `INSERT … ON CONFLICT (tenant_id, email) DO NOTHING RETURNING` (Drizzle `.onConflictDoNothing({ target: [users.tenantId, users.email] })`), naming the target so other conflicts still raise, and treat no returned row as the conflict, or wrap the insert in a savepoint (a nested `tx.transaction()` in Drizzle, `session.begin_nested()` in SQLAlchemy). In a multi-tenant table, include the tenant column in the unique constraint, `UNIQUE (tenant_id, email)`, so one tenant's value never blocks or reveals another's, and lead with it so the index also serves tenant-scoped lookups.

**Adding a constraint to a table that already holds data** is a locking problem as much as a data one: add a foreign key, `CHECK` or `NOT NULL` as `NOT VALID` and validate it in a later deploy, and build a `UNIQUE` index concurrently first. The recipes are in [Schema Evolution](./schema-evolution.md#adding-constraints-to-existing-tables).

### Normalise at Ingest

String values that serve as categories or statuses must be normalised on entry — lowercase at insert — then checked against the set of valid values, which also rejects any case variant that slips through. For emails, where you usually keep the case the user typed, enforce case-insensitive uniqueness instead: a unique index on `lower(email)`, or the `citext` column type.

```sql
-- PostgreSQL
ALTER TABLE users ADD CONSTRAINT chk_role_valid
  CHECK (role IN ('member', 'admin'));

CREATE UNIQUE INDEX users_email_lower_key ON users (lower(email));
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

If your code throws between `BEGIN` and `COMMIT`, the database only rolls back on its own when the connection closes — and a pooled connection is never closed, just returned to the pool. The transaction stays open on that session, holding its locks (and, after a failed statement, rejecting every command) until something sends `ROLLBACK`, and the next request to borrow the connection inherits it. So roll back explicitly, or use a helper that does it on throw.

### In Application Code

**TypeScript (Drizzle):**

```typescript
// drizzle-orm 0.36+
import { eq, sql } from 'drizzle-orm';

await db.transaction(async (tx) => {
  await tx.update(accounts).set({ balance: sql`${accounts.balance} - ${amount}` }).where(eq(accounts.id, fromId));
  await tx.update(accounts).set({ balance: sql`${accounts.balance} + ${amount}` }).where(eq(accounts.id, toId));
});
// Commits when the callback resolves. If it throws, Drizzle sends ROLLBACK and re-throws,
// so the error still reaches your error hierarchy and the connection goes back to the pool clean.
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
- User signup (create user + create profile + queue the welcome email as an outbox row, below)

Single operations (one INSERT, one UPDATE) are already atomic — they don't need explicit transactions.

### Connection to Error Handling

Transactions connect directly to your error hierarchy (see [Error Handling](./error-handling.md)): if step 3 of 5 fails, the transaction rolls back steps 1-2 automatically. Your error handler then classifies the failure (was it a validation error? a constraint violation? a timeout?) and responds appropriately.

### Atomicity Is Not Isolation

A transaction makes its writes all-or-nothing; it does not stop two transactions interleaving. Postgres defaults to READ COMMITTED, where each statement sees whatever was committed before it began, so read-then-write logic still loses updates: two requests both read a balance of 100, both subtract 80, and both write 20. Concurrency Control below closes that gap. Nor does a transaction reach outside the database. An email sent, an HTTP call made or a message published inside it stays done when the transaction rolls back, and waiting on the call holds a connection and its locks open (see [Resilience](./resilience.md#idempotency)).

**The transactional outbox** answers "commit, then send". Write the message as a row in an outbox table inside the same transaction as the data change, and let a separate relay read committed rows, send them and mark them sent. The message then exists exactly when the change does. The relay can crash between sending and marking, so delivery is at-least-once and the receiver must tolerate a repeat.

### Concurrency Control

When the check and the write fit in one statement, put the check in the `WHERE` clause and read the row count:

```sql
-- PostgreSQL
UPDATE accounts SET balance = balance - 80
WHERE id = 123 AND balance >= 80;
-- 0 rows affected → insufficient funds; a concurrent withdrawal cannot overdraw
```

When logic must run between the read and the write, take a lock:

- **Optimistic locking:** keep a `version` column, write with `WHERE id = $1 AND version = $2`, and bump the version. Zero rows affected means someone else changed the row: re-read and retry, or return 409. It pays in retries, so it suits rare conflicts, which is most web apps.
- **Pessimistic locking:** `SELECT … FOR UPDATE` inside an explicit transaction, so other writers wait (in autocommit the lock ends with the statement). It pays in waiting, so it suits a hot row many requests update.

**Deadlocks** happen when two transactions each hold a lock the other needs. Postgres detects the cycle after `deadlock_timeout` (1s by default) and aborts one of them with SQLSTATE `40P01`. Taking locks in a consistent order, such as ascending id, makes deadlocks rarer but cannot rule them out, because foreign-key checks, unique-index inserts and lock upgrades take locks your code never ordered. So retry the whole transaction a bounded number of times on `40P01`, and on `40001` (serialization failure, raised at REPEATABLE READ and SERIALIZABLE). Retry the transaction, not the failed statement, which has already aborted it. [Testing → Concurrency and Race-Condition Tests](./testing.md#concurrency-and-race-condition-tests--does-the-guard-hold-when-two-callers-race) shows how to prove a guard holds.

### Transactions Behind a Pooler

Managed pooled endpoints (Neon's pooled connection string, Supabase's pooler, PgBouncer) usually run in transaction mode, where consecutive transactions from one client may land on different server connections. Session state breaks there: a session-level `SET`, a session advisory lock, `LISTEN`. A session `SET` of tenant context is worse than broken, because it can stay on the server connection for the next client's transaction to inherit, which is a cross-tenant leak. Use `SET LOCAL` (or `set_config(…, true)`) and `pg_advisory_xact_lock` inside a transaction, and the direct connection for `LISTEN`. See [Multi-Tenant Isolation](./multi-tenant-isolation.md#the-database-backstop) and the [Leaky Pooled Connection](./pitfalls.md#the-leaky-pooled-connection) pitfall.

---

## Strict Type Checking as Data Integrity

Strict compiler settings are a data integrity tool:

- **TypeScript:** `strict: true` in tsconfig (especially `strictNullChecks`). Without it, `null` and `undefined` flow silently through the entire codebase — the single biggest category of runtime crashes.
- **Python:** mypy with strict settings + type annotations on all function signatures.

Prefer enabling strict mode from day one. Retrofitting it onto an existing codebase is possible but painful — the volume of newly-surfaced errors scales with the amount of loose code already written, and fixes often cascade through call chains. The earlier you turn it on, the smaller the backlog.

---

## Testing Data Correctness

Zod and Pydantic only help if your schemas are correct and actually wired in — testing that `z.string().parse("hello")` works is testing the library, not your system. Four things are worth asserting, each mapping to a layer or boundary defined above:

- **Schema-to-reality alignment.** Parse real rows from the tables you own (and real responses from the APIs you consume) against your schema — a schema-conformance test that proves the schema matches what the store actually sends, not what you assume. This is also where lossy serialization hides (a value that parses but changes shape on the round trip through `jsonb` or timezone normalisation), which matters most at the repository-layer bridge, where the ORM and application representations deliberately differ.
- **Validation wiring.** A schema that is never called protects nothing. Drive an endpoint with an invalid payload and assert it is rejected at the boundary — a missing required field returns a 400, not a 500 or a silent insert. (The *shape* of that 400 — the RFC 9457 envelope and its field-level error array — is Error Handling's to verify.)
- **Transformation correctness.** Data enters valid but is reshaped at every stage (DB row → API → hook → component props), and each stage can mangle it — so test the stages that derive or aggregate, not the ones that just pass through.
- **Complex schema logic.** Any hand-written schema logic — a `.refine()`, a discriminated union, conditional validation — has branches that can be wrong, so assert both the accept and the reject case (the classic trap: a percentage discount must be 0–100 but a fixed discount may exceed 100).

These all lean on a real database rather than a mock — see [Testing](./testing.md) for the real-database test setup and the broader test craft.

---

## Anti-Patterns

| Don't                                       | Do Instead                                        | Why                                                                                                 |
| ------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Pass raw dicts/objects between functions    | Define schemas for data structures                | Raw objects have no contract — any function can put anything in them                                |
| Use `any` or `unknown` without parsing      | Parse through a schema, then use the typed result | `any` turns off all type safety — it's an escape hatch, not a strategy                              |
| Use loose strings for constrained values    | Use `z.enum()` / `Literal` types                  | Loose strings accept typos: `"actve"` instead of `"active"`                                         |
| Scatter validation throughout code          | Validate once at the boundary, trust internally   | Redundant validation clutters code and creates maintenance burden                                   |
| Skip validation for "trusted" internal data | Trust the model, validate at entry                | Internal data was external data once — the boundary is where trust is established                   |
| Store unvalidated external data             | Always parse through a schema first               | Garbage in, garbage out — but worse, garbage stored permanently                                     |
| Use TypeScript `as` type assertions         | Use `.parse()` — assertions skip validation       | `as User` tells the compiler to trust you; `.parse()` actually checks                               |
| Validate at the database layer only         | Validate at the application boundary too          | DB errors are cryptic ("constraint violation on column X") vs schema errors ("email must be valid") |
| Put server-owned fields (`id`, `createdAt`, tenant, role) in the input schema | Separate input and output schemas | A client that sends them gets to set them (mass assignment) |
| Pre-check uniqueness with a `SELECT` before inserting | Insert and map `23505` to 409; inside a transaction, `ON CONFLICT DO NOTHING` or a savepoint | Two requests both pass the check, and a caught error still aborts the surrounding transaction |
| Read, compute and write back with no guard | A conditional `UPDATE`, or optimistic or pessimistic locking | Under READ COMMITTED two read-then-write requests overwrite each other |
| Acquire locks in inconsistent order | Lock in a consistent order (e.g. by id), and retry the transaction on `40P01` and `40001` | Inconsistent ordering causes deadlocks, and ordering alone cannot prevent them all |
| Send an email or call an API inside a transaction | Write an outbox row in the transaction and send after commit | A rollback cannot unsend, and the open transaction holds its locks across the call |

---

## Deciding for Your Project

When starting a new project, decide these. Each line gives the default.

1. **Where are the trust boundaries?** Every request body, third-party response, webhook, file and env var is parsed at entry, and code inside trusts the typed result.
2. **Which schema library?** Zod on TypeScript, Pydantic on Python.
3. **Strict or coercing?** Coerce, with field-level `Strict` where a coerced value would be wrong (a quantity, an amount). Model-wide strict only with `model_validate_json`.
4. **Which database constraints?** `NOT NULL`, foreign keys and `UNIQUE` on every table from creation, plus `CHECK` for enumerated values. On a document store, which enforces less, application validation carries more of the weight.
5. **Which reads get parsed?** `jsonb` columns and tables other writers share; conformance-test the rest.
6. **How are concurrent writes guarded?** A conditional `UPDATE` first, optimistic locking where logic runs between the read and the write, pessimistic locking for a hot row, and a bounded transaction retry on `40001` and `40P01`.
7. **What follows a commit?** Anything sent outside the database goes through an outbox row, never from inside the transaction.

---

## Related Topics

- **When validation fails** — see [Error Handling](./error-handling.md) for how to structure error responses and classify validation errors
- **Validating configuration** — see [Configuration](./configuration.md) for treating env vars and settings as validated data
- **When schemas change over time** — see [Schema Evolution](./schema-evolution.md) for migrations, expand-and-contract, and adding constraints to tables that already hold data
- **Side effects around a transaction** — see [Resilience](./resilience.md) → Idempotency for keeping a provider call out of the transaction and making a repeated request safe
- **Tenant context per transaction** — see [Multi-Tenant Isolation](./multi-tenant-isolation.md) → The Database Backstop for confining the tenant setting to the transaction
- **Validation as security** — see [Security](./security.md) for the OWASP perspective on input validation as a defence against injection attacks
- **Testing data at every stage** — see [Testing](./testing.md) for schema-conformance tests, transformation tests, and the race tests that prove a concurrency guard holds
